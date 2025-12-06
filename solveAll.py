# Solves all the problems in problems.txt using the solve.py module
import json

import solve

test_data = "cse_476_final_project_test_data.json"
output = "cse_476_final_project_answers.json"

answers = []

with open(test_data, "r") as f:
  problems = json.load(f)

  for problem in problems:
    question = problem["input"]
    answer = solve.solve(question)
    answers.append({"output": answer})

    # Dump at every step
    with open(output, "w") as f:
      json.dump(answers, f, indent=2)