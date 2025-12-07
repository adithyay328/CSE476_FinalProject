# Hello!

To run this codebase, I personally reccomend using uv, which is an industry standard Python package manager that also automatically maintains the correct Python version + libraries at the same time. In the case that you get uv(the reccomended way is on the website, but if you want it fast just run pip/pip3 install uv). Then, run "uv run solve.py What is the biggest school in Arizona" to have it answer a single question. To do full computation, do uv run solveAll.py, which hits the backend server with a multi-threaded pool to populate the JSON as fast as possible.

If uv is not going to be used, simply install everything in pyproject.toml, and this should run just fine 

# Inference time techniques used:
- Self-consistency sampling, using n=5 rollouts by default
- LLM as Judge, where another model extracts the answer from the initial 5 rollouts with its own decision making process
- ReACT prompting, to force it to follow a loop better than a single prompt
- Few shot prompting, giving it an example of a few ReACT loops in the prompt to help out
- Tool calling, especially giving it the ability to execute code to do analysis.

# Deprecated modules
Ignore everything in the codebase but solve.py, model.py, and solveAll.py. The other .py files are from an older iteration of my approach, but made the assumption we would have tool calling support, which ended up not being the case(mainly structured output parsers).