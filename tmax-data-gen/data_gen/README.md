# data_gen

Generates terminal tasks from tmax's knowledge-graph artifact catalog, solves
them with a real agent in a remote sandbox, and collects the ones that
actually pass verification as gold (task + trajectory) reference data.

## Pipeline overview

```
artifacts/*.yaml (KG catalog)
        │  kg_builder.py
        ▼
   data_gen/kg.db (Kùzu graph)
        │  kg_retrieve.py (embedding search)
        ▼
question_sampler.py + question_gen.py   ──►  GeneratedQuestion
        │  (task, truth, test_final_state.py, setup_script)
        ▼
   harbor.py  ──►  Harbor task dir (instruction.md, task.toml, tests/, ...)
        │
        ▼
 multi_turn_rollout.py  ──►  runs the agent in a Daytona/W&B Sandbox,
        │                    verifies each turn, records reward
        ▼
     gold.py  ──►  keeps turns with reward ≥ threshold as gold_tasks/<name>/
```

One rollout = **one persistent sandbox + one continuous mini-swe-agent
conversation** across `max_turns` questions, not a fresh container per
question. Turn 0 is seeded from tmax's own published RL-task corpus (a real,
pre-vetted task); every turn after that is generated dynamically, retrieved
against the KG using the previous turn's task text as the query.

## One-time setup

1. **Artifacts + graph**: `artifacts/*.yaml` is checked in already. Build the
   graph once (and again whenever artifacts change):
   ```bash
   cd tmax-data-gen
   uv run python -m data_gen.kg_builder --artifacts-dir artifacts --db-path data_gen/kg.db
   ```
2. **`.env`** (copy `.env.example` if starting fresh): needs
   - `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` — the generation
     + solving model endpoint. Defaults to W&B Weave Inference
     (`https://api.inference.wandb.ai/v1`). **Only `meta-llama/Llama-3.1-8B-Instruct`
     and `meta-llama/Llama-3.3-70B-Instruct` are confirmed live there as of
     2026-09-13** — Weave Inference's public-preview roster changes; verify
     any other model with a direct `curl` before relying on it.
   - `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` — a
     *separate* endpoint for `kg_retrieve.py` (Weave Inference has no
     `/v1/embeddings`, it 404s). Recommended: a local MLX embedding server
     on Apple Silicon serving `mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ`
     (see "Local embedding server" below) — not yet a committed script.
   - `WANDB_API_KEY` — used by `cwsandbox`'s `AuthStrategy.WANDB` (the
     "sandbox" environment backend) and by Weave tracing.
   - `DAYTONA_API_KEY` / `DAYTONA_URL` — the Daytona backend.
   - `WEAVE_PROJECT` — where traces are logged (defaults to `tmax-data-gen`).
3. **Sandbox backend**: two interchangeable options, both implementing the
   same environment interface so nothing else changes when switching:
   - `--environment daytona` — just needs `DAYTONA_API_KEY`, works today.
   - `--environment sandbox` (W&B/CoreWeave) — currently blocked on
     org-level approval (`PERMISSION_DENIED: sandboxes not enabled for this
     organization`); it's public preview, request access via
     support@wandb.com.

### Local embedding server (not yet a committed script)

`kg_retrieve.py` needs an OpenAI-compatible `/v1/embeddings` endpoint. The
one used throughout this session was a throwaway FastAPI wrapper around
`mlx_embeddings` (Apple Silicon only):

```python
# scratch script, not part of the repo
from mlx_embeddings import load, generate
from fastapi import FastAPI
import uvicorn

MODEL_ID = "mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ"
model, processor = load(MODEL_ID)
app = FastAPI()

@app.post("/v1/embeddings")
def embeddings(request: dict):
    texts = [request["input"]] if isinstance(request["input"], str) else request["input"]
    vectors = generate(model, processor, texts).text_embeds.tolist()
    return {"object": "list", "model": MODEL_ID, "usage": {"prompt_tokens": 0, "total_tokens": 0},
            "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)]}

uvicorn.run(app, host="127.0.0.1", port=8712)
```

Install: `uv pip install mlx-embeddings fastapi uvicorn` in a scratch venv.
Point `.env`'s `EMBEDDING_BASE_URL` at `http://127.0.0.1:8712/v1`. Worth
promoting to a real `data_gen/` module if this becomes permanent.

## Running things

All commands run from `tmax-data-gen/` via `uv run python -m data_gen.<module>`.

### Build/inspect the knowledge graph

