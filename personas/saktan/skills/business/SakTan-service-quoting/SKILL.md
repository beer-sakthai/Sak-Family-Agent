---
name: SakTan-service-quoting
description: "Use when constructing a customer quote from stored pricing facts and when deciding whether to capture a lead instead of answering from memory."
version: 1.0.0
author: Beer + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [business, quoting, leads, sales, service-bot]
    related_skills: [SakTan-ocr-and-documents, SakTan-sakthai]
---

# Service Quoting

## Overview

Use this skill when a customer asks for a price, a package comparison, or a
custom quote. The goal is to answer from facts that already exist in memory,
then capture a lead if the request needs follow-up or a human quote review.

## When to Use

- A customer asks "how much does this cost?"
- A price book or FAQ has already been ingested
- The agent needs to build a quote from stored pricing facts
- A request is too custom to answer safely without follow-up

## Workflow

1. Recall relevant pricing facts before answering.
2. Summarize the known package, rate, or service boundary.
3. If details are missing, ask one focused clarification question.
4. If the customer wants follow-up, capture the lead with name, phone/email,
   and the request summary.
5. Keep the response short, direct, and grounded in the stored facts.

## Common Pitfalls

1. Quoting from memory when a price book exists.
2. Inventing discounts, scope, or turnaround times.
3. Asking multiple clarifying questions when one is enough.
4. Dropping the lead details instead of storing them for follow-up.

## Verification Checklist

- [ ] Relevant facts were recalled first.
- [ ] The quote only uses known pricing facts.
- [ ] Ambiguity is either clarified or escalated.
- [ ] Lead details are captured when follow-up is needed.
