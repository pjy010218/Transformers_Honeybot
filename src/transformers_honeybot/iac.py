"""Docker Compose YAML parsing and rendering."""

from pathlib import Path
from typing import Any, Optional

import yaml


class IaCParser:
    """Load a YAML-based infrastructure definition."""

    def parse(self, file_path: str | Path) -> Optional[dict[str, Any]]:
        path = Path(file_path)
        try:
            with path.open("r", encoding="utf-8") as source:
                data = yaml.safe_load(source)
            if not isinstance(data, dict):
                print(f"ERROR: '{path}' must contain a YAML mapping.")
                return None
            print(f"Successfully parsed: '{path}'")
            return data
        except FileNotFoundError:
            print(f"ERROR: The file '{path}' was not found.")
        except yaml.YAMLError as error:
            print(f"ERROR: Failed to parse YAML file '{path}'.\n{error}")
        return None


class IaCRenderer:
    """Write a generated Compose blueprint as YAML."""

    def render(self, blueprint: dict[str, Any], output_path: str | Path) -> bool:
        path = Path(output_path)
        print(f"Rendering final blueprint to '{path}'...")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as output:
                yaml.safe_dump(
                    blueprint,
                    output,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                )
            print(f"Successfully saved the final blueprint to '{path}'")
            return True
        except OSError as error:
            print(f"ERROR: Could not render YAML file '{path}': {error}")
            return False
