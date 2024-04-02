import fnmatch
from datetime import datetime
from typing import Any, Literal, Mapping

import gh_util
from gh_util.client import GHClient
from gh_util.contexts import clone_repo
from gh_util.logging import get_logger
from gh_util.types import (
    GitHubComment,
    GitHubCommit,
    GitHubEvent,
    GitHubIssue,
    GitHubLabel,
    GitHubPullRequest,
    GitHubRelease,
    GitHubUser,
)
from gh_util.utilities.process import run_gh_command, run_git_command
from gh_util.utilities.pydantic import parse_as

logger = get_logger(__name__)


async def fetch_repo_issue(
    owner: str,
    repo: str,
    issue_number: int,
    include_comments: bool = False,
) -> GitHubIssue:
    """Fetch an issue or pull request from a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        issue_number: The issue or pull request number.
        include_comments: Whether to include comments for the issue. Default is False.

    Returns:
        GitHubIssue: The issue or pull request.

    Example:
        Fetch an issue from the `prefecthq/marvin` repository:
        ```python
        from gh_util.functions import fetch_repo_issue
        from gh_util.print import print_repo_issue

        issue = await fetch_repo_issue(
            owner="prefecthq",
            repo="marvin",
            issue_number=723,
            include_comments=True
        )
        print_repo_issue(issue)

        ```
    """
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
        issue = parse_as(GitHubIssue, response.json())
        logger.debug_kv("Fetched issue", f"{(issue.title or issue.number)!r}", "blue")

        if include_comments:
            response = await client.get(issue.comments_url)
            data = response.json()
            logger.debug_kv("Comments", f"retrieved {len(data)}", "blue")
            issue.user_comments = parse_as(list[GitHubComment], data)

        return issue


async def fetch_repo_issues(
    owner: str,
    repo: str,
    state: str = "open",
    n: int = 10,
    per_page: int = 100,
    include_comments: bool = False,
    fetch_type: Literal["issues", "pulls", "all"] = "all",
) -> list[GitHubIssue]:
    """Fetch issues and pull requests from a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        state: The state of the issues to fetch. Default is "open".
        n: The number of issues to fetch. Default is 10.
        per_page: The number of issues to fetch per page. Default is 100.
        include_comments: Whether to include comments for each issue. Default is False.
        fetch_type: The type of items to fetch, e.g. "issues", "pulls", or "all". Default is "all".

    Returns:
        list[GitHubIssue]: A list of issues and pull requests.

    Example:
        Get the last 10 pull requests from a repository:
        ```python
        from gh_util.functions import fetch_repo_issues

        issues = await fetch_repo_issues(
            owner="prefecthq",
            repo="marvin",
            n=10,
            include_comments=True,
            fetch_type="pulls"
        )
        for issue in issues:
            print_repo_issue(issue)
        ```
    """
    page = 1
    issues: list[dict[str, Any]] = []
    async with GHClient() as client:
        while len(issues) < n:
            response = await client.get(
                f"/repos/{owner}/{repo}/issues",
                params={
                    "state": state,
                    "per_page": min(n - len(issues), per_page),
                    "page": page,
                },
            )
            if not (new_items := response.json()):
                break

            for item in new_items:
                is_pull_request = item.get("pull_request") is not None

                if fetch_type != "all" and (
                    fetch_type == "issues"
                    and is_pull_request
                    or fetch_type == "pulls"
                    and not is_pull_request
                ):
                    logger.debug_kv(
                        "Skipped item",
                        f"Skipping {item.get('title')!r} as not of {fetch_type=!r}",
                        "blue",
                    )
                    continue

                if include_comments:
                    comments_response = await client.get(item.get("comments_url"))
                    item["user_comments"] = (
                        comments_response.json() if comments_response else []
                    )

                issues.append(item)
                if len(issues) == n:
                    break

            page += 1
            if fetch_type != "all" and len(new_items) == 0:
                break

        return parse_as(list[GitHubIssue], issues)


