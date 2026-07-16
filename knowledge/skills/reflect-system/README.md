# Reflect - Self-Improving Skills System

> *"Correct once, never again"*

Ein intelligentes Lernsystem für Claude Code, das aus Ihren Korrekturen lernt und Skills automatisch verbessert.

> Repo override for `workflow-starter`: do not promote project facts, workflow rules, incidents, or personal preferences to global/system/personal memory. Useful learnings must land in repo-local `CLAUDE.md`, `CONTRIBUTING.md`, `framework/`, or `repos/`; machine facts belong only in ignored `local/`. Otherwise they should not be persisted.

---

## 🚀 Quick Start

```bash
# Status prüfen
/reflect-status

# Manuelle Analyse nach einer Session mit Korrekturen
/reflect

# Mit AI-powered Semantic Detection (Multi-Language!)
/reflect --semantic

# Cross-Skill Learnings anzeigen
/reflect-stats

# Learnings zu global promoten
/reflect-promote

# Auto-Reflection aktivieren (optional)
/reflect-on
```

---

## 🧠 Semantic Detection (v1.1)

### Was ist das?

Semantic Detection nutzt Claude selbst als ML-Engine für intelligentere Pattern-Erkennung:

| Feature | Regex (Standard) | Semantic (--semantic) |
|---------|------------------|----------------------|
| **Sprachen** | Englisch + Deutsch | Alle Sprachen |
| **Genauigkeit** | Gut | Exzellent |
| **Geschwindigkeit** | Sofort | ~2-3s pro Message |
| **False Positives** | Möglich | Sehr selten |

### Multi-Language Beispiele

```
🇬🇧 "No, use uv instead of pip"           → ✓ Detected
🇩🇪 "Nein, benutze pytest statt unittest" → ✓ Detected  
🇪🇸 "No, usa Python en vez de JavaScript" → ✓ Detected
🇫🇷 "Non, utilise toujours ruff"          → ✓ Detected
```

---

## 🔄 NEU: Cross-Skill Learning (v1.2)

### Was ist das?

Learnings werden über Skills und Repositories hinweg getrackt. Wenn ein Learning in 2+ Repos auftaucht, kann es zu deiner globalen `~/.claude/CLAUDE.md` promoted werden.

### Der Workflow

```
Repo A: "Verwende uv statt pip" → Learning gespeichert
Repo B: "Verwende uv statt pip" → Gleiche Learning erkannt!
        ↓
    Threshold erreicht (2 Repos)
        ↓
    /reflect-promote → Global CLAUDE.md
        ↓
    Claude weiß es ÜBERALL ✨
```

### Commands

```bash
# Statistiken anzeigen
/reflect-stats

# Promotion-Kandidaten anzeigen
python3 ~/.claude/skills/reflect-system/scripts/promote_learning.py list

# Preview einer Promotion
python3 ~/.claude/skills/reflect-system/scripts/promote_learning.py preview <fingerprint>

# Learning promoten
python3 ~/.claude/skills/reflect-system/scripts/promote_learning.py promote <fingerprint>

# Alle eligible Learnings promoten
python3 ~/.claude/skills/reflect-system/scripts/promote_learning.py all --dry-run
```

### Beispiel Output

```
$ python3 promote_learning.py list

2 learnings ready for promotion:

  [a1b2c3d4] (3 repos)
    Use uv instead of pip for Python projects
    From: python-project-creator

  [e5f6g7h8] (2 repos)
    Always run tests before committing
    From: general
```

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `~/.claude/reflect/learnings.db` | SQLite Ledger |
| `~/.claude/CLAUDE.md` | Globale Regeln |
| `~/.claude/backups/` | Automatische Backups |

---

## 📖 Was ist Reflect?

Reflect analysiert Ihre Konversationen mit Claude und:

- ✅ **Erkennt Korrekturen** - Wenn Sie Claude korrigieren
- ✅ **Identifiziert Patterns** - Wenn Ansätze gut funktionieren
- ✅ **Aktualisiert Skills** - Basierend auf Ihrem Feedback
- ✅ **Versioniert Änderungen** - Mit Git-Integration
- ✅ **Trackt Cross-Repo** - Erkennt Patterns über Projekte hinweg

### Das Problem

```
Session 1: "Verwende uv statt pip"
Session 2: Claude verwendet wieder pip 😞
Session 3: "Ich hab's dir doch gesagt!" 😤
```

### Die Lösung

```
Session 1: "Verwende uv statt pip" → /reflect → Skill aktualisiert
Session 2: Claude verwendet uv ✅
Session 3: Claude verwendet uv ✅
Session N: Claude verwendet uv ✅
```

---

## 🎯 Features

