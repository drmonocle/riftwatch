"""
Unit tests for RiftScout networking and host security allowlist.
"""

from riftscout.net import is_allowed_host


def test_allowed_hosts():
    assert is_allowed_host("https://esports-api.lolesports.com/persisted/gw/getSchedule") is True
    assert is_allowed_host("http://static.lolesports.com/teams/t1.png") is True
    assert is_allowed_host("https://lol.fandom.com/api.php") is True
    assert is_allowed_host("https://lolworlds.com/api.ashx") is True
    assert is_allowed_host("https://api.github.com/repos/drmonocle/rift-scout") is True
    assert is_allowed_host("https://objects.githubusercontent.com/download/RiftScout.exe") is True


def test_blocked_hosts():
    assert is_allowed_host("https://malicious-site.com/payload.exe") is False
    assert is_allowed_host("http://evil-tracker.io/ping") is False
    assert is_allowed_host("file:///C:/Windows/System32/cmd.exe") is False
    assert is_allowed_host("ftp://insecure.org") is False
