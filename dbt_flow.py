"""
Example flow that simulates a dbt job with a configurable failure mode.
Used to demonstrate auto-resuming failed flows when a hotfix PR is merged.
"""
import json
from pathlib import Path

from prefect import flow, task


@task
def load_config() -> dict:
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    return json.loads(config_path.read_text())


@task
def run_dbt_model(model_name: str, config: dict):
    """Simulate running a dbt model - fails if config has bad dependency"""
    print(f"Running dbt model: {model_name}")

    if config.get("missing_dependency"):
        raise ValueError(
            f"Model '{model_name}' failed: missing dependency "
            f"'{config['missing_dependency']}'"
        )

    print(f"Model '{model_name}' completed successfully!")
    return {"model": model_name, "status": "success"}


@flow(log_prints=True)
def daily_dbt_job():
    """Daily dbt job that processes models"""
    print("Starting daily dbt job...")

    config = load_config()

    # Run the model (will fail if config has missing_dependency)
    result = run_dbt_model("my_model", config)

    print(f"Job completed: {result}")
    return result


if __name__ == "__main__":
    daily_dbt_job()
