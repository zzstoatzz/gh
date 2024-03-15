"""Label issues based on incoming webhook events from GitHub.

Uses `marvin` to prompt an LLM to label issues and return structured output.

Uses `prefect` to deploy/serve the webhook event handler (Prefect Cloud required for webhook events).

Setup:
    ```bash
    pip install gh-util marvin prefect

    export GITHUB_TOKEN=<your-github-token>
    export OPENAI_API_KEY=<your-openai-api-key>
    ```
"""

from enum import Enum

import marvin
from gh_util.functions import (
    fetch_repo_issue,
    fetch_repo_labels,
    update_labels_on_issue,
)
from gh_util.types import GitHubIssue, GitHubIssueEvent, GitHubLabel
from prefect import task
from prefect.task_server import serve as serve_tasks


async def get_appropriate_labels(
    issue: GitHubIssue, label_options: set[GitHubLabel]
) -> set[str]:
    """Return appropriate labels for a GitHub issue based on its body, comments, and existing labels."""

    LabelOption = Enum(
        "LabelOption",
        {label.name: label.name for label in label_options},
    )

    @marvin.fn
    async def get_labels(issue: GitHubIssue) -> set[LabelOption]:  # type: ignore
        """Return appropriate labels for a GitHub issue based on its body.

        If existing labels are sufficient, return them. If existing labels are no
        longer relevant, do _not_ return them.
        """

    return {i.value for i in await get_labels(issue)}


@task(
    log_prints=True,
    retries=(r := 5),
    retry_delay_seconds=list(map(lambda x: 2**x, range(r - 2, r * 2 - 2))),
)
async def label_issues(event: GitHubIssueEvent):
    """Label issues based on incoming webhook events from GitHub."""

    print(f"Issue '#{event.issue.number} - {event.issue.title}' was {event.action}")

    owner, repo = event.repository.owner.login, event.repository.name

    issue = await fetch_repo_issue(
        owner, repo, event.issue.number, include_comments=True
    )

    label_options = await fetch_repo_labels(owner, repo)

    labels = await get_appropriate_labels(issue=issue, label_options=label_options)

    await update_labels_on_issue(
        owner=owner,
        repo=repo,
        issue_number=issue.number,
        labels=labels,
    )

    print(f"Labeled issue with {' | '.join(labels)!r}")


if __name__ == "__main__":
    serve_tasks(label_issues)
