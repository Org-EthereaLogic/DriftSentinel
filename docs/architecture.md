# DriftSentinel Architecture

For the canonical architecture specification, see
`specs/DS-SDD-001_Architecture_Blueprint.md`.

This document provides supplementary explanatory context for operators and
contributors who want a narrative overview before diving into the canonical
spec suite.

## Overview

DriftSentinel consolidates three Enterprise Data Trust control patterns into a
single Databricks application: intake certification (Chapter 1), drift gating
(Chapter 2), and control benchmarking (Chapter 3).

The repository is organized into an agentic layer (specs, commands, agents,
hooks, evidence) and an application layer (product code, notebooks, bundle
resources, templates).

## Module Map

- **intake** — validates, quarantines, and certifies incoming data
- **drift** — measures distribution stability against a baseline and emits gate verdicts
- **benchmark** — runs controls against known failures and produces scored evidence
- **evidence** — writes append-only artifacts for auditability
- **orchestration** — sequences the control workflow end-to-end
- **config** — loads dataset contracts, drift policies, and benchmark policies
