As a researcher organizing datasets, I need to analyze a citation graph represented as a JSONL file. The file contains a collection of papers, each with a unique identifier, title, and a list of references to other papers. My goal is to identify the paper with the most citations, which is equivalent to finding the node with the highest in-degree in a directed graph.

The JSONL file is located at /home/user/citation_graph/data/papers.jsonl, and each line represents a paper in the following format:
- `id` (string): The unique identifier of the paper.
- `title` (string): The title of the paper.
- `references` (array of strings): A list of `id`s of other papers that this paper cites.

I need to implement the logic to read this file, build the graph, calculate the in-degrees, and identify the most cited paper in the /home/user/citation_graph/src/main.rs file.

The Cargo project is already set up with the necessary dependencies, including `serde` and `serde_json`. I will use the `cargo run` command to build and run the project, which should generate the final output file.

The output of the program should be a single string representing the `id` of the most cited paper, written to /home/user/top_cited.txt without any quotes or newlines. This will be the final result of the task.

To verify the correctness of the task, I will check the contents of the /home/user/top_cited.txt file to ensure it matches the expected output.

Please note that I will be working within the provided Rust Cargo project, and all changes should be made to the /home/user/citation_graph/src/main.rs file. The `cargo run` command should be used to build and run the project, and the final output file should be generated accordingly.
