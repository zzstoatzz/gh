from datetime import UTC, datetime

from pydantic import Field, HttpUrl, PrivateAttr

from gh_util.types.core import (
    GitHubComment,
    GitHubIssue,
    GitHubPullRequest,
    GitHubRepo,
    GitHubResourceModel,
    GitHubUser,
)


class GitHubHookConfig(GitHubResourceModel):
    content_type: str
    insecure_ssl: str
    url: HttpUrl


class GitHubHook(GitHubResourceModel):
    type: str
    id: int
    name: str
    active: bool
    events: list[str]
    config: GitHubHookConfig
    updated_at: datetime
    created_at: datetime
    app_id: int
    deliveries_url: HttpUrl


class GitHubPingEvent(GitHubResourceModel):
    zen: str
    hook_id: int
    hook: GitHubHook


class GitHubWebhookEventHeaders(GitHubResourceModel):
    model_config = dict(extra="ignore")

    host: str = Field(...)
    event: str = Field(alias="x-github-event")
    hook_id: int = Field(alias="x-github-hook-id")
    delivery: str = Field(alias="x-github-delivery")


class GitHubWebhookEvent(GitHubResourceModel):
    action: str | None = None

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
