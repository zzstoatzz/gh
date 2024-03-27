from datetime import UTC, datetime

from pydantic import Field, PrivateAttr

from gh_util.types.core import (
    GitHubComment,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRepo,
    GitHubResourceModel,
    GitHubUser,
)


class GitHubWebhookEventHeaders(GitHubResourceModel):
    model_config = dict(extra="ignore")

    host: str = Field(...)
    event: str = Field(alias="x-github-event")
    hook_id: int = Field(alias="x-github-hook-id")
    delivery: str = Field(alias="x-github-delivery")


class GitHubWebhookEvent(GitHubResourceModel):
    action: str

    repository: GitHubRepo | None = None
    sender: GitHubUser | None = None


class GitHubIssueEvent(GitHubWebhookEvent):
    issue: GitHubIssue
    comment: GitHubComment | None = None


class GitHubPullRequestEvent(GitHubWebhookEvent):
    pull_request: GitHubPullRequest


class GitHubWebhookRequest(GitHubResourceModel):
    _received_at: datetime = PrivateAttr(default_factory=lambda: datetime.now(UTC))

    headers: GitHubWebhookEventHeaders
    event: GitHubWebhookEvent