```bash
uv run python -m data_gen.kg_builder --artifacts-dir artifacts --db-path data_gen/kg.db
uv run python -m data_gen.kg_export --db-path data_gen/kg.db --out data_gen/kg_export.json
uv run python -m data_gen.kg_visualize --db-path data_gen/kg.db --out ../assets/knowledge_graph.png
uv run python -m data_gen.kg_retrieve "how do I harden SSH keys" --db-path data_gen/kg.db --top-k 5
```
(`kg_visualize` needs Graphviz's `sfdp`; if it segfaults intermittently,
that's a known issue with some Homebrew Graphviz builds, not this code.)

### Generate one standalone Harbor task (no rollout)

```bash
uv run python -m data_gen.next_question \
    --artifacts-dir artifacts --out-dir generated_tasks \
    --model meta-llama/Llama-3.3-70B-Instruct
```
Add `--query "..."` + `--kg-db-path data_gen/kg.db` to seed it via retrieval
instead of pure random sampling.

### Solve + verify one materialized task

```bash
uv run python -m data_gen.rollout \
    --task-dir generated_tasks/<task> \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --environment daytona --step-limit 40
```

### Run a full multi-turn rollout (the main pipeline)

```bash
uv run python -m data_gen.multi_turn_rollout \
    --environment daytona \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --max-turns 3 --step-limit 90
```

### Collect gold trajectories

```bash
uv run python -m data_gen.gold \
    --environment daytona \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --max-turns 3 --step-limit 90 --gold-threshold 1.0 \
    --out-dir gold_tasks
```
Prints `N/max_turns turns were gold`; each gold turn lands in
`gold_tasks/<domain>-<primitive>-<hash>/` as a normal Harbor task plus
`trajectory.json` (the exact messages that solved it).

**Reasoning models** (e.g. GLM-5.2): pass `--agent-max-tokens` and
`--generation-max-tokens` generously (their `reasoning` field eats into the
budget before `content` is ever produced; too small a limit → empty
response → retries exhausted → crash). Some reasoning models burn the
entire budget on trivial prompts even at 16k+ tokens regardless — verify
with a direct `curl` before trusting one in a real run.

Every run prints a Weave trace link (`wandb.ai/<you>/tmax-data-gen/weave`)
with the full nested trace: retrieval query + matches, generated
task/truth/tests, every agent tool call, and the verifier result.

## What each module does

| Module | Role |
|---|---|
| `catalog.py` | Dataclasses for `artifacts/*.yaml` (Domain/SkillType/Primitive/Persona/Language) |
| `kg_builder.py` | Builds the Kùzu graph from the catalog |
| `kg_export.py` / `kg_visualize.py` | Schema-agnostic export/plot of the graph |
| `embeddings.py` / `kg_retrieve.py` | OpenAI-compatible embedding client + NL-query → KG-triplet retrieval |
| `question_sampler.py` | `sample_entry` (random) / `sample_entry_via_retrieval` (retrieval-seeded) |
| `question_gen.py` | 3 LLM calls per question: `<task>`+`<truth>` → `test_final_state.py` → `setup_script` (retries on malformed output) |
| `tmax_rl_seed.py` | Cold-start source: pulls a real row from tmax's published RL-task HF dataset for turn 0 |
| `harbor.py` | Materializes a `GeneratedQuestion` as a Harbor task directory |
| `inference_config.py` | `.env`-driven `OPENAI_*` config, defaults to Weave Inference, swappable to any OpenAI-compatible endpoint |
| `sandbox_environment.py` / `daytona_environment.py` | Two interchangeable remote-execution backends, same interface |
| `env_exec.py` | Shared `run`/`write_file`/`read_file`/`query_platform_info` helpers built on any environment's `.execute()` |
| `harness.py` | Builds a mini-swe-agent `DefaultAgent` (uses `LitellmTextbasedModel` + `default.yaml` — see note below) |
| `rollout.py` | Single question → solve → verify, one sandbox |
| `multi_turn_rollout.py` | The main loop: cold start + N dynamic turns, one sandbox/conversation throughout |
| `gold.py` | Runs a rollout, keeps turns above the reward threshold as gold |

## Real bugs found and fixed this session (worth knowing about)

- **Agent model/config mismatch**: `harness.py` originally used
  `LitellmModel` (native tool-calling — always passes `tools=[BASH_TOOL]`
  and only ever parses `tool_calls`) together with `default.yaml`, whose
  prompt instead describes a markdown-code-block format that model class
  never looks at. Every single agent turn failed with `RepeatedFormatError`,
  regardless of model quality. Fixed by switching to `LitellmTextbasedModel`
  (regex-parses one ` ```mswea_bash_command ` block from plain text), which
  is what `default.yaml`'s prompt was actually written for.
- **Wrong `<system_information>` in every agent prompt**: `get_template_vars()`
  used Python's local `platform.uname()` — the orchestrator's own machine
  (a Mac), not the remote Linux sandbox. It was telling the agent to use
  BSD `sed -i ''` inside an Ubuntu container. Fixed via
  `env_exec.query_platform_info()`, which runs `uname` *inside* the sandbox
  once at startup and caches it.
- **Generated turns never materialized their own "given" data**: the LLM
  writes `<truth>` describing input files/services that should already
  exist, but nothing created them — the agent was left to guess/fabricate
  fake data, which then failed verification against the real truth no
  matter how well the task itself was solved. Fixed by adding a third
  generation call (`setup_script`) that's actually run in the sandbox
  before each generated turn starts.
- **`n_consecutive_format_errors` leaking across turns**: `_continue_with_task`
  (our custom continuation of `DefaultAgent.run()`'s inner loop, needed
  because `run()` unconditionally resets `messages`) didn't reset this
  counter, so a turn that ended via `RepeatedFormatError` left the *next*
  turn with zero error budget instead of a fresh one.
- **Weave Inference model roster ≠ its docs page**: several models the
  docs list (DeepSeek-V3/R1, Llama-4-Scout, Phi-4-mini) 404 in practice.
  Always verify with a direct `curl` before wiring a model in.
