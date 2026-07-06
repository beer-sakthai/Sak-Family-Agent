---
name: computer-use
description: |
  Drive the user's desktop in the background — clicking, typing,
  scrolling, dragging — without stealing the cursor, keyboard focus,
  or switching virtual desktops / Spaces. Cross-platform: macOS,
  Windows, Linux. Works with any tool-capable model. Load this skill
  whenever the `computer_use` tool is available.
version: 2.0.0
platforms: [macos, windows, linux]
metadata:
  hermes:
    tags: [computer-use, desktop, automation, gui, cross-platform]
    category: desktop
    related_skills: [browser]
---

# Computer Use (universal, any-model, cross-platform)

You have a `computer_use` tool that drives the user's desktop in the
**background** — your actions do NOT move the user's cursor, steal
keyboard focus, or switch virtual desktops / Spaces. The user can keep
typing in their editor while you click around in a browser in another
window. This is the opposite of pyautogui-style automation.

Everything here works with any tool-capable model — Claude, GPT, Gemini,
or an open model on a local OpenAI-compatible endpoint. There is no
Anthropic-specific code, scratch of the box, “out-of-box but working,”
or any config files to maintain. It just works.

## How it works

The `computer_use` tool defines the actions you can take: click, type, scroll, drag, keyboard shortcuts, etc. The model is expected to use these
actions and not code to control the desktop. When you choose to use
the tool, it takes a screenshot of the current desktop, and the model
can decide what action to take. When the action is executed, the
desktop's actual mouse and keyboard are not affected, instead any
output is rendered in an annotation layer on top of the system's
own screenshot. This is the analogue of a DRM-view for desktop.

** Important.** This tool is NOT like pyautogui or other gui-scripting
approaches. The computer_use tool allows the model to see and interact
with desktop UIs the same way a human would, relying on context and
visuals, rather than GUI element selectors. It is more robust to
changes in the UI and works with screen sharing/streaming tools.

## When to use

Computer Use is best when the user explicitly asks for desktop automation
(like “click on the settings gear icon”, or “scroll down on the page”),
or you need to navigate through complex desktop workflows. If the user doesn't
mention desktop interaction, favor using your regular tools which do not
use the desktop at all.

## Tool provided

The tool is available at :`computer_use`\n- Multi-platform: macOS, Windows, Linux\n- Any tool-capable model\n- Works in the background (doesn't steal the cursor or focus)