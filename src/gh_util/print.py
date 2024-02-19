from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from gh_util import types

console = Console()


def print_user(user: types.GitHubUser) -> None:
    console.print(
        Panel(
            Markdown(
                f"**[{user.login}]({user.url})** is from **{user.location}**."
                f"\n\nthey have been on **[github.com](https://github.com)** since **{user.created_at:%A, %B %d, %Y %I:%M %p}**."
                f"\n\nif they had to say words about themselves, they might say:\n{user.bio}"
            ),
            title=f"{user.login}'s GitHub Profile",
            border_style="green",
        )
    )


def print_repo_issue(issue: types.GitHubIssue) -> None:
    console.print(
        Panel(
            Markdown(
                (
                    f"**[{issue.number} {issue.title}]({issue.url})**"
                    f"was created by **{issue.user.login}** on **{issue.created_at}**.\n\n{issue.body}"
                )
            ),
            title="GitHub Issue",
            subtitle=f"Created by {issue.user.login} on {issue.created_at:%A, %B %d, %Y %I:%M %p}",
        )
    )

    for comment in issue.user_comments:
        comment_panel_content = (
            f"**[{comment.user.login}]({comment.user.url})** said:\n\n{comment.body}"
        )
        console.print(
            Panel(
                Markdown(comment_panel_content),
                title="Comment",
                subtitle=f"{comment.created_at:%A, %B %d, %Y %I:%M %p}",
                border_style="green",
            )
        )
