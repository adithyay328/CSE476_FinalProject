# Defines our ingest model,
# which is responsible for ingesting the question,
# calling into another agent to handle the question,
# and then returning the final answer.
from typing import List, Tuple

from pydantic import BaseModel

from core import Agent, AgentState, ConvoMessage, make_tool
from loop import loop

class IngestAgentState(AgentState):
  messages : List[ConvoMessage] = [
    ConvoMessage(
      role="system",
      content="You are a helpful agent that ingests a question and provides the final answer."
    )
  ]

  is_done : bool = False

  # Question is here
  question : str = ""

  # The answer is stored here
  answer : str = ""

  def get_agent(self):
    return IngestAgent()

# Define our first tool, which
# allows the agent to answer
class AnswerToolArgs(BaseModel):
  answer : str

def _answer_tool( state : IngestAgentState, args: AnswerToolArgs) -> Tuple[IngestAgentState, str]:
  # Set the answer, and indicate done
  state.answer = args.answer
  state.is_done = True

  return state, "Answer set, exexution complete."

answer_tool = make_tool( _answer_tool, AnswerToolArgs )

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
      # In this case, just run loop
      # and return that
      nextState = loop(state)
      nextState.is_done = False

      # Add the answer to the messages
      if nextState.answer == "":
        raise ValueError("After loop, answer is still empty")
    
      nextState.messages.append(
        ConvoMessage(
          role="assistant",
          content="The final answer is: " + nextState.answer
        )
      )

      return nextState

  def get_tools(self):
    return [answer_tool]

  def prints_before_done_string(self):
    return """
    If you have the final answer, please use the Answer tool to provide it. Otherwise, keep working.
    You are not allowed to respond before that
    """

if __name__ == "__main__":
  # Simple test
  state = IngestAgentState(
    question="What is the capital of France?"
  )

  # Get the next state
  agent = state.get_agent()
  nextState = agent._evolve(state)

  # Print the answer
  print(nextState.answer)