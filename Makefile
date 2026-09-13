.PHONY: kg-db kg-viz kg kg-embeddings dashboard sync-artifacts-to-tharun

# Rebuilds the Kùzu knowledge graph from tmax-data-gen/artifacts/.
kg-db:
	cd tmax-data-gen && uv run --project .. python -m data_gen.kg_builder \
		--artifacts-dir artifacts \
		--db-path data_gen/kg.db

# Renders the knowledge graph to assets/knowledge_graph.png (requires kg-db to have been run at least once).
kg-viz:
	cd tmax-data-gen && uv run --project .. python -m data_gen.kg_visualize \
		--db-path data_gen/kg.db \
		--out ../assets/knowledge_graph.png

# Rebuilds the graph and re-renders the visualization in one step.
kg: kg-db kg-viz

# Builds/refreshes data_gen/kg.db.embeddings.json (the retrieval cache
# kg_retrieve.py uses) without running a query. Requires EMBEDDING_API_KEY /
# EMBEDDING_BASE_URL / EMBEDDING_MODEL in tmax-data-gen/.env (see
# tmax-data-gen/.env.example) - e.g. a local MLX embedding server.
kg-embeddings:
	cd tmax-data-gen && uv run --project .. python -m data_gen.kg_retrieve \
		--db-path data_gen/kg.db --build-only

# Opens the local experiment dashboard. Run `data_gen.run_experiment` first.
dashboard:
	uv run streamlit run tmax-data-gen/data_gen/dashboard.py -- --db-path tmax-data-gen/runs/tmax_results.sqlite

# Pushes tmax-data-gen/artifacts/ to the tharun branch on origin, mirroring
# it exactly (files removed locally are removed there too). Uses a
# throwaway git worktree so your current checkout/branch is left untouched.
# tharun keeps artifacts/ at the repo root (not nested under tmax-data-gen/),
# so this also handles that path difference.
sync-artifacts-to-tharun:
	git fetch origin tharun
	worktree_dir=$$(mktemp -d) && \
	git worktree add "$$worktree_dir" origin/tharun --detach && \
	rsync -a --delete tmax-data-gen/artifacts/ "$$worktree_dir/artifacts/" && \
	(cd "$$worktree_dir" && git add artifacts && \
		(git diff --cached --quiet && echo "No artifact changes to sync." || \
		(git commit -m "Sync artifacts from tmax-data-gen/artifacts/" && git push origin HEAD:tharun))) ; \
	git worktree remove "$$worktree_dir" --force
