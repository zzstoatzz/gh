import asyncio

from gh_util.functions import fetch_latest_release
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table


async def main(owner: str, repo: str) -> None:
    console = Console()
    release = await fetch_latest_release(owner, repo)

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
    table.add_row("Description", Markdown(release.body))

    console.print(table)
    console.print(
        f"[link={release.html_url}]View this release on GitHub[/link]",
        style="bold blue",
    )


if __name__ == "__main__":
    asyncio.run(main("prefecthq", "marvin"))
