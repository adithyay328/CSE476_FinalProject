# Modified version of the CSE476
# model call file

import os
import requests

from core import AgentState

API_KEY  = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")  
MODEL    = os.getenv("MODEL_NAME", "bens_model")              

def rawCall(agentState : AgentState, temperature: float = 0.0, timeout: int = 60):
  url = f"{API_BASE}/chat/completions"
  headers = {
      "Authorization": f"Bearer {API_KEY}",
      "Content-Type":  "application/json",
  }

  messages = [
    msg.model_dump() for msg in agentState.messages
  ]
  payload = {
      "model": MODEL,
      "messages": messages,
      "temperature": temperature,
      "max_tokens": 128,
  }

  # Also get all tool definitions
  tool_definitions = []
  agent = agentState.get_agent()
  for tool in agent.get_tools():
    tool_definitions.append(tool.tool_definition.model_dump())

  payload["tools"] = tool_definitions

  resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
  return resp

# Try out a raw call
if __name__ == "__main__":
  from ingest import IngestAgentState
  from core import ConvoMessage

  state = IngestAgentState()

  # Add a system message
  state.messages.append(
    ConvoMessage(
      role="system",
      content="You are a helpful assistant."
    )
  )

  response = rawCall(state)
  print("Response status:", response.status_code)
  print("Response body:", response.text)