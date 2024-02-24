from urllib.parse import unquote

from devtools import debug
from gh_util.types import GitHubIssueEvent
from prefect import flow
from prefect.events.schemas import DeploymentTrigger


# pip install prefect
@flow
def on_issue_event(webhook_event_str: str):
    webhook_event = GitHubIssueEvent.model_validate_json(
        unquote(webhook_event_str).replace("payload=", "")
    )
    debug(webhook_event)


if __name__ == "__main__":
    on_issue_event.serve(
        name="Handle GitHub webhook",
        triggers=[
            DeploymentTrigger(
                expect={"gh.issue*"},
                parameters={"webhook_event_str": "{{ event.payload.body }}"},
            )
        ],
    )
