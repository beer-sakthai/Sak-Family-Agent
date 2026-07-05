---
name: findmy
description: "Apple Find My network: locate devices and people via CLI."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Find My, Apple, location, macOS]
prerequisites:
  commands: [findmy]
---

# Find My

Locate Apple devices and people via the Find My network from the terminal. Uses the `findmy` CLI.

## Prerequisites

- macOS
- Install: `brew install findmy`
- Must be signed into iCloud on the Mac

## Basic Usage

```bash
# List all devices
findmy list

# Locate a device
findmy locate "MacBook Pro"

# Play a sound on a device
findmy sound "iPhone"

# Get just the location
findmy locate "AirPods" --json
```

## People

```bash
# List people sharing location
findmy people

# Locate a person
findmy locate "Friend Name"
```