import asyncio
import tempfile

from gh_util.client import GHClient
from gh_util.functions import clone_repo_to_tmpdir
from gh_util.types import GitHubRelease
from gh_util.utils import parse_as


async def clone_and_get_latest_release(owner: str, repo: str) -> GitHubRelease:
    """Clone a repository to a temp directory and fetch its latest release.

    Args:
        owner: The owner of the repository.
        repo: The repository name.

    Returns:
        GitHubRepo: The latest release of the repository.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        await clone_repo_to_tmpdir(owner, repo, tmpdir)
        async with GHClient() as client:
            response = await client.get(f"/repos/{owner}/{repo}/releases/latest")
            return parse_as(GitHubRelease, response.json())


if __name__ == "__main__":
    asyncio.run(clone_and_get_latest_release("prefecthq", "marvin"))
