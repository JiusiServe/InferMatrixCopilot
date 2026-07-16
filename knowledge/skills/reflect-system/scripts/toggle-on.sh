#!/bin/bash
SKILL_DIR="$HOME/.claude/skills/reflect-system"
STATE_FILE="$SKILL_DIR/.state/auto-reflection.json"

mkdir -p "$SKILL_DIR/.state"

echo "{\"enabled\": true, \"updated\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$STATE_FILE"

echo "✓ Auto-Reflection aktiviert"
echo ""
echo "  Reflection läuft automatisch bei jedem Session-Ende"
echo "  Analysiert Korrekturen und schlägt Skill-Verbesserungen vor"
echo ""
echo "  Deaktivieren mit: /reflect-off"
echo "  Status prüfen mit: /reflect-status"
