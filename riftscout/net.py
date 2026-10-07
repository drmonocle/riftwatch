"""
RiftScout Network Module
Handles secure HTTP requests, rate-limiting, host verification, and file downloads.
"""

import json
import logging
import time
import urllib.parse
import urllib.request
import webbrowser
from typing import Any, Callable, Dict, Optional

from . import config as C

log = logging.getLogger(__name__)


def is_allowed_host(url: str) -> bool:
    """Verify that a URL belongs to the approved host allowlist."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        if hostname in C.ALLOWED_HOSTS:
            return True
        # Allow subdomains of allowed hosts (e.g. *.githubusercontent.com)
        for allowed in C.ALLOWED_HOSTS:
            if hostname.endswith("." + allowed):
                return True
        return False
    except Exception:
        return False


def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = C.HTTP_TIMEOUT_DEFAULT,
    max_retries: int = C.HTTP_MAX_RETRIES,
) -> Optional[Dict[str, Any]]:
    """
    Fetch JSON payload from a remote endpoint with exponential backoff.
    """
    if not is_allowed_host(url):
        log.warning("Blocked request to unauthorized host: %s", url)
        return None

    req_headers = {
        "User-Agent": C.USER_AGENT,
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers)
    backoff = C.HTTP_BACKOFF_FACTOR

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    raw_data = resp.read().decode("utf-8", errors="replace")
                    return json.loads(raw_data)
                elif resp.status == 429:
                    log.warning("Rate limited on %s (attempt %d/%d)", url, attempt + 1, max_retries)
                    time.sleep(backoff * (attempt + 1))
                    continue
                else:
                    log.warning("HTTP %d received from %s", resp.status, url)
                    return None
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                log.warning("Rate limit HTTP 429 on %s, backing off...", url)
                time.sleep(backoff * (attempt + 1))
                continue
            if exc.code == 404 and "api.github.com" in url:
                log.debug("Release not published yet on %s", url)
            else:
                log.warning("HTTP error %d fetching %s: %s", exc.code, url, exc.reason)
            return None
        except Exception as exc:
            if attempt < max_retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            log.warning("Request failed fetching %s: %s", url, exc)
            return None

    return None


def download_file(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    timeout: float = C.HTTP_TIMEOUT_DOWNLOAD,
) -> bool:
    """
    Download a file from an allowed host to dest_path with progress updates.
    """
    if not is_allowed_host(url):
        log.warning("Blocked download from unauthorized host: %s", url)
        return False

    req = urllib.request.Request(url, headers={"User-Agent": C.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB chunks

            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
            return True
    except Exception as exc:
        log.error("Failed to download file from %s to %s: %s", url, dest_path, exc)
        return False


def open_in_browser(url: str) -> bool:
    """
    Safely open an external URL in the system's default browser.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme in ("http", "https") and is_allowed_host(url):
            webbrowser.open(url)
            return True
        log.warning("Refused to open untrusted or non-http browser URL: %s", url)
        return False
    except Exception as exc:
        log.error("Failed opening URL in browser: %s", exc)
        return False
