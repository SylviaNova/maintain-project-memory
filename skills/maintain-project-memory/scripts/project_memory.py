#!/usr/bin/env python3
"""Initialize, inspect, and validate local verified project memory."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MEMORY_NAME = ".project-memory"
IGNORE_RULE = f"/{MEMORY_NAME}/"
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "context-template"
REQUIRED_FILES = {
    "INDEX.md": "<!-- project-memory:document=index schema=1 -->",
    "OVERVIEW.md": "<!-- project-memory:document=overview schema=1 -->",
    "STATUS.md": "<!-- project-memory:document=status schema=1 -->",
    "DECISIONS.md": "<!-- project-memory:document=decisions schema=1 -->",
    "CHANGELOG.md": "<!-- project-memory:document=changelog schema=1 -->",
}
CONFIG_KEYS = {
    "schema_version",
    "language",
    "update_mode",
    "storage_mode",
    "publish_policy",
    "max_active_log_entries",
}
SECRET_PATTERNS = {
    "private key": re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "API token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
}


class ProjectMemoryError(RuntimeError):
    """Raised when project memory cannot be handled safely."""


def run_command(
    args: list[str], cwd: Path, *, check: bool = False
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise ProjectMemoryError(f"{' '.join(args)}: {detail}")
    return result


def normalize_start(path_value: str) -> Path:
    candidate = Path(path_value).expanduser().resolve()
    if not candidate.exists():
        raise ProjectMemoryError(f"Project path does not exist: {candidate}")
    return candidate.parent if candidate.is_file() else candidate


def nearest_git_marker(candidate: Path) -> Path | None:
    for directory in (candidate, *candidate.parents):
        if (directory / ".git").exists():
            return directory
    return None


def discover_project(path_value: str) -> tuple[Path, bool]:
    candidate = normalize_start(path_value)
    if shutil.which("git"):
        result = run_command(
            ["git", "rev-parse", "--show-toplevel"], cwd=candidate
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve(), True
        marker = nearest_git_marker(candidate)
        if marker:
            raise ProjectMemoryError(
                f"Git metadata exists at {marker}, but Git cannot inspect the repository"
            )
    elif nearest_git_marker(candidate):
        raise ProjectMemoryError(
            "Git metadata exists, but the git executable is unavailable; "
            "privacy cannot be verified"
        )
    return candidate, False


def git_output(root: Path, args: list[str], default: str = "") -> str:
    result = run_command(["git", *args], cwd=root)
    if result.returncode != 0:
        return default
    return result.stdout.strip()


def git_lines(root: Path, args: list[str]) -> list[str]:
    output = git_output(root, args)
    return [line for line in output.splitlines() if line.strip()]


def memory_tracked_files(root: Path) -> list[str]:
    return git_lines(root, ["ls-files", "--", MEMORY_NAME])


def memory_staged_files(root: Path) -> list[str]:
    return git_lines(
        root, ["diff", "--cached", "--name-only", "--", MEMORY_NAME]
    )


def memory_is_ignored(root: Path) -> bool:
    result = run_command(
        [
            "git",
            "check-ignore",
            "--no-index",
            "-q",
            "--",
            f"{MEMORY_NAME}/INDEX.md",
        ],
        cwd=root,
    )
    return result.returncode == 0


def git_metadata(root: Path) -> dict[str, Any]:
    branch = git_output(root, ["rev-parse", "--abbrev-ref", "HEAD"], "unborn")
    commit = git_output(root, ["rev-parse", "--short", "HEAD"], "unborn")
    raw_changes = git_lines(
        root, ["status", "--short", "--untracked-files=all"]
    )
    task_changes = [
        line for line in raw_changes if f"{MEMORY_NAME}/" not in line
    ]
    return {
        "branch": branch,
        "commit": commit,
        "dirty": bool(task_changes),
        "changes": task_changes,
        "memory_ignored": memory_is_ignored(root),
        "memory_tracked": memory_tracked_files(root),
        "memory_staged": memory_staged_files(root),
    }


def resolve_git_path(root: Path, git_path: str) -> Path:
    value = git_output(root, ["rev-parse", "--git-path", git_path])
    if not value:
        raise ProjectMemoryError(f"Cannot resolve Git path: {git_path}")
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def append_ignore_rule(path: Path) -> bool:
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        normalized = {
            line.strip()
            for line in existing.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        if IGNORE_RULE in normalized or f"{MEMORY_NAME}/" in normalized:
            return False

    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = existing
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix and not prefix.endswith("\n\n"):
        prefix += "\n"
    block = (
        "# maintain-project-memory: keep verified project memory local\n"
        f"{IGNORE_RULE}\n"
    )
    path.write_text(prefix + block, encoding="utf-8")
    return True


def ensure_local_private(root: Path) -> str:
    tracked = memory_tracked_files(root)
    staged = memory_staged_files(root)
    if tracked:
        raise ProjectMemoryError(
            "Project memory is already tracked; refusing to change Git tracking automatically"
        )
    if staged:
        raise ProjectMemoryError(
            "Project memory is staged; refusing to change the Git index automatically"
        )
    if memory_is_ignored(root):
        return "existing ignore rule"

    exclude_error = ""
    try:
        exclude_path = resolve_git_path(root, "info/exclude")
        append_ignore_rule(exclude_path)
        if memory_is_ignored(root):
            return str(exclude_path)
    except (OSError, ProjectMemoryError) as exc:
        exclude_error = str(exc)

    try:
        gitignore_path = root / ".gitignore"
        append_ignore_rule(gitignore_path)
        if memory_is_ignored(root):
            return str(gitignore_path)
    except OSError as exc:
        fallback_error = str(exc)
    else:
        fallback_error = "ignore verification failed"

    details = "; ".join(
        value
        for value in (
            f"local exclude: {exclude_error}" if exclude_error else "",
            f".gitignore: {fallback_error}",
        )
        if value
    )
    raise ProjectMemoryError(
        f"Cannot establish a verified local-private Git exclusion ({details})"
    )


def read_config(memory_dir: Path) -> dict[str, Any] | None:
    path = memory_dir / "config.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectMemoryError(f"Invalid config.json: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectMemoryError("config.json must contain a JSON object")
    return value


def template_values(
    root: Path, is_git: bool, storage_mode: str
) -> dict[str, str]:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    if is_git:
        metadata = git_metadata(root)
        revision = str(metadata["commit"])
        if metadata["dirty"]:
            revision += " (uncommitted changes)"
        branch = str(metadata["branch"])
        kind = "git"
    else:
        revision = "local"
        branch = "not-applicable"
        kind = "local"
    return {
        "{{PROJECT_NAME}}": root.name,
        "{{PROJECT_KIND}}": kind,
        "{{STORAGE_MODE}}": storage_mode,
        "{{GENERATED_AT}}": now,
        "{{GIT_BRANCH}}": branch,
        "{{GIT_COMMIT}}": revision,
    }


def render_template(source: Path, values: dict[str, str]) -> str:
    content = source.read_text(encoding="utf-8")
    for token, value in values.items():
        content = content.replace(token, value)
    return content


def initialize(args: argparse.Namespace) -> int:
    root, is_git = discover_project(args.project)
    memory_dir = root / MEMORY_NAME
    existing_config = read_config(memory_dir)
    existing_mode = (
        str(existing_config.get("storage_mode"))
        if existing_config and existing_config.get("storage_mode")
        else None
    )
    storage_mode = args.storage_mode or existing_mode or "local-private"

    if existing_mode and args.storage_mode and existing_mode != args.storage_mode:
        raise ProjectMemoryError(
            f"Existing storage mode is {existing_mode}; init will not change it"
        )
    if storage_mode == "tracked" and not args.confirm_publish:
        raise ProjectMemoryError(
            "Tracked mode requires --confirm-publish after explicit user consent"
        )
    if storage_mode == "tracked" and not is_git:
        raise ProjectMemoryError("Tracked mode requires a Git project")

    privacy_method = "not-applicable"
    if is_git and storage_mode == "local-private":
        privacy_method = ensure_local_private(root)
    elif is_git and storage_mode == "tracked" and memory_is_ignored(root):
        raise ProjectMemoryError(
            "Project memory is ignored; remove the ignore rule manually before tracked initialization"
        )

    if not TEMPLATE_DIR.is_dir():
        raise ProjectMemoryError(f"Template directory is missing: {TEMPLATE_DIR}")

    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "archive").mkdir(exist_ok=True)
    values = template_values(root, is_git, storage_mode)
    created: list[str] = []
    preserved: list[str] = []

    for source in sorted(TEMPLATE_DIR.iterdir()):
        if not source.is_file():
            continue
        destination = memory_dir / source.name
        if destination.exists():
            preserved.append(source.name)
            continue
        destination.write_text(
            render_template(source, values), encoding="utf-8"
        )
        created.append(source.name)

    config_path = memory_dir / "config.json"
    if "config.json" in created:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["storage_mode"] = storage_mode
        config_path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if is_git and storage_mode == "local-private":
        metadata = git_metadata(root)
        if (
            not metadata["memory_ignored"]
            or metadata["memory_tracked"]
            or metadata["memory_staged"]
        ):
            raise ProjectMemoryError(
                "Post-initialization Git privacy verification failed"
            )

    print(
        json.dumps(
            {
                "result": "initialized" if created else "already-initialized",
                "project_root": str(root),
                "project_kind": "git" if is_git else "local",
                "storage_mode": storage_mode,
                "privacy_method": privacy_method,
                "created": created,
                "preserved": preserved,
                "next_action": (
                    "Inspect the project, replace empty template statements with "
                    "verified facts, then run validate --strict."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def inspect_project(args: argparse.Namespace) -> int:
    root, is_git = discover_project(args.project)
    memory_dir = root / MEMORY_NAME
    output: dict[str, Any] = {
        "project_root": str(root),
        "project_kind": "git" if is_git else "local",
        "memory_exists": memory_dir.is_dir(),
        "memory_path": str(memory_dir),
    }
    if memory_dir.is_dir():
        try:
            output["config"] = read_config(memory_dir)
        except ProjectMemoryError as exc:
            output["config_error"] = str(exc)
    if is_git:
        output["git"] = git_metadata(root)
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


def find_secrets(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return findings
    for line_number, line in enumerate(lines, start=1):
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(line):
                findings.append((line_number, label))
    return findings


def validate(args: argparse.Namespace) -> int:
    root, is_git = discover_project(args.project)
    memory_dir = root / MEMORY_NAME
    errors: list[str] = []
    warnings: list[str] = []

    if not memory_dir.is_dir():
        errors.append(f"Missing {MEMORY_NAME} directory")
    else:
        config: dict[str, Any] | None = None
        try:
            config = read_config(memory_dir)
        except ProjectMemoryError as exc:
            errors.append(str(exc))

        if config is None:
            errors.append("Missing config.json")
        else:
            missing_keys = sorted(CONFIG_KEYS - set(config))
            if missing_keys:
                errors.append(
                    f"config.json missing keys: {', '.join(missing_keys)}"
                )
            if config.get("schema_version") != 1:
                errors.append("config.json schema_version must be 1")
            if config.get("update_mode") not in {"auto", "manual"}:
                errors.append("config.json update_mode must be auto or manual")
            if config.get("storage_mode") not in {
                "local-private",
                "tracked",
            }:
                errors.append(
                    "config.json storage_mode must be local-private or tracked"
                )
            if config.get("publish_policy") != "explicit-opt-in":
                errors.append(
                    "config.json publish_policy must be explicit-opt-in"
                )
            limit = config.get("max_active_log_entries")
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                errors.append(
                    "config.json max_active_log_entries must be a positive integer"
                )

        for filename, marker in REQUIRED_FILES.items():
            path = memory_dir / filename
            if not path.is_file():
                errors.append(f"Missing {filename}")
                continue
            content = path.read_text(encoding="utf-8")
            if not content.startswith(marker):
                errors.append(f"{filename} has a missing or invalid schema marker")
            if re.search(r"\{\{[A-Z0-9_]+\}\}", content):
                errors.append(f"{filename} contains unresolved template tokens")
            if re.search(r"(?i)\bTODO\b", content):
                warnings.append(f"{filename} contains TODO")

        archive_dir = memory_dir / "archive"
        if not archive_dir.is_dir():
            errors.append("Missing archive directory")
        else:
            for archive_path in archive_dir.glob("*.md"):
                archive_marker = (
                    "<!-- project-memory:document=archive schema=1 -->"
                )
                if not archive_path.read_text(encoding="utf-8").startswith(
                    archive_marker
                ):
                    errors.append(
                        f"{archive_path.relative_to(memory_dir)} has a missing "
                        "or invalid schema marker"
                    )

        for candidate in memory_dir.rglob("*"):
            if not candidate.is_file() or candidate.suffix not in {".md", ".json"}:
                continue
            for line_number, label in find_secrets(candidate):
                relative = candidate.relative_to(memory_dir)
                errors.append(
                    f"{relative}:{line_number} contains a likely {label}"
                )

        if config and isinstance(config.get("max_active_log_entries"), int):
            changelog = memory_dir / "CHANGELOG.md"
            if changelog.is_file():
                count = len(
                    re.findall(
                        r"^## \d{4}-\d{2}-\d{2}(?:\s|:)",
                        changelog.read_text(encoding="utf-8"),
                        flags=re.MULTILINE,
                    )
                )
                if count > config["max_active_log_entries"]:
                    warnings.append(
                        "CHANGELOG.md exceeds max_active_log_entries; archive older entries"
                    )

        if is_git and config and config.get("storage_mode") == "local-private":
            metadata = git_metadata(root)
            if not metadata["memory_ignored"]:
                errors.append("Local-private project memory is not Git-ignored")
            if metadata["memory_tracked"]:
                errors.append("Local-private project memory is tracked by Git")
            if metadata["memory_staged"]:
                errors.append("Local-private project memory is staged in Git")

    result = {
        "result": "valid" if not errors else "invalid",
        "project_root": str(root),
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if errors or (args.strict and warnings):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain a local, verified .project-memory document set."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect project, Git, and memory state"
    )
    inspect_parser.add_argument("--project", default=".")
    inspect_parser.set_defaults(handler=inspect_project)

    init_parser = subparsers.add_parser(
        "init", help="Initialize project memory without overwriting existing files"
    )
    init_parser.add_argument("--project", default=".")
    init_parser.add_argument(
        "--storage-mode",
        choices=("local-private", "tracked"),
        default=None,
    )
    init_parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Confirm explicit user consent for tracked storage",
    )
    init_parser.set_defaults(handler=initialize)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate structure, privacy, and likely secrets"
    )
    validate_parser.add_argument("--project", default=".")
    validate_parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures"
    )
    validate_parser.set_defaults(handler=validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ProjectMemoryError as exc:
        print(
            json.dumps(
                {"result": "error", "error": str(exc)},
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(
            json.dumps(
                {"result": "error", "error": str(exc)},
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
