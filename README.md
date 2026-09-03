# Transformers Honeybot

**Transformers Honeybot is an IaC Reflection framework for building and keeping a cyber-deception environment in sync with a source infrastructure definition.**

Rather than hand-crafting a separate honeypot, the project treats Docker Compose (and, for policy tagging, Kubernetes) manifests as a structural blueprint. It applies explicit transformation policies to create a separately deployable, look-alike environment: infrastructure-facing details such as service layout, exposed ports, selected configuration, and build context are retained where appropriate, while selected images or application logic are replaced with safe deception components. When the source Compose file changes, the watcher can regenerate and redeploy the generated environment.

This repository is a prototype for authorized cyber-deception research and controlled test environments. It is not a production deployment system, and generated environments must never be exposed publicly or used to collect data without authorization.

## Core ideas

- **IaC Reflection:** parse infrastructure definitions as structured YAML and transform services through policy rules, rather than using broad text replacement.
- **Look-alike deception environments:** retain useful operational structure from the source definition while substituting selected service images or application behavior.
- **Policy-driven transformation:** choose the services to transform by image name or build context in a reviewable YAML policy.
- **Self-synchronization:** watch the source Compose file; after a change, regenerate the blueprint and optionally recreate the deception environment.
- **Observable deployment:** inject Fluentd logging configuration and health-aware service dependencies into generated Compose output.

## Supported scope

| Input | Current capability |
| --- | --- |
| Docker Compose YAML | Parse, apply `image_replace` and `dynamic_build` policies, render a new Compose file, and manage it through Docker Compose. |
| Kubernetes YAML | Parse resources and attach matching policy tags for inspection. Rendering and deployment of transformed Kubernetes manifests are not implemented yet. |

## Project layout

```text
src/transformers_honeybot/  Python package and command-line interface
tests/                      Automated regression tests
scripts/                    Development utilities and fixture generators
docker-compose.yml          Example source infrastructure definition
policy.yml                  Example Compose transformation policy
k8s/                        Example Kubernetes manifests
policy_k8s.yml              Example Kubernetes tagging policy
fake_apps/                  Replacement application templates
fluentd/                    Generated-environment logging configuration
```

## Requirements

- Python 3.9 or newer
- Docker Engine with the Docker Compose v2 plugin (`docker compose`) for deployment and log commands

Install the project and its Python dependencies from the repository root:

```bash
python -m pip install -e .
```

## Quick start

Generate a Compose deception blueprint without starting containers:

```bash
honeybot compose --no-interactive
```

The command uses `docker-compose.yml` and `policy.yml` by default. It writes `deception-compose.yml`, and a matching `dynamic_build` policy generates `Dockerfile.honeypot` inside the selected build context.

Use custom paths when the source files live elsewhere:

```bash
honeybot compose \
  --source path/to/docker-compose.yml \
  --policy path/to/policy.yml \
  --output path/to/deception-compose.yml \
  --no-interactive
```

Omit `--no-interactive` to open a controller after generation:

```text
up      Build and start the generated environment in the background
down    Stop and remove the generated environment
status  Show generated-environment container status
exit    Leave the controller
```

You can also run the package without installing its console command after adding `src` to your environment:

```bash
python -m transformers_honeybot compose --no-interactive
```

## Configure transformation policies

`policy.yml` defines which services are transformed and how. Rules are evaluated in order; the first matching rule tags a service for transformation.

```yaml
rules:
  - name: Replace a database image
    condition:
      image_name_contains: "mysql"
    action:
      type: image_replace
      payload:
        image: example/deception-database:latest

  - name: Build a replacement application
    condition:
      build_context: "./api"
    action:
      type: dynamic_build
      payload:
        use_original_base_image: true
        fake_app_path: "./fake_apps/python-flask-generic"
        copy_dependencies:
          - requirements.txt
```

`image_replace` switches the selected service image and removes its `build` setting. `dynamic_build` copies the selected fake application into the selected build context, creates `Dockerfile.honeypot`, and changes the service to use that Dockerfile. Relative paths are resolved from the source Compose file's directory, so the same command works from another current directory.

Always review the generated Compose file before deployment. It can retain source-defined ports, volumes, environment variables, and other configuration that may be unsuitable for a test environment.

## Synchronize with source changes

Watch a source Compose file and recreate the generated environment after edits:

```bash
honeybot watch
```

The watcher regenerates the blueprint, stops the prior generated environment, and starts a rebuilt replacement. Use the same `--source`, `--policy`, and `--output` arguments as `compose` to work with non-default paths. Press `Ctrl+C` to stop watching and enter the manual controller.

## Kubernetes policy inspection

Kubernetes support currently helps inspect which resources match policies; it does not alter or deploy manifests:

```bash
honeybot k8s --manifests k8s --policy policy_k8s.yml
```

This command replaces the previous hardcoded Windows paths with portable command-line options.

## Logs and cleanup

Generated services send logs through the bundled Fluentd service. After deployment:

```bash
docker compose -f deception-compose.yml ps
docker compose -f deception-compose.yml logs -f logging
docker compose -f deception-compose.yml down
```

Dynamic builds create `_honeypot_app/` and `Dockerfile.honeypot` in the relevant build context. They are regenerated whenever the pipeline runs.

## Development checks

Run the regression tests without installation by setting the source path:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Create disposable Compose and policy fixtures outside the repository root:

```bash
python scripts/generate_test_files.py --output-dir .tmp/honeybot-fixtures
```

## Safety notes

- Use only systems, networks, and data that you own or are explicitly authorized to assess.
- Replace sample credentials and review every published port before any non-local run.
- Treat generated output as test infrastructure, not a substitute for production security controls.

## License

No license file is currently included. Reuse and distribution require the repository owner's permission unless a license is added.
