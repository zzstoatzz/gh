import asyncio

from gh_util.client import GHClient
from gh_util.print import print_user
from gh_util.types import GitHubUser


async def get_current_user() -> GitHubUser:
    async with GHClient() as client:
        response = await client.get("/user")
        return GitHubUser.model_validate(response.json())


async def main():
    print_user(await get_current_user())


if __name__ == "__main__":
    asyncio.run(main())
