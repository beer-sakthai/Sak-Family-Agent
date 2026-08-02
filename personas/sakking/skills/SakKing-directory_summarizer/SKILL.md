---
name: SakKing-directory_summarizer
version: 1.0.0
description: Reads files from a specified directory (e.g., root/ or out/data/), summarizes all details, and generates a comprehensive report.

---
# Directory Summarizer

When instructed to read files from a directory (such as root/ or out/data/) and summarize the details, follow these steps:

1. **Identify the Target Directory**: Confirm the path to the directory (e.g., `/opt/data`, `root/`, `out/data/`).
2. **List Files**: Use the `list_dir` tool to recursively or iteratively find all files in the target directory. Limit the scope if the directory is too large.
3. **Read Files**: Use the `view_file` tool to read the contents of the files. For large files, extract key sections or use `grep_search` to find relevant information.
4. **Summarize**: Create a comprehensive summary of the details found in the files.
5. **Generate Report**: Write the summary to an artifact (e.g., `directory_summary_report.md`) outlining the files processed, key findings, and overall details.
