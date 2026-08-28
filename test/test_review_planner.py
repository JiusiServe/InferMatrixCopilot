"""Hybrid review-depth planner (review/planner.py): deterministic signals +
rule table, depth invariants, and the gray-zone LLM call's guardrails."""

import json

import pytest

from infermatrix_copilot.engine.steps.review.prompts import _REVIEW_LENSES
from infermatrix_copilot.llm import Block, Reply
from infermatrix_copilot.review.planner import (
    DEFAULT_STANDARD_LENSES,
    DEPTHS,
    diff_signals,
    classify,
    plan_review,
)

NAMES = tuple(l["name"] for l in _REVIEW_LENSES)
RISKY = ("vllm_omni/worker/", "vllm_omni/core/")


class OneShotLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []
        self.available = True

    def create(self, *, system, messages, tools=None, model=None,
               max_tokens=None, on_text=None, role=""):
        self.calls.append({"system": system, "messages": [*messages],
                           "model": model, "max_tokens": max_tokens})
        if isinstance(self._reply, Exception):
            raise self._reply
        return self._reply


def _reply(obj) -> Reply:
    text = obj if isinstance(obj, str) else json.dumps(obj)
    return Reply(blocks=[Block(type="text", text=text)])


def _diff(*files, lines_per_file=2, minus=False):
    """Synthetic unified diff: `files` are b-side paths; each gets
    `lines_per_file` added (or removed) plain lines."""
    parts = []
    for f in files:
        sign = "-" if minus else "+"
        old = "/dev/null" if not minus else f"a/{f}"
        new = f"b/{f}" if not minus else "/dev/null"
        parts.append(f"diff --git a/{f} b/{f}\n--- {old}\n+++ {new}\n"
                     + "\n".join(f"{sign}line {i}" for i in range(lines_per_file)))
    return "\n".join(parts) + "\n"


# ---- signal parsing ---------------------------------------------------------

def test_signals_counts_and_classes():
    diff = (_diff("src/mod.py", lines_per_file=3)
            + _diff("tests/test_mod.py", lines_per_file=2)
            + _diff("docs/guide.md", lines_per_file=1)
            + _diff("deploy/stage.yaml", lines_per_file=1))
    sig = diff_signals(diff)
    assert len(sig.files) == 4 and sig.insertions == 7 and sig.deletions == 0
    assert sig.code_files == ("src/mod.py",)
    assert sig.test_files == ("tests/test_mod.py",)
    assert sig.doc_files == ("docs/guide.md",)
    assert sig.config_files == ("deploy/stage.yaml",)
    assert sig.asset_files == ()
    assert not sig.docs_only


def test_signals_api_hints_split_changed_vs_added():
    diff = ("diff --git a/src/mod.py b/src/mod.py\n"
            "--- a/src/mod.py\n+++ b/src/mod.py\n"
            "-def handler(x):\n+def handler(x, y):\n"
            "+MAX_RETRIES = 3\n"
            "diff --git a/tests/test_mod.py b/tests/test_mod.py\n"
            "--- a/tests/test_mod.py\n+++ b/tests/test_mod.py\n"
            "+def test_handler():\n")
    sig = diff_signals(diff)
    # only the `-` line is a changed-surface hint (it had old consumers);
    # +def/+CONST count as additions and never disqualify light; test files
    # are excluded entirely
    assert len(sig.api_change_hints) == 1
    assert sig.api_change_hints[0].startswith("src/mod.py")
    assert sig.api_added == 2


def test_rules_pure_addition_of_a_function_stays_light(settings):
    diff = ("diff --git a/src/mod.py b/src/mod.py\n"
            "--- a/src/mod.py\n+++ b/src/mod.py\n"
            "+def warn_on_overflow(req):\n"
            "+    return len(req) > CAP\n")
    assert classify(diff_signals(diff), settings)[0] == "light"


def test_signals_pure_deletion_counts_the_old_side():
    diff = ("diff --git a/vllm_omni/worker/x.py b/vllm_omni/worker/x.py\n"
            "deleted file mode 100644\n"
            "--- a/vllm_omni/worker/x.py\n+++ /dev/null\n"
            "-def gone():\n-    pass\n")
    sig = diff_signals(diff, RISKY)
    assert sig.files == ("vllm_omni/worker/x.py",)
    assert sig.high_risk_files == ("vllm_omni/worker/x.py",)
    assert sig.deletions == 2


