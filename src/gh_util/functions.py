from gh_util.client import GHClient
from gh_util.types import GitHubComment, GitHubIssue


async def fetch_github_issue(
    owner: str,
    repo: str,
    issue_number: int,
    include_comments: bool = False,
) -> GitHubIssue:
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
        issue = GitHubIssue.model_validate(response.json())

        if include_comments:
            response = await client.get(issue.comments_url)
            issue.user_comments = [
                GitHubComment.model_validate(comment) for comment in response.json()
            ]

        return issue
