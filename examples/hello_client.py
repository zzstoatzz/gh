from gh_util.client import GHClient


async def main():
    async with GHClient() as client:
        response = await client.get("/user")
        print(response.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
