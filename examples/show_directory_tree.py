import asyncio

from gh_util.functions import fetch_directory_structure

if __name__ == "__main__":
    print(asyncio.run(fetch_directory_structure("zzstoatzz", "gh", "examples")))
