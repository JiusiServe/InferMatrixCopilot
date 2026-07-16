#!/bin/bash
SKILL_DIR="$HOME/.claude/skills/reflect-system"
STATE_FILE="$SKILL_DIR/.state/auto-reflection.json"
TIMESTAMP_FILE="$SKILL_DIR/.state/last-reflection.timestamp"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                    REFLECTION STATUS"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ ! -f "$STATE_FILE" ]; then
    echo "Status:        Nicht konfiguriert"
    echo "Mode:          Manuell"
    echo ""
    echo "Aktivieren mit: /reflect-on"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
fi

ENABLED=$(cat "$STATE_FILE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('enabled', False))" 2>/dev/null)
UPDATED=$(cat "$STATE_FILE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('updated', 'unknown'))" 2>/dev/null)

if [ "$ENABLED" = "True" ]; then
    echo "Status:        ✓ Aktiviert"
    echo "Mode:          Automatisch (bei Session-Ende)"
else
    echo "Status:        ⊘ Deaktiviert"
    echo "Mode:          Nur manuell"
fi

echo "Konfiguriert:  $UPDATED"

if [ -f "$TIMESTAMP_FILE" ]; then
    LAST_REFLECTION=$(cat "$TIMESTAMP_FILE" 2>/dev/null || echo "never")
    echo "Letzte Analyse: $LAST_REFLECTION"
fi

echo ""
echo "───────────────────────────────────────────────────────────"
echo "Commands:"
echo "  /reflect           - Manuelle Analyse der aktuellen Session"
echo "  /reflect-on        - Auto-Reflection aktivieren"
echo "  /reflect-off       - Auto-Reflection deaktivieren"
echo "  /reflect-status    - Status anzeigen (dieser Befehl)"
echo ""
echo "Wie es funktioniert:"
echo "  • Erkennt Korrekturen in Konversationen (HIGH confidence)"
echo "  • Identifiziert erfolgreiche Patterns (MEDIUM confidence)"
echo "  • Notiert Überlegungen (LOW confidence)"
echo "  • Schlägt Skill-Updates vor mit Diff-Ansicht"
echo "  • Commitet genehmigte Änderungen zu Git"
echo "═══════════════════════════════════════════════════════════"
echo ""
