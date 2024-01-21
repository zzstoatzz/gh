from typing import Set

from jinja2 import Template

from gh_util.client import GHClient
from gh_util.logging import get_logger
from gh_util.types import GitHubComment, GitHubIssue, GitHubLabel, GitHubRelease
from gh_util.utils import parse_as

logger = get_logger(__name__)


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


async def add_labels_to_issue(
    owner: str, repo: str, issue_number: int, new_labels: Set[str]
) -> bool:
    async with GHClient() as client:
        current_labels_response = await client.get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels"
        )

        if labels_to_add := set(new_labels) - {
            label["name"] for label in current_labels_response.json()
        }:
            response = await client.post(
                f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
                json=list(labels_to_add),
            )

            if response.status_code == 200:
                return True

        else:
            logger.warning_kv(
                "No change", "Selected labels already exist on issue", "blue"
            )

    return False


async def fetch_latest_release(owner: str, repo: str) -> GitHubRelease:
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/releases/latest")
        return GitHubRelease.model_validate(response.json())


async def describe_latest_release(
    owner: str, repo: str, template: Template | str | None = None, **render_kwargs
) -> str:
    release = await fetch_latest_release(owner, repo)
    if template is None:
        template = Template(
            "Latest release: {{ release.tag_name }} @ {{ release.html_url }}"
        )
    elif isinstance(template, str):
        template = Template(template)

    return template.render(
        release=release, **dict(owner=owner, repo=repo, **render_kwargs)
    )
