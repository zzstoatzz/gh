import fnmatch
import json
from datetime import UTC, datetime
from typing import Any, Literal, Mapping

from httpx import HTTPStatusError
from rich.status import Status

import gh_util
from gh_util.client import GHClient
from gh_util.logging import get_logger
from gh_util.types import (
    GitHubComment,
    GitHubCommit,
    GitHubEvent,
    GitHubIssue,
    GitHubLabel,
    GitHubPullRequest,
    GitHubRef,
    GitHubRelease,
    GitHubTag,
    GitHubTagger,
    GitHubUser,
)
from gh_util.utilities.process import run_gh_command
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

        try:
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
        except HTTPStatusError as e:
            logger.error_kv(
                "Failed to open PR",
                f"Failed to open PR from {head} to {base} in {owner}/{repo}",
                "red",
            )
            match err := e.response.json()["errors"][0]:
                case {"field": "head", "code": "invalid"}:
                    raise ValueError(f"Invalid head branch {head!r}: {err}")
                case _:
                    logger.error_kv("Error", err)
                    raise e

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
    create_branch: bool = True,
) -> GitHubCommit:
    """
    Create a commit with the given file content on a specified branch in a remote repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        path: The path within the repository to write the file to.
        content: The content of the file.
        message: The commit message.
        branch: The branch to create the commit on.
        base_branch: The base branch to create the new branch from. If not provided, the default branch will be used.
        create_branch: Whether to create the branch if it doesn't exist. Default is True.

    Returns:
        GitHubCommit: The created commit.

    Example:
        ```python
        from gh_util.functions import create_commit

        commit = await create_commit(
            owner="prefecthq",
            repo="marvin",
            path="data/example.txt",
            content="Hello, World!",
            message="Add example file",
            branch="feature/example",
            base_branch="main",
            create_branch=True
        )
        print(commit)
        ```
    """
    async with GHClient() as client:
        base_branch = base_branch or await get_default_branch_name_for_repo(owner, repo)

        # Get the SHA of the base branch
        base_branch_sha = await client.get(
            f"/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
        )
        base_tree_sha = base_branch_sha.json()["object"]["sha"]

        # Create a new tree with the file content
        new_tree = await client.post(
            f"/repos/{owner}/{repo}/git/trees",
            json={
                "base_tree": base_tree_sha,
                "tree": [
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "content": content,
                    }
                ],
            },
        )
        new_tree_sha = new_tree.json()["sha"]

        # Create a new commit with the new tree
        new_commit = await client.post(
            f"/repos/{owner}/{repo}/git/commits",
            json={
                "message": message,
                "tree": new_tree_sha,
                "parents": [base_tree_sha],
            },
        )
        new_commit_sha = new_commit.json()["sha"]

        # Create the branch reference if it doesn't exist
        if create_branch:
            try:
                await client.get(f"/repos/{owner}/{repo}/git/refs/heads/{branch}")
            except Exception as e:
                if "Not Found" in str(e):
                    await client.post(
                        f"/repos/{owner}/{repo}/git/refs",
                        json={
                            "ref": f"refs/heads/{branch}",
                            "sha": new_commit_sha,
                        },
                    )
                else:
                    raise

        # Update the branch reference to point to the new commit
        await client.patch(
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
            json={"sha": new_commit_sha},
        )

        logger.info_kv(
            "Commit created",
            f"Created commit with message '{message}' on branch '{branch}' in repository '{owner}/{repo}'",
            "green",
        )

        return GitHubCommit.model_validate(new_commit.json())


async def read_file(
    owner: str,
    repo: str,
    path: str,
    branch: str | None = None,
) -> str:
    """
    Read the content of a file from a remote repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        path: The path of the file within the repository.
        branch: The branch to read the file from. If not provided, the default branch will be used.

    Returns:
        str: The content of the file.

    Example:
        ```python
        from gh_util.functions import read_file

        content = await read_file(
            owner="prefecthq",
            repo="marvin",
            path="cookbook/translate_schemas.py",
            branch="main"
        )
        print(content)
        ```
    """
    async with GHClient() as client:
        branch = branch or gh_util.settings.default_base

        try:
            response = await client.get(f"/raw/{owner}/{repo}/{branch}/{path}")

        except json.JSONDecodeError:
            logger.warning_kv(
                "File not found",
                f"File '{path}' not found in branch '{branch}' in repository '{owner}/{repo}'",
            )
            return ""

        logger.info_kv(
            "File read",
            f"Read content of file '{path}' from branch '{branch}' in repository '{owner}/{repo}'",
        )

        return response.text


