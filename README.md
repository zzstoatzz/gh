# gh_util

A minimal Python library for interacting with GitHub's API, using `httpx` and `Pydantic`.

## Installation

```bash
pip install gh_util
```

## Usage

### Get the current user's GitHub profile
```python
from devtools import debug
from gh_util.client import GHClient
from gh_util.types import GitHubUser

async def get_current_user() -> GitHubUser:
    async with GHClient() as client:
        response = await client.get("/user")
        return GitHubUser.model_validate(response.json())

if __name__ == "__main__":
    import asyncio
    debug(asyncio.run(get_current_user()))
```

### Read a GitHub issue and its comments
```python
from gh_util.functions import fetch_github_issue

async def read_github_issue() -> None:
    issue = await fetch_github_issue("prefecthq", "marvin", 723, include_comments=True)
    print(f"[{issue.number} {issue.title}]({issue.url})")
    print(issue.body)

    for comment in issue.user_comments:
        print(f"[{comment.user.login}]({comment.user.url}) said:")
        print(f"{comment.body}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(read_github_issue())
```

... and more at [gh_util/functions.py](src/gh_util/functions.py)

## Development

```bash
git clone https://github.com/zzstoatzz/gh.git
cd gh
python -m venv gh_util
source gh_util/bin/activate
pip install -e .
```