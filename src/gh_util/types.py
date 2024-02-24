from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GitHubResourceModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    created_at: datetime | None = None
    updated_at: datetime | None = None


class GitHubUser(GitHubResourceModel):
    login: str
    url: HttpUrl


class GitHubLabel(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: int
    name: str
    color: str

    description: str | None = None


class GitHubRepo(GitHubResourceModel):
    name: str
    owner: GitHubUser
    description: str | None = None


class GitHubComment(GitHubResourceModel):
    url: HttpUrl
    user: GitHubUser
    body: str


class GitHubIssue(GitHubResourceModel):
    title: str
    url: HttpUrl
    number: int
    user: GitHubUser
    user_comments: list[GitHubComment] = Field(default_factory=list)
    labels: list[GitHubLabel] = Field(default_factory=list)

    body: str | None = None
    comments_url: HttpUrl | None = None


class GitHubRelease(GitHubResourceModel):
    tag_name: str
    published_at: datetime
    html_url: HttpUrl
    author: GitHubUser

    name: str | None = None
    body: str | None = None


class GitHubBranch(GitHubResourceModel):
    # Basic branch data
    label: str
    ref: str
    sha: str

    # User who last committed to the branch
    user: GitHubUser

    # The repository this branch is part of
    repo: GitHubRepo


class GitHubPullRequest(GitHubResourceModel):
    # Basic pull request data
    title: str
    body: str | None = None
    url: HttpUrl
    html_url: HttpUrl
    number: int
    state: str
    labels: list[GitHubLabel] = Field(default_factory=list)

    # User who created the PR
    user: GitHubUser

    # Branches and repository data
    head: GitHubBranch
    base: GitHubBranch

    # Timestamps
    closed_at: datetime | None = None
    merged_at: datetime | None = None


class GitHubWebhookEvent(GitHubResourceModel):
    action: str

    repository: GitHubRepo | None = None
    sender: GitHubUser | None = None


class GitHubIssueEvent(GitHubWebhookEvent):
    issue: GitHubIssue
    comment: GitHubComment | None = None