def test_signals_rename_from_high_risk_path():
    diff = ("diff --git a/vllm_omni/core/sched.py b/other/sched.py\n"
            "similarity index 98%\n"
            "rename from vllm_omni/core/sched.py\n"
            "rename to other/sched.py\n")
    sig = diff_signals(diff, RISKY)
    assert "vllm_omni/core/sched.py" in sig.files
    assert "other/sched.py" in sig.files
    assert sig.high_risk_files == ("vllm_omni/core/sched.py",)


def test_signals_binary_and_mode_only_have_only_the_git_header():
    diff = ("diff --git a/vllm_omni/worker/blob.bin b/vllm_omni/worker/blob.bin\n"
            "Binary files a/vllm_omni/worker/blob.bin and /dev/null differ\n"
            "diff --git a/scripts/run.sh b/scripts/run.sh\n"
            "old mode 100644\nnew mode 100755\n")
    sig = diff_signals(diff, RISKY)
    assert "vllm_omni/worker/blob.bin" in sig.files
    assert "scripts/run.sh" in sig.files
    assert sig.high_risk_files == ("vllm_omni/worker/blob.bin",)


def test_signals_quoted_paths_unquoted():
    diff = ('diff --git "a/docs/my guide.md" "b/docs/my guide.md"\n'
            '--- "a/docs/my guide.md"\n+++ "b/docs/my guide.md"\n+hello\n')
    sig = diff_signals(diff)
    assert sig.files == ("docs/my guide.md",)
    assert sig.docs_only


# ---- rule table -------------------------------------------------------------

def test_rules_light_on_tiny_low_risk_diff(settings):
    sig = diff_signals(_diff("src/a.py", "src/b.py", lines_per_file=10))
    depth, reason = classify(sig, settings)
    assert depth == "light" and "small low-risk" in reason


def test_rules_docs_only_depth_scales_with_size(settings):
    # docs PRs are reviews of claims; only genuinely small ones stay light
    # (wave-2: the light tier ran at ~half the baseline's recall on every
    # docs item). Mid-size docs go standard, large docs go full.
    small = diff_signals(_diff("docs/small.md", lines_per_file=30))
    depth, reason = classify(small, settings)
    assert depth == "light" and "docs-only" in reason
    mid = diff_signals(_diff("docs/mid.md", lines_per_file=200))
    assert classify(mid, settings)[0] == "standard"
    big = diff_signals(_diff("docs/big.md", lines_per_file=900))
    assert classify(big, settings)[0] == "full"


def test_rules_docs_heavy_with_asset_rider_is_not_gray(settings):
    # a nav yml or an image beside doc files must not push a docs PR into
    # the gray zone (wave-2 pr5610: 3 docs + 1 asset fell to the LLM
    # planner, which failed, and the docs pass set was never selected)
    diff = _diff("docs/a.md", "docs/b.md", lines_per_file=120)
    diff += _diff("docs/.nav.yml", lines_per_file=4)
    sig = diff_signals(diff)
    assert sig.docs_heavy
    assert classify(sig, settings)[0] == "standard"


def test_rules_full_on_large_diff(settings):
    sig = diff_signals(_diff("src/a.py", lines_per_file=401))
    assert classify(sig, settings)[0] == "full"
    sig = diff_signals(_diff(*(f"src/f{i}.py" for i in range(9)),
                             lines_per_file=1))
    assert classify(sig, settings)[0] == "full"


def test_rules_test_asset_heavy_diff_goes_gray_not_full(settings):
    diff = (
        _diff("src/a.py", "src/b.py", "src/c.py", lines_per_file=70)
        + _diff("tests/test_a.py", "tests/test_b.py", lines_per_file=120)
        + _diff("tests/assets/ref.txt", lines_per_file=160)
        + _diff("tests/assets/ref.png", lines_per_file=1)
    )
    sig = diff_signals(diff)
    assert sig.lines_changed > settings.large_diff_lines
    assert len(sig.files) > settings.large_diff_files or sig.lines_changed > 400
    assert sig.code_lines_changed <= settings.large_diff_lines
    assert classify(sig, settings) is None


