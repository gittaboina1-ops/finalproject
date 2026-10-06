import base64
import json
import os
import requests
from typing import Any, Dict, List, Optional, Union

# ============================================================
# .ENV FILE LOADER
# ============================================================

def load_env_file():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(root_dir, ".env"),
        ".env",
        os.path.join(root_dir, "LPITUTOR", ".env")
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")
                            if key:
                                os.environ[key] = value
            except Exception:
                pass

load_env_file()

# OpenRouter is the single LLM provider used by the application.
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")


# ============================================================
# OPENROUTER LLM GENERATOR (DIRECT HTTP POST REQUEST VIA REQUESTS)
# ============================================================

def generate_openrouter_response(
    prompt: str,
    multimodal_payload: Optional[Union[List[Any], Dict[str, Any]]] = None,
    multimodal_context: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> str:
    """
    Generates tutor response using OpenRouter's direct HTTP Chat Completions API.
    Reads OPENROUTER_API_KEY, OPENROUTER_BASE_URL, and OPENROUTER_MODEL from environment.
    """
    if not api_key:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        return (
            "### ⚠️ PragTutor OpenRouter Notice\n\n"
            "No active OpenRouter API key detected in your environment or `.env` file.\n"
            "The backend has successfully processed your course material, identified the topic, checked prerequisites, and constructed the dynamic prompt.\n\n"
            "**To connect PragTutor to live OpenRouter AI:**\n\n"
            "Add your key to the `.env` file in your project directory:\n\n"
            "```env\n"
            "OPENROUTER_API_KEY=\"your_openrouter_api_key\"\n"
            "OPENROUTER_BASE_URL=\"https://openrouter.ai/api/v1\"\n"
            "OPENROUTER_MODEL=\"openai/gpt-4o-mini\"\n"
            "```\n"
        )

    base_url = os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL).rstrip("/")
    if not model_name:
        model_name = os.environ.get("OPENROUTER_MODEL", "").strip()

    if not model_name:
        return "[OpenRouter LLM Error]: OPENROUTER_MODEL environment variable is not set."

    url = f"{base_url}/chat/completions"

    if multimodal_payload and isinstance(multimodal_payload, list):
        messages = multimodal_payload
    elif multimodal_context and multimodal_context.get("has_images"):
        content_blocks = [{"type": "text", "text": prompt}]
        image_payloads = multimodal_context.get("llm_image_payloads", [])
        content_blocks.extend(image_payloads)
        messages = [{"role": "user", "content": content_blocks}]
    else:
        messages = [{"role": "user", "content": prompt}]

    max_tokens_val = int(os.environ.get("OPENROUTER_MAX_TOKENS", 1000))
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens_val
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://pragtutor.edu",
        "X-Title": "PragTutor EdTech"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            try:
                err_json = response.json()
                err_msg = err_json.get("error", {}).get("message") or response.text
            except Exception:
                err_msg = response.text or f"HTTP Status {response.status_code}"
            return f"[OpenRouter LLM Error HTTP {response.status_code}]: {err_msg}"

        res_json = response.json()
        choices = res_json.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            if content:
                return content
            return "[OpenRouter API]: Returned empty answer content."
        return "[OpenRouter API]: Returned empty response structure (no choices)."

    except requests.exceptions.Timeout:
        return "[OpenRouter LLM Error]: Request timed out after 60 seconds."
    except requests.exceptions.ConnectionError as conn_err:
        return f"[OpenRouter LLM Error]: Connection failed ({conn_err})"
    except requests.exceptions.HTTPError as http_err:
        return f"[OpenRouter LLM Error]: HTTP error ({http_err})"
    except json.JSONDecodeError:
        return "[OpenRouter LLM Error]: Failed to parse JSON response from server."
    except Exception as err:
        return f"[OpenRouter LLM Error]: {err}"


# ============================================================
# UNIFIED GENERATE RESPONSE
# ============================================================

def generate_response(
    prompt: str,
    multimodal_payload: Optional[Any] = None,
    multimodal_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates tutor response using OpenRouter direct HTTP request as sole LLM provider.
    """
    return generate_openrouter_response(
        prompt=prompt,
        multimodal_payload=multimodal_payload,
        multimodal_context=multimodal_context
    )


# ============================================================
# TEST FUNCTION
# ============================================================

def test_llm():
    test_prompt = """
You are a helpful Operating Systems tutor.
Explain the concept of a process in simple language.
Give:
1. Definition
2. Simple explanation
3. Example
"""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model_name = os.environ.get("OPENROUTER_MODEL", "")
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else ("Set" if api_key else "None")
    print("=" * 80)
    print("TESTING PRAGTUTOR OPENROUTER LLM SERVICE (DIRECT HTTP REQUEST)")
    print(f"Active Provider : OpenRouter Direct HTTP (requests)")
    print(f"Base URL        : {OPENROUTER_BASE_URL}")
    print(f"Model Configured: {model_name}")
    print(f"API Key Status  : {masked_key}")
    print("=" * 80)

    res = generate_response(test_prompt)
    print(res)


if __name__ == "__main__":
    test_llm()