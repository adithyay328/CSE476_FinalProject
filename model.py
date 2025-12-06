# Modified version of the CSE476
# model call file

import os
from typing import List

import requests

from core import ConvoMessage

API_KEY  = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")  
MODEL    = os.getenv("MODEL_NAME", "bens_model")              

def rawCall(messages : List[ConvoMessage], temperature: float = 0.0, timeout: int = 60):
  url = f"{API_BASE}/chat/completions"
  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type":  "application/json",
  }

  messages = [
    msg.model_dump() for msg in messages
  ]

  payload = {
      "model": MODEL,
      "messages": messages,
      "temperature": temperature,
      "max_tokens": 5000,
  }
  resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
  return resp