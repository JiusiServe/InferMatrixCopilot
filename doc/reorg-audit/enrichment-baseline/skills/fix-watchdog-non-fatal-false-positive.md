---
name: fix-watchdog-non-fatal-false-positive
description: When a test name contains 'non_fatal' (or any substring matching a Tier-1 critical pattern case-insensitively), the watchdog will false-positive kill the pytest process. Add the substring to the allowlist in test_watchdog.sh.
trigger: Test fails with rc=143/SIGTERM and watchdog message 'CRITICAL error detected' pointing to a test name that contains a substring matching a Tier-1 pattern case-insensitively (e.g., 'non_fatal' matching 'FATAL'). All individual tests PASS.
modules: [scheduler]
status: active
created_at: 2026-07-08
last_used_at: 2026-07-11
run_count: 5
---

## Diagnose
1. Check if the failing test exits with rc=143 (SIGTERM) but all individual tests PASS.
2. Look for watchdog messages in the log tail: `[watchdog] CRITICAL error detected: ...`
3. The matched line will contain a substring that matches a Tier-1 critical pattern case-insensitively.
4. Verify the test is legitimate (not a real engine failure) by running it in isolation: `python -m pytest <test_path> -xvs`

## Fix
Add the problematic substring to `WATCHDOG_SIMULATION_ALLOWLIST` in `agent/lib/test_watchdog.sh`:
```bash
# Description of why this substring causes false positives
"non_fatal"                # test_non_fatal_* test names match Tier-1 "FATAL" pattern
```

## Verification
```bash
cd /rebase/vllm-omni-rebase-agent && source agent/lib/test_watchdog.sh
_is_simulated_test_error "<matched_line>" "<test_group_name>" && echo "IGNORED - CORRECT"
```

Also run the affected tests in isolation:
```bash
cd /rebase/vllm-omni && python -m pytest <test_path> -xvs
```