async def fetch_repo_labels(owner: str, repo: str) -> set[GitHubLabel]:
    """Fetch the labels from a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.

    Returns:
        set[GitHubLabel]: A set of labels.

    Example:
        Get the labels from the `prefecthq/marvin` repository:
        ```python
        from gh_util.functions import fetch_repo_labels

        fetch_repo_labels(owner="zzstoatzz", repo="gh")
        ```
    """
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/labels")
        data = response.json()
        label_names = {label["name"] for label in data}
        logger.debug_kv("Fetched labels", label_names, "blue")
        return parse_as(set[GitHubLabel], data)


async def add_labels_to_issue(
    owner: str, repo: str, issue_number: int, new_labels: list[str] | set[str]
) -> bool:
    """Add labels to an issue or pull request. If the label already exists on the issue, it will not be added again.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        issue_number: The issue or pull request number.
        new_labels: The labels to add to the issue.

    Returns:
        bool: True if any labels were added, False if no labels were added.

    Example:
        ```python
        from gh_util.functions import add_labels_to_issue

        await add_labels_to_issue(
            owner="zzstoatzz",
            repo="gh",
            issue_number=1,
            new_labels={"bug"}
        )
        ```
    """
    new_labels = set(new_labels)

    async with GHClient() as client:
        current_labels_response = await client.get(
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels"
        )
        names = {label["name"] for label in current_labels_response.json()}
        logger.debug_kv(
            "Fetched current labels", " | ".join(names) or "No labels", "blue"
        )

        if labels_to_add := new_labels - names:
            await client.post(
                f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
                json=list(labels_to_add),
            )

            logger.info_kv(
                "Added labels",
                f"Added labels {labels_to_add} to issue #{issue_number}",
                "green",
            )
            return True

        else:
            logger.warning_kv(
                "No change", "Selected labels already exist on issue", "blue"
            )

    return False


async def update_labels_on_issue(
    owner: str, repo: str, issue_number: int, labels: set[str]
) -> bool:
    """Put a set of labels on an issue or pull request. If labels exist on the issue but are no longer relevant, they will be removed.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        issue_number: The issue or pull request number.
        labels: The labels to add to the issue.

    Returns:
        bool: True if any labels were added, False if no labels were added.

    Example:
        ```python
        from gh_util.functions import update_labels_on_issue

        await update_labels_on_issue(
            owner="zzstoatzz",
            repo="gh",
            issue_number=1,
            labels={"bug", "enhancement"}
        )
        ```
    """
    current_labels = (await fetch_repo_issue(owner, repo, issue_number)).labels

    async with GHClient() as client:
        # Remove labels that are no longer relevant
        for label in current_labels:
            if label.name not in labels:
                await client.delete(
                    f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label.name}"
                )

        await add_labels_to_issue(owner, repo, issue_number, labels)
        return True


async def fetch_latest_release(owner: str, repo: str) -> GitHubRelease:
    """Fetch the latest release from a repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.

    Returns:
        GitHubRelease: The latest release.

    Example:
        Get the latest release from the `prefecthq/marvin` repository:
        ```python
        from gh_util.functions import fetch_latest_release

        fetch_latest_release(owner="prefecthq", repo="marvin")
        ``
    """
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/releases/latest")
        return GitHubRelease.model_validate(response.json())


async def open_pull_request(
    owner: str,
    repo: str,
    head: str,
    title: str = "👾 stop the lizard people 👾",  # had to do it to em
    base: str = gh_util.settings.default_base,
    body: str | None = None,
    draft: bool = False,
    check_for_existing: bool = True,
) -> GitHubPullRequest:
    """Open a pull request from a branch to a base.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        head: The branch to pull from.
        title: The title of the pull request. Default is "👾 stop the lizard people 👾".
        base: The branch to pull into. Default is "main".
        body: The body of the pull request. Default is None.
        draft: Whether the pull request is a draft. Default is False.
        check_for_existing: Whether to check for an existing pull request. Default is True.

    Returns:
        GitHubPullRequest: The pull request.
    """
    if not body:
        body = (
            f"Pull request from {head} to {base}"
            f" This PR was created by the gh_util library."
        )

    async with GHClient() as client:
        if check_for_existing:
            existing_prs = await client.get(
                f"/repos/{owner}/{repo}/pulls?head={owner}:{head}&base={base}&state=open"
            )
            if existing_prs.status_code == 200 and existing_prs.json():
                logger.warning_kv(
                    "Existing PR found",
                    f"PR already exists for {owner}:{head} -> {base}",
                    "blue",
                )
                return GitHubPullRequest.model_validate(existing_prs.json()[0])

        response = await client.post(
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft,
            },
        )
        return GitHubPullRequest.model_validate(response.json())


