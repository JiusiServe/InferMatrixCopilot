# Copilot skills

Procedural knowledge retrieved by the agent-step runtime
(`engine/agent_runtime/`): top-k summaries are injected into every agent
step's dispatch context, and agents can `skill_search` for more. Agents may
only PROPOSE changes (`skill_update_candidate` -> `_candidates.json`);
promotion to an active SKILL.md is a curator/human action.
