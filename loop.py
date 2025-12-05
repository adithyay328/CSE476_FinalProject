# A general loop implementation.
# For most agents, this is all
# _evolve needs to do.
from core import AgentState, Agent, ConvoMessage
from model import rawCall

def loop( initial_state : AgentState ) -> AgentState:
  """
  A basic loop taht runs till
  the agent state is marked as done
  """

  state = initial_state

  while not state.is_done:
    agent = state.get_agent()

    # Get the next response from the API
    modelResp = rawCall( state )

    # If tool calls is an empty
    # list, add to the messages
    print("Model response:", modelResp.json())
    if modelResp.json()["choices"][0]["tool_calls"] == []:
      # If done is not set,
      # inject the help message
      if not modelResp.is_done:
        state.messages.append(
          ConvoMessage(
            role="assistant",
            content=agent.prints_before_done_string()
          )
        )
      else:
        # We're done, return that
        state.is_done = True
    else:
      raise NotImplementedError("Tool calls not yet implemented in loop, this is what the response contained: " + str(modelResp))

  return state