from gh_util.functions import fetch_repo_labels


async def main():
    labels = await fetch_repo_labels("python", "cpython")
    print(labels)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
