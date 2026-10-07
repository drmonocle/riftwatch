from riftscout import net


def test_fetch_allowlist():
    assert net.is_allowed_host("https://esports-api.lolesports.com/persisted/gw/getLive")
    assert net.is_allowed_host("https://lolworlds.com/api.ashx")
    assert not net.is_allowed_host("https://evil.com/x")
    assert not net.is_allowed_host("https://lolesports.com.evil.com/x")
    assert not net.is_allowed_host("file:///C:/Windows/win.ini")


def test_browser_allowlist():
    assert net.is_safe_browser_url("https://www.twitch.tv/lolworldchampionship")
    assert net.is_safe_browser_url("https://www.youtube.com/watch?v=abc")
    assert net.is_safe_browser_url("https://lolesports.com/schedule")
    assert not net.is_safe_browser_url("http://www.twitch.tv/x")       # https only
    assert not net.is_safe_browser_url("https://evil.com")
    assert not net.is_safe_browser_url("javascript:alert(1)")


def test_https_upgrade():
    assert net.https("http://static.lolesports.com/a.png") == "https://static.lolesports.com/a.png"
    assert net.https("") == ""


def test_blocked_fetch_returns_none():
    assert net.fetch_json("https://evil.com/data.json") is None
