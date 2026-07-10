"""Escalation channel (design task 6): notify, never guess.

Every escalation writes ESCALATION.md + a RunTrace event; email (Resend then
SMTP fallback) goes out when configured. Blocked runs exit BLOCKED_EXIT so
schedulers and the CLI can tell "needs a human" from "failed".
"""

from __future__ import annotations

import json
import smtplib
import time
import urllib.request
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from pathlib import Path

from .config import Settings
from .run_trace import RunTrace

BLOCKED_EXIT = 3


@dataclass
class Escalation:
    """One "needs a human" event: `reason` and `phase` describe what stalled,
    `severity` (info | blocked | failed) tiers it, and `state_summary` /
    `artifacts` carry the context rendered into ESCALATION.md and emailed."""

    reason: str
    phase: str
    run_id: str
    severity: str = "blocked"  # info | blocked | failed
    state_summary: dict = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)


class Notifier:
    """The escalation channel for one run: writes ESCALATION.md, records a trace
    event, and emails when configured. Bound to a `run_dir`/`run_id` and keeps a
    `sent` log of every Escalation raised."""

    def __init__(self, settings: Settings, run_dir: Path, trace: RunTrace, run_id: str = ""):
        """Bind the notifier to `settings` (email/SMTP config), the run's
        `run_dir` and `trace`, and a `run_id` (defaults to the dir name)."""
        self.settings = settings
        self.run_dir = Path(run_dir)
        self.trace = trace
        self.run_id = run_id or self.run_dir.name
        self.sent: list[Escalation] = []

    def escalate(self, *, reason: str, phase: str, severity: str = "blocked",
                 state_summary: dict | None = None, artifacts: list[str] | None = None) -> Path:
        """Raise an escalation: build the Escalation, append it to `sent`, write
        the rendered ESCALATION.md into the run dir, record a trace event, and
        fire the notification email. Returns the path to the written file."""
        esc = Escalation(
            reason=reason, phase=phase, run_id=self.run_id, severity=severity,
            state_summary=state_summary or {}, artifacts=artifacts or [],
        )
        self.sent.append(esc)
        body = self._render(esc)
        path = self.run_dir / "ESCALATION.md"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        self.trace.record("escalation", reason=reason, phase=phase, severity=severity)
        self._email(f"[omni-copilot] {severity}: {phase}", body)
        return path

    def _render(self, esc: Escalation) -> str:
        """Render an Escalation into the ESCALATION.md Markdown body: run/phase/
        timestamp header, the reason, the state summary as a JSON block, and an
        artifacts list when present."""
        lines = [
            f"# Escalation — {esc.severity}",
            "",
            f"- **run**: {esc.run_id}",
            f"- **phase/step**: {esc.phase}",
            f"- **when**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Why blocked",
            esc.reason,
            "",
            "## State reached",
            "```json",
            json.dumps(esc.state_summary, indent=2, default=str),
            "```",
        ]
        if esc.artifacts:
            lines += ["", "## Artifacts"] + [f"- {a}" for a in esc.artifacts]
        return "\n".join(lines) + "\n"

    # -- email: Resend HTTP first, SMTP fallback; failures never crash a run --
    def _email(self, subject: str, body: str) -> bool:
        """Best-effort send `subject`/`body` to the configured recipient: try
        the Resend HTTP API first, then SMTP. Returns True on a successful send,
        False when no recipient is set or every transport fails — exceptions are
        swallowed so notification never crashes a run."""
        to = self.settings.notify_email
        if not to:
            return False
        if self.settings.resend_api_key:
            try:
                req = urllib.request.Request(
                    "https://api.resend.com/emails",
                    data=json.dumps({
                        "from": "omni-copilot <onboarding@resend.dev>",
                        "to": [to], "subject": subject, "text": body,
                    }).encode(),
                    headers={
                        "Authorization": f"Bearer {self.settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                )
                urllib.request.urlopen(req, timeout=15)
                return True
            except Exception:
                pass
        if self.settings.smtp_host:
            try:
                msg = MIMEText(body)
                msg["Subject"], msg["From"], msg["To"] = subject, self.settings.smtp_user, to
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port,
                                  timeout=15) as s:
                    s.starttls()
                    if self.settings.smtp_user:
                        s.login(self.settings.smtp_user, self.settings.smtp_password)
                    s.send_message(msg)
                return True
            except Exception:
                pass
        return False