### Drei Detection-Modi

1. **Regex** (Standard) - Schnell, Pattern-basiert
2. **Semantic** (`--semantic`) - AI-powered, Multi-Language
3. **Cross-Skill** - Tracking über Repos hinweg

### Drei Nutzungsmodi

1. **Manual** - `/reflect` nach Bedarf
2. **Automatic** - Läuft bei jedem Session-Ende (wenn aktiviert)
3. **Toggle** - Ein/Aus mit `/reflect-on` und `/reflect-off`

### Confidence Levels

- 🔴 **HIGH** - Explizite Korrekturen ("Verwende X statt Y")
- 🟡 **MEDIUM** - Approvals ("Ja, perfekt!")
- 🟢 **LOW** - Überlegungen ("Have you considered...")

### Sicherheit

- ✅ Timestamped Backups vor jedem Update
- ✅ YAML-Validation
- ✅ Automatischer Rollback bei Fehlern
- ✅ Git-Integration mit descriptiven Commit-Messages

---

## 📂 Struktur

```
reflect/
├── README.md                  # Diese Datei
├── USER_GUIDE.md             # Ausführlicher Guide
├── SKILL.md                  # Skill-Definition
├── commands/                 # Slash Commands
│   ├── reflect-promote.md    # /reflect-promote
│   └── reflect-stats.md      # /reflect-stats
├── scripts/
│   ├── reflect.py            # Haupt-Engine
│   ├── extract_signals.py    # Pattern-Detection (Regex + Semantic)
│   ├── semantic_detector.py  # AI-powered Detection
│   ├── learning_ledger.py    # SQLite Cross-Skill Tracking (NEU!)
│   ├── scope_analyzer.py     # Project vs Global (NEU!)
│   ├── promote_learning.py   # Promotion zu Global (NEU!)
│   ├── update_skill.py       # Safe Skill-Updates
│   ├── present_review.py     # Interactive Review
│   └── ...
├── .state/
│   └── auto-reflection.json  # Toggle-Status
└── references/
    └── signal-patterns.md    # Pattern-Library
```

---

## 🔗 Commands Cheat Sheet

| Command | Beschreibung |
|---------|--------------|
| `/reflect` | Manuelle Analyse (Regex) |
| `/reflect --semantic` | Manuelle Analyse (AI-powered) |
| `/reflect <skill>` | Analysiere nur einen Skill |
| `/reflect-on` | Auto-Reflection aktivieren |
| `/reflect-off` | Auto-Reflection deaktivieren |
| `/reflect-status` | Status anzeigen |
| `/reflect-stats` | Cross-Skill Statistiken (NEU!) |
| `/reflect-promote` | Learnings zu Global promoten (NEU!) |

### CLI-Optionen

| Option | Beschreibung |
|--------|--------------|
| `--semantic` | AI-powered Detection (Multi-Language) |
| `--model <name>` | Modell für Semantic (default: haiku) |

### Review-Optionen

| Taste | Aktion |
|-------|--------|
| `A` | Approve - Alle Änderungen übernehmen |
| `M` | Modify - Mit Natural Language modifizieren |
| `S` | Skip - Diesen Skill überspringen |
| `Q` | Quit - Review abbrechen |

---

## 🎓 Empfohlener Lernpfad

### Woche 1-2: Manual Mode + Semantic
- `/reflect --semantic` nach Sessions mit Korrekturen
- Verschiedene Sprachen ausprobieren

### Woche 3-4: Cross-Skill Tracking
- `/reflect-stats` regelmäßig prüfen
- Beobachten wie Learnings über Repos akkumulieren

### Ab Woche 5: Promotion Flow
- `/reflect-promote` für reife Learnings
- Globale CLAUDE.md aufbauen

---

## 🚨 Troubleshooting Quick Ref

| Problem | Lösung |
|---------|--------|
| Keine Signale erkannt | `--semantic` nutzen |
| Ledger leer | Mehr `/reflect` Sessions durchführen |
| Promotion schlägt fehl | Threshold noch nicht erreicht (2 repos) |
| Backup nötig | `~/.claude/backups/` prüfen |

---

## 📜 Lizenz

MIT License

---

## 🙏 Credits

Inspiriert von:
- [BayramAnnakov/claude-reflect](https://github.com/BayramAnnakov/claude-reflect) - Semantic Detection
- [netresearch/claude-coach-plugin](https://github.com/netresearch/claude-coach-plugin) - Cross-Repo Learning

Entwickelt für Claude Code mit ❤️

---

**Happy Learning!** 🚀

---

*Version: 1.2.0 | Semantic Detection: v1.1 | Cross-Skill Learning: v1.2*
