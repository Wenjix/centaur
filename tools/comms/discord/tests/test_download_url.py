from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from client import DiscordClient


class _FakeStream:
    def __init__(self, chunks=(b"data",)):
        self.status_code = 200
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def iter_bytes(self):
        yield from self._chunks


class _FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def stream(self, _method, _url):
        return _FakeStream()


_CDN_URL = "https://cdn.discordapp.com/attachments/1/2/file.txt"


def test_download_url_writes_attachment(tmp_path, monkeypatch):
    monkeypatch.setattr("client.httpx.Client", _FakeClient)
    out_dir = tmp_path / "out"

    result = DiscordClient().download_url(
        _CDN_URL, output_dir=str(out_dir), filename="file.txt"
    )

    assert (out_dir / "file.txt").read_bytes() == b"data"
    assert result["path"] == str(out_dir / "file.txt")


def test_download_url_rejects_foreign_hosts(tmp_path):
    with pytest.raises(ValueError):
        DiscordClient().download_url(
            "https://evil.example.com/file.txt", output_dir=str(tmp_path)
        )


def test_download_url_refuses_symlink_destination(tmp_path, monkeypatch):
    if not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("O_NOFOLLOW unavailable on this platform")
    monkeypatch.setattr("client.httpx.Client", _FakeClient)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"keep me")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "file.txt").symlink_to(outside)

    with pytest.raises(OSError):
        DiscordClient().download_url(
            _CDN_URL, output_dir=str(out_dir), filename="file.txt"
        )

    assert outside.read_bytes() == b"keep me"
