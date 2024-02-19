from devtools import debug
from gh_util.functions import fetch_repo_labels

if __name__ == "__main__":
    import asyncio

    labels = asyncio.run(fetch_repo_labels("zzstoatzz", "gh"))

    debug(labels)
