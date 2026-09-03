# Transformers Honeybot

Transformers Honeybot is a Python-based prototype for turning an existing infrastructure definition into a deployable deception environment. It reads Docker Compose or Kubernetes manifests, applies configurable transformation policies, and produces a Docker Compose blueprint that can be started and managed locally.

The project is intended for controlled security research and authorized test environments. Do not expose a generated environment to the public internet or use it to collect data without appropriate authorization.

## What it does

- Parses a Docker Compose file and evaluates services against rules in `policy.yml`.
- Replaces a matched image with a configured deception image.
- Builds a replacement application image dynamically from a selected fake application and the original build context.
- Adds a Fluentd logging service, service-level logging configuration, health checks, and generation metadata.
- Renders the result as `deception-compose.yml`.
- Provides an interactive Docker Compose controller and a file watcher for regeneration and redeployment.
- Parses Kubernetes manifests and tags matching resources using `policy_k8s.yml`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `main.py` | Docker Compose transformation pipeline and interactive deployment controller. |
| `IaC_Parser.py` / `IaC_Renderer.py` | YAML input parsing and generated Compose rendering. |
| `Policy_Engine.py` | Matches Compose services or Kubernetes resources against policy rules. |
| `Blueprint_Generator.py` | Applies tagged Compose policies and injects logging and metadata. |
| `Dockerfile_Generator.py` | Copies a fake app into a build context and writes `Dockerfile.honeypot`. |
| `Deployer.py` | Wraps `docker-compose up`, `down`, and `ps`. |
| `Sync_Controller.py` | Watches `docker-compose.yml`, regenerates the blueprint, and redeploys it. |
| `docker-compose.yml` | Example source infrastructure definition. |
| `policy.yml` | Example Docker Compose transformation rules. |
| `fake_apps/` | Fake application templates used for dynamic builds. |
| `fluentd/conf/fluent.conf` | Fluentd receiver configuration; logs are written to its standard output. |
| `k8s/`, `main_k8s.py`, `policy_k8s.yml` | Kubernetes manifest parsing and policy-tagging example. |

## Prerequisites

- Python 3.9 or newer
- Docker Engine and the legacy `docker-compose` command available on `PATH` for deployment commands
- Python packages `PyYAML` and `watchdog`

Install the pipeline dependencies:

```bash
python -m pip install PyYAML watchdog
```

The dynamically generated API image installs its own runtime dependencies from [`api/requirements.txt`](api/requirements.txt).

## Quick start: Docker Compose pipeline

From the repository root, generate the deception Compose blueprint without starting containers:

```bash
python main.py --no-interactive
```

The command reads `docker-compose.yml` and `policy.yml`, generates or updates `api/Dockerfile.honeypot` when the dynamic-build rule matches, and writes the final configuration to `deception-compose.yml`.

To generate the blueprint and then manage it interactively:

```bash
python main.py
```

Available commands are:

```text
up      # build and start the generated environment in the background
down    # stop and remove the generated environment
status  # show container status
exit    # leave the controller
```

## Configure policies

Rules live in `policy.yml`. A Compose service can be selected by an image substring or a build-context path.

```yaml
rules:
  - name: Replace a database image
    condition:
      image_name_contains: "mysql"
    action:
      type: image_replace
      payload:
        image: example/deception-image:latest

  - name: Build a replacement API
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

`image_replace` updates the service image and removes its `build` setting. `dynamic_build` copies the fake app into the matched build context and configures that service to build with `Dockerfile.honeypot`.

Before deploying, review `deception-compose.yml`: policy values, published ports, source volumes, environment variables, and generated dependency settings are inherited or derived from the input definition.

## Watch and redeploy on Compose changes

To watch the source Compose file and redeploy after changes:

```bash
python Sync_Controller.py
```

The watcher monitors `docker-compose.yml` in the repository root. On a change, it regenerates the blueprint, runs `docker-compose down`, then runs `docker-compose up --build -d`. Stop it with `Ctrl+C` to enter the interactive controller.

## Kubernetes policy tagging

The Kubernetes path currently parses YAML documents and attaches matching `x-honeypot-policy` tags; it does not render or deploy a transformed Kubernetes manifest.

`main_k8s.py` contains machine-specific absolute paths. Update `k8s_manifest_dir` and `policy_file` to paths on your machine before running it, or use the parser and policy engine directly:

```python
from Kubernetes_Parser import KubernetesParser
from Policy_Engine import PolicyEngine

resources = KubernetesParser().parse("k8s")
tagged_resources = PolicyEngine("policy_k8s.yml").apply(resources)
```

## Logs and verification

Generated Compose services send logs to the bundled Fluentd service using the `fluentd` logging driver. After starting the environment, inspect logs and status with:

```bash
docker-compose -f deception-compose.yml ps
docker-compose -f deception-compose.yml logs -f logging
```

## Notes

- The sample configuration includes example credentials and exposed ports. Replace them before any non-local use.
- Dynamic builds modify the selected build context by creating `_honeypot_app/` and `Dockerfile.honeypot`. These generated files can be regenerated by rerunning the pipeline.
- Test only systems and networks you own or are explicitly authorized to assess.

## License

No license file is currently included in this repository. Treat reuse and distribution as requiring the repository owner's permission unless a license is added.
