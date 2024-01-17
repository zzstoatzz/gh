# gh_util

A minimal Python library for interacting with GitHub's API, using `httpx` and `Pydantic`.

## Usage

```python
from gh_util.functions import fetch_github_issue

async def main():
    issue = await fetch_github_issue("prefecthq", "marvin", 723, include_comments=True)
    print(f"[{issue.number} {issue.title}]({issue.url})")
    print(issue.body)

    for comment in issue.user_comments:
        print(f"[{comment.user.login}]({comment.user.url}) said:")
        print(f"{comment.body}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Installation

```bash
pip install gh_util
```

## Development

```bash
git clone https://github.com/zzstoatzz/gh.git
cd gh
python -m venv gh_util
source gh_util/bin/activate
pip install -e .
```