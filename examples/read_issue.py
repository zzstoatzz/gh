from gh_util.functions import fetch_github_issue


async def main():
    issue = await fetch_github_issue("prefecthq", "marvin", 723, include_comments=True)

    print(
        f"[{issue.number} {issue.title}]({issue.url}) was created by {issue.user.login} on {issue.created_at}."
    )

    print(issue.body)

    print()

    for comment in issue.user_comments:
        print(f"[{comment.user.login}]({comment.user.url}) said:")
        print(comment.body)
        print()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
