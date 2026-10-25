"""Settings, read from environment variables.

The values come from .env, passed into the app container by docker-compose.yml.
The defaults here are used when a variable is not set.
"""
import os


def env_bool(name, default):
    """Read a true/false setting: "true", "1", "yes" and "on" mean true (any case)."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes", "on")


# Where the model server is (inside Compose: the service name "ollama", not localhost)
BASE_URL = os.environ.get("LLM_BASE_URL", "http://ollama:11434/v1")

# Which model to talk to
MODEL = os.environ.get("LLM_MODEL", "qwen3:4b-q4_K_M")

# Max tokens the model sees at once. Only shown here: the Ollama server applies it
# (OLLAMA_CONTEXT_LENGTH), because the OpenAI-style API has no option for it.
CONTEXT_SIZE = int(os.environ.get("LLM_CONTEXT_SIZE", "4096"))

# Qwen3 "thinking": the model writes hidden reasoning before answering (slower)
THINKING = env_bool("LLM_THINKING", False)
