from typing import Set

from gh_util.client import GHClient
from gh_util.types import GitHubComment, GitHubIssue, GitHubLabel
from gh_util.utils import parse_as


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
            issue.user_comments = parse_as(list[GitHubComment], response.json())

        return issue


async def fetch_repo_labels(owner: str, repo: str) -> Set[GitHubLabel]:
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/labels")
        response.raise_for_status()
        return parse_as(set[GitHubLabel], response.json())
