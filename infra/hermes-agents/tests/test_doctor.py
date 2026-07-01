import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def load_doctor_module():
    doctor_path = Path(__file__).resolve().parents[1] / "doctor.py"
    spec = importlib.util.spec_from_file_location("hermes_agents_doctor", doctor_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_github_config(repo_root: Path, enabled: bool = True) -> None:
    config_dir = repo_root / "default"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.joinpath("config.yaml").write_text(
        "\n".join(
            [
                "mcp_servers:",
                "  github:",
                "    url: https://api.githubcopilot.com/mcp/",
                "    headers:",
                "      Authorization: Bearer ${GITHUB_TOKEN}",
                f"    enabled: {'true' if enabled else 'false'}",
                "    timeout: 120",
                "    connect_timeout: 30",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_env_file(repo_root: Path, token: str) -> None:
    repo_root.joinpath(".env").write_text(f"GITHUB_TOKEN={token}\n", encoding="utf-8")


def test_check_github_mcp_passes_with_token_and_live_probe(tmp_path, monkeypatch):
    doctor = load_doctor_module()
    repo_root = tmp_path / "repo"
    write_github_config(repo_root)
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_test_token")
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: "/usr/bin/hermes")

    calls = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="probe ok\n", stderr="")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    result = doctor.check_github_mcp(str(repo_root))

    assert result["status"] == "PASS"
    assert "live probe passed" in result["details"]
    assert calls == [["hermes", "mcp", "test", "github"]]


def test_check_github_mcp_warns_when_token_missing(tmp_path, monkeypatch):
    doctor = load_doctor_module()
    repo_root = tmp_path / "repo"
    write_github_config(repo_root)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def unexpected_run(*_args, **_kwargs):
        raise AssertionError("probe should not run without GITHUB_TOKEN")

    monkeypatch.setattr(doctor.subprocess, "run", unexpected_run)

    result = doctor.check_github_mcp(str(repo_root))

    assert result["status"] == "WARN"
    assert "GITHUB_TOKEN" in result["details"]
    assert "GITHUB_TOKEN" in result["remediation"]


def test_check_github_mcp_loads_token_from_local_env_file(tmp_path, monkeypatch):
    doctor = load_doctor_module()
    repo_root = tmp_path / "repo"
    write_github_config(repo_root)
    write_env_file(repo_root, "ghs_local_token")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: "/usr/bin/hermes")

    calls = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(doctor.subprocess, "run", fake_run)

    result = doctor.check_github_mcp(str(repo_root))

    assert result["status"] == "PASS"
    assert calls == [["hermes", "mcp", "test", "github"]]


def test_check_github_mcp_fails_on_probe_error(tmp_path, monkeypatch):
    doctor = load_doctor_module()
    repo_root = tmp_path / "repo"
    write_github_config(repo_root)
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_test_token")
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: "/usr/bin/hermes")
    monkeypatch.setattr(
        doctor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="stdout line\n", stderr="stderr line\n"),
    )

    result = doctor.check_github_mcp(str(repo_root))

    assert result["status"] == "FAIL"
    assert "exit code 1" in result["details"]
    assert "stdout line" in result["details"]
    assert "stderr line" in result["details"]
    assert "Refresh the GitHub MCP token" in result["remediation"]


def test_main_reports_warn_when_github_mcp_is_degraded(tmp_path, monkeypatch, capsys):
    doctor = load_doctor_module()

    monkeypatch.setattr(doctor, "check_git_status", lambda _repo_path: {"status": "PASS", "details": "ok"})
    monkeypatch.setattr(doctor, "check_omp_files", lambda _repo_path: {"status": "PASS", "details": "ok"})
    monkeypatch.setattr(doctor, "check_yaml_integrity", lambda _repo_path: {"status": "PASS", "details": "ok"})
    monkeypatch.setattr(doctor, "check_github_mcp", lambda _repo_path: {"status": "WARN", "details": "warn"})
    monkeypatch.setattr(doctor, "check_deployment_script", lambda _repo_path: {"status": "PASS", "details": "ok"})
    monkeypatch.setattr(doctor, "check_systemd_files", lambda _repo_path: {"status": "PASS", "details": "ok"})
    monkeypatch.setattr(doctor.os.path, "dirname", lambda _path: str(tmp_path))
    monkeypatch.setattr(doctor.os.path, "abspath", lambda _path: "doctor.py")

    doctor.main()

    captured = json.loads(capsys.readouterr().out)
    assert captured["overall_health"] == "WARN"
    assert captured["diagnostics"]["github_mcp"]["status"] == "WARN"
