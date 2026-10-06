"""Source identities and pinned links do not require a GitHub repository."""
from urllib.parse import quote


def source_base(repository, pin):
    if repository.startswith("repo://"):
        return repository.rstrip("/") + "/blob/" + pin + "/"
    if repository.startswith(("https://", "http://")):
        root = repository.rstrip("/").removesuffix(".git")
        return root + ("/blob/" if root.startswith("https://github.com/") else "/-/blob/") + pin + "/"
    if repository.count("/") == 1:
        return f"https://github.com/{repository}/blob/{pin}/"
    return f"repo://{quote(repository, safe='')}/blob/{pin}/"


def source_link(repository, pin, path, start, end):
    return source_base(repository, pin) + quote(path, safe="/") + f"#L{start}-L{end}"
