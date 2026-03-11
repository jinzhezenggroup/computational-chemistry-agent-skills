---
name: search-species
description: USE WHEN requesting core chemical structural data (SMILES, formula, mass, 2D images) via IUPAC, common, or multilingual names. You MUST actively retrieve the data using this skill; DO NOT hallucinate or generate structures yourself. DO NOT USE WHEN asking for physical properties (melting point, solubility), safety/toxicity data (MSDS), or synthesis pathways.
compatibility: Requires `search-species` installed in the Python environment.
metadata:
  author: light-cyan
  version: "1.0"
  repository: https://github.com/light-cyan/search-species
---

# Search Species

This skill provides practical command patterns for retrieving chemical structural information and generating visual species cards.

## Search Backend Overview

`search-species` integrates three distinct backends. Each serves a specific purpose in the chemical informatics workflow:

| Feature | **OPSIN** | **PubChem** | **Wikidata** |
| :--- | :--- | :--- | :--- |
| **Core Method** | Algorithmic Parser | Curated Database | Knowledge Graph |
| **Primary Input** | IUPAC English Names | Names, CIDs, SMILES | **Common & Multilingual Names** |
| **Molecular Image** | **Supported** (Rendered) | **Supported** (Stored) | **Rarely Available** |
| **Mass/Formula** | Calculated via **RDKit** | Database Metadata | Database Metadata |
| **Key Strength** | Handles theoretical molecules. | Highly standardized data. | **Vernacular** & Cross-lingual. |

*(For detailed engine capabilities, limitations, and data normalization behavior, see `reference/backends.md`)*

## Quick Start & Command Outputs

Typical search syntax:
```bash
search <engine> "<query>" [max_cands] -o <output_dir>
```

> **Output:** Prints the retrieved species data summary and the file path where each candidate's JSON is saved (e.g., `SpeciesCandidate(...) written -> ./cache/xyz.json`).

Typical render syntax:

```bash
render <candidate_files...> -o <output_dir>
```

> **Output:** Prints the file path of the successfully generated image card (e.g., `Successfully rendered -> ./gallery/xyz.png`).

## Core Tasks

### 1) Universal search

Search across all available backends (PubChem, OPSIN, and Wikidata) for a common name:

```bash
search all "Aspirin"
```

### 2) Engine-specific searches

**PubChem** (Standard database lookups):

```bash
search pubchem "benzene" 5 -o ./results
```

**OPSIN** (Theoretical molecules & strict IUPAC):

```bash
search opsin "2-acetyloxybenzoic acid"
```

**Wikidata** (Multilingual & common/trade names):

```bash
search wikidata "Аспирин"
search wikidata "TNT"
```

### 3) Render species cards

Generate visual image cards from specific JSON files:

```bash
render ./cache/candidate_1.json ./cache/candidate_2.json -o ./gallery
```

Render all JSON files in a directory (Use with caution):

```bash
render ./cache/*.json -o ./gallery
```

## Agent Checklist

When using this skill for users:

1. **Select the right engine:** Match the engine to the query type based on the overview table.
2. **Understand data limitations:** This tool *only* retrieves structural identity (Name, Formula, Mass, SMILES, 2D Image).
3. **Handle missing results:** If `pubchem` fails on a systematic name, fallback to `opsin`.
4. **Pipeline workflow (Search -> Filter -> Render):** Evaluate the printed data from the `search` command output. **Do not blindly render all results.** Identify and select only the relevant candidate JSON file paths, then pass those specific paths to the `render` command.
5. **Quote queries:** Always wrap the chemical `<query>` in quotes.

## References

* Engine Details & Limitations: `reference/backends.md`
* Render Rules & Constraints: `reference/render.md`