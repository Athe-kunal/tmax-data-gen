# tmax-data-gen

Knowledge-graph-driven task generation for tmax: builds a Kùzu graph from
`tmax-data-gen/artifacts/*.yaml` (domains, skills, personas, languages),
retrieves and generates terminal tasks from it, solves them with a real
agent in a remote sandbox (Daytona / W&B Sandbox), and collects the ones
that actually pass verification as gold (task + trajectory) reference data.

See **[`tmax-data-gen/data_gen/README.md`](tmax-data-gen/data_gen/README.md)**
for the full pipeline walkthrough, setup instructions, and every CLI
command (`kg_builder`, `kg_retrieve`, `next_question`, `rollout`,
`multi_turn_rollout`, `gold`, ...).

## Makefile targets

- `make kg-db` — build the Kùzu graph from `artifacts/`.
- `make kg-viz` — render it to `assets/knowledge_graph.png`.
- `make kg` — both of the above.
- `make kg-embeddings` — build/refresh the retrieval embeddings cache
  (`data_gen/kg.db.embeddings.json`) without running a query.
- `make sync-artifacts-to-tharun` — push `tmax-data-gen/artifacts/` to the
  `tharun` branch on origin.

## Recent updates

- `kg_retrieve.py`: added `build_embeddings_cache()` + a `--build-only` CLI
  flag (query becomes optional) — backs the new `make kg-embeddings` target.
- `embeddings.py`: now loads `.env` itself (previously only
  `inference_config.py` did), so `EmbeddingClient` works standalone.
- `Makefile`: new `kg-embeddings` target.
- `harness.py` / `multi_turn_rollout.py` / `gold.py`: finished the
  `model_style` (`"text"` vs `"toolcall"`) plumbing — lets the agent's
  action-parsing convention be picked per model (see
  `data_gen.harness._MODEL_STYLES`) instead of being hardcoded.
