---
description: How to add new AI Agents to the system
---

## Overview
The system is designed to support multiple AI agents that perform different types of analysis on GitHub repositories. All agents use the same payment and backend infrastructure.

## Steps to Add a New Agent

1. **Update `agents/views.py`**:
   - Locate the `get_agent_prompt` function.
   - Add a new `elif agent_type == 'your_new_agent_name':` block.
   - Define the `context` fetching logic (e.g., fetch a specific file, issue list, etc.).
   - create a specialized prompt using the `fmt_instr` template for consistent HTML output.
   - Ensure the prompt asks for specific HTML tags (`<h3>`, `<ul class="...">`, etc.).

2. **Update `templates/dashboard.html`**:
   - Locate the "Agents Grid" section.
   - Copy an existing `.agent-card` div.
   - Update the `data-agent="your_new_agent_name"` attribute to match the name used in `views.py`.
   - Update the icon, title, description, and price (if different).
   - The JavaScript logic will automatically pick up the new card and send the correct `agent_type`.

3. **Verify Functionality**:
   - Restart the Django server.
   - Select the new agent in the dashboard.
   - Perform a test payment (Sepolia ETH).
   - Verify the output formatting matches the design.

## Current Agents
- **setup_runner**: Extracts setup steps.
- **architecture**: Maps project structure.
- **contributing**: Explains contribution guidelines.
- **issues**: Triages open issues.
- **pr_review**: Reviews the latest PR.
- **release_notes**: Summarizes releases.
- **dependencies**: Checks dependency risks.
- **license**: Analyzes licensing.
