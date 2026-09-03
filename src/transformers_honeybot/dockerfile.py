"""Dynamic Dockerfile generation for replacement applications."""

import shutil
from pathlib import Path
from typing import Any, Optional


class DockerfileGenerator:
    """Create a honeypot Dockerfile inside an existing build context."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.base_dir / candidate

    @staticmethod
    def _get_original_info(context_path: Path, instruction: str) -> Optional[str]:
        try:
            with (context_path / "Dockerfile").open("r", encoding="utf-8") as source:
                for line in source:
                    if line.strip().upper().startswith(instruction.upper()):
                        return line.strip()
        except FileNotFoundError:
            return None
        return None

    def generate(
        self,
        build_policy: dict[str, Any],
        original_context_path: str | Path,
        output_filename: str = "Dockerfile.honeypot",
    ) -> Optional[Path]:
        context_path = self._resolve(original_context_path)
        fake_app_path = build_policy.get("fake_app_path")
        if not fake_app_path:
            print("ERROR: DockerfileGenerator requires 'fake_app_path' in the policy.")
            return None
        fake_app_source = self._resolve(fake_app_path)
        honeypot_app_in_context = context_path / "_honeypot_app"
        print(f"DockerfileGenerator: generating '{output_filename}' for '{context_path}'...")

        try:
            if honeypot_app_in_context.exists():
                shutil.rmtree(honeypot_app_in_context)
            shutil.copytree(fake_app_source, honeypot_app_in_context)
        except OSError as error:
            print(f"ERROR: DockerfileGenerator could not copy fake app: {error}")
            return None

        base_image = "FROM python:3.9-slim"
        if build_policy.get("use_original_base_image"):
            base_image = self._get_original_info(context_path, "FROM") or base_image

        lines = [base_image, "WORKDIR /app"]
        dependencies = build_policy.get("copy_dependencies", [])
        for dependency in dependencies:
            lines.append(f"COPY {dependency} .")
        if "requirements.txt" in dependencies:
            lines.append("RUN pip install -r requirements.txt")
        lines.extend([
            f"COPY {honeypot_app_in_context.name} .",
            'CMD ["python", "app.py"]',
        ])

        try:
            output_path = context_path / output_filename
            output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"Successfully created '{output_path}'")
            return output_path
        except OSError as error:
            print(f"ERROR: DockerfileGenerator could not write Dockerfile: {error}")
            return None
