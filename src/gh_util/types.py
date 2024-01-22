from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GitHubUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    login: str
    url: HttpUrl


class GitHubLabel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    color: str

    description: str | None = None

    def __hash__(self) -> int:
        return hash(self.name)


class GitHubRepo(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    owner: GitHubUser


class GitHubComment(BaseModel):
    model_config = ConfigDict(extra="allow")

    url: HttpUrl
    user: GitHubUser
    body: str
    created_at: datetime
    updated_at: datetime


class GitHubIssue(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    url: HttpUrl
    number: int
    user: GitHubUser
    user_comments: list[GitHubComment] = Field(default_factory=list)

    body: str | None = None
    comments_url: HttpUrl | None = None


class GitHubIssueEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: str
    issue: GitHubIssue
    repository: GitHubRepo


class GitHubRelease(BaseModel):
    model_config = ConfigDict(extra="allow")

    tag_name: str
    published_at: datetime
    html_url: HttpUrl

    name: str | None = None
    body: str | None = None


class GitHubBranch(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Basic branch data
    label: str
    ref: str
    sha: str

    # User who last committed to the branch
    user: GitHubUser

    # The repository this branch is part of
    repo: GitHubRepo


class GitHubPullRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Basic pull request data
    title: str
    body: str | None = None
    url: HttpUrl
    html_url: HttpUrl
    number: int
    state: str

    # User who created the PR
    user: GitHubUser

    # Branches and repository data
    head: GitHubBranch
    base: GitHubBranch

    # Timestamps
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    merged_at: datetime | None = None
