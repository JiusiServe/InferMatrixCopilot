# Autonomous workflow

This page documents the optional autonomous CLI and workflow MCP. It is separate
from the default Direct MCP described in the repository README.

The autonomous workflow runs its own model and supports longer repo-maintenance
playbooks such as review, issue handling, CI debugging, and rebase. It therefore
requires model credentials and repository configuration.

## Install

```bash
bash install.sh
```

Edit `.env`, set the required model credentials and `REPO_PATHS`, then run:

```bash
./infermatrix-copilot doctor
```

## Use

```bash
./infermatrix-copilot
./infermatrix-copilot -p "review pr 4830" --yes
./infermatrix-copilot -p "answer issue 4842, do not post"
./infermatrix-copilot -p "rebase pr 4830, then review it"
./infermatrix-copilot --resume
```

The autonomous MCP command is:

```text
infermatrix-copilot-workflow-mcp
```

It is not registered by the default Codex installer.

## Safety

- Pushes require an allowing policy and are dry-run unless explicitly enabled.
- Protected branches are never direct-pushed.
- Posting requires explicit intent and configuration.
- Blocked runs write escalation artifacts instead of guessing.

Implementation details:

- [`../QUICKSTART.md`](../QUICKSTART.md)
- [`../doc/DESIGN.md`](../doc/DESIGN.md)
- [`../doc/IMPLEMENTATION_STATUS.md`](../doc/IMPLEMENTATION_STATUS.md)
