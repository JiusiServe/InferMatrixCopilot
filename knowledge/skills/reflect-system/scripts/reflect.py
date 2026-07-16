#!/usr/bin/env python3
"""
Main reflection orchestration engine.
Coordinates signal extraction, skill updates, and user review.

Modes:
  (default)            interactive — extract signals + present_review() with input()
                       (only safe when run from a real terminal, not a background hook)
  --non-interactive    hook mode — extract signals, write pending-review.json, exit
                       (no input(); safe to run from Stop hook or any non-TTY context)
  --apply-pending      apply previously-pending signals (after user confirms via /reflect-review)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess

# Force UTF-8 on stdout/stderr so emoji prints (✓ ✗ 📝 🧠) don't crash on Windows GBK locales.
# No-op on POSIX where stdout is already UTF-8.
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from extract_signals import extract_signals
from update_skill import update_skill

PENDING_REVIEW_FILE = Path.home() / '.claude' / 'skills' / 'reflect-system' / '.state' / 'pending-review.json'


def _make_serializable(obj):
    """Convert tuples (e.g. regex match groups) to lists so JSON can roundtrip."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(v) for v in obj]
    return obj


def main():
    """Main reflection workflow (interactive)."""
    if '--non-interactive' in sys.argv:
        return cmd_non_interactive()
    if '--apply-pending' in sys.argv:
        return cmd_apply_pending()

    # Lazy import — avoid pulling in input()-using code on hook path
    from present_review import present_review

    # 1. Get transcript path from env or argument
    transcript_path = os.getenv('TRANSCRIPT_PATH') or (sys.argv[1] if len(sys.argv) > 1 else None)

    print("🧠 Reflection Analysis Starting...")

    # 2. Extract signals from transcript
    try:
        signals_by_skill = extract_signals(transcript_path)
    except Exception as e:
        print(f"✗ Error extracting signals: {e}")
        return 1

    if not signals_by_skill:
        print("✓ No improvement suggestions found")
        return 0

    print(f"Found signals in {len(signals_by_skill)} skill(s)")

    # 3. Present for review
    try:
        approved_changes = present_review(signals_by_skill)
    except KeyboardInterrupt:
        print("\n\nReview interrupted by user")
        return 1
    except Exception as e:
        print(f"✗ Error during review: {e}")
        return 1

    if not approved_changes:
        print("\nNo changes approved")
        return 0

    # 4. Apply changes with backups
    success_count = 0
    for change in approved_changes:
        try:
            if update_skill(change):
                success_count += 1
        except Exception as e:
            print(f"✗ Error updating {change['skill_name']}: {e}")

    if success_count == 0:
        print("\n✗ No skills were updated successfully")
        return 1

    # 5. Git commit
    try:
        commit_changes(approved_changes)
    except Exception as e:
        print(f"Warning: Git commit failed: {e}")
        print("Changes were applied but not committed. Commit manually if needed.")

    print(f"\n✓ {success_count} skill(s) updated successfully")

    # 6. Update reflection timestamp
    update_last_reflection_timestamp()

    return 0


def cmd_non_interactive():
    """Hook mode: extract signals, write pending-review.json, exit. No input() calls."""
    transcript_path = os.getenv('TRANSCRIPT_PATH') or (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else None)

    try:
        signals_by_skill = extract_signals(transcript_path)
    except Exception as e:
        print(f"✗ Error extracting signals: {e}")
        return 1

    if not signals_by_skill:
        print("✓ No improvement suggestions found")
        # Clear any stale pending file so we don't keep reminding about old data
        if PENDING_REVIEW_FILE.exists():
            PENDING_REVIEW_FILE.unlink()
        return 0

    pending_data = {
        'timestamp': datetime.now().isoformat(),
        'transcript_path': transcript_path,
        'session_id': os.getenv('SESSION_ID', 'unknown'),
        'signals_by_skill': _make_serializable(signals_by_skill),
    }

    PENDING_REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_REVIEW_FILE.write_text(json.dumps(pending_data, indent=2, ensure_ascii=False))

    skill_count = len(signals_by_skill)
    signal_count = sum(len(s) for s in signals_by_skill.values())
    print(f"📝 Reflection collected {signal_count} signal(s) across {skill_count} skill(s)")
    print(f"   Pending review at: {PENDING_REVIEW_FILE}")
    print(f"   Run /reflect-review in Claude Code to inspect and approve.")
    return 0


