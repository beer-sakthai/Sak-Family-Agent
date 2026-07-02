---
name: mo-cli
description: "A hypothetical CLI tool for demonstration."
version: 1.0.0
author: Your Name
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [mo]
metadata:
  hermes:
    tags: [example, cli, tool]
    homepage: https://example.com
---

# mo-cli

This is a sample skill for a command-line tool named `mo`.

## Installation

Since this is a hypothetical tool, you would include installation instructions here.

```bash
# Example installation
go install example.com/mo/cmd/mo@latest
```

## Common Commands

### Basic Operations

- Show status: `mo status`
- List items: `mo list`
- Get item details: `mo get <item-id>`

### Advanced Operations

- Create a new item: `mo create --name "My New Item"`
- Delete an item: `mo delete <item-id> --force`

## Example Output

```
$ mo status
System OK
Version: 1.0.0
```
