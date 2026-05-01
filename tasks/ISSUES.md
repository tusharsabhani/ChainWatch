# ISSUES

This file tracks bugs, blockers, and follow-ups discovered during implementation.

## Issue Template

| ID | Type | Severity | Status | Owner | Summary | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| ISS-00 | bug, blocker, follow-up, question | low, medium, high | open, investigating, blocked, resolved | name or `unassigned` | Short description | Concrete next step |

## Current Items

| ID | Type | Severity | Status | Owner | Summary | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| ISS-01 | follow-up | medium | open | unassigned | Final LLM provider has not been selected yet | Choose the provider and implement the `LLMAdapter` |
| ISS-02 | follow-up | medium | open | unassigned | Final web-search provider has not been selected yet | Choose the provider and implement the `SearchAdapter` |
| ISS-03 | follow-up | medium | resolved | unassigned | A representative retail sample dataset still needs to be chosen or generated | Resolved in `BE-04` with the local demo seed workflow |

## Notes

- Use this file for active implementation issues, not long-term architecture decisions.
- Move durable reasoning and tradeoff history into `tasks/DECISIONS.md`.