async def fetch_contributor_data(
    owner: str,
    repo: str,
    since: datetime | None = None,
    max: int = 100,
    excluded_users: set | None = None,
) -> Mapping[GitHubUser, list[GitHubIssue | GitHubPullRequest | GitHubCommit]]:
    since = since or gh_util.settings.default_since

    excluded_users = excluded_users or {}

    contributors_activity = {}

    async with GHClient() as client:
        events = await client.get(
            f"/repos/{owner}/{repo}/events", params={"per_page": max}
        )

        for event in parse_as(list[GitHubEvent], events.json()):
            if event.actor.login in excluded_users or event.created_at < since:
                continue

            activity = contributors_activity.setdefault(
                event.actor,
                {
                    "created_issues": [],
                    "created_pull_requests": [],
                    "merged_commits": [],
                },
            )

            if event.type == "IssuesEvent" and event.payload.action == "opened":
                activity["created_issues"].append(event.payload.issue)

            elif event.type == "PullRequestEvent" and event.payload.action == "opened":
                activity["created_pull_requests"].append(event.payload.pull_request)

            elif event.type == "PushEvent":
                commits = [
                    commit
                    for commit in event.payload.commits
                    if "Merge" not in commit.message
                ]
                activity["merged_commits"].extend(commits)

    return contributors_activity


async def get_filenames_from_directory(
    owner: str, repo: str, directory_path: str, pattern: str | None = None
) -> list[str]:
    async with GHClient() as client:
        response = await client.get(f"/repos/{owner}/{repo}/contents/{directory_path}")

        filenames: list[str] = [
            item["name"] for item in response.json() if item["type"] == "file"
        ]

        if pattern:
            filenames = [
                filename for filename in filenames if fnmatch.fnmatch(filename, pattern)
            ]

        return filenames


async def get_default_branch_name_for_repo(owner: str, repo: str) -> str:
    return await run_gh_command(
        "repo",
        "view",
        f"{owner}/{repo}",
        "--json",
        "defaultBranchRef",
        "--jq",
        ".defaultBranchRef.name",
    )


async def create_commit(
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str,
    base_branch: str | None = None,
):
    """
    Create a commit with the given file content on a specified branch.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        path: The path within the repository to write the file to.
        content: The content of the file.
        message: The commit message.
        branch: The branch to create the commit on.
        base_branch: The base branch to create the new branch from. If not provided, the default branch will be used.

    Returns:
        None
    """
    async with clone_repo(owner, repo) as repo_path:
        try:
            await run_git_command("checkout", branch, cwd=repo_path)
            logger.info(
                f"Checked out branch '{branch}' in the '{owner}/{repo}' repository."
            )
        except Exception:
            base_branch = base_branch or await get_default_branch_name_for_repo(
                owner, repo
            )
            await run_git_command("checkout", "-b", branch, base_branch, cwd=repo_path)
            logger.info(
                f"Created new branch '{branch}' based on '{base_branch}' in the '{owner}/{repo}' repository."
            )

        file_path = repo_path / path
        await file_path.parent.mkdir(parents=True, exist_ok=True)

        await file_path.write_text(content)
        await run_git_command("add", path, cwd=repo_path)
        logger.info(
            f"Staged changes for file '{path}' in the '{owner}/{repo}' repository."
        )

        try:
            await run_git_command("commit", "-m", message, cwd=repo_path)
            logger.info(
                f"Created commit with message '{message}' in the '{owner}/{repo}' repository."
            )
        except Exception as e:
            logger.error(
                f"Failed to create commit in the '{owner}/{repo}' repository. Error: {str(e)}"
            )
            raise

        try:
            await run_git_command("push", "-u", "origin", branch, cwd=repo_path)
            logger.info(
                f"Pushed changes to branch '{branch}' in the '{owner}/{repo}' repository."
            )
        except Exception as e:
            logger.error(
                f"Failed to push changes to branch '{branch}' in the '{owner}/{repo}' repository. Error: {str(e)}"
            )
            raise
