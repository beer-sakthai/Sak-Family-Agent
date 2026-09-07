#!/usr/bin/env python3
"""
Systematic Environment Analysis Script

This script performs deep analysis of environment files and directories,
generating structured reports of findings.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def analyze_directory_structure(path: str) -> dict[str, Any]:
    """Analyze the directory structure and return structured information."""
    result = {"path": path, "directories": [], "files": [], "total_size": 0, "file_types": {}}

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return {"error": f"Path {path} does not exist"}

        # Get directory contents
        for item in path_obj.iterdir():
            if item.is_dir():
                result["directories"].append(
                    {"name": item.name, "path": str(item.relative_to(path_obj))}
                )
            elif item.is_file():
                result["files"].append(
                    {
                        "name": item.name,
                        "path": str(item.relative_to(path_obj)),
                        "size": item.stat().st_size,
                    }
                )
                result["total_size"] += item.stat().st_size

                # Track file types
                suffix = item.suffix.lower() if item.suffix else "no_extension"
                result["file_types"][suffix] = result["file_types"].get(suffix, 0) + 1

    except Exception as e:
        return {"error": str(e)}

    return result


def find_files_by_pattern(root_path: str, pattern: str) -> list[str]:
    """Find files matching a pattern recursively."""
    matches = []
    try:
        for path in Path(root_path).rglob(pattern):
            if path.is_file():
                matches.append(str(path))
    except Exception as e:
        print(f"Error searching for pattern {pattern}: {e}", file=sys.stderr)
    return matches


def analyze_file_content(file_path: str, sample_lines: int = 10) -> dict[str, Any]:
    """Analyze the content of a file."""
    result = {"path": file_path, "size": 0, "lines": 0, "sample_content": []}

    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return {"error": f"File {file_path} does not exist"}

        result["size"] = path_obj.stat().st_size

        # Read sample content
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i < sample_lines:
                    result["sample_content"].append(line.rstrip())
                result["lines"] = i + 1

    except Exception as e:
        return {"error": str(e)}

    return result


def generate_analysis_report(analysis_data: dict[str, Any]) -> str:
    """Generate a markdown report from analysis data."""
    report = []
    report.append("# Environment Analysis Report")
    report.append(f"**Generated**: {analysis_data.get('timestamp', 'N/A')}")
    report.append("")

    # Directory structure
    if "directory_structure" in analysis_data:
        dir_struct = analysis_data["directory_structure"]
        report.append("## Directory Structure")
        report.append(f"- Path: {dir_struct.get('path', 'N/A')}")
        report.append(f"- Total directories: {len(dir_struct.get('directories', []))}")
        report.append(f"- Total files: {len(dir_struct.get('files', []))}")
        report.append(f"- Total size: {dir_struct.get('total_size', 0)} bytes")
        report.append("")

        # File types summary
        if dir_struct.get("file_types"):
            report.append("### File Types")
            for ext, count in dir_struct.get("file_types", {}).items():
                report.append(f"- {ext}: {count}")
            report.append("")

    # File pattern matches
    if "pattern_matches" in analysis_data:
        report.append("## Pattern Matches")
        for pattern, matches in analysis_data["pattern_matches"].items():
            report.append(f"### Files matching '{pattern}'")
            for match in matches[:10]:  # Limit to first 10 matches
                report.append(f"- {match}")
            if len(matches) > 10:
                report.append(f"- ... and {len(matches) - 10} more")
        report.append("")

    # File content analysis
    if "file_analysis" in analysis_data:
        report.append("## File Content Analysis")
        for file_info in analysis_data["file_analysis"][:5]:  # Limit to first 5 files
            report.append(f"### {file_info.get('path', 'Unknown')}")
            report.append(f"- Size: {file_info.get('size', 0)} bytes")
            report.append(f"- Lines: {file_info.get('lines', 0)}")
            report.append("- Sample content:")
            for line in file_info.get("sample_content", [])[:5]:
                report.append(f"  ```{line}```")
            report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Perform deep environment analysis")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--pattern", help="Pattern to search for in files")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")

    args = parser.parse_args()

    # Collect analysis data
    analysis_data = {
        "timestamp": "2026-07-07",  # In a real script this would be dynamic
        "target_path": args.path,
    }

    # Analyze directory structure
    analysis_data["directory_structure"] = analyze_directory_structure(args.path)

    # Find files by pattern
    if args.pattern:
        analysis_data["pattern_matches"] = {
            args.pattern: find_files_by_pattern(args.path, args.pattern)
        }

    # Analyze some key files
    key_files = find_files_by_pattern(args.path, "*.md")[:3]  # Analyze first 3 markdown files
    file_analysis = []
    for file_path in key_files:
        file_analysis.append(analyze_file_content(file_path))
    analysis_data["file_analysis"] = file_analysis

    # Generate output
    if args.json:
        output = json.dumps(analysis_data, indent=2)
    else:
        output = generate_analysis_report(analysis_data)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