async def fetch_filenames_from_directory(
    owner: str, repo: str, directory_path: str = ".", pattern: str | None = None
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


async def fetch_directory_structure(
    owner: str,
    repo: str,
    directory_path: str = ".",
    branch: str | None = None,
    levels: int = 2,
    pattern: str | None = None,
) -> str:
    """
    Fetch the directory structure of a remote repository with a specified number of levels and glob pattern.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        directory_path: The path of the directory within the repository. Default is ".".
        branch: The branch to fetch the directory structure from. If not provided, the default branch will be used.
        levels: The number of levels to traverse in the directory structure. Default is 1.
        pattern: The glob pattern to filter the files and directories. Default is None.

    Returns:
        str: The directory structure as a string.

    Example:
        ```python
        from gh_util.functions import fetch_directory_structure

        structure = await fetch_directory_structure(
            owner="prefecthq",
            repo="marvin",
            directory_path="cookbook",
            levels=3,
        )
        print(structure)
        ```
    """
    async with GHClient() as client:
        branch = branch or gh_util.settings.default_base

        async def traverse_directory(path: str, level: int) -> str:
            response = await client.get(
                f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch}
            )
            items = response.json()

            output = ""
            for item in items:
                if pattern and not fnmatch.fnmatch(item["name"], pattern):
                    continue

                if item["type"] == "dir":
                    output += f"{'  ' * level}📁 {item['name']}\n"
                    if level < levels:
                        output += await traverse_directory(item["path"], level + 1)
                elif item["type"] == "file":
                    output += f"{'  ' * level}📄 {item['name']}\n"

            return output

        with Status(f"Fetching directory structure of '{directory_path}'"):
            structure = await traverse_directory(directory_path, 0)

        logger.info_kv(
            f"tree -L {levels} {directory_path}",
            f"in the '{branch}' branch of '{owner}/{repo}'",
        )

        return structure


async def create_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
) -> GitHubComment:
    """
    Create a comment on an issue or pull request.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        issue_number: The issue or pull request number.
        body: The body of the comment.

    Returns:
        GitHubComment: The created comment.

    Example:
        ```python
        from gh_util.functions import create_issue_comment

        comment = await create_issue_comment(
            owner="zzstoatzz",
            repo="gh",
            issue_number=4,
            body="oi bruv"
        )
        print(comment)
        ```
    """
    async with GHClient() as client:
        response = await client.post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

        logger.info_kv(
            "Comment created",
            f"Created comment on issue #{issue_number} in repository '{owner}/{repo}'",
            "green",
        )

        return GitHubComment.model_validate(response.json())


async def create_repo_tag(
    owner: str,
    repo: str,
    tag_name: str,
    commit_sha: str,
    message: str | None = None,
    tagger: GitHubTagger | None = None,
) -> GitHubTag:
    """
    Create a tag in a GitHub repository.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        tag_name: The name of the tag to create.
        commit_sha: The SHA of the commit to tag.
        message: Optional message associated with the tag creation.
        tagger: Optional dictionary containing the tagger's name, email, and date.

    Returns:
        GitHubTag: The created tag.

    Example:
        ```python
        from gh_util.functions import create_repo_tag

        tag = await create_repo_tag(
            owner="zzstoatzz",
            repo="gh",
            tag_name="v42.0",
            commit_sha="92fb40d0a05fbd5e4b1faf0678a6c88cc2688951",
            message="Creating test tag",

        )
        print(tag)
        ```
    """
    async with GHClient() as client:
        if not tagger:
            current_user = GitHubUser.model_validate((await client.get("/user")).json())
            tagger = GitHubTagger(
                name=current_user.name,
                email=current_user.email,
                date=datetime.now(UTC),
            )
        tag_data = {
            "tag": tag_name,
            "message": message or "",
            "object": commit_sha,
            "type": "commit",
            "tagger": tagger.model_dump(mode="json"),
        }

        response = await client.post(f"/repos/{owner}/{repo}/git/tags", json=tag_data)

        tag_sha = response.json()["sha"]

        # Creating a ref for the tag
        try:
            await client.post(
                f"/repos/{owner}/{repo}/git/refs",
                json={"ref": f"refs/tags/{tag_name}", "sha": tag_sha},
            )
        except HTTPStatusError as e:
            if "Reference already exists" in e.response.json()["message"]:
                logger.warning_kv(
                    "Tag already exists",
                    f"Tag '{tag_name}' already exists in repository '{owner}/{repo}'",
                    "blue",
                )
                return GitHubTag.model_validate(response.json())

        logger.info_kv(
            "Tag created",
            f"Created tag '{tag_name}' at '{commit_sha}' in repository '{owner}/{repo}'",
            "green",
        )
        return GitHubTag.model_validate(response.json())


