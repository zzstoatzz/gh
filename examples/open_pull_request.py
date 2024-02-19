import asyncio

from gh_util.functions import open_pull_request


async def main():
    pr = await open_pull_request(
        owner="zzstoatzz",
        repo="raggy",
        head="gh-pages",
        body="Even a broken clock is right twice a day",
        draft=True,
        check_for_existing=True,
    )
    print(f"Pull Request URL: {pr.html_url}")


asyncio.run(main())
