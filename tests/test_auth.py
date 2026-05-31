"""Tests for auth service — 🟡 LOW: minimal coverage, missing most test cases."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from auth import AuthService


def test_hash_password():
    """Tests password hashing."""
    svc = AuthService()
    h1 = svc.hash_password("hello123")
    h2 = svc.hash_password("hello123")
    assert h1 == h2, "Same password should produce same hash"


def test_verify_password():
    """Tests password verification."""
    svc = AuthService()
    h = svc.hash_password("mypass")
    assert svc.verify_password("mypass", h) is True
    assert svc.verify_password("wrong", h) is False


# 🟡 LOW: No test for:
#   - token generation / verification
#   - rate limiting / lockout
#   - race conditions
#   - refresh token flow
#   - revoked tokens
#   - edge cases (empty passwords, special chars, unicode)
#   - concurrent access
