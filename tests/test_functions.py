from gh_util.functions import (
    add_labels_to_issue,
    fetch_repo_issue,
    fetch_repo_issues,
    fetch_repo_labels,
    update_labels_on_issue,
)


async def test_fetch_repo_issue():
    owner = "prefecthq"
    repo = "marvin"
    issue_number = 723
    issue = await fetch_repo_issue(owner, repo, issue_number)
    assert issue.number == issue_number
    assert issue.title is not None


async def test_fetch_repo_issues():
    owner = "prefecthq"
    repo = "marvin"
    issues = await fetch_repo_issues(owner, repo, n=5)
    assert len(issues) == 5


async def test_fetch_repo_labels():
    owner = "prefecthq"
    repo = "marvin"
    labels = await fetch_repo_labels(owner, repo)
    assert len(labels) > 0


async def test_add_labels_to_issue():
    owner = "prefecthq"
    repo = "marvin"
    issue_number = 723
    new_labels = {"test-label"}  # Use a unique label
    result = await add_labels_to_issue(owner, repo, issue_number, new_labels)
    assert result


async def test_update_labels_on_issue():
    owner = "prefecthq"
    repo = "marvin"
    issue_number = 723
    labels = {"enhancement"}
    result = await update_labels_on_issue(owner, repo, issue_number, labels)
    assert result
