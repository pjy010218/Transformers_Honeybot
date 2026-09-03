"""Command-line interface for Transformers Honeybot."""

import argparse
import pprint
from pathlib import Path

from .kubernetes import KubernetesParser
from .pipeline import run_pipeline_generation, start_interactive_control
from .policy import PolicyEngine


def _add_compose_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", default="docker-compose.yml", help="source Docker Compose YAML")
    parser.add_argument("--policy", default="policy.yml", help="Compose policy YAML")
    parser.add_argument("--output", default="deception-compose.yml", help="generated Compose YAML")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="honeybot",
        description="Generate and synchronize IaC-derived deception environments.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    compose = subcommands.add_parser("compose", help="generate a Compose blueprint")
    _add_compose_arguments(compose)
    compose.add_argument("--no-interactive", action="store_true", help="generate only; do not open the controller")

    watch = subcommands.add_parser("watch", help="watch a Compose source and redeploy after changes")
    _add_compose_arguments(watch)

    kubernetes = subcommands.add_parser("k8s", help="parse and tag Kubernetes manifests")
    kubernetes.add_argument("--manifests", default="k8s", help="directory containing Kubernetes YAML files")
    kubernetes.add_argument("--policy", default="policy_k8s.yml", help="Kubernetes policy YAML")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "compose":
        output = run_pipeline_generation(args.source, args.policy, args.output)
        if output and not args.no_interactive:
            start_interactive_control(output)
    elif args.command == "watch":
        from .sync import watch_and_sync

        watch_and_sync(args.source, args.policy, args.output)
    elif args.command == "k8s":
        resources = KubernetesParser().parse(args.manifests)
        if resources is not None:
            pprint.pprint(PolicyEngine(args.policy).apply(resources), sort_dicts=False)
