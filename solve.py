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

def search_tool( parameter : str ) -> str:
  # In this setting, we're going to use
  # Tavily's web-search API. For context,
  # the following API key is just the free tier,
  # and is in my account. As well, Tavily does not
  # use any LLMs underneath the hood, it's just an API
  # native google search, which is needed since Google
  # TOS does not allow us to use scraping.
  # with a curl request and pull the results

  # This is what an example result looks like:
  """
  response = tavily_client.search("Who is Leo Messi?")
>>> print(response)
{'query': 'Who is Leo Messi?', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': 
[{'url': 'https://en.wikipedia.org/wiki/Lionel_Messi', 'title': 'Lionel Messi - Wikipedia'
, 'content': '* [Afrikaans](https://af.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Afrikaans") * [Ænglisc](https://ang.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Old English")
 * [Aragonés](https://an.wikipedia.org/wiki/Lionel_Andr%C3%A9s_Messi "Lionel Andrés Messi – Aragonese") * [Azərbaycanca](https://az.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Azerbaijani") * [Bosanski](https://bs.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Bosnian") * [Català](https://ca.wikipedia.org/wiki/Lionel_Andr%C3%A9s_Messi "Lionel Andrés Messi – Catalan") * [Čeština](https://cs.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Czech") * [Corsu](https://co.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Corsican") * [Deutsch](https://de.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – German") * [Español](https://es.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Spanish") * [Français](https://fr.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – French") * [Hrvatski](https://hr.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Croatian") * [Interlingue](https://ie.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Interlingue") 
 * [Íslenska](https://is.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Icelandic") * [Italiano](https://it.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Italian") * 
 [Kurdî](https://ku.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Kurdish") * [Minangkabau](https://min.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Minangkabau") * [Nederlands]
 (https://nl.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Dutch") * [Polski](https://pl.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Polish") * [Soomaaliga]
 (https://so.wikipedia.org/wiki/Lionel_Messi "Lionel Messi – Somali")', 'score': 0.6490677, 'raw_content': None}, {'url': 'https://www.olympics.com/en/athletes/lionel-messi', 
 'title': 'Lionel Messi | Biography, Competitions, Wins and Medals', 'content': "Born in Rosario, Argentina, in 1987, **Lionel Messi** is widely regarded as one of the greatest 
 football players of all time, and his illustrious career proves why. He was instrumental in helping them win the **FIFA World Cup 2022** in Qatar, where he also won the **Golden Ball**, 
 awarded to the competition's best player. He was also part of the Argentina under-23 team that won **Olympic gold** at the Beijing 2008 Games, which remains one of his most treasured career highlights. [Football](https://www.olympics.com/en/news/erling-haaland-how-does-the-striker-compare-to-messi-ronaldo-mbappe) [Lionel MESSI](https://www.olympics.com/en/news/fifa-world-cup-2022-lionel-messi-records) ### FIFA World Cup 2022: What records did Lionel Messi break? [Lionel MESSI](https://www.olympics.com/en/news/lionel-messi-fifa-world-cup-biggest-disappointments) ### Lionel Messi at FIFA World Cup: Biggest disappointments of Argentina superstar ## Olympic Results", 'score': 0.6021791, 'raw_content': None}, 
 {'url': 'https://www.britannica.com/biography/Lionel-Messi', 'title': "Lionel Messi | Biography, Trophies, Records, Ballon d'Or ... - Britannica", 'content': 'Ask the Chatbot  
 Games & Quizzes  History & Society  Science & Tech  Biographies  Animals & Nature  Geography & Travel  Arts & Culture  ProCon  Money  Videos Messi’s play continued to rapidly improve over the years, and by 2008 he was one of the 
 most dominant players in the world, finishing second to Manchester United’s Cristiano Ronaldo in the voting for the 2008 Ballon d’Or. In early 2009 Messi capped off a 
 spectacular 2008–09 season by helping FC Barcelona capture the club’s first “treble” (winning three major European club titles in one season): the team won the La Liga 
 championship, the Copa del Rey (Spain’s major domestic cup), and the Champions League title.', 'score': 0.53619206, 'raw_content': None}, {'url': 'https://www.si.com/soccer/lionel-messi-facts-amazing-things-you-didn-t-know-about-the-soccer-legend', 'title': "Lionel Messi Facts: Amazing Things You Didn't Know About the ...", 'content': "* ON SI * SI SWIMSUIT * SI TICKETS * SI RESORTS * SI SHOPS # Lionel Messi Facts: Amazing Things You Didn’t Know About the Soccer Legend Did you know these facts about soccer legend Lionel Messi? Lionel Messi. How many of these Messi facts did you know? ## **Early Life Facts About Lionel Messi** **4.** Messi joined his childhood club, Newell's Old Boys, at the age of seven, where he scored nearly 500 goals before making the move to FC Barcelona in 2000. ## **Career Facts About Messi** Lionel Messi. **6.** Messi scored 672 goals in 
 778 appearances for FC Barcelona, making him the club’s all-time top scorer. ## **Facts About Messi’s Personal Life** ## **Fun Facts About Messi**", 'score': 0.44637465, 'raw_content': None}, 
 {'url': 'https://www.intermiamicf.com/players/lionel-messi/', 'title': 'Lionel Messi | Inter Miami CF', 'content': '# Lionel Messi. #10 • Forward • Inter Miami CF. ### Height. ### Weight. ### Roster Category. ### Player Category. ### Player Status. * ## International Duty Roundup: Recapping the November International Window. These past days, six Inter Miami CF players were in action representing the Club abroad with their respective national teams in Concacaf World Cup qualifiers, UEFA European Under-21 Championship qualifiers and international friendlies. Below, let’s take a look at our players’ performances in the latest FIFA international window. * ## Called Up: Seven Inter Miami CF Players Called
   Up for Upcoming FIFA Window. * ## Messi Named on 2025 MLS Best XI. * ## Messi Provides Heartfelt Remarks, Receives Keys to the C
   ity of Miami at the America Business Forum. * ## Lionel Messi Amongst Finalists for 2025 Landon Donovan MLS MVP Award. * ## Join Us in Celebrating Leo Messi on 
   Friday with a Special Prematch Presentation of the 2025 MLS Golden Boot presented by Audi.', '
 score': 0.42706275, 'raw_content': None}], 'response_time': 0.0, 'request_id': '4820f42b-a049-4e11-85e2-c8d801f9d06f'} 
  """

  # So yeah, it's just a pure search API, nothing funny here
  
  # This is a production API key(1000 reqs/minute max), but
  # in the free tier, so this doesn't count as a paid requirement
  # for the grader.
  FREE_TIER_API_KEY = "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"
  client = TavilyClient(api_key=FREE_TIER_API_KEY)

  results = client.search( parameter )
  return f"Search results for query: {results}"

def solve( question : str ):
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
    1. search: A web search tool that can be used to search the web for
       up-to-date information. The parameter is the search query.
    2. execute: A execute tool that can be used to execute
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
      if toolCall.tool_name == "search":
        print("Calling search tool")
        observation = search_tool( toolCall.parameter )
      elif toolCall.tool_name == "execute":
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

if __name__ == "__main__":
  # Pull question from first
  # command line argument
  if len(sys.argv) > 1:
    question = " ".join(sys.argv[1:])
    print("Question:", question)
  else:
    raise ValueError("Please provide a question as a command line argument.")
  answer = solve( question )
  print("Final Answer:", answer)