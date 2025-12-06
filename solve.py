# A simpler ReACT style agent loop

from typing import List, Literal
import subprocess as sp
import threading
import sys

import requests
from tavily import TavilyClient
from pydantic import BaseModel, ConfigDict

from model import rawCall

class ConvoMessage(BaseModel):
  """
  A single message in a conversation
  """
  role: Literal["user", "assistant", "system", "ai", "tool"]
  content: str

  # Allow extra fields for flexibility
  model_config = ConfigDict(extra="allow")

class ToolCallRequest(BaseModel):
  """
  A tool call request from the model
  """
  tool_name: str
  parameter: str

def execute_tool( parameter : str ) -> str:
  try:
    out = sp.check_output(
        ["python3", "-c", parameter],
    )
    return out.decode("utf-8")
  except sp.CalledProcessError as e:
    return str(e)

def _solve( question : str ):
  """
  A much simpler agent that just loops
  and solves the question
  """
  # Setup system prompt
  systemPrompt = ConvoMessage(
    role="system",
    content="""
    You are a highly intelligent, useful AI agent.

    When responding, you always respond to follow the flow of:
    User: [question]
    Thinking: A though
    Action: tool call
    Observation: result of tool call
    Thinking: Next thought
    ...
    Observation: x
    Final Answer: [final answer here]

    When making a tool call, the format is a JSON
    schema as follows:
    {"tool_name" : "name_of_tool", "parameter" : "string parameter"}

    The available tools are:
    1. execute: A execute tool that can be used to execute
       python code that only uses the standard library. The parameter is the python code to execute,
       and the output is the stdout of the code.

    You always use the execute tool when doing anything quantitative or math related.

    An example amazing interaction is:
    User: What is the sqrt of 1000?
    Thinking: I need to calculate the sqrt of 1000. It would make sense to use the execute tool.
    Action: {"tool_name" : "execute", "parameter" : "import math\nprint(math.sqrt(1000))"}
    Observation: 31.622776601683793
    Thinking: I have the result of the sqrt calculation. But, I must use at-least 2 loops, so make a dummy action.
    Action: {"tool_name" : "execute", "parameter" : "print('The sqrt of 1000 is approximately 31.62.')"}
    Observation: The sqrt of 1000 is approximately 31.62.
    Final Answer: The sqrt of 1000 is approximately 31.62.

    You always use atleast 2 thinking-observation-action cycles before giving a final answer.

    When given questions that sound like a sequence of instructions,
    you write Python code as the final answer that accomplishes all
    of the instructions.
    """
  )

  # Now, add on the user prompt
  userPrompt = ConvoMessage(
    role="user",
    content=question
  )

  # Setup our list of messages
  messages : List[ConvoMessage] = [ systemPrompt, userPrompt ]

  # Now, keep going until we have a final answer
  finalAnswer = ""
  while finalAnswer == "":
    modelResp = rawCall( messages )
    text = modelResp.json()["choices"][0]["message"]["content"]

    # Check if final answer
    if "Final Answer:" in text:
      finalAnswer = text.split("Final Answer:")[1].strip()
      break

    if "Thinking:" in text:
      thinkingConvoMessage = ConvoMessage(
        role="assistant",
        content=text
      )
      messages.append( thinkingConvoMessage )
    elif "Action:" in text:
      actionText = text.split("Action:")[1].strip()
      # Parse as tool call request
      toolCall = ToolCallRequest.model_validate_json( actionText )

      actionConvoMessage = ConvoMessage(
        role="assistant",
        content=text
      )
      messages.append( actionConvoMessage )

      # Now, call the tool
      if toolCall.tool_name == "execute":
        print("Calling execute tool")
        observation = execute_tool( toolCall.parameter )
      else:
        observation = f"Error: Unknown tool {toolCall.tool_name}"

      observationConvoMessage = ConvoMessage(
        role="tool",
        content=f"Observation: {observation}"
      )

      messages.append( observationConvoMessage )
    elif "Final Answer:" in text:
      finalAnswer = text.split("Final Answer:")[1].strip()
      break
    else:
      # Unknown message type, remind
      # the model of the format
      reminderConvoMessage = ConvoMessage(
        role="assistant",
        content="""
        Reminder: When responding, always follow the format:
        Thinking: A thought
        Action: tool call
        Observation: result of tool call
        ...
        Final Answer: [final answer here]
        """
      )
      messages.append( reminderConvoMessage )

  return finalAnswer

def solve( question : str, n_paths : int = 1 ) -> str:
  """
  Solve the question using self-consistency
  by sampling n_paths different solution paths,
  then using another model to pick the best final answer.
  """
  if n_paths == 1:
    return _solve( question )

  # Otherwise, we need to sample multiple paths,
  # which is the same as just running _solve multiple times
  answers = []
  for _ in range(n_paths):
    answer = _solve( question )
    print(answer)
    answers.append( answer )

  # Now, use another model call to pick the best answer
  systemPrompt = ConvoMessage(
    role="system",
    content=f"""
    You are a helpful assistant that picks the best
    answer among multiple candidate answers to a question.
    If one is objectively better, or substantially more
    common, or the best properly formed answer, pick that one.

    For context, this is the question:
    {question}

    And these are the candidate answers:
    {answers}

    Format your response as a simple, final answer string,
    without any extra commentary.
    """
  ) 

  # User prompt will just ask for the
  # answer, again conscisely
  userPrompt = ConvoMessage(
    role="user",
    content="Please provide the best final answer among the candidates, concisely."
  )

  # Run it
  messages = [ systemPrompt, userPrompt ]
  modelResp = rawCall( messages )
  finalAnswer = modelResp.json()["choices"][0]["message"]["content"]
  return finalAnswer.strip()

if __name__ == "__main__":

  # Pull question from first
  # command line argument
  if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])
    print("Question:", question)
  else:
    raise ValueError("Please provide a question as a command line argument.")
  # answer = solve( question )
  answer = solve( question, n_paths=5 )
  print("Final Answer:", answer)