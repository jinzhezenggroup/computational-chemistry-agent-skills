# Engine Backends Reference

`search-species` integrates three distinct backends. Each serves a specific purpose in the chemical informatics workflow:

| Feature | **OPSIN** | **PubChem** | **Wikidata** |
| :--- | :--- | :--- | :--- |
| **Core Method** | Algorithmic Parser | Curated Database | Knowledge Graph |
| **Primary Input** | IUPAC English Names | Names, CIDs, SMILES | **Common & Multilingual Names** |
| **Molecular Image** | **Supported** (Rendered) | **Supported** (Stored) | **Rarely Available** |
| **Mass/Formula** | Calculated | Database Metadata | Database Metadata |
| **Key Strength** | Handles theoretical molecules. | Highly standardized data. | **Vernacular** & Cross-lingual. |

## 1. OPSIN 
* **Capabilities**: Interprets strict IUPAC grammar to "build" molecules dynamically. Excellent for theoretical or uncatalogued structures. Automatically renders 2D images.
* **Deficiencies**: **Strict Nomenclature Only**. It will completely fail on common names or trade names (e.g., it understands `2-acetyloxybenzoic acid` but fails on `Aspirin`).

## 2. PubChem
* **Capabilities**: The primary choice for known substances. Excellent matching for industry aliases and trade names. Provides high-quality, standardized 2D structural images.
* **Deficiencies**: **Limited to Knowns**. Cannot interpret or generate data for novel molecules not registered in the database.

## 3. Wikidata
* **Capabilities**: The best engine for **Common Names** and **Non-English/Multilingual** queries (e.g., `阿司匹林`, `Аспирин`).
* **Deficiencies**: **Image Scarcity**. Often lacks structural images. No cross-database indexing (only returns native Wikidata info).
* **Data Processing Note**: Automatically normalizes messy Unicode formulas into standard ASCII (e.g., `CuSO₄·5H₂O` becomes `CuSO4*5H2O`).

---

## Current Scope & Limitations

**⚠️ Strict Boundaries (DO NOT USE FOR):**
* ❌ Physical properties (Melting point, Boiling point, Solubility, etc.)
* ❌ Toxicity, Hazards, or Safety data (MSDS)
* ❌ Literature references and Patent links

**Guaranteed Output Fields**:
1.  **Name**: Primary common or systematic name.
2.  **Formula**: Normalized ASCII molecular formula.
3.  **Relative Atomic Mass**: Numerical mass value.
4.  **SMILES**: Canonical structural string.
5.  **Molecular Image**: Visual 2D structure (where available; placeholder used otherwise).