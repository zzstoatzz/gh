from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class GitHubUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    login: str
    url: HttpUrl


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
