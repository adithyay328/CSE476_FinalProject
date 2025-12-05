"""
This module defines the core functionality and
design of our Agents.

Fundamentally, I want every agent to really just be
a map from a state -> state, where a state contains
data akin to the way that a stack frame
stores the data for a function call.

A primary reason this is attractive is since, in my own
programs, we want to be able to serialize and deserialize
the state of an agent at any point in time. By making
the agent a pure function from state to state, this
is trivial.
"""
from abc import ABC, abstractmethod
from typing import List, Literal, Callable, TypeVar, Type, Any, Tuple

from pydantic import BaseModel, ConfigDict, Field

class ConvoMessage(BaseModel):
  """
  A single message in a conversation
  """
  role: Literal["user", "assistant", "system", "ai", "tool"]
  content: str

  # Allow extra fields for flexibility
  model_config = ConfigDict(extra="allow")

# Now, we define the agent
# state. This is the data that the agent
# will operate on and return
class AgentState(BaseModel, ABC):
  messages : List[ConvoMessage] = []
  is_done : bool = False

  # This must return an instance
  # of the agent class responsible
  # for mapping this state to the next state.
  @abstractmethod
  def get_agent(self) -> "Agent":
    pass

# Now, the basics of the agent itself
class Agent(ABC):
  """
  Fudnamentally, an agent can do
  whatever it wants, THE ONLY
  constraint is that it must
  be able to map an AgentState
  to a new agent state, with
  no params but the state itself.
  This makes them super simple to
  work with
  """
  @abstractmethod
  def _evolve(self, state: AgentState) -> AgentState:
    pass

  def evolve(self, state: AgentState) -> AgentState:
    """
    Evolves the agent from one state to the next
    """
    nextState = state.get_agent()._evolve(state)
    if not isinstance(nextState, AgentState):
      raise ValueError("Evolved state must be an instance of AgentState")

    if nextState.is_done:
      raise ValueError("Evolved state cannot be marked as done, this prevents the agent from continuing")

    return nextState

  @abstractmethod
  def get_tools(self):
    # Return a list of all tool
    # functiosn we can use
    pass

  @abstractmethod
  def prints_before_done_string(self) -> str:
    """
    This string will be fed into
    the messages if the agent
    tries to make a assistant
    message before marking done.
    """
    pass

# Now, we just need one more thing,
# which is a "Tool". The biggest
# problem with tools is that they
# need to have a JSON serializable
# dict compatible with the OpenAI spec(everyone
# else also uses this spec for tools).
# so I'll define a validation bit

# Better yet; this function
# "makes" a tool from a function callable.
# This is inspired by Langchain's tool
# calling business.

# One important thing here is that we want
# to take the tool call, and wrap it so that
# it can take a tool call request from the model,
# and directly turn it into the right convo message
# to inject right after

class ToolCallRequestFunctionBody(BaseModel):
  name : str
  arguments : dict

class ToolCallRequest(BaseModel):
  """
  Every API more or less
  uses this tool call
  request format
  """
  id : str
  type : Literal["tool"]
  function : ToolCallRequestFunctionBody

class ToolResponseContentBody(BaseModel):
  value : Any
  success : bool

  # Allow extra fields for flexibility
  model_config = ConfigDict(extra="allow")

class ToolResponse(ConvoMessage):
  role : Literal["tool"] = "tool"
  tool_call_id : str
  content : ToolResponseContentBody

class ToolInnerDefinition(BaseModel):
  name : str
  description : str
  parameters : dict

class ToolDefinition(BaseModel):
  type : Literal["function"] = "function"
  function : ToolInnerDefinition

T = TypeVar("T")
def make_tool(f: Callable[[AgentState, T], Tuple[AgentState, str]], jsonSchema : Type[T]):
  """
  Turns an ordinary function into a tool call.

  Internally, every tool must take in
  an AgentState and a typed argument, with
  the return being a new AgentState and
  a typed return value. This passing in
  of AgentStates makes it very easy to do things
  like allowing the model to print things out,
  or mutate the state in other ways.

  What we will do is wrap this function up, handling
  the parsing of the ToolCallRequest and the
  construction of the ToolResponse for you.
  """
  def tool_wrapper(state : AgentState, toolCallRequest : ToolCallRequest) -> Tuple[AgentState, ToolResponse]:
    # First, parse the arguments
    parsedArgs = jsonSchema.model_validate(toolCallRequest.function.arguments)

    # Now, call the function
    newState, returnValue = f(state, parsedArgs)

    # Now, make the tool response
    toolResponse = ToolResponse(
      tool_call_id = toolCallRequest.id,
      content = ToolResponseContentBody(
        value = returnValue,
        success = True
      )
    )

    # Add the tool response to the state messages
    newState.messages.append(toolResponse)

    return newState, toolResponse

  # An important thing
  # we need is to make the tool's
  # definition JSON be available. We
  # define this as an attribute
  # of the function, called tool_definition
  toolName = f.__name__
  toolDescription = f.__doc__ or "No description provided"
  toolParameters = jsonSchema.model_json_schema()

  # Build the tool definition
  toolInnerDefn = ToolInnerDefinition(
    name = toolName,
    description = toolDescription,
    parameters = toolParameters
  )
  toolDefn = ToolDefinition(
    function = toolInnerDefn
  )

  tool_wrapper.tool_definition = toolDefn

  # Also over-write the tool wrapper's
  # name with the function name
  tool_wrapper.__name__ = toolName

  return tool_wrapper

# An example; a tool to talk
# to the user!
class TalkToUserArgs(BaseModel):
  message : str

def talk_to_user_tool(state: AgentState, args: TalkToUserArgs) -> Tuple[AgentState, str]:
  # Since the outer wrapper
  # already handles addingg us
  # to the messages, we just
  # need to print and return the current
  # state
  print(f"AI: {args.message}")
  return state, "Message sent to user"

talk_to_user_tool = make_tool(talk_to_user_tool, TalkToUserArgs)