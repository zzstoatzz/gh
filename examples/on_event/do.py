"""React to arbitrary events from a GitHub repository.

Setup:
    ```bash
    pip install gh-util marvin prefect
    
    export GITHUB_TOKEN=<your-github-token>
    export OPENAI_API_KEY=<your-openai-api-key>
    ```
"""
from urllib.parse import unquote

from devtools import debug
from gh_util.types import GitHubWebhookEvent
from prefect import flow
from prefect.events.schemas import DeploymentTrigger


@flow(log_prints=True)
async def do(event_body_json: str):
    """Label issues based on incoming webhook events from GitHub."""
    event = GitHubWebhookEvent.model_validate_json(
        unquote(event_body_json).replace("payload=", "")
    )

    debug(event)


if __name__ == "__main__":
    do.serve(
        name="React to repo events",
        triggers=[
            DeploymentTrigger(
                expect={"gh.issue*"},
                parameters={"event_body_json": "{{ event.payload.body }}"},
            )
        ],
    )
