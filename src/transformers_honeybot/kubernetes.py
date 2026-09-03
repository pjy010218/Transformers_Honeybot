"""Kubernetes manifest parsing."""

from pathlib import Path
from typing import Any, Optional

import yaml


class KubernetesParser:
    """Load every YAML document found directly under a manifest directory."""

    def parse(self, directory_path: str | Path) -> Optional[list[dict[str, Any]]]:
        path = Path(directory_path)
        print(f"Parsing Kubernetes manifests in '{path}'...")
        if not path.is_dir():
            print(f"ERROR: The directory '{path}' was not found.")
            return None

        resources: list[dict[str, Any]] = []
        yaml_files = sorted({*path.glob("*.yaml"), *path.glob("*.yml")})
        if not yaml_files:
            print(f"ERROR: No YAML files found in '{path}'.")
            return []

        try:
            for file_path in yaml_files:
                with file_path.open("r", encoding="utf-8") as manifest:
                    documents = [document for document in yaml.safe_load_all(manifest) if document]
                print(f"  - Parsed {len(documents)} resource(s) from '{file_path.name}'")
                resources.extend(documents)
        except (OSError, yaml.YAMLError) as error:
            print(f"ERROR: Could not parse Kubernetes manifests: {error}")
            return None

        print(f"Parsed {len(resources)} Kubernetes resource(s).")
        return resources
