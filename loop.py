"""
Also commenting this out, deprecated
"""

# # A general loop implementation.
# # For most agents, this is all
# # _evolve needs to do.
# from core import AgentState, Agent, ConvoMessage, ToolCallRequest
# from model import rawCall
# 
# def loop( initial_state : AgentState ) -> AgentState:
#   """
#   A basic loop that runs till
#   the agent state is marked as done. We
#   mandate that all text out is a tool call
#   """
#   state = initial_state
# 
#   while not state.is_done:
#     agent = state.get_agent()
# 
#     # Get the next response from the API
#     try:
#       modelResp = rawCall( state )
#     except Exception as e:
#       raise ValueError("Error calling model: " + str(e))
# 
#     try:
#       # If tool calls is an empty
#       # list, add to the messages
#       text = modelResp.json()["choices"][0]["message"]["content"]
#       # print("Model response:", text)
#     except Exception as e:
#       print("Failed to parse model response as JSON:", str(e))
#       # Failed to parse as JSON,
#       # add that to the messages
#       state.messages.append(
#         ConvoMessage(
#           role="assistant",
#             content=f"Error calling model: {str(e)}. Be careful and ensure all responses are valid tool call JSONs."
#         )
#       )
#       # PROBLEM; our end is causing the prompt
#       # to eventually not be valid. We are dumping
#       # in junk somewhere
#       # print("Model response:", modelResp.text)
#       continue
#     
#     # As per our new rule,
#     # all responses must be tool calls
#     try:
#       toolCall = ToolCallRequest.model_validate_json( text )
#       # Call the tool
#       toolName = toolCall.function.name
#       print("Calling tool:", toolName)
#       toolFunc = [ t for t in agent.get_tools() if t.__name__ == toolName ]
#       if len(toolFunc) == 0:
#         raise ValueError("No tool found with name: " + toolName)
#       elif len(toolFunc) > 1:
#         raise ValueError("Multiple tools found with name: " + toolName)
# 
#       toolResult = toolFunc[0]( state, toolCall )
# 
#       state = toolResult[0]
#       result = toolResult[1]
# 
#       # Add the tool call request and result to the messages
#       state.messages.append(
#         ConvoMessage(
#           role="assistant",
#           content=toolCall.model_dump_json()
#         )
#       )
# 
#       state.messages.append(
#         ConvoMessage(
#           role="tool",
#           content=result.model_dump_json()
#         )
#       )
#     except Exception as e:
#       # If we failed to parse as a tool call,
#       # just add the error message
#       state.messages.append(
#         ConvoMessage(
#           role="assistant",
#           content=f"""Error parsing, invalid tool call: {str(e)}. All responses must be tool calls JSONs"""
#         )
#       )
# 
#   return state