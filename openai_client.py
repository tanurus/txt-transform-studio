import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("[DEBUG] OPENAI_API_KEY not set. Configure it before using process features.")
client = None

from config import PROMPT_PATH
import openai

if api_key:
    client = openai.OpenAI(api_key=api_key)


def is_configured() -> bool:
    return client is not None


def ask_chatgpt(text, model="gpt-4.1", system_prompt=None, temperature=None, top_p=None):
    if client is None:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")
    if system_prompt is None:
        with open(PROMPT_PATH, "r", encoding="utf-8") as pf:
            system_prompt = pf.read()
    import time

    t0 = time.time()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    }
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if top_p is not None:
        payload["top_p"] = float(top_p)
    resp = client.chat.completions.create(**payload)
    t1 = time.time()
    usage = resp.usage
    return resp.choices[0].message.content.strip(), {
        "model": model,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "response_time": round(t1 - t0, 2),
    }
