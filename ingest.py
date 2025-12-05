# Defines our ingest model,
# which is responsible for ingesting the question,
# calling into another agent to handle the question,
# and then returning the final answer.
from typing import List, Tuple
import copy

from pydantic import BaseModel

from core import Agent, AgentState, ConvoMessage, make_tool, ToolCallRequest
from loop import loop

# Define our first tool, which
# allows the agent to answer
class AnswerToolArgs(BaseModel):
  answer : str

def answer_tool( state : "IngestAgentState", args: AnswerToolArgs) -> Tuple["IngestAgentState", str]:
  """
  This tool is to be called with
  the answer to the question.
  """

  # Set the answer, and indicate done
  state.answer = args.answer
  state.is_done = True

  return state, "Answer set, exexution complete."

answer_tool = make_tool( answer_tool, AnswerToolArgs )

_ingestTools = [
  answer_tool
]

class IngestAgentState(AgentState):
  messages : List[ConvoMessage] = [
    
  ]

  is_done : bool = False

  # Question is here
  question : str = ""

  # The answer is stored here
  answer : str = ""

  def get_agent(self):
    return IngestAgent()


class IngestAgent(Agent):
  # We are default constructible,
  # so that's fine.

  # Define our evolve function
  def _evolve(self, state: IngestAgentState) -> IngestAgentState:
    # Check that we are not done
    if state.question == "":
      raise ValueError("Question cannot be empty")

    if state.is_done:
      raise ValueError("State is already done")
    
    # If the answer is populated, simply
    # add that to the messages and mark done
    if state.answer != "":
      state.messages.append(
        ConvoMessage(
          role="assistant",
          content="The final answer is: " + state.answer
        )
      )

      # False since we need to
      # allow the next iteration
      # to not error
      state.is_done = False
      return state
    else:
      # Create the system prompt
      systemPrompt = ConvoMessage(
        role="system",
        content=f"""
        You are a helpful agent that ingests a question and provides the final answer.

        You only respond with tool calls. The formal schema for a tool call is:
        {
          ToolCallRequest.model_json_schema()
        }

        The list of tool calls you have is:
        {
          [ m.tool_definition.model_dump_json() for m in _ingestTools ]
        }
      
        """
      )

      # Also create the user prompt
      userPrompt = ConvoMessage(
        role="user",
        content=f"""
        Here is the question to answer:
        {state.question}

        Please use the tools to provide the final answer.
        """
      )

      state = copy.deepcopy(state)
      state.messages = [ systemPrompt, userPrompt ] + state.messages

      # In this case, just run loop
      # and return that
      nextState = loop(state)
      nextState.is_done = False

      # Add the answer to the messages
      if nextState.answer == "":
        raise ValueError("After loop, answer is still empty")
    
      return nextState

  def get_tools(self):
    return _ingestTools

  def prints_before_done_string(self):
    return """
    If you have the final answer, please use the Answer tool to provide it. Otherwise, keep working.
    You are not allowed to respond before that
    """

  def answer_question(self, question: str) -> str:
    """
    A helper function that ingests
    a question and returns the answer
    directly.
    """
    state = IngestAgentState(
      question=question
    )

    nextState = self.evolve(state)

    return nextState.answer

if __name__ == "__main__":
  print("Testing ingest agent...")
  agent = IngestAgent()
  question = "What is 2+2?"
  answer = agent.answer_question( question )
  print  ("Question:", question)
  print  ("Answer:", answer)