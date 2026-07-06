---
name: sakthai-excalidraw
description: "Hand-drawn Excalidraw JSON diagrams (arch, flow, seq)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [excalidraw, diagram, architecture, flow, sequence, design]
---

# Excalidraw

## Description

Creates Excalidraw diagrams for architecture, sequence, and flow diagrams. This skill contains scripts that generate Excalidraw-format JSON and upload it to S3 for sharing.

## Workflow

1. Understand user request (architecture, sequence, flow)
2. Decide elements and connections for the diagram
3. Generate Excalidraw JSON
4. Upload to S3 for sharing (optional)
