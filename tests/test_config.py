"""Settings come from environment variables, with defaults when they are not set."""
import importlib

import pytest

import config


@pytest.fixture
def reload_config():
    """config reads the environment once, when it is imported. To test other values,
    change the environment, then reload the module. Afterwards, reload it again so the
    other tests see the real settings."""
    yield lambda: importlib.reload(config)
    importlib.reload(config)


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on", " On "])
def test_env_bool_true(monkeypatch, value):
    monkeypatch.setenv("X", value)
    assert config.env_bool("X", False) is True


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "", "maybe"])
def test_env_bool_false(monkeypatch, value):
    monkeypatch.setenv("X", value)
    assert config.env_bool("X", True) is False


def test_env_bool_not_set_uses_default(monkeypatch):
    monkeypatch.delenv("X", raising=False)
    assert config.env_bool("X", True) is True
    assert config.env_bool("X", False) is False


def test_defaults_without_env(monkeypatch, reload_config):
    # Compose passes LLM_* variables into the container: remove them for this test
    for name in ["LLM_BASE_URL", "LLM_MODEL", "LLM_CONTEXT_SIZE", "LLM_THINKING",
                 "LLM_SYSTEM", "LLM_TRACE"]:
        monkeypatch.delenv(name, raising=False)
    c = reload_config()
    assert c.BASE_URL == "http://ollama:11434/v1"  # the Compose service name, not localhost
    assert c.MODEL == "qwen3:4b-q4_K_M"           # not plain qwen3:4b (see CLAUDE.md)
    assert c.CONTEXT_SIZE == 4096
    assert c.THINKING is False                    # thinking off by default
    assert c.SYSTEM == ""
    assert c.TRACE is True


def test_values_from_env(monkeypatch, reload_config):
    monkeypatch.setenv("LLM_MODEL", "qwen3:1.7b")
    monkeypatch.setenv("LLM_CONTEXT_SIZE", "8192")
    monkeypatch.setenv("LLM_THINKING", "true")
    c = reload_config()
    assert c.MODEL == "qwen3:1.7b"
    assert c.CONTEXT_SIZE == 8192  # a number, not the text "8192"
    assert c.THINKING is True
