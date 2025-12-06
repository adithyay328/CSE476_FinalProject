# Modified version of the CSE476
# model call file

import os
from typing import List

import requests

from core import ConvoMessage

API_KEY  = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")  
MODEL    = os.getenv("MODEL_NAME", "bens_model")              

def rawCall(messages : List[ConvoMessage], temperature: float = 0.0, timeout: int = 60, key=API_KEY, base=API_BASE, model=MODEL):
  url = f"{base}/chat/completions"
  headers = {
      "Authorization": f"Bearer {key}",
      "Content-Type":  "application/json",
  }

  messages = [
    msg.model_dump() for msg in messages
  ]

  payload = {
      "model": model,
      "messages": messages,
      "temperature": temperature,
      "max_tokens": 1024,
  }
  resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
  return resp