def cmd_apply_pending():
    """Apply pending signals to skills (called after user confirmation via /reflect-review)."""
    if not PENDING_REVIEW_FILE.exists():
        print("No pending review found.")
        return 0

    try:
        pending = json.loads(PENDING_REVIEW_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"✗ Error reading pending review: {e}")
        return 1

    signals_by_skill = pending.get('signals_by_skill', {})
    if not signals_by_skill:
        print("Pending review is empty; nothing to apply.")
        PENDING_REVIEW_FILE.unlink()
        return 0

    # Lazy import — generate_proposed_changes lives in present_review but doesn't call input()
    from present_review import generate_proposed_changes

    success_count = 0
    applied_changes = []
    for skill_name, signals in signals_by_skill.items():
        proposed = generate_proposed_changes(skill_name, signals)
        change = {
            'skill_name': skill_name,
            'signals': signals,
            'proposed_updates': proposed,
        }
        try:
            if update_skill(change):
                success_count += 1
                applied_changes.append(change)
        except Exception as e:
            print(f"✗ Error updating {skill_name}: {e}")

    if success_count == 0:
        print("✗ No skills were updated successfully.")
        # Keep pending file so user can retry/inspect
        return 1

    try:
        commit_changes(applied_changes)
    except Exception as e:
        print(f"Warning: Git commit failed: {e}")

    print(f"\n✓ {success_count} skill(s) updated and committed.")
    update_last_reflection_timestamp()
    PENDING_REVIEW_FILE.unlink()
    return 0


def commit_changes(changes):
    """Commit skill updates to git"""
    skills_dir = Path.home() / '.claude' / 'skills'

    # Check if git repo exists
    if not (skills_dir / '.git').exists():
        print("\nNote: Skills directory is not a git repository")
        print("Initialize with: cd ~/.claude/skills && git init")
        return

    skill_names = [c['skill_name'] for c in changes]

    # Build commit message
    message_lines = ["refactor(skills): apply reflection learnings\n"]
    message_lines.append("Signals detected:")

    for change in changes:
        proposed = change.get('proposed_updates', {})
        high_count = len(proposed.get('high_confidence', []))
        medium_count = len(proposed.get('medium_confidence', []))
        low_count = len(proposed.get('low_confidence', []))

        if high_count:
            message_lines.append(f"- HIGH ({high_count}): {change['skill_name']}")
        if medium_count:
            message_lines.append(f"- MEDIUM ({medium_count}): {change['skill_name']}")
        if low_count:
            message_lines.append(f"- LOW ({low_count}): {change['skill_name']}")

    message_lines.append(f"\nSkills updated: {', '.join(skill_names)}\n")

    # Add session info if available
    session_id = os.getenv('SESSION_ID', 'unknown')
    auto_reflected = os.getenv('AUTO_REFLECTED', 'false')
    message_lines.append(f"Session: {session_id}")
    message_lines.append(f"Auto-reflected: {auto_reflected}\n")

    message_lines.append("🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    message_lines.append("Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>")

    commit_message = "\n".join(message_lines)

    try:
        # Stage all changes in skills directory
        subprocess.run(['git', 'add', '.'], cwd=skills_dir, check=True, capture_output=True)

        # Commit
        subprocess.run(['git', 'commit', '-s', '-m', commit_message], cwd=skills_dir, check=True, capture_output=True)

        print("\n✓ Changes committed to git")

        # Note: We don't auto-push for safety
        # User can push manually if they want
        print("  (Run 'cd ~/.claude/skills && git push' to push to remote)")

    except subprocess.CalledProcessError as e:
        # Check if it's just "nothing to commit"
        if b'nothing to commit' in e.stdout or b'nothing to commit' in e.stderr:
            print("\nNote: Git reported nothing to commit (files may be unchanged)")
        else:
            raise

def update_last_reflection_timestamp():
    """Update the last reflection timestamp to prevent duplicates"""
    timestamp_file = Path.home() / '.claude' / 'skills' / 'reflect-system' / '.state' / 'last-reflection.timestamp'
    try:
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
    except Exception as e:
        print(f"Warning: Could not update timestamp: {e}")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nReflection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
