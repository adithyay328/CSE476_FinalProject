# Solves all the problems in problems.txt using the solve.py module.
# We are gonna run this in parralel to make this a lot faster
import json
import threading
from queue import Queue
import os
import random
import time


import solve

test_data = "cse_476_final_project_test_data.json"
output = "cse_476_final_project_answers.json"

# Answers is just a map from
# index to answer
answers = {}

# We dump index + question onto
# one thread-safe queue,
# and then have a response thread
# that allows responses
queries = Queue()
responses = Queue()

def worker():
  while True:
    backoffSeconds = random.uniform(5, 10)
    solved = False
    item = queries.get()
    if item is None:
      break

    index, question = item

    while not solved:
      try:
        answer = solve.solve(question, n_paths=5)
        solved = True
      except:
        time.sleep(backoffSeconds)
        backoffSeconds = min(backoffSeconds * 1.5, 600)
        pass

    responses.put( (index, answer) )
    solved = True

with open(test_data, "r") as f:
  problems = json.load(f)

  # First, start up worker threads
  NUM_WORKERS = 100
  threads = []
  for i in range(NUM_WORKERS):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

  # Dump all the problems onto the queue
  for i, problem in enumerate(problems):
    question = problem["input"]
    queries.put( (i, question) )

  # Now, wait until we have
  # 1 answer for each problem
  num_problems = len(problems)
  while len(answers) < num_problems:
    starting_answers = len(answers)
    while not responses.empty():
      index, answer = responses.get()
      answers[index] = answer

    if len(answers) == starting_answers:
      time.sleep(1.5)
      continue

    # Report time
    print(f"Solved {len(answers)}/{num_problems} problems.")

    # Save to disk
    with open(output, "w") as f_out:
      output_data = []
      for i in range(num_problems):
        if i in answers:
          output_data.append({
            "output": answers[i]
          })
        else:
          output_data.append({
            "output": ""
          })
      json.dump(output_data, f_out, indent=2)

  # # Save the answers
  # with open(output, "w") as f_out:
  #   output_data = []
  #   for i in range(num_problems):
  #     output_data.append({
  #       "output": answers[i]
  #     })
  #   json.dump(output_data, f_out, indent=2)