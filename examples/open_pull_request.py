import asyncio

from gh_util.functions import open_pull_request


async def main():
    pr = await open_pull_request(
        owner="PrefectHQ",
        repo="marvin",
        title="Test PR",
        head="rag",
        base="main",
        body="Even a broken clock is right twice a day",
        draft=True,
        check_for_existing=True,
    )
    print(f"Pull Request URL: {pr.html_url}")


asyncio.run(main())
