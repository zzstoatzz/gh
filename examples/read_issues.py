import asyncio

from gh_util.functions import fetch_repo_issues
from gh_util.print import print_repo_issue


async def main():
    issues = await fetch_repo_issues(
        "prefecthq", "marvin", n=1, include_comments=True, fetch_type="all"
    )
    for issue in issues:
        print_repo_issue(issue)


if __name__ == "__main__":
    asyncio.run(main())
