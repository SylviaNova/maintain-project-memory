from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "maintain-project-memory"
    / "scripts"
    / "project_memory.py"
)


class ProjectMemoryCliTests(unittest.TestCase):
    def run_cli(
        self, *args: str, expected: int = 0
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def test_local_project_init_is_idempotent_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "local-project"
            project.mkdir()
            (project / "main.py").write_text("print('ok')\n", encoding="utf-8")

            first = self.run_cli("init", "--project", str(project))
            first_data = json.loads(first.stdout)
            self.assertEqual(first_data["project_kind"], "local")
            self.assertEqual(first_data["storage_mode"], "local-private")
            self.assertTrue((project / ".project-memory" / "INDEX.md").is_file())

            second = self.run_cli("init", "--project", str(project))
            second_data = json.loads(second.stdout)
            self.assertEqual(second_data["result"], "already-initialized")

            self.run_cli(
                "validate", "--project", str(project), "--strict"
            )

    @unittest.skipUnless(shutil.which("git"), "Git is not available")
    def test_git_project_is_local_private_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "git-project"
            project.mkdir()
            subprocess.run(
                ["git", "init", "-q"],
                cwd=project,
                check=True,
                text=True,
            )

            result = self.run_cli("init", "--project", str(project))
            data = json.loads(result.stdout)
            self.assertEqual(data["storage_mode"], "local-private")

            ignored = subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "--no-index",
                    "-q",
                    "--",
                    ".project-memory/INDEX.md",
                ],
                cwd=project,
                check=False,
            )
            self.assertEqual(ignored.returncode, 0)
            self.assertEqual(
                subprocess.run(
                    ["git", "ls-files", "--", ".project-memory"],
                    cwd=project,
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout,
                "",
            )
            self.run_cli(
                "validate", "--project", str(project), "--strict"
            )

    @unittest.skipUnless(shutil.which("git"), "Git is not available")
    def test_tracked_mode_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "git-project"
            project.mkdir()
            subprocess.run(
                ["git", "init", "-q"],
                cwd=project,
                check=True,
                text=True,
            )

            self.run_cli(
                "init",
                "--project",
                str(project),
                "--storage-mode",
                "tracked",
                expected=2,
            )
            self.assertFalse((project / ".project-memory").exists())

    @unittest.skipUnless(shutil.which("git"), "Git is not available")
    def test_local_private_init_refuses_already_tracked_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "git-project"
            memory = project / ".project-memory"
            memory.mkdir(parents=True)
            (memory / "INDEX.md").write_text("existing\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "-q"],
                cwd=project,
                check=True,
                text=True,
            )
            subprocess.run(
                ["git", "add", ".project-memory/INDEX.md"],
                cwd=project,
                check=True,
                text=True,
            )

            result = self.run_cli(
                "init", "--project", str(project), expected=2
            )
            self.assertIn("already tracked", result.stderr)

    @unittest.skipUnless(shutil.which("git"), "Git is not available")
    def test_tracked_mode_still_does_not_stage_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "git-project"
            project.mkdir()
            subprocess.run(
                ["git", "init", "-q"],
                cwd=project,
                check=True,
                text=True,
            )

            self.run_cli(
                "init",
                "--project",
                str(project),
                "--storage-mode",
                "tracked",
                "--confirm-publish",
            )
            config = json.loads(
                (project / ".project-memory" / "config.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(config["storage_mode"], "tracked")
            staged = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=project,
                text=True,
                capture_output=True,
                check=True,
            ).stdout
            self.assertEqual(staged, "")
            self.run_cli(
                "validate", "--project", str(project), "--strict"
            )

    def test_validation_detects_likely_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "local-project"
            project.mkdir()
            self.run_cli("init", "--project", str(project))
            status_path = project / ".project-memory" / "STATUS.md"
            with status_path.open("a", encoding="utf-8") as stream:
                stream.write("\nAKIA1234567890ABCDEF\n")

            result = self.run_cli(
                "validate",
                "--project",
                str(project),
                "--strict",
                expected=1,
            )
            self.assertIn("AWS access key", result.stdout)

    def test_validation_scans_archived_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "local-project"
            project.mkdir()
            self.run_cli("init", "--project", str(project))
            archive = project / ".project-memory" / "archive" / "2026.md"
            archive.write_text(
                "<!-- project-memory:document=archive schema=1 -->\n"
                "# Archive\n\n"
                "ghp_abcdefghijklmnopqrstuvwxyz1234567890\n",
                encoding="utf-8",
            )

            result = self.run_cli(
                "validate",
                "--project",
                str(project),
                "--strict",
                expected=1,
            )
            self.assertIn("GitHub token", result.stdout)


if __name__ == "__main__":
    unittest.main()
