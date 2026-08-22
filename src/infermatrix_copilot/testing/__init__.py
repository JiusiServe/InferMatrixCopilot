"""Repo-neutral test-execution substrate: the Python port of the rebase
agent's shell test layer (gpu_lock.sh, kill_test_tree.sh, test_watchdog.sh,
test_runner.sh). Repo-specific data — watchdog patterns, artifact globs, the
test manifest — lives adapter-side; these modules take it as input."""