def test_rules_full_on_high_risk_and_name_fallback(settings):
    sig = diff_signals(_diff("vllm_omni/worker/w.py", lines_per_file=1), RISKY)
    assert classify(sig, settings)[0] == "full"
    # bare module-name fallback matches as a path segment
    sig = diff_signals(_diff("x/scheduler/y.py", lines_per_file=1),
                       ("scheduler",))
    assert classify(sig, settings)[0] == "full"


def test_rules_mixed_docs_plus_deletion_is_not_light(settings):
    diff = (_diff("docs/guide.md", lines_per_file=2)
            + _diff("vllm_omni/worker/x.py", lines_per_file=3, minus=True))
    sig = diff_signals(diff, RISKY)
    assert not sig.docs_only
    assert classify(sig, settings)[0] == "full"  # deleted high-risk file


def test_rules_empty_diff_goes_gray_not_light(settings):
    assert classify(diff_signals(""), settings) is None


def test_rules_api_change_disqualifies_light(settings):
    diff = ("diff --git a/src/mod.py b/src/mod.py\n"
            "--- a/src/mod.py\n+++ b/src/mod.py\n"
            "-def handler(x):\n+def handler(x, y):\n")
    assert classify(diff_signals(diff), settings) is None  # gray, not light


def test_rules_value_flip_disqualifies_light(settings):
    # a tiny diff that flips an existing assignment's value (default lists,
    # flags, thresholds) can have repo-wide blast radius — it must go gray,
    # never light, even though no def/class/CONST shape changed
    diff = ("diff --git a/src/platform.py b/src/platform.py\n"
            "--- a/src/platform.py\n+++ b/src/platform.py\n"
            '-        default = ["native"] if using_inductor else ["c", "native"]\n'
            '+        default = ["c", "native"]\n')
    sig = diff_signals(diff)
    assert sig.value_flips == ('src/platform.py: `default`',)
    assert classify(sig, settings) is None  # gray, not light


def test_signals_code_motion_is_not_a_value_flip(settings):
    # same LHS, same RHS: the assignment merely moved — still light
    diff = ("diff --git a/src/mod.py b/src/mod.py\n"
            "--- a/src/mod.py\n+++ b/src/mod.py\n"
            "-    limit = 10\n"
            "+    limit = 10\n")
    sig = diff_signals(diff)
    assert sig.value_flips == ()
    assert classify(sig, settings)[0] == "light"


def test_signals_config_file_flip_stays_light(settings):
    # the flip signal is code-file-only: a 2-line yaml value change keeps the
    # light tier (config semantics are the config owner's checklist, and tiny
    # config deletions measured as safe light items)
    diff = ("diff --git a/deploy/a.yaml b/deploy/a.yaml\n"
            "--- a/deploy/a.yaml\n+++ b/deploy/a.yaml\n"
            "-timeout = 30\n"
            "+timeout = 60\n")
    sig = diff_signals(diff)
    assert sig.value_flips == ()
    assert classify(sig, settings)[0] == "light"


# ---- plan_review: overrides and invariants ----------------------------------

def test_override_wins_with_zero_llm_calls(settings):
    llm = OneShotLLM(_reply({"depth": "standard"}))
    plan = plan_review(_diff("src/a.py"), settings=settings, lens_names=NAMES,
                       override="full", llm=llm)
    assert plan.depth == "full" and plan.planner == "override"
    assert plan.lens_names == NAMES
    assert not llm.calls


def test_depth_invariants_hold_for_every_source(settings):
    light = plan_review(_diff("docs/a.md"), settings=settings, lens_names=NAMES)
    assert light.depth == "light" and light.lens_names == ()
    full = plan_review(_diff("src/a.py", lines_per_file=500),
                       settings=settings, lens_names=NAMES)
    assert full.depth == "full" and full.lens_names == NAMES


def test_default_standard_lenses_stay_in_sync_with_prompts():
    assert set(DEFAULT_STANDARD_LENSES) <= set(NAMES)
    assert set(DEPTHS) == {"light", "standard", "full"}


