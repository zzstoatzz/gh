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
    body: str | None = None

    user_comments: list[GitHubComment] = Field(default_factory=list)

    comments_url: HttpUrl | None = None


class GitHubIssueEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: str
    issue: GitHubIssue
