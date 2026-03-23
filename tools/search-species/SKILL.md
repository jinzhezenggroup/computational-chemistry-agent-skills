---
name: search-species
description: >
  USE WHEN requesting core chemical structural data (SMILES, formula, mass, 2D images) via IUPAC, common, or multilingual names. You MUST actively retrieve the data using this skill; DO NOT hallucinate or generate structures yourself.
  DO NOT USE WHEN asking for physical properties (melting point, solubility), safety/toxicity data (MSDS), or synthesis pathways.
compatibility: Requires `uv` installed.
license: LGPL-3.0-or-later
metadata:
  author: light-cyan
  version: 0.1.0
  repository: https://github.com/light-cyan/search-species
---

# Search Species

## 🔄 Core Workflow (CRITICAL)

When assisting users with chemical searches, you **MUST** adhere to the following step-by-step workflow. **Note: Searching can be highly time-consuming; always prioritize efficiency.**

1. **Acquire Target**: Identify the chemical name, identifier, or SMILES the user wants to query.
1. **Select Engine**: Choose the most targeted search backend (`pubchem`, `opsin`, `wikidata`, or `all`) based on the query type. Avoid using `all` unless strictly necessary, to minimize search times.
1. **Execute Search**: Use the `search` command to query the database. You must set an appropriate `max_cands` limit to prevent excessively long processing times and reduce data noise.
1. **Evaluate Results**: Carefully review the returned summary data in the output.
1. **Confirm & Iterate**: Present the retrieved data to the user for confirmation. If the result is ambiguous or incorrect, communicate with the user to adjust the search keywords and restart the process.

______________________________________________________________________

## Search Backend Overview

`search-species` integrates three distinct backends. Each serves a specific purpose in the chemical informatics workflow:

| Feature             | **OPSIN**                      | **PubChem**               | **Wikidata**                    |
| :------------------ | :----------------------------- | :------------------------ | :------------------------------ |
| **Core Method**     | Algorithmic Parser             | Curated Database          | Knowledge Graph                 |
| **Primary Input**   | IUPAC English Names            | Names, CIDs, SMILES       | **Common & Multilingual Names** |
| **Molecular Image** | **Supported** (Rendered)       | **Supported** (Stored)    | **Rarely Available**            |
| **Mass/Formula**    | Calculated via **RDKit**       | Database Metadata         | Database Metadata               |
| **Key Strength**    | Handles theoretical molecules. | Highly standardized data. | **Vernacular** & Cross-lingual. |

*(For more detailed engine capabilities, limitations, and data normalization behavior, see `reference/backends.md`)*

## Quick Start & Command Outputs

Typical search syntax:

```bash
uvx search-species <engine> "<query>" [max_cands] -o <output_dir>

```

> **Output:** Prints the retrieved species data summary and the file path where each candidate's JSON is saved (e.g., `SpeciesCandidate(...) written -> ./cache/xyz.json`).

Typical render syntax:

```bash
uvx --from search-species render-species <candidate_files...> -o <output_dir>

```

> **Output:** Prints the file path of the successfully generated image card (e.g., `Successfully rendered -> ./gallery/xyz.png`).

## Example

**PubChem** (Standard database lookups):

```bash
uvx search-species pubchem "benzene" 5 -o ./results

```

**OPSIN** (Theoretical molecules & strict IUPAC):

```bash
uvx search-species opsin "2-acetyloxybenzoic acid"

```

**Wikidata** (Multilingual & common/trade names):

```bash
uvx search-species wikidata "Аспирин"
uvx search-species wikidata "TNT"

```

## Agent Checklist

When using this toolkit for users, ensure you cross-check these points with the Core Workflow:

- **Engine Match:** Match the engine to the query type based on the overview table.
- **Data Scope:** Remember this tool *only* retrieves structural identity (Name, Formula, Mass, SMILES, 2D Image).
- **Fallback:** If `pubchem` fails on a systematic name, fallback to `opsin`.
- **Quoting:** Always wrap the chemical `<query>` in quotes.

## References

- Engine Details & Limitations: `reference/backends.md`
