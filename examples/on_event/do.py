"""React to arbitrary events from a GitHub repository.

Setup:
    Install and export the necessary environment variables:
    ```bash
    pip install gh-util marvin prefect

    export GITHUB_TOKEN=<your-github-token>
    export OPENAI_API_KEY=<your-openai-api-key>
    export PREFECT_API_URL=<your-prefect-api-url>
    export PREFECT_API_KEY=<your-prefect-api-key>
    ```

    see `Dockerfile.do`
"""

from urllib.parse import unquote

from devtools import debug
from gh_util.types import GitHubWebhookEvent
from prefect import flow
from prefect.client.schemas.objects import Flow, FlowRun, State
from prefect.events.schemas import DeploymentTrigger
from tasks import label_issues

TYPES_OF_ACTIONS_I_CARE_ABOUT = {"opened", "reopened", "edited", "labeled", "unlabeled"}


async def label_issues_if_appropriate(
    flow: Flow, flow_run: FlowRun, state: State
) -> None:
    """Run a task asynchronously."""
    _, _ = flow, flow_run
    event = await state.result().get()

    if event.action not in TYPES_OF_ACTIONS_I_CARE_ABOUT:
        return

    await label_issues.submit(event=event)


@flow(
    log_prints=True,
    persist_result=True,
    on_completion=[label_issues_if_appropriate],
)
async def do(event_json_str: str) -> GitHubWebhookEvent | None:
    """do something when GitHub some event occurs"""

    debug(
        event := GitHubWebhookEvent.model_validate_json(
            unquote(event_json_str).replace("payload=", "")
        )
    )

    print(f"responding to {(kind := getattr(event, 'action', 'unknown'))} event")

    if kind == "unknown":
        return None
    return event


if __name__ == "__main__":
    do.serve(
        name="React to repo events",
        triggers=[
            DeploymentTrigger(
                expect={"gh.issue*"},
                parameters={"event_json_str": "{{ event.payload.body }}"},
            )
        ],
    )
