from __future__ import annotations

from pathlib import Path
import sys


def iter_env_file_paths(compose_text: str) -> list[str]:
    paths: list[str] = []
    in_env_file_block = False

    for raw_line in compose_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("env_file:"):
            in_env_file_block = True
            continue

        if in_env_file_block and stripped.startswith("- "):
            value = stripped[2:].strip().strip("'").strip('"')
            paths.append(value)
            continue

        if in_env_file_block and not stripped.startswith("- "):
            in_env_file_block = False

    return paths


def main() -> int:
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    compose_text = compose_path.read_text(encoding="utf-8")

    missing: list[Path] = []
    for rel_path in iter_env_file_paths(compose_text):
        candidate = (compose_path.parent / rel_path).resolve()
        if not candidate.exists():
            missing.append(candidate)

    if missing:
        print("Missing env files referenced by docker-compose.yml:")
        for path in missing:
            print(f" - {path}")
        return 1

    print("All docker-compose env_file paths exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
