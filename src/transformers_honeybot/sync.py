"""Source-IaC file watching and automatic regeneration."""

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .deployment import DeploymentActuator
from .pipeline import run_pipeline_generation, start_interactive_control


class ChangeHandler(FileSystemEventHandler):
    """Regenerate and redeploy when the selected source file changes."""

    def __init__(self, source_file: Path, policy_file: Path, output_file: Path):
        self.source_file = source_file.resolve()
        self.policy_file = policy_file.resolve()
        self.output_file = output_file.resolve()
        self.actuator = DeploymentActuator(self.output_file)
        print(f"Watching for changes in: '{self.source_file}'")

    def on_modified(self, event) -> None:
        if event.is_directory or Path(event.src_path).resolve() != self.source_file:
            return
        print(f"\n[CHANGE] Change detected in '{self.source_file.name}'.")
        generated = run_pipeline_generation(self.source_file, self.policy_file, self.output_file)
        if not generated:
            print("[ERROR] Blueprint generation failed; deployment was not changed.")
            return
        self.actuator.down()
        self.actuator.up(build=True)
        print("Auto redeployment finished successfully. Watching for changes again...")


def watch_and_sync(
    source_file: str | Path = "docker-compose.yml",
    policy_file: str | Path = "policy.yml",
    output_file: str | Path = "deception-compose.yml",
) -> None:
    """Watch a Compose source file until interrupted."""
    source_path = Path(source_file).resolve()
    handler = ChangeHandler(source_path, Path(policy_file), Path(output_file))
    observer = Observer()
    observer.schedule(handler, str(source_path.parent), recursive=False)
    observer.start()
    print("====== Sync Controller Started (Auto-Deploy Mode) ======")
    print("Press Ctrl+C to stop watching and switch to manual control.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Sync Controller stopped. Starting manual control...")
    observer.join()
    start_interactive_control(handler.output_file)
