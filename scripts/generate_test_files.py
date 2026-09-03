"""Create disposable Compose and policy fixtures for local scalability experiments."""

import argparse
from pathlib import Path

import yaml


def generate_files(output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Generating test fixtures in '{output_path}'...")

    compose_data = {"services": {}}
    for index in range(1, 25):
        compose_data["services"][f"service-{index}"] = {"image": f"alpine:3.{index % 10 + 10}"}
    compose_data["services"]["buildable-service"] = {"build": "./buildable_service_context"}
    (output_path / "docker-compose.complex.yml").write_text(
        yaml.safe_dump(compose_data, sort_keys=False), encoding="utf-8"
    )

    rules = [
        {
            "name": f"Replace service-{index}",
            "condition": {"image_name_contains": f"alpine:3.{index + 9}"},
            "action": {"type": "image_replace", "payload": {"image": f"honeypot/dummy:{index}.0"}},
        }
        for index in range(1, 10)
    ]
    rules.append(
        {
            "name": "Dynamic build for buildable-service",
            "condition": {"build_context": "./buildable_service_context"},
            "action": {
                "type": "dynamic_build",
                "payload": {
                    "use_original_base_image": True,
                    "fake_app_path": "./fake_apps/python-flask-generic",
                    "copy_dependencies": ["requirements.txt"],
                },
            },
        }
    )
    (output_path / "policy.complex.yml").write_text(
        yaml.safe_dump({"rules": rules}, sort_keys=False), encoding="utf-8"
    )

    context = output_path / "buildable_service_context"
    context.mkdir(exist_ok=True)
    (context / "Dockerfile").write_text('FROM python:3.9-slim\nCMD ["echo", "hello"]\n', encoding="utf-8")
    (context / "requirements.txt").write_text("flask\n", encoding="utf-8")
    print("Test fixture generation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=".tmp/honeybot-fixtures")
    generate_files(parser.parse_args().output_dir)
