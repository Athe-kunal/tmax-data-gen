.PHONY: kg-db kg-viz kg

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
