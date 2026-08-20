import os
from unittest.mock import patch

import pytest
from generate_report import build_report
from reportlab.platypus import Paragraph, Table


def test_build_report_creates_file_on_disk(tmp_path):
    """Verify that build_report actually creates a PDF file."""
    report_path = tmp_path / "subdir" / "test_report.pdf"

    # Run the actual function
    result = build_report(str(report_path))

    assert result == str(report_path)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 0


def test_build_report_mocked(tmp_path):
    """Verify the internal calls of build_report using mocks."""
    report_path = tmp_path / "mocked_report.pdf"

    with patch("generate_report.SimpleDocTemplate") as MockDoc:
        mock_instance = MockDoc.return_value

        build_report(str(report_path))

        # Verify SimpleDocTemplate was initialized with correct path
        MockDoc.assert_called_once()
        args, kwargs = MockDoc.call_args
        assert args[0] == str(report_path)

        # Verify build was called
        mock_instance.build.assert_called_once()

        # Verify story is not empty
        story = mock_instance.build.call_args[0][0]
        assert len(story) > 0


def test_build_report_directory_creation(tmp_path):
    """Verify that the parent directory is created if it doesn't exist."""
    nested_path = tmp_path / "a" / "b" / "c" / "report.pdf"
    assert not os.path.exists(os.path.dirname(nested_path))

    # We can mock SimpleDocTemplate to avoid actual PDF generation for this test
    with patch("generate_report.SimpleDocTemplate"):
        build_report(str(nested_path))

    assert os.path.exists(os.path.dirname(nested_path))


def test_build_report_default_path():
    """Verify that build_report uses the default path when none is provided."""
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("generate_report.SimpleDocTemplate") as MockDoc,
    ):
        mock_instance = MockDoc.return_value

        result = build_report()

        assert result == "reports/phase1_validation_report.pdf"
        mock_makedirs.assert_called_once_with("reports", exist_ok=True)
        MockDoc.assert_called_once()
        assert MockDoc.call_args[0][0] == "reports/phase1_validation_report.pdf"
        mock_instance.build.assert_called_once()


def test_build_report_story_elements(tmp_path):
    """Verify that the story contains all the required document sections, text, and tables."""
    report_path = tmp_path / "test_sections_report.pdf"

    with patch("generate_report.SimpleDocTemplate") as MockDoc:
        mock_instance = MockDoc.return_value

        build_report(str(report_path))

        mock_instance.build.assert_called_once()
        story = mock_instance.build.call_args[0][0]

        # Extract text from paragraphs and sizes of tables in the story
        paragraph_texts = []
        tables_info = []

        for element in story:
            if isinstance(element, Paragraph):
                paragraph_texts.append(element.text)
            elif isinstance(element, Table):
                # Table data is stored in element._cellvalues
                tables_info.append(element._cellvalues)

        # Verify key sections exist in the story
        assert any("Hermes Agent Self-Evolution" in text for text in paragraph_texts)
        assert any("Phase 1 Validation Report" in text for text in paragraph_texts)
        assert any("Results" in text for text in paragraph_texts)
        assert any("Safety and Guardrails" in text for text in paragraph_texts)
        assert any("Roadmap" in text for text in paragraph_texts)
        assert any("Immediate Next Steps" in text for text in paragraph_texts)

        # Verify that we have at least the expected number of tables
        assert len(tables_info) >= 3

        # Match tables by their headers to verify contents
        results_table = None
        safety_table = None
        roadmap_table = None

        for tbl in tables_info:
            if len(tbl) > 0:
                if tbl[0] == ["Metric", "Baseline", "Optimized", "Change"]:
                    results_table = tbl
                elif tbl[0] == ["Constraint", "Enforcement", "Status"]:
                    safety_table = tbl
                elif tbl[0] == ["Phase", "Target", "Engine", "Timeline", "Status"]:
                    roadmap_table = tbl

        assert results_table is not None, "Results table not found in report story"
        assert safety_table is not None, "Safety table not found in report story"
        assert roadmap_table is not None, "Roadmap table not found in report story"

        # Results table verification
        assert results_table[1] == ["Validation Example 1", "0.408", "0.569", "+39.5%"]
        assert results_table[2] == ["Validation Example 2", "0.374", "0.374", "0.0%"]
        assert results_table[3] == ["Average", "0.391", "0.472", "+20.7%"]

        # Safety table verification
        assert any("Full test suite" in row[0] for row in safety_table[1:])

        # Roadmap table verification
        assert any("Phase 1" in row[0] for row in roadmap_table[1:])


def test_build_report_os_error(tmp_path):
    """Verify that build_report propagates OS/Permission errors from directory creation."""
    report_path = tmp_path / "denied_dir" / "report.pdf"

    with (
        patch("os.makedirs", side_effect=OSError("Permission denied")),
        pytest.raises(OSError, match="Permission denied"),
    ):
        build_report(str(report_path))
