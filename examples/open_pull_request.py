import asyncio

from gh_util.functions import open_pull_request
from gh_util.print import print_repo_issue


async def main():
    pr = await open_pull_request(
        owner="zzstoatzz",
        repo="gh",
        head="🦀",
        body="Even a broken clock is right twice a day",
        draft=True,
    )
    print_repo_issue(pr)
    print(f"Pull Request URL: {pr.html_url}")


asyncio.run(main())
