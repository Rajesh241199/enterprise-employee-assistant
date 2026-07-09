import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
REPORT_DIR = BACKEND_ROOT / "evals" / "reports"


@dataclass
class QualityGateResult:
    name: str
    passed: bool
    details: str
    command: str | None = None
    output_preview: str | None = None


class BackendQualityGate:
    def __init__(self):
        self.results: list[QualityGateResult] = []

    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def preview(self, text: str, max_chars: int = 2000) -> str:
        if len(text) <= max_chars:
            return text

        return text[-max_chars:]

    def record(
        self,
        name: str,
        passed: bool,
        details: str,
        command: str | None = None,
        output_preview: str | None = None,
    ) -> None:
        self.results.append(
            QualityGateResult(
                name=name,
                passed=passed,
                details=details,
                command=command,
                output_preview=output_preview,
            )
        )

        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
        print(f"  Details: {details}")

    def run_command(
        self,
        name: str,
        command: list[str],
        cwd: Path,
        expected_substrings: list[str] | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        command_text = " ".join(command)

        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )

            output = f"{completed.stdout}\n{completed.stderr}".strip()

            passed = completed.returncode == 0

            if expected_substrings:
                passed = passed and all(
                    expected_text in output
                    for expected_text in expected_substrings
                )

            self.record(
                name=name,
                passed=passed,
                details=(
                    "Command completed successfully."
                    if passed
                    else f"Command failed with exit code {completed.returncode}."
                ),
                command=command_text,
                output_preview=self.preview(output),
            )

        except Exception as exc:
            self.record(
                name=name,
                passed=False,
                details=str(exc),
                command=command_text,
            )

    def check_required_files(self) -> None:
        required_files = [
            BACKEND_ROOT / "app" / "main.py",
            BACKEND_ROOT / "app" / "api" / "chat.py",
            BACKEND_ROOT / "app" / "api" / "documents.py",
            BACKEND_ROOT / "app" / "core" / "logging_config.py",
            BACKEND_ROOT / "app" / "services" / "audit_logger.py",
            BACKEND_ROOT / "app" / "security" / "llm_guardrails.py",
            BACKEND_ROOT / "app" / "security" / "document_domain_validator.py",
            BACKEND_ROOT / "evals" / "run_security_eval.py",
            BACKEND_ROOT / "evals" / "run_backend_smoke_tests.py",
            PROJECT_ROOT / ".github" / "workflows" / "backend-ci.yml",
        ]

        missing_files = [
            str(path.relative_to(PROJECT_ROOT))
            for path in required_files
            if not path.exists()
        ]

        self.record(
            name="QUALITY_REQUIRED_FILES_001",
            passed=not missing_files,
            details=(
                "All required backend quality-gate files exist."
                if not missing_files
                else f"Missing files: {missing_files}"
            ),
        )

    def check_requirements(self) -> None:
        requirements_path = BACKEND_ROOT / "requirements.txt"

        if not requirements_path.exists():
            self.record(
                name="QUALITY_REQUIREMENTS_001",
                passed=False,
                details="backend/requirements.txt is missing.",
            )
            return

        requirements_text = requirements_path.read_text(encoding="utf-8")

        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "pydantic",
            "pydantic-settings",
            "python-jose",
            "passlib",
            "requests",
            "qdrant-client",
            "sentence-transformers",
            "pandas",
            "openpyxl",
            "PyMuPDF",
            "pdfplumber",
            "pypdf",
            "email-validator",
            "pytesseract",
        ]

        missing_packages = [
            package
            for package in required_packages
            if package.lower() not in requirements_text.lower()
        ]

        self.record(
            name="QUALITY_REQUIREMENTS_001",
            passed=not missing_packages,
            details=(
                "All critical backend dependencies are present."
                if not missing_packages
                else f"Missing packages: {missing_packages}"
            ),
        )

    def check_gitignore_rules(self) -> None:
        gitignore_path = PROJECT_ROOT / ".gitignore"

        if not gitignore_path.exists():
            self.record(
                name="QUALITY_GITIGNORE_001",
                passed=False,
                details=".gitignore is missing.",
            )
            return

        gitignore_text = gitignore_path.read_text(encoding="utf-8")

        required_rules = [
            "logs/",
            "storage/",
            "evals/reports/*.json",
            "evals/reports/*.csv",
            "evals/test_uploads/",
            ".vscode/",
        ]

        missing_rules = [
            rule
            for rule in required_rules
            if rule not in gitignore_text
        ]

        self.record(
            name="QUALITY_GITIGNORE_001",
            passed=not missing_rules,
            details=(
                "Runtime/generated files are ignored."
                if not missing_rules
                else f"Missing .gitignore rules: {missing_rules}"
            ),
        )

    def check_runtime_files_not_tracked(self) -> None:
        command = [
            "git",
            "ls-files",
        ]

        try:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            tracked_files = completed.stdout.splitlines()

            forbidden_prefixes = [
                "backend/logs/",
                "backend/storage/",
                "backend/evals/test_uploads/",
                ".vscode/",
            ]

            forbidden_suffixes = [
                ".json",
                ".csv",
            ]

            bad_files = []

            for tracked_file in tracked_files:
                normalized_file = tracked_file.replace("\\", "/")

                if any(
                    normalized_file.startswith(prefix)
                    for prefix in forbidden_prefixes
                ):
                    bad_files.append(normalized_file)

                if normalized_file.startswith("backend/evals/reports/"):
                    if any(normalized_file.endswith(suffix) for suffix in forbidden_suffixes):
                        bad_files.append(normalized_file)

            self.record(
                name="QUALITY_RUNTIME_FILES_NOT_TRACKED_001",
                passed=not bad_files,
                details=(
                    "No runtime/generated files are tracked."
                    if not bad_files
                    else f"Tracked runtime files found: {bad_files}"
                ),
            )

        except Exception as exc:
            self.record(
                name="QUALITY_RUNTIME_FILES_NOT_TRACKED_001",
                passed=False,
                details=str(exc),
            )

    def check_backend_ci_workflow(self) -> None:
        workflow_path = PROJECT_ROOT / ".github" / "workflows" / "backend-ci.yml"

        if not workflow_path.exists():
            self.record(
                name="QUALITY_BACKEND_CI_WORKFLOW_001",
                passed=False,
                details="Backend CI workflow file is missing.",
            )
            return

        workflow_text = workflow_path.read_text(encoding="utf-8")

        expected_keywords = [
            "Backend CI",
            "compileall app",
            "Validate FastAPI app import",
            "Block runtime files from being tracked",
            "backend/requirements.txt",
        ]

        missing_keywords = [
            keyword
            for keyword in expected_keywords
            if keyword not in workflow_text
        ]

        self.record(
            name="QUALITY_BACKEND_CI_WORKFLOW_001",
            passed=not missing_keywords,
            details=(
                "Backend CI workflow contains required validation gates."
                if not missing_keywords
                else f"Missing workflow keywords: {missing_keywords}"
            ),
        )

    def check_git_status_warning(self) -> None:
        """
        This is a warning-style check.

        It does not fail the quality gate because during development this script
        itself may be uncommitted. Use final `git status` manually before pushing.
        """
        try:
            completed = subprocess.run(
                ["git", "status", "--short"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            status_output = completed.stdout.strip()

            self.record(
                name="QUALITY_GIT_STATUS_INFO_001",
                passed=True,
                details=(
                    "Git working tree is clean."
                    if not status_output
                    else "Git has local changes. Review before final commit."
                ),
                command="git status --short",
                output_preview=status_output or "clean",
            )

        except Exception as exc:
            self.record(
                name="QUALITY_GIT_STATUS_INFO_001",
                passed=True,
                details=f"Could not read git status: {exc}",
            )

    def write_report(self) -> Path:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORT_DIR / f"backend_quality_gate_report_{timestamp}.json"

        payload: dict[str, Any] = {
            "created_at": self.now_iso(),
            "project_root": str(PROJECT_ROOT),
            "backend_root": str(BACKEND_ROOT),
            "total": len(self.results),
            "passed": sum(1 for result in self.results if result.passed),
            "failed": sum(1 for result in self.results if not result.passed),
            "pass_rate": self.pass_rate(),
            "results": [asdict(result) for result in self.results],
        }

        report_path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        return report_path

    def pass_rate(self) -> float:
        if not self.results:
            return 0.0

        passed_count = sum(1 for result in self.results if result.passed)

        return round((passed_count / len(self.results)) * 100, 2)

    def run(self) -> int:
        print("Running final backend quality gate")
        print("=" * 55)

        self.check_required_files()
        self.check_requirements()
        self.check_gitignore_rules()
        self.check_runtime_files_not_tracked()
        self.check_backend_ci_workflow()

        self.run_command(
            name="QUALITY_COMPILE_APP_001",
            command=[sys.executable, "-m", "compileall", "app"],
            cwd=BACKEND_ROOT,
            timeout_seconds=300,
        )

        self.run_command(
            name="QUALITY_COMPILE_EVALS_001",
            command=[sys.executable, "-m", "py_compile", "evals/run_security_eval.py"],
            cwd=BACKEND_ROOT,
            timeout_seconds=120,
        )

        self.run_command(
            name="QUALITY_COMPILE_SMOKE_001",
            command=[sys.executable, "-m", "py_compile", "evals/run_backend_smoke_tests.py"],
            cwd=BACKEND_ROOT,
            timeout_seconds=120,
        )

        self.run_command(
            name="QUALITY_IMPORT_APP_001",
            command=[
                sys.executable,
                "-c",
                "from app.main import app; print(app.title)",
            ],
            cwd=BACKEND_ROOT,
            expected_substrings=["Enterprise Employee Knowledge Assistant"],
            timeout_seconds=120,
        )

        self.run_command(
            name="QUALITY_SECURITY_REGRESSION_001",
            command=[sys.executable, "evals/run_security_eval.py"],
            cwd=BACKEND_ROOT,
            expected_substrings=[
                "Total: 20",
                "Passed: 20",
                "Failed: 0",
                "Pass Rate: 100.0%",
            ],
            timeout_seconds=600,
        )

        self.run_command(
            name="QUALITY_BACKEND_SMOKE_TESTS_001",
            command=[sys.executable, "evals/run_backend_smoke_tests.py"],
            cwd=BACKEND_ROOT,
            expected_substrings=[
                "Total: 11",
                "Passed: 11",
                "Failed: 0",
                "Pass Rate: 100.0%",
            ],
            timeout_seconds=900,
        )

        self.check_git_status_warning()

        total = len(self.results)
        passed = sum(1 for result in self.results if result.passed)
        failed = total - passed
        pass_rate = self.pass_rate()
        report_path = self.write_report()

        print("")
        print("Final Backend Quality Gate Summary")
        print("=" * 55)
        print(f"Total: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {pass_rate}%")
        print(f"Report: {report_path}")

        if failed:
            print("")
            print("Failed Cases")
            print("=" * 55)

            for result in self.results:
                if not result.passed:
                    print(f"{result.name}: {result.details}")

            return 1

        return 0


def main() -> None:
    gate = BackendQualityGate()
    exit_code = gate.run()

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()