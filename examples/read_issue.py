from gh_util.functions import fetch_repo_issue
from gh_util.print import print_repo_issue


async def main():
    issue = await fetch_repo_issue("prefecthq", "marvin", 723, include_comments=True)
    print_repo_issue(issue)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
