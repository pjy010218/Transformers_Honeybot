"""End-to-end Docker Compose transformation workflow."""

from pathlib import Path
from time import perf_counter
from typing import Optional

from .blueprint import HoneypotBlueprintGenerator
from .deployment import DeploymentActuator
from .iac import IaCParser, IaCRenderer
from .policy import PolicyEngine


def run_pipeline_generation(
    source_iac_file: str | Path = "docker-compose.yml",
    policy_file: str | Path = "policy.yml",
    output_iac_file: str | Path = "deception-compose.yml",
) -> Optional[Path]:
    """Generate a Docker Compose deception blueprint from a source definition."""
    source_path = Path(source_iac_file).resolve()
    policy_path = Path(policy_file).resolve()
    output_path = Path(output_iac_file).resolve()
    start_time = perf_counter()
    print("Starting the blueprint-generation pipeline...")

    original_data = IaCParser().parse(source_path)
    if original_data is None:
        return None

    tagged_data = PolicyEngine(policy_path).apply(original_data)
    blueprint = HoneypotBlueprintGenerator(source_path.parent).generate(tagged_data)
    if not IaCRenderer().render(blueprint, output_path):
        return None

    print(f"Pipeline completed in {perf_counter() - start_time:.3f} seconds.")
    print(f"[SUCCESS] Blueprint generation finished: '{output_path}'")
    return output_path


def start_interactive_control(compose_file_path: str | Path) -> None:
    """Run a small interactive controller for an already-generated blueprint."""
    actuator = DeploymentActuator(compose_file_path)
    while True:
        print("\n======= Deception Environment Control =======")
        action = input("Enter command (up / down / status / exit): ").strip().lower()
        if action == "up":
            actuator.up(build=True)
        elif action == "down":
            actuator.down()
        elif action == "status":
            actuator.status()
        elif action == "exit":
            print("Exiting controller.")
            return
        else:
            print(f"Unknown command: '{action}'")
