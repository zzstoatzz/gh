from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from gh_util import types

console = Console()


def print_release(release: types.GitHubRelease) -> None:
    owner = release.author.login
    repo = str(release.html_url).split("/")[-4]
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title=f"{owner}/{repo} {release.name}",
        caption=f"Released by {release.author.login}",
    )
    table.add_column("Field", style="dim", width=12)
    table.add_column("Value")
    table.add_row("Repository", f"{owner}/{repo}")
    table.add_row("Release", release.name)
    table.add_row(
        "Published", release.published_at.strftime("%A, %d %B %Y %H:%M:%S %Z")
    )
    if release.reactions:
        table.add_row("Reactions", str(release.reactions))
    table.add_row(
        "Body",
        Markdown(release.body),
    )

    console.print(table)
    console.print(
        f"[link={release.html_url}]View this release on GitHub[/link]",
        style="bold blue",
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

    for comment in getattr(issue, "user_comments", []):
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
