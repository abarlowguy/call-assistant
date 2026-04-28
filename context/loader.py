from pathlib import Path


def load_context(file_path: str) -> str:
    """Loads a .md or .txt file as project context. Strips Obsidian frontmatter."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Context file not found: {file_path}")
    text = path.read_text(encoding="utf-8")
    # strip YAML frontmatter if present
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:].strip()
    return text


def vault_search(query: str, vault_root: str = "/Users/andrewbarlow/andrewvault/Andrew") -> list[dict]:
    """Returns list of {path, name} for vault files matching query in filename."""
    root = Path(vault_root)
    query_lower = query.lower()
    matches = []
    for f in root.rglob("*.md"):
        if query_lower in f.stem.lower():
            matches.append({"path": str(f), "name": f.stem})
    return matches[:10]
