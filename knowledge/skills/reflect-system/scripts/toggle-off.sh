#!/bin/bash
SKILL_DIR="$HOME/.claude/skills/reflect-system"
STATE_FILE="$SKILL_DIR/.state/auto-reflection.json"

mkdir -p "$SKILL_DIR/.state"

echo "{\"enabled\": false, \"updated\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > "$STATE_FILE"

echo "✓ Auto-Reflection deaktiviert"
echo ""
echo "  Manuelle Reflection weiterhin verfügbar mit: /reflect"
echo "  Reaktivieren mit: /reflect-on"
echo ""
echo "  Alle Skills bleiben unverändert."
