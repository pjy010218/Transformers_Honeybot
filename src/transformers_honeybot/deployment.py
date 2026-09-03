"""Docker Compose deployment commands."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


class DeploymentActuator:
    """Start, stop, and inspect a generated Docker Compose environment."""

    def __init__(self, compose_file_path: str | Path):
        self.compose_file_path = Path(compose_file_path).resolve()
        print(f"Deployer initialized for '{self.compose_file_path}'")

    @staticmethod
    def _compose_prefix() -> list[str]:
        if shutil.which("docker"):
            return ["docker", "compose"]
        return ["docker-compose"]

    def _run_command(self, command: list[str]) -> bool:
        try:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=True,
                encoding="utf-8",
                cwd=self.compose_file_path.parent,
            )
            if result.stdout:
                print(result.stdout)
            return True
        except FileNotFoundError:
            print("ERROR: Docker Compose was not found. Install Docker Desktop or Docker Compose.")
        except subprocess.CalledProcessError as error:
            print(f"ERROR: command failed with exit code {error.returncode}")
            if error.stderr:
                print(error.stderr)
        return False

    def _command(self, *arguments: str) -> list[str]:
        return [*self._compose_prefix(), "-f", str(self.compose_file_path), *arguments]

    def up(self, detach: bool = True, build: bool = False) -> bool:
        print("Starting deception environment...")
        arguments = ["up"]
        if build:
            arguments.append("--build")
        if detach:
            arguments.append("-d")
        return self._run_command(self._command(*arguments))

    def down(self) -> bool:
        print("Stopping deception environment...")
        return self._run_command(self._command("down"))

    def status(self) -> bool:
        print("Checking deception environment status...")
        return self._run_command(self._command("ps"))
