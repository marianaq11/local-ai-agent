import requests

from config import MODELS


class ModelError(Exception):
    pass


def chat(model, messages, *, json_mode=False):
    if model not in MODELS:
        raise ValueError("Choose a supported local model.")
    payload = {"model": model, "messages": messages, "stream": False,
               "options": {"temperature": 0, "seed": 42, "num_ctx": 8192, "num_predict": 512}}
    if json_mode:
        payload["format"] = "json"
    try:
        with requests.Session() as session:
            session.trust_env = False  # Keep localhost traffic out of environment proxies.
            response = session.post("http://127.0.0.1:11434/api/chat", json=payload,
                                    timeout=(5, 180), allow_redirects=False)
            if response.status_code != 200:
                raise ModelError(f"Ollama returned HTTP {response.status_code}. Check ollama list.")
            content = response.json()["message"]["content"]
        if not isinstance(content, str) or not 0 < len(content) <= 8192:
            raise ModelError("Ollama returned invalid message content.")
        return content.strip()
    except requests.RequestException as error:
        raise ModelError("Ollama request failed. Check the local service and model.") from error
    except (ValueError, KeyError, TypeError, RecursionError) as error:
        raise ModelError("Ollama returned an invalid chat envelope.") from error
