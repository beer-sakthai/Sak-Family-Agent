# tests/test_governance_doctor.py
from sakthai.governance.doctor import RepoDoctor
from sakthai.governance.models import IssueSeverity


def test_repo_doctor_diagnose_clean():
    doctor = RepoDoctor()
    report = doctor.run_diagnostics()

    assert report.health_score >= 80
    assert report.total_checks > 0
    assert isinstance(report.issues, list)


def test_repo_doctor_add_custom_check():
    doctor = RepoDoctor()

    def dummy_check():
        return [("SECURITY_WARNING", "Test security advisory", IssueSeverity.LOW)]

    doctor.register_check("custom_security", dummy_check)
    report = doctor.run_diagnostics()

    assert any(i.code == "SECURITY_WARNING" for i in report.issues)


def test_repo_doctor_auto_heal():
    doctor = RepoDoctor()
    # Test auto heal execution
    res = doctor.auto_heal()
    assert res.success is True
    assert "actions_taken" in res.to_dict()
