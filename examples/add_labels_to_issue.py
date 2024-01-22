from gh_util.functions import add_labels_to_issue


async def label_issue():
    await add_labels_to_issue(
        owner="PrefectHQ",
        repo="marvin",
        issue_number=1,
        new_labels=["bug", "enhancement"],
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(label_issue())