async def fetch_latest_repo_tag(
    owner: str, repo: str, pattern: str | None = None
) -> GitHubRef:
    """
    Fetch the latest tag in a GitHub repository that matches a given pattern.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        pattern: The glob pattern to filter the tags. If None, fetches the latest tag.

    Returns:
        GitHubRef: The latest tag matching the pattern.

    Raises:
        ValueError: If no tag matching the pattern is found.

    Example:
        ```python
        from gh_util.functions import fetch_latest_repo_tag

        latest_tag = await fetch_latest_repo_tag(
            owner="zzstoatzz",
            repo="gh",
            pattern="*.1.1*"
        )
        print(f"The latest tag matching the pattern is: {latest_tag}")
        ```
    """
    tags = await fetch_latest_n_repo_tags(owner, repo, n=1, pattern=pattern)
    return tags[0]


async def fetch_latest_n_repo_tags(
    owner: str, repo: str, n: int = 10, pattern: str | None = None
) -> list[GitHubRef]:
    async with GHClient() as client:
        params = {"per_page": 1, "order": "desc", "sort": "created"}
        if pattern:
            params["q"] = f"{pattern} in:ref type:tag"

        response = await client.get(
            f"/repos/{owner}/{repo}/git/refs/tags", params=params
        )

        tags = response.json()
        if not tags:
            raise ValueError(f"No tags found matching the pattern: {pattern}")
        return parse_as(list[GitHubRef], tags)[-n:]


async def create_project_ticket(
    owner: str,
    repo: str,
    project_id: int,
    title: str,
    body: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
) -> GitHubIssue:
    """
    Create a ticket on a GitHub project board.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        project_id: The ID of the project board.
        title: The title of the ticket.
        body: Optional body content of the ticket.
        assignee: Optional login of the user to assign the ticket to.
        labels: Optional list of label names to add to the ticket.

    Returns:
        GitHubIssue: The created ticket.

    Example:
    ```python
    from gh_util.functions import create_project_ticket

    ticket = await create_project_ticket(
        owner="zzstoatzz",
        repo="gh",
        project_id=1,
        title="Implement new feature",
        body="Add support for XYZ functionality",
        assignee="zzstoatzz",
        labels=["enhancement", "backend"],
    )
    print(ticket)
    ```
    """
    async with GHClient() as client:
        # Create the issue
        issue_data = {
            "title": title,
            "body": body or "",
        }
        if assignee:
            issue_data["assignee"] = assignee
        if labels:
            issue_data["labels"] = labels

        response = await client.post(f"/repos/{owner}/{repo}/issues", json=issue_data)
        issue = GitHubIssue.model_validate(response.json())

        # Add the issue to the project board
        await client.post(
            f"/projects/columns/{project_id}/cards",
            json={"content_id": issue.number, "content_type": "Issue"},
        )

        logger.info_kv(
            "Ticket created",
            f"Created ticket '{title}' on project board '{project_id}' in repository '{owner}/{repo}'",
            "green",
        )

        return issue


async def get_prs_between_releases(
    owner: str,
    repo: str,
    base: str,
    head: str,
) -> list[GitHubPullRequest]:
    """
    Get the Pull Requests between two releases.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        base: The base release tag (earlier release).
        head: The head release tag (later release).

    Returns:
        list[GitHubPullRequest]: A list of Pull Requests between the two releases.

    Example:
        ```python
        from gh_util.functions import get_prs_between_releases

        prs = await get_prs_between_releases(
            owner="PrefectHQ",
            repo="on-release",
            base="0.0.7",
            head="0.0.8"
        )
        for pr in prs:
            print(f"#{pr.number}: {pr.title}")
        ```
    """
    async with GHClient() as client:
        # 1. Compare the two releases
        compare_url = f"/repos/{owner}/{repo}/compare/{base}...{head}"
        compare_response = await client.get(compare_url)
        compare_data = compare_response.json()

        # 2. Extract PR numbers from the comparison
        pr_numbers = set()
        for commit in compare_data.get("commits", []):
            message = commit.get("commit", {}).get("message", "")
            if message.startswith("Merge pull request #"):
                pr_number = message.split("#")[1].split(" ")[0]
                pr_numbers.add(pr_number)

        # 3. Fetch details for each PR
        prs = []
        for pr_number in pr_numbers:
            pr_url = f"/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_response = await client.get(pr_url)
            pr_data = pr_response.json()
            prs.append(GitHubPullRequest.model_validate(pr_data))

        logger.info_kv(
            "PRs fetched",
            f"Fetched {len(prs)} PRs between releases {base} and {head} in repository '{owner}/{repo}'",
            "green",
        )

        return prs
