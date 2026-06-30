import os
from unittest.mock import patch
import pytest
from generate_report import build_report

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
