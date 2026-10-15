---
description: Ensure the memory graph is updated whenever structural changes are made to the Miku 1.0 project.
trigger: always_on
---

# Update Memory MCP on Structural Changes

This project uses the official Memory MCP (`@modelcontextprotocol/server-memory`) to maintain a Knowledge Graph of the project's structure. The project is named **Miku 1.0**.

Whenever you (the agent) make **structural changes** to the codebase, you MUST proactively update the memory graph.

Structural changes include:
- Creating a new core module or file.
- Deleting an existing module.
- Significantly changing the responsibility or dependencies of a file (e.g., `main.py` now depends on `database.py`).
- Adding a new major feature or technology.

**How to update the memory:**
1. Use the `call_mcp_tool` with the server `memory`.
2. Use tools like `create_entities`, `create_relations`, or `add_observations`.
3. If an entity is removed or renamed, use `delete_entities` and recreate it if necessary.
4. Keep the relations updated (e.g., `from: "Miku 1.0", relationType: "has_component", to: "new_file.py"`).

Do not ask the user for permission to update the memory graph; do it automatically as part of your task.
