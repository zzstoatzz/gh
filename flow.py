"""Example flow that fails based on config."""
import json
from pathlib import Path
from prefect import flow


@flow(log_prints=True)
def my_flow():
    config = json.loads((Path(__file__).parent / "config.json").read_text())

    if config.get("should_fail"):
        raise ValueError(f"Flow failed: {config['should_fail']}")

    print("Flow completed successfully!")


if __name__ == "__main__":
    my_flow()
