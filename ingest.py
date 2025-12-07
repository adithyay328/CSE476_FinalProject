"""
As with core.py, now depracated. This
is too complex for the language model
we have to run. This is more appropriate for Opus 4.5
and Sonnet 4.5 inside of my projects, not whatever
local model they are running.
"""

## # Defines our ingest model,
## # which is responsible for ingesting the question,
## # calling into another agent to handle the question,
## # and then returning the final answer.
## from typing import List, Tuple
## import copy
## import subprocess as sp
## 
## from pydantic import BaseModel
## from RestrictedPython import compile_restricted, safe_builtins, utility_builtins, limited_builtins
## from RestrictedPython.PrintCollector import PrintCollector
## 
## from core import Agent, AgentState, ConvoMessage, make_tool, ToolCallRequest
## from loop import loop
## 
## # Define our first tool, which
## # allows the agent to answer
## class AnswerToolArgs(BaseModel):
##   answer : str
## 
## def answer_tool( state : "IngestAgentState", args: AnswerToolArgs) -> Tuple["IngestAgentState", str]:
##   """
##   This tool is to be called with
##   the answer to the question.
##   """
## 
##   # Set the answer, and indicate done
##   state.answer = args.answer
##   state.is_done = True
## 
##   return state, "Answer set, exexution complete."
## 
## answer_tool = make_tool( answer_tool, AnswerToolArgs )
## 
## class EmtpyArgs(BaseModel):
##   placeholder : str = ""
## 
## def read_code_tool( state : "IngestAgentState", args: EmtpyArgs) -> Tuple["IngestAgentState", str]:
##   """
##   This tool reads the source code
##   you have written so far and
##   returns it to you
##   """
##   return state, state.source_code
## 
## read_code_tool = make_tool( read_code_tool, EmtpyArgs )
## 
## class WriteCodeArgs(BaseModel):
##   code : str
## 
## def write_code_tool( state : "IngestAgentState", args: WriteCodeArgs) -> Tuple["IngestAgentState", str]:
##   """
##   This tool over-writes all the code
##   in the environment
##   """
##   state.source_code = args.code
##   return state, "Code written."
## 
## write_code_tool = make_tool( write_code_tool, WriteCodeArgs )
## 
## def execute_code_tool( state : "IngestAgentState", args: EmtpyArgs) -> Tuple["IngestAgentState", str]:
##   """
##   This tool executes the current
##   source code in the environment,
##   returning any output or errors.
## 
##   The result of the execution
##   must be stored in a variable
##   called 'result' in the code,
##   as this is what we will extract
##   """
##   if state.source_code.strip() == "":
##     return state, "Refusing to execute, code is empty. Please write code first."
## 
##   try:
##     # Prepare the restricted environment
##     restricted_globals = {
##       '__builtins__': safe_builtins,
##     }
##     restricted_globals['__builtins__'].update(utility_builtins)
##     restricted_globals['__builtins__'].update(limited_builtins)
## 
##     # Compile the code
##     byte_code = compile_restricted(state.source_code, filename='<inline code>', mode='exec')
## 
##     # Prepare local dictionary to capture output
##     restricted_locals = {}
## 
##     # Execute the code
##     exec(byte_code, restricted_globals, restricted_locals)
## 
##     if 'result' not in restricted_locals:
##       raise ValueError("The executed code did not define a 'result' variable Re-write the code.")
## 
##     result = restricted_locals.get('result', "No result variable defined.")
## 
##     return state, f"Code executed successfully. Result: {result}"
##   except Exception as e:
##     return state, f"Error during code execution: {str(e)}"
## 
## execute_code_tool = make_tool( execute_code_tool, EmtpyArgs )
## 
## _ingestTools = [
##   answer_tool,
##   read_code_tool,
##   write_code_tool,
##   execute_code_tool
## ]
## 
## class IngestAgentState(AgentState):
##   messages : List[ConvoMessage] = [
##     
##   ]
## 
##   is_done : bool = False
## 
##   # Question is here
##   question : str = ""
## 
##   # The answer is stored here
##   answer : str = ""
## 
##   # Python source code
##   # is in here
##   source_code : str = ""
## 
##   def get_agent(self):
##     return IngestAgent()
## 
## 
## class IngestAgent(Agent):
##   # We are default constructible,
##   # so that's fine.
## 
##   # Define our evolve function
##   def _evolve(self, state: IngestAgentState) -> IngestAgentState:
##     # Check that we are not done
##     if state.question == "":
##       raise ValueError("Question cannot be empty")
## 
##     if state.is_done:
##       raise ValueError("State is already done")
##     
##     # If the answer is populated, simply
##     # add that to the messages and mark done
##     if state.answer != "":
##       state.messages.append(
##         ConvoMessage(
##           role="assistant",
##           content="The final answer is: " + state.answer
##         )
##       )
## 
##       # False since we need to
##       # allow the next iteration
##       # to not error
##       state.is_done = False
##       return state
##     else:
##       # Create the system prompt
##       systemPrompt = ConvoMessage(
##         role="system",
##         content=f"""
##         You are a helpful agent that ingests a question and provides the final answer,
##         thinking about it step by step if needed.
## 
##         You only respond with tool calls. The formal schema for a tool call is:
##         {
##           ToolCallRequest.model_json_schema()
##         }
## 
##         The list of tool calls you have is:
##         {
##           [ m.tool_definition.model_dump_json() for m in _ingestTools ]
##         }
## 
##         You use the coding feature extensively for any non-trivial math, to avoid
##         simple errors and to take advantage of Python's determinism,
##         with a safe subset of the language being imported automatically.
##         You do not write any imports of your own as that will cause
##         a failure. You assume that the math, random and other safe
##         subsets of the standard library are available automatically,
##         with no external dependencies.
##         """
##       )
## 
##       # Also create the user prompt
##       userPrompt = ConvoMessage(
##         role="user",
##         content=f"""
##         Here is the question to answer:
##         {state.question}
## 
##         Please use the tools to provide the final answer.
##         """
##       )
## 
##       state = copy.deepcopy(state)
##       state.messages = [ systemPrompt, userPrompt ] + state.messages
## 
##       # In this case, just run loop
##       # and return that
##       nextState = loop(state)
##       nextState.is_done = False
## 
##       # Add the answer to the messages
##       if nextState.answer == "":
##         raise ValueError("After loop, answer is still empty")
##     
##       return nextState
## 
##   def get_tools(self):
##     return _ingestTools
## 
##   def prints_before_done_string(self):
##     return """
##     If you have the final answer, please use the Answer tool to provide it. Otherwise, keep working.
##     You are not allowed to respond before that
##     """
## 
##   def answer_question(self, question: str) -> str:
##     """
##     A helper function that ingests
##     a question and returns the answer
##     directly.
##     """
##     state = IngestAgentState(
##       question=question
##     )
## 
##     nextState = self.evolve(state)
## 
##     return nextState.answer
## 
## if __name__ == "__main__":
##   print("Testing ingest agent...")
##   agent = IngestAgent()
##   question = input("Enter a question to ingest: ")
##   answer = agent.answer_question( question )
##   print  ("Question:", question)
##   print  ("Answer:", answer)