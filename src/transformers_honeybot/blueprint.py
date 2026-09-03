"""Compose blueprint transformation and common service injection."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .dockerfile import DockerfileGenerator


class HoneypotBlueprintGenerator:
    """Turn policy-tagged Compose data into a deployable blueprint."""

    def __init__(self, workspace_dir: str | Path):
        self.dockerfile_gen = DockerfileGenerator(workspace_dir)

    def generate(self, tagged_data: dict[str, Any]) -> dict[str, Any]:
        print("BlueprintGenerator: starting final blueprint generation...")
        blueprint = deepcopy(tagged_data)
        for service_name, service in blueprint.get("services", {}).items():
            policy = service.get("x-honeypot-policy")
            if not policy:
                continue
            policy_type = policy.get("type")
            payload = policy.get("payload", {})
            print(f"  - Processing policy '{policy_type}' for service '{service_name}'...")
            if policy_type == "image_replace":
                self._apply_image_replace(service, payload)
            elif policy_type == "dynamic_build":
                self._apply_dynamic_build(service, payload, service_name)
            else:
                print(f"  - Warning: unsupported policy type '{policy_type}'.")

        self._inject_logging_service(blueprint)
        self._inject_metadata(blueprint)
        print("BlueprintGenerator: blueprint generation complete.")
        return blueprint

    @staticmethod
    def _apply_image_replace(service: dict[str, Any], payload: dict[str, Any]) -> None:
        replacement_image = payload.get("image")
        if replacement_image:
            service["image"] = replacement_image
            service.pop("build", None)
        service.pop("x-honeypot-policy", None)

    def _apply_dynamic_build(
        self,
        service: dict[str, Any],
        payload: dict[str, Any],
        service_name: str,
    ) -> None:
        build_info = service.get("build", {})
        context = build_info if isinstance(build_info, str) else build_info.get("context")
        if not context:
            print(f"  - Warning: no build context for '{service_name}'; skipping dynamic build.")
            return

        generated = self.dockerfile_gen.generate(payload, context)
        if generated:
            service["build"] = {"context": context, "dockerfile": generated.name}
            service.pop("x-honeypot-policy", None)

    @staticmethod
    def _inject_logging_service(blueprint: dict[str, Any]) -> None:
        print("  - Injecting unified Fluentd logging service with health checks...")
        services = blueprint.setdefault("services", {})
        services["logging"] = {
            "image": "fluent/fluentd:v1.16-1",
            "ports": ["24224:24224", "24224:24224/udp"],
            "volumes": ["./fluentd/conf:/fluentd/etc"],
            "restart": "always",
            "healthcheck": {
                "test": ["CMD-SHELL", "nc -z 127.0.0.1 24224"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
                "start_period": "10s",
            },
        }
        for name, service in services.items():
            if name == "logging":
                continue
            service["logging"] = {
                "driver": "fluentd",
                "options": {"tag": f"honeypot.{name}"},
            }
            service["depends_on"] = {"logging": {"condition": "service_healthy"}}

    @staticmethod
    def _inject_metadata(blueprint: dict[str, Any]) -> None:
        timestamp = datetime.now(timezone(timedelta(hours=9))).isoformat()
        blueprint["x-metadata"] = {
            "blueprint_version": "1.0",
            "generated_at": timestamp,
            "generator": "HoneypotBlueprintGenerator",
        }
