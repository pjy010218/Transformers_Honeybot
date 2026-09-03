"""Policy matching for Docker Compose and Kubernetes resources."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class PolicyEngine:
    """Apply the first matching policy rule to each parsed resource."""

    def __init__(self, policy_file_path: str | Path):
        path = Path(policy_file_path)
        try:
            with path.open("r", encoding="utf-8") as policy_file:
                policy_data = yaml.safe_load(policy_file) or {}
            self.rules = policy_data.get("rules", [])
            if not isinstance(self.rules, list):
                raise ValueError("'rules' must be a list")
            print(f"PolicyEngine: loaded {len(self.rules)} rule(s) from '{path}'")
        except (OSError, ValueError, yaml.YAMLError) as error:
            print(f"ERROR: PolicyEngine failed loading policy file '{path}': {error}")
            self.rules: list[dict[str, Any]] = []

    @staticmethod
    def _get_value_by_path(data: dict[str, Any], path: str) -> Any:
        current: Any = data
        for key in path.split("."):
            if key.isdigit():
                index = int(key)
                if not isinstance(current, list) or index >= len(current):
                    return None
                current = current[index]
            elif not isinstance(current, dict) or key not in current:
                return None
            else:
                current = current[key]
        return current

    def _apply_docker_compose_rules(self, data: dict[str, Any]) -> dict[str, Any]:
        for service_name, service_details in data.get("services", {}).items():
            for rule in self.rules:
                condition = rule.get("condition", {})
                action = rule.get("action", {})
                image_substring = condition.get("image_name_contains")
                image_match = bool(image_substring) and image_substring in service_details.get("image", "")
                build_info = service_details.get("build", {})
                build_context = build_info if isinstance(build_info, str) else build_info.get("context")
                expected_context = condition.get("build_context")
                build_match = bool(expected_context) and expected_context == build_context

                if image_match or build_match:
                    service_details["x-honeypot-policy"] = action
                    print(f"  - Tagged policy '{rule.get('name', '[unnamed]')}' on service '{service_name}'")
                    break
        return data

    def _apply_kubernetes_rules(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for resource in resources:
            for rule in self.rules:
                condition = rule.get("condition", {}).get("kubernetes_resource", {})
                if resource.get("kind") != condition.get("kind"):
                    continue
                value = self._get_value_by_path(resource, condition.get("path", ""))
                value_substring = condition.get("value_contains")
                if value is not None and value_substring is not None and value_substring in str(value):
                    resource["x-honeypot-policy"] = rule.get("action", {})
                    name = resource.get("metadata", {}).get("name", "[unknown]")
                    print(f"  - Tagged policy '{rule.get('name', '[unnamed]')}' on resource '{name}'")
                    break
        return resources

    def apply(self, parsed_data: Any) -> Any:
        """Return a copy of *parsed_data* annotated with matching policies."""
        print("PolicyEngine: applying policies by tagging...")
        tagged_data = deepcopy(parsed_data)
        if isinstance(tagged_data, list):
            return self._apply_kubernetes_rules(tagged_data)
        if isinstance(tagged_data, dict) and "services" in tagged_data:
            return self._apply_docker_compose_rules(tagged_data)
        print("Warning: unrecognized data structure. No policies applied.")
        return tagged_data
