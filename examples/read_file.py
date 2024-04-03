import asyncio

from gh_util.functions import read_file

if __name__ == "__main__":
    print(asyncio.run(read_file("zzstoatzz", "gh", "README.md")))
