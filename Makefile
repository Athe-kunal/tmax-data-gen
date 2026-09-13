.PHONY: kg-db kg-viz kg sync-artifacts-to-tharun

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
