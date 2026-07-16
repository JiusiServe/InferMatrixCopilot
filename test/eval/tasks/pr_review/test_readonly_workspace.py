import subprocess

from eval.tasks.pr_review.repository.readonly_workspace import ReadOnlyWorkspace


def test_snapshot_does_not_contain_review_after_commit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=source, check=True)
    subprocess.run(["git", "config", "user.name", "a"], cwd=source, check=True)
    (source / "a.txt").write_text("A\n")
    subprocess.run(["git", "add", "a.txt"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-qm", "A"], cwd=source, check=True)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    (source / "a.txt").write_text("A\nB\n")
    subprocess.run(["git", "commit", "-qam", "B"], cwd=source, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    (source / "a.txt").write_text("A\nB\nC\n")
    subprocess.run(["git", "commit", "-qam", "review-after"], cwd=source, check=True)
    after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    bare = tmp_path / "cache.git"
    subprocess.run(["git", "clone", "-q", "--bare", "--no-local", str(source), str(bare)], check=True)

    with ReadOnlyWorkspace(bare, head, base_sha=base) as workspace:
        assert subprocess.run(["git", "cat-file", "-e", head], cwd=workspace).returncode == 0
        assert subprocess.run(["git", "cat-file", "-e", base], cwd=workspace).returncode == 0
        assert subprocess.run(["git", "cat-file", "-e", after], cwd=workspace).returncode != 0
        assert (workspace / "a.txt").read_text() == "A\nB\n"
