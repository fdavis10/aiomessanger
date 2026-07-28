from __future__ import annotations

import base64
import os

import pytest


@pytest.fixture
def encryption_key(settings):
    """Fresh random master key per test that uses encryption."""
    key = base64.b64encode(os.urandom(32)).decode()
    settings.MESSAGE_ENCRYPTION_KEY = key
    return key
