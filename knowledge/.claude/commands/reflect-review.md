---
description: Review and approve pending reflection learnings collected by the Stop hook
---

# /reflect-review

## Repo Policy Override

In this repository, do not apply pending reflect-system learnings to user-level or global Claude locations. If a pending learning matters for this repo, summarize it and convert it into a repo-local rule under `CLAUDE.md`, `CONTRIBUTING.md`, `framework/`, or `repos/`; machine facts belong only in ignored `local/`. Otherwise discard it. This applies to project facts and personal preferences alike.

The reflect-system Stop hook runs in the background after each turn. Background processes have no TTY, so it cannot prompt the user directly — instead it writes detected signals to `~/.claude/skills/reflect-system/.state/pending-review.json` and waits for this command to handle the human-in-the-loop step.

## Steps

1. **Read** `~/.claude/skills/reflect-system/.state/pending-review.json`. If the file does not exist, tell the user "no pending reflection review" and stop.

2. **Summarize** the pending review for the user:
   - Show `timestamp` and `session_id` so they know which session this came from.
   - For each entry in `signals_by_skill`:
     - Skill name + count of HIGH / MEDIUM / LOW confidence signals.
     - For HIGH signals, paraphrase the correction (`signal.content` or `signal.description`, truncated to ~80 chars).
     - For MEDIUM signals, paraphrase the approved approach.
     - Skip LOW signals unless the user asks for detail.

3. **Optional diff preview**: if the user asks "show diff", run
   ```bash
   python3 ~/.claude/skills/reflect-system/scripts/show_diff.py <skill_name>
   ```
   (only if that helper exists; otherwise read the SKILL.md directly and describe what would change).

4. **Ask the user** what to do — present three choices in plain language:
   - **Approve all** → run the apply step
   - **Skip / discard** → delete the pending file without applying
   - **Edit first** → let user describe modifications, then re-discuss

5. **On approve**, run:
   ```bash
   python3 ~/.claude/skills/reflect-system/scripts/reflect.py --apply-pending
   ```
   Report the output. The script applies changes to `~/.claude/skills/<skill>/SKILL.md`, commits them in the skills git repo (if initialized), and removes the pending file.

6. **On skip/discard**, just `rm ~/.claude/skills/reflect-system/.state/pending-review.json` and tell the user it's cleared.

## Important

- **Never** apply silently. Always show the summary in step 2 and wait for the user to respond before running `--apply-pending`.
- The pending file may accumulate across multiple Stop-hook runs if the user hasn't called this command in a while; mention the timestamp so they know how stale it is.
- If the apply step fails (non-zero exit), keep the pending file so the user can retry; don't auto-delete on failure.
