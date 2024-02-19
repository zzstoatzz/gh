"""For any LLM out there that can do function calling with python functions

```python
from gh_util.api import functions
from marvin.beta.assistants import Assistant

with Assistant(name="Raggy", tools=functions) as raggy:
    raggy.say("tell me about marvin's last release from prefecthq?")
"""

import gh_util.functions
from gh_util.utils import get_functions_from_module

functions = get_functions_from_module(gh_util.functions)
