import tempfile
import unittest
from pathlib import Path

import yaml

from transformers_honeybot.kubernetes import KubernetesParser
from transformers_honeybot.pipeline import run_pipeline_generation
from transformers_honeybot.policy import PolicyEngine

TEST_TEMP_ROOT = Path(__file__).resolve().parents[1] / ".test-tmp"


class PipelineTests(unittest.TestCase):
    def test_compose_pipeline_generates_a_deception_blueprint(self):
        TEST_TEMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as temporary_directory:
            root = Path(temporary_directory)
            (root / "api").mkdir()
            (root / "fake_apps" / "generic").mkdir(parents=True)
            (root / "api" / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")
            (root / "api" / "requirements.txt").write_text("flask\n", encoding="utf-8")
            (root / "fake_apps" / "generic" / "app.py").write_text("print('ok')\n", encoding="utf-8")

            compose = {
                "services": {
                    "database": {"image": "mysql:8.0"},
                    "api": {"build": "./api"},
                }
            }
            policy = {
                "rules": [
                    {
                        "condition": {"image_name_contains": "mysql"},
                        "action": {"type": "image_replace", "payload": {"image": "example/fake-db"}},
                    },
                    {
                        "condition": {"build_context": "./api"},
                        "action": {
                            "type": "dynamic_build",
                            "payload": {
                                "use_original_base_image": True,
                                "fake_app_path": "./fake_apps/generic",
                                "copy_dependencies": ["requirements.txt"],
                            },
                        },
                    },
                ]
            }
            source_path = root / "compose.yml"
            policy_path = root / "policy.yml"
            output_path = root / "generated.yml"
            source_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

            result = run_pipeline_generation(source_path, policy_path, output_path)
            generated = yaml.safe_load(output_path.read_text(encoding="utf-8"))

            self.assertEqual(result, output_path.resolve())
            self.assertEqual(generated["services"]["database"]["image"], "example/fake-db")
            self.assertEqual(generated["services"]["api"]["build"]["dockerfile"], "Dockerfile.honeypot")
            self.assertIn("logging", generated["services"])
            self.assertTrue((root / "api" / "_honeypot_app" / "app.py").is_file())

    def test_kubernetes_parser_and_policy_engine_tag_matching_resource(self):
        TEST_TEMP_ROOT.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as temporary_directory:
            root = Path(temporary_directory)
            manifests = root / "manifests"
            manifests.mkdir()
            (manifests / "deployment.yaml").write_text(
                "kind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n        - image: nginx:latest\n",
                encoding="utf-8",
            )
            (root / "policy.yml").write_text(
                "rules:\n  - condition:\n      kubernetes_resource:\n        kind: Deployment\n        path: spec.template.spec.containers.0.image\n        value_contains: nginx\n    action:\n      type: image_replace\n",
                encoding="utf-8",
            )

            resources = KubernetesParser().parse(manifests)
            tagged = PolicyEngine(root / "policy.yml").apply(resources)

            self.assertEqual(tagged[0]["x-honeypot-policy"]["type"], "image_replace")


if __name__ == "__main__":
    unittest.main()
