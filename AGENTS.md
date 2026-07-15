# ML-Detector AGENTS.md

## Project overview

**ML Detector** is a Python 3.13 FastAPI service that uses YOLO11 (ultralytics) for object detection in images. Default configuration detects persons (COCO class 0) but can be configured for any COCO classes.

- Runtime: `uv` (package manager), `uvicorn` (ASGI server)
- ML: `ultralytics` (YOLO11), `opencv-python-headless`, `torch`/`torchvision`
- Config: YAML via `config/configuration.yaml`
- Linting: `ruff` (all rules, line-length 120), `basedpyright` (strict mode)
- Testing: `pytest` + `pytest-asyncio` (all mocked — no GPU needed)
- Hooks: `pre-commit` (ruff-format, ruff-check, basedpyright, yamllint, markdownlint, gitleaks, etc.)
- CI: reusable workflows from `techtales-io/github-workflows` for Docker build and Renovate

## Repo initialization checklist

Before any code changes, run in this exact order:

1. `git switch main && git pull origin main`
2. `task sync -- cpu`
3. `task lint`

If a different branch is needed, create it AFTER step 1.

## Architecture

### Source files (`src/`)

| File               | Purpose                                                                                                                                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/config.py`    | `ConfigurationManager` — loads `config/configuration.yaml`, returns typed dataclasses: `ServerConfig`, `ModelConfig`, `InferenceConfig`, `AppConfig`. Uses `CONFIG_PATH` env var for path override.                     |
| `src/model.py`     | `PersonDetector` — wraps YOLO11 model. Lazy-loads from `./models/`. Supports model download on startup. `detect_persons()` accepts bytes/str/np.ndarray/PIL.Image. `_process_results()` filters by `classes_to_detect`. |
| `src/inference.py` | FastAPI app (`app`) with lifespan-managed model loading. State machine: `INITIALIZING → READY → SHUTTING_DOWN`. 4 endpoints: `GET /`, `GET /livez`, `GET /readyz`, `POST /detect`.                                      |

### Configuration (`config/configuration.yaml`)

```yaml
server: # host, port, reload
model: # size (nano/small/medium/large/xlarge), device (cpu/cuda), custom_model_path, models_dir, download_on_startup
inference: # conf_threshold, iou_threshold, max_detections, img_size, half_precision, retina_masks, verbose
classes_to_detect: [0] # COCO class IDs; 0 = person
```

### Tests (`tests/`)

- `conftest.py` — shared fixtures (`mock_image_bytes`, `base_config_dict`)
- `test_api.py` — health, liveness, readiness (ready + not-ready), detection success + empty file. Uses `TestClient` with mocked globals (`state`, `model`).
- `test_config.py` — valid YAML loads, defaults fallback, missing file raises `FileNotFoundError`. Uses `monkeypatch` + `tmp_path`.
- `test_model.py` — detects persons, filters non-person classes, handles empty results. Uses `MockBoxes`/`MockResult` to fake YOLO output.

### Docker (`Dockerfile`)

Multi-stage: `base` runs lint/type checks; `build` strips dev deps; `production` is slim Python 3.13 + libGL (for OpenCV). Entrypoint: `python src/inference.py`.

### Task runner (Taskfile)

| Task                                                                   | Does                                                  |
| ---------------------------------------------------------------------- | ----------------------------------------------------- |
| `task lint`                                                            | pre-commit init + run all hooks                       |
| `task sync -- cpu\|cuda`                                               | uv sync with frozen lock, extra selects torch variant |
| `task pre-commit:init`                                                 | install git hooks                                     |
| `task check:device-local -- cuda`                                      | test torch device availability                        |
| `task docker:build`                                                    | build Docker image                                    |
| `task docker:inference`                                                | run container with NVIDIA runtime, volume mounts      |
| `task test:info\|liveness\|readiness\|detection-true\|detection-false` | curl-based API smoke tests (requires running server)  |

## Code conventions

- **Python 3.13 only** — no backwards compatibility needed
- **Type strict** — basedpyright in strict mode; all functions annotated
- **Ruff all-rules** — line length 120; ignores: COM812, FIX, TD, D203, D212
- **No line comments** — use docstrings and well-named functions instead
- **No linting exclude annotations** (`# noqa`, `# type: ignore`, `# pylint: disable`, etc.) unless strictly necessary and approved. Always aim to rewrite the code to pass checks cleanly instead.
- **Dataclasses for config** — typed, with defaults at class level
- **Global state pattern in `inference.py`** — `model` and `state` are module-level globals, managed via FastAPI lifespan. Tests mock these directly.
- **Model lazy-loading** — `PersonDetector._model` is `None` until first access; download happens in `download()` called via lifespan
- **Pytest fixtures** — use `monkeypatch` + `tmp_path` for config tests; `MagicMock` for model; `patch()` for global state in API tests
- **Error handling** — `ValueError` for validation, `HTTPException` for endpoints, `RuntimeError` for model failures. `detect_persons()` returns a safe fallback dict instead of raising on runtime errors.

## Common tasks

### Run lint + type checks

```shell
task lint
```

For faster iteration on Python-only checks:

```shell
uv run ruff check . && uv run basedpyright .
```

### Run tests

```shell
uv run pytest -v
```

### Run the API locally

```shell
uv run src/inference.py
```

### Add a new detection class

1. Edit `config/configuration.yaml` — change `classes_to_detect` to desired COCO class IDs
2. The API response field names (`person_detected`, `person_boxes`, `num_persons`) are hardcoded in `src/model.py:_process_results()` — rename them if detecting non-person classes
3. No code changes needed otherwise — the model already handles multi-class filtering via `class_mask`

### Add an API endpoint

1. Add route function to `src/inference.py` using FastAPI decorators
2. Check `state` and `model` for readiness (copy pattern from existing endpoints)
3. Add test to `tests/test_api.py` using the `client` fixture (which patches globals to `READY` state)

### Change model size/device

- Edit `config/configuration.yaml` `model:` section
- Or set via env: the config just reads the YAML; there's no per-field env overrides

## Dependency management

- **Lock file is pinned** (`uv.lock`) — use `uv sync --frozen` in CI
- **Torch extras are mutually exclusive** — `cpu` and `cuda` extras conflict; only one can be installed
- **Dev deps** (`basedpyright`, `ruff`, `pytest`, `pytest-asyncio`, `httpx`) are in `[dependency-groups].dev`
- **No runtime deps in dev group** — production Docker image runs `uv sync --no-dev`

## Branch & commit rules

- Do NOT commit directly to `main` — use feature branches
- Use the git-commit skill for commit messages
- Pre-commit hooks must pass (ruff, basedpyright, yamllint, gitleaks, etc.)
- Do NOT push without approval
- The `.gitignore` is managed in the repository — use it as-is
