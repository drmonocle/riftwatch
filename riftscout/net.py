"""
RiftScout Network Module
Handles secure HTTP requests, rate-limiting, host verification, and file downloads.
"""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Callable, Dict, Optional

from . import config as C

log = logging.getLogger(__name__)


def _host_in(url: str, hosts: set, schemes=("https", "http")) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in schemes:
            return False
        hostname = (parsed.hostname or "").lower()
        return hostname in hosts or any(hostname.endswith("." + h) for h in hosts)
    except Exception:
        return False


def is_allowed_host(url: str) -> bool:
    """Verify that a URL belongs to the approved data-fetch allowlist."""
    return _host_in(url, C.ALLOWED_HOSTS)


def is_safe_browser_url(url: str) -> bool:
    """Only https links to known esports/stream sites may be opened in a browser."""
    return _host_in(url, C.BROWSER_HOSTS, schemes=("https",))


def https(url: str) -> str:
    """Upgrade http:// asset URLs (Riot still serves some logos as http) to https://."""
    if url and url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url or ""


def _open(url: str, headers: Optional[Dict[str, str]], timeout: float):
    req_headers = {"User-Agent": C.USER_AGENT}
    if headers:
        req_headers.update(headers)
    return urllib.request.urlopen(urllib.request.Request(url, headers=req_headers), timeout=timeout)


def fetch_bytes(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = C.HTTP_TIMEOUT_DEFAULT,
    max_retries: int = C.HTTP_MAX_RETRIES,
    max_bytes: int = C.HTTP_MAX_JSON_BYTES,
) -> Optional[bytes]:
    """Fetch raw bytes from an allowed host with retry/backoff and a size cap."""
    if not is_allowed_host(url):
        log.warning("Blocked request to unauthorized host: %s", url)
        return None

    for attempt in range(max_retries):
        try:
            with _open(url, headers, timeout) as resp:
                data = resp.read(max_bytes + 1)
                if len(data) > max_bytes:
                    log.warning("Response from %s exceeded %d bytes; discarded", url, max_bytes)
                    return None
                return data
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                time.sleep(C.HTTP_BACKOFF_FACTOR * (attempt + 1))
                continue
            if exc.code == 404 and "api.github.com" in url:
                log.debug("Release not published yet on %s", url)
            else:
                log.warning("HTTP error %d fetching %s: %s", exc.code, url, exc.reason)
            return None
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(C.HTTP_BACKOFF_FACTOR * (attempt + 1))
                continue
            log.warning("Request failed fetching %s: %s", url, exc)
            return None
    return None


def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = C.HTTP_TIMEOUT_DEFAULT,
    max_retries: int = C.HTTP_MAX_RETRIES,
) -> Optional[Any]:
    """Fetch and decode a JSON payload. Returns None on any failure."""
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    raw = fetch_bytes(url, headers=h, timeout=timeout, max_retries=max_retries)
    if raw is None:
        return None
    if not raw.strip():  # e.g. livestats for a game the feed doesn't cover
        log.debug("Empty response from %s", url)
        return None
    try:
        return json.loads(raw.decode("utf-8", errors="replace"))
    except ValueError as exc:
        log.warning("Invalid JSON from %s: %s", url, exc)
        return None


def download_file(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    timeout: float = C.HTTP_TIMEOUT_DOWNLOAD,
) -> bool:
    """Download a file from an allowed host to dest_path with progress updates."""
    if not is_allowed_host(url):
        log.warning("Blocked download from unauthorized host: %s", url)
        return False
    try:
        with _open(url, None, timeout) as resp:
            # GitHub redirects to a CDN; re-validate the final host.
            if not is_allowed_host(resp.geturl()):
                log.warning("Download redirected to unauthorized host: %s", resp.geturl())
                return False
            total_size = int(resp.headers.get("Content-Length", 0) or 0)
            downloaded = 0
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        return True
    except Exception as exc:
        log.error("Failed to download %s to %s: %s", url, dest_path, exc)
        return False


def open_in_browser(url: str) -> bool:
    """Open an external URL in the default browser if it is on the allowlist."""
    if not is_safe_browser_url(url):
        log.warning("Refused to open untrusted browser URL: %s", url)
        return False
    try:
        webbrowser.open(url)
        return True
    except Exception as exc:
        log.error("Failed opening URL in browser: %s", exc)
        return False
