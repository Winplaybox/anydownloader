"""Regression tests for SSRF/IP classification and DNS preflight behavior.

These tests deliberately mock DNS: they verify fail-closed handling without relying
on the machine's network or resolver configuration.
"""
import socket
from unittest.mock import patch

from backend.utils.security import is_ip_allowed, verify_public_dns_resolution


def _answer(address):
    return (socket.AF_INET6 if ":" in address else socket.AF_INET,
            socket.SOCK_STREAM, 6, "", (address, 443, 0, 0) if ":" in address else (address, 443))


def test_ip_allowlist_accepts_public_address():
    assert is_ip_allowed("8.8.8.8")


def test_ip_allowlist_rejects_private_and_special_addresses():
    for address in (
        "127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1",
        "169.254.169.254", "0.0.0.0", "::1", "fc00::1", "fe80::1",
        "224.0.0.1", "2001:db8::1", "not-an-ip",
    ):
        assert not is_ip_allowed(address), address


def test_dns_preflight_rejects_mixed_public_and_private_answers():
    answers = [_answer("8.8.8.8"), _answer("127.0.0.1")]
    with patch("backend.utils.security.socket.getaddrinfo", return_value=answers):
        assert not verify_public_dns_resolution("https://example.com/video")


def test_dns_preflight_accepts_only_public_answers():
    answers = [_answer("8.8.8.8"), _answer("1.1.1.1")]
    with patch("backend.utils.security.socket.getaddrinfo", return_value=answers):
        assert verify_public_dns_resolution("https://example.com/video")


def test_dns_preflight_rejects_empty_answer_set():
    with patch("backend.utils.security.socket.getaddrinfo", return_value=[]):
        assert not verify_public_dns_resolution("https://example.com/video")


def test_dns_preflight_fails_closed_on_resolver_error():
    with patch("backend.utils.security.socket.getaddrinfo", side_effect=socket.gaierror("resolver failure")):
        assert not verify_public_dns_resolution("https://example.com/video")


def test_dns_preflight_rejects_non_http_scheme():
    assert not verify_public_dns_resolution("file:///etc/passwd")
