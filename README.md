# gh_util

A minimal Python library for interacting with GitHub's API, using `httpx` and `Pydantic`.

## **NOTE**
This library is under active development and will likely change.


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
from gh_util.functions import fetch_repo_issue
from gh_util.print import print_repo_issue


async def main():
    issue = await fetch_repo_issue("prefecthq", "marvin", 723, include_comments=True)
    print_repo_issue(issue)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

<details>
<summary>Output</summary>

![read issue demo](docs/assets/gifs/gh-util-demo-read-issue.gif)

</details>