import asyncio

from gh_util.functions import fetch_latest_release
from gh_util.print import print_release


async def main(owner: str, repo: str) -> None:
    print_release(await fetch_latest_release(owner, repo))


if __name__ == "__main__":
    asyncio.run(main("prefecthq", "prefect"))
