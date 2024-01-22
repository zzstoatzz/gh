# gh_util

A minimal Python library for interacting with GitHub's API, using `httpx` and `Pydantic`.

## Installation

```bash
pip install gh_util
```

Either set `GH_UTIL_TOKEN` or `GITHUB_TOKEN` as an env var or in a `.env` file to enable authenticated requests and increase your rate limit.

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
<details>
<summary>Output</summary>

```python
# [01/22/24 00:23:18] DEBUG    gh_util.client: AUTH: Using GitHub token set in environment via `GH_UTIL_TOKEN`
<ipython-input-1-8745118bb0ba>:12 <module>
    asyncio.run(get_current_user()): GitHubUser(
        login='zzstoatzz',
        url=Url('https://api.github.com/users/zzstoatzz'),
        id=31014960,
        node_id='MDQ6VXNlcjMxMDE0OTYw',
        avatar_url='https://avatars.githubusercontent.com/u/31014960?v=4',
        gravatar_id='',
        html_url='https://github.com/zzstoatzz',
        followers_url='https://api.github.com/users/zzstoatzz/followers',
        following_url='https://api.github.com/users/zzstoatzz/following{/other_user}',
        gists_url='https://api.github.com/users/zzstoatzz/gists{/gist_id}',
        starred_url='https://api.github.com/users/zzstoatzz/starred{/owner}{/repo}',
        subscriptions_url='https://api.github.com/users/zzstoatzz/subscriptions',
        organizations_url='https://api.github.com/users/zzstoatzz/orgs',
        repos_url='https://api.github.com/users/zzstoatzz/repos',
        events_url='https://api.github.com/users/zzstoatzz/events{/privacy}',
        received_events_url='https://api.github.com/users/zzstoatzz/received_events',
        type='User',
        site_admin=False,
        name='nate nowack',
        company='@PrefectHQ ',
        blog='askmarvin.ai',
        location='Chicago, IL',
        email='nate@prefect.io',
        hireable=None,
        bio=(
            'data + software engineering @ Prefect\r\n'
            '\r\n'
            'building PrefectHQ/marvin'
        ),
        twitter_username=None,
        public_repos=52,
        public_gists=23,
        followers=47,
        following=12,
        created_at='2017-08-14T18:02:41Z',
        updated_at='2024-01-17T14:34:54Z',
        private_gists=15,
        total_private_repos=6,
        owned_private_repos=6,
        disk_usage=179750,
        collaborators=0,
        two_factor_authentication=True,
        plan={
            'name': 'pro',
            'space': 976562499,
            'collaborators': 0,
            'private_repos': 9999,
        },
    ) (GitHubUser)

```
</details>

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

<details>
<summary>Output</summary>
# [723 Dependency error with `openai`](https://api.github.com/repos/PrefectHQ/marvin/issues/723)

### First check

- [X] I added a descriptive title to this issue.
- [X] I used the GitHub search to try to find a similar issue and didn't find one.
- [X] I searched the Marvin documentation for this issue.

### Bug summary

I am getting the error ```bash ImportError: cannot import name 'OpenAI' from 'openai' ``` when trying to run a simple marvin ai function.

When tried to fix this using `pip install openai --upgrade` I get the error:
` ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
marvin 1.5.6 requires openai<1.0.0,>=0.27.8, but you have openai 1.6.1 which is incompatible.
`

### Reproduction

```python3
My code:

from marvin import ai_model
from pydantic import BaseModel, Field
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY))


class Location(BaseModel):
    city: str
    state_abbreviation: str = Field(
        ..., description="The two-letter state abbreviation"
    )


ai_model(Location, client=client)("The Big Apple")



When running this using `python marvin_scirpt.py` I am getting the mentioned error.
```


### Error

_No response_

### Versions

```Text
Version:		1.5.6
Python version:		3.11.4
OS/Arch:		darwin/arm64
```


### Additional context

_No response_
[zzstoatzz](https://api.github.com/users/zzstoatzz) said:
hi @cyai - this is our fault since our docs suggest 1.5.6 has 2.x syntax

please install from main instead (for now)
```
pip install git+https://github.com/PrefectHQ/marvin.git
```
[zzstoatzz](https://api.github.com/users/zzstoatzz) said:
hi @cyai - we've released marvin 2.1, so `pip install -U marvin` to upgrade and the docs should now be in line with that version :)
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