# ---- gray zone: the LLM planner and its guardrails --------------------------

GRAY = _diff("src/a.py", "src/b.py", "src/c.py", "src/d.py", lines_per_file=50)


def test_gray_zone_llm_picks_standard(settings):
    llm = OneShotLLM(_reply({"depth": "standard",
                             "lenses": ["logic", "verification"],
                             "reason": "no api changes"}))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm,
                       model="m")
    assert plan.depth == "standard" and plan.planner == "llm"
    assert plan.lens_names == ("logic", "verification")
    # 2000, not 400: reasoning models spend tokens thinking before the JSON;
    # at 400 the planner reply was cut pre-JSON and silently failed every time
    assert len(llm.calls) == 1 and llm.calls[0]["max_tokens"] == 8_000
    # untrusted diff content is fenced in the prompt
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "<untrusted_data>" in prompt and "</untrusted_data>" in prompt


def test_gray_zone_llm_cannot_pick_light(settings):
    llm = OneShotLLM(_reply({"depth": "light", "lenses": []}))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.planner == "llm-fallback"
    assert plan.depth == "standard"
    assert plan.lens_names == DEFAULT_STANDARD_LENSES


def test_gray_zone_llm_full_with_partial_lenses_coerces_to_all(settings):
    llm = OneShotLLM(_reply({"depth": "full", "lenses": ["logic"]}))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.depth == "full" and plan.lens_names == NAMES


def test_gray_zone_lens_coercion_pads_and_filters(settings):
    llm = OneShotLLM(_reply({"depth": "standard",
                             "lenses": ["behavior", "bogus-lens"]}))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.depth == "standard"
    assert len(plan.lens_names) == 2 and "bogus-lens" not in plan.lens_names
    assert "behavior" in plan.lens_names


@pytest.mark.parametrize("llm", [
    None,
    OneShotLLM(_reply("no json here, just prose")),
    OneShotLLM(RuntimeError("api down")),
])
def test_gray_zone_failures_fall_back_deterministically(settings, llm):
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.planner == "llm-fallback"
    assert plan.depth == "standard" and plan.lens_names == DEFAULT_STANDARD_LENSES


# ---- planner_error: WHY the gray-zone call produced no plan -----------------
# `planner=="llm-fallback"` said only THAT it failed. A missing client, a
# transport error and a model answering off-contract are three different
# operational problems, and the silent `except Exception: return None` made them
# indistinguishable — which is how an 8000-token ceiling bug hid across two
# campaigns behind a deliberate-looking standard fallback.
@pytest.mark.parametrize(("llm", "expected"), [
    (None, "unavailable"),
    (OneShotLLM(RuntimeError("api down")), "transport:RuntimeError: api down"),
    (OneShotLLM(_reply("")), "empty_reply (stop_reason="),
    (OneShotLLM(_reply("no json here, just prose")),
     "unparseable: no json here"),
    (OneShotLLM(_reply({"depth": "light", "lenses": []})),
     "rejected_depth:light"),
])
def test_planner_error_distinguishes_every_failure_cause(settings, llm, expected):
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.planner == "llm-fallback"
    assert plan.planner_error.startswith(expected)


def test_planner_error_is_empty_on_deterministic_paths(settings):
    """Rules and override are not failures and must not look like ones."""
    ruled = plan_review(_diff("docs/x.md"), settings=settings, lens_names=NAMES)
    assert ruled.planner in ("rules", "override") and ruled.planner_error == ""
    forced = plan_review(GRAY, settings=settings, lens_names=NAMES,
                         override="full")
    assert forced.planner == "override" and forced.planner_error == ""


def test_planner_error_is_empty_when_the_call_succeeds(settings):
    llm = OneShotLLM(_reply({"depth": "full", "lenses": list(NAMES)}))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert plan.planner == "llm" and plan.planner_error == ""


def test_planner_error_clips_and_carries_no_payload(settings):
    """Causes are truncated: a planner error is a diagnostic line in a run
    report, not a channel for an unbounded model reply."""
    llm = OneShotLLM(_reply("x" * 5_000))
    plan = plan_review(GRAY, settings=settings, lens_names=NAMES, llm=llm)
    assert len(plan.planner_error) < 200
