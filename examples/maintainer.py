import controlflow as cf
from controlflow.tools.code import python, shell
from controlflow.tools.filesystem import ALL_TOOLS as FILESYSTEM_TOOLS
from controlflow.utilities.logging import get_logger

logger = get_logger(__name__)


maintenance_agent = cf.Agent(
    name="MaintenanceBot",
    description="An agent that maintains and improves the gh-util repository",
    instructions=(
        "You are an expert in Python development and GitHub utilities. "
        "Your goal is to maintain and improve the gh-util repository. "
        "Read, iterate on, and commit changes to the `dev` branch. "
        "Always think step-by-step, start simple, and use pytest for testing. "
    ),
    tools=[shell, python, *FILESYSTEM_TOOLS],
    user_access=True,
)


@cf.flow
def maintain_gh_util():
    cf.Task(
        "Analyze current codebase",
        agents=[maintenance_agent],
        instructions="Analyze the current gh-util codebase and identify areas for improvement.",
    )

    cf.Task(
        "Improve a concrete thing within the codebase",
        agents=[maintenance_agent],
        instructions="Based on the analysis, make improvements to the codebase.",
    )

    cf.Task(
        "Test improvements",
        agents=[maintenance_agent],
        instructions="Write and run doc examples or pytest tests to ensure the improvements work as expected.",
    )

    if cf.Task(
        "Evaluate test results",
        agents=[maintenance_agent],
        instructions="Evaluate the test results to determine if the improvements are successful.",
        result_type=bool,
    ):
        pr_task = cf.Task(
            "Create pull request",
            agents=[maintenance_agent],
            instructions="Create a pull request with the improvements using the gh CLI.",
        )
        pr_task.run()


if __name__ == "__main__":
    maintain_gh_util()
