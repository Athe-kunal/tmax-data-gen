As a data engineer building ETL pipelines, I have a task that involves processing a large dataset of user interactions and extracting a specific subset of users based on their weighted degree centrality. I have a relational SQLite database at `/home/user/data.db` with a table `users` containing user information (`id INTEGER PRIMARY KEY`, `name TEXT`, `department TEXT`). Additionally, I have a JSON file at `/home/user/interactions.json` containing communication interactions in the format: `[{"src": <user_id>, "dst": <user_id>, "weight": <integer>}, ...]`.

My goal is to perform the following steps:

1. Load the users from the SQLite database and the interactions from the JSON file to build an in-memory graph.
2. Calculate the weighted degree centrality for each user, which is the sum of the `weight` of all interactions where they are either the `src` or the `dst`.
3. Drop any users from the result set whose weighted degree centrality is strictly less than 10.
4. Sort the remaining users by their weighted degree centrality in descending order. If two users have the exact same centrality score, break the tie by sorting their `name` in ascending alphabetical order.
5. Implement pagination on the sorted results using a page size of 3.
6. Extract Page 3 (items 7, 8, and 9 from the sorted filtered list) and write this exact page to `/home/user/output_page3.json` as a JSON array of objects with the schema: `[{"id": <integer>, "name": "<string>", "centrality": <integer>}, ...]`.

To complete this task, I will use the Rust programming language and the required libraries, which can be installed using cargo. I will write a Rust program at `/home/user/process_graph.rs` that performs these steps and run it using the command `cargo run` to generate the output file.

After running the program, I expect the output file `/home/user/output_page3.json` to contain the exact page of results in the specified format. I will verify the correctness of the output by checking its contents against the expected results.
