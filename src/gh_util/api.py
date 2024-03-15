"""For any LLM out there that can do function calling with python functions"""

import gh_util.functions
from gh_util.utilities.inspect import get_functions_from_module

functions = get_functions_from_module(gh_util.functions)
