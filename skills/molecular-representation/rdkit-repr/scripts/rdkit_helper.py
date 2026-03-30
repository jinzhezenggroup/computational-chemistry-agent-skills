#!/usr/bin/env python
# /// script
# dependencies = [
#   "rdkit",
#   "pandas",
#   "numpy",
# ]
# ///

"""
rdkit_helper.py

A minimal CLI wrapper for RDKit molecular feature extraction:

- desc   : Compute common physicochemical descriptors (outputs .csv)
- fp     : Compute molecular fingerprints (outputs .npy or .csv)

Design goal: Work with `uv run` to complete common molecular featurization tasks
in a single command, printing absolute paths of result files upon completion.
Bad/illegal SMILES are skipped and logged to *.skipped.csv (no crash).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

if TYPE_CHECKING:
    import pandas as pd


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def detect_env() -> dict:
    env = {
        "python": sys.version.replace("\n", " "),
        "executable": sys.executable,
        "cwd": str(Path.cwd().resolve()),
        "rdkit": None,
        "numpy": None,
        "pandas": None,
    }
    for pkg in ("rdkit", "numpy", "pandas"):
        try:
            import importlib

            m = importlib.import_module(pkg if pkg != "rdkit" else "rdkit")
            env[pkg] = getattr(m, "__version__", "installed")
        except Exception as e:
            env[pkg] = f"unavailable ({type(e).__name__}: {e})"
    return env


def print_env():
    env = detect_env()
    print("======== rdkit_helper Environment Detection ========", flush=True)
    print(f"python  : {env['python']}", flush=True)
    print(f"exe     : {env['executable']}", flush=True)
    print(f"cwd     : {env['cwd']}", flush=True)
    print(f"rdkit   : {env['rdkit']}", flush=True)
    print(f"numpy   : {env['numpy']}", flush=True)
    print(f"pandas  : {env['pandas']}", flush=True)
    print("====================================================", flush=True)


# ---------------------------------------------------------------------------
# SMILES I/O and validation
# ---------------------------------------------------------------------------


@dataclass
class SmilesRecord:
    idx: int
    smiles: str
    error: str


def validate_smiles_with_idx(
    smiles: Sequence[str],
) -> Tuple[List[Tuple[int, str]], List[SmilesRecord]]:
    from rdkit import Chem  # type: ignore

    valid: List[Tuple[int, str]] = []
    bad: List[SmilesRecord] = []
    for i, s in enumerate(smiles):
        s = (s or "").strip()
        if not s:
            bad.append(SmilesRecord(i, s, "empty_smiles"))
            continue
        try:
            mol = Chem.MolFromSmiles(s)
            if mol is None:
                bad.append(SmilesRecord(i, s, "rdkit_parse_failed"))
            else:
                valid.append((i, s))
        except Exception as e:
            bad.append(SmilesRecord(i, s, f"rdkit_exception:{type(e).__name__}:{e}"))
    return valid, bad


def read_smiles_from_smi(path: Path) -> List[str]:
    smiles: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            token = line.split()[0]
            smiles.append(token)
    return smiles


def read_smiles_from_csv(
    path: Path, smiles_col: str
) -> Tuple[List[str], "pd.DataFrame", str]:
    """Return (smiles_list, dataframe, actual_smiles_col).

    ``actual_smiles_col`` is the column name as it actually appears in the CSV
    (may differ in case from the requested ``smiles_col``).
    """
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("Reading .csv files requires pandas.") from e
    df = pd.read_csv(path)
    if smiles_col not in df.columns:
        candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
        if candidates:
            smiles_col = candidates[0]
        else:
            raise ValueError(
                f"SMILES column '{smiles_col}' not found in CSV. "
                f"Available columns: {list(df.columns)}"
            )
    return [str(x) for x in df[smiles_col].tolist()], df, smiles_col


def ensure_parent_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def write_skipped_csv(path: Path, rows: Sequence[SmilesRecord]):
    ensure_parent_dir(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "smiles", "error"])
        for r in rows:
            w.writerow([r.idx, r.smiles, r.error])


def _default_out_for_input(in_path: Optional[Path], suffix: str) -> Path:
    if in_path is None:
        return Path.cwd() / f"rdkit_{suffix}"
    return in_path.with_suffix("").with_suffix(f".{suffix}")


# ---------------------------------------------------------------------------
# Descriptor definitions
# ---------------------------------------------------------------------------

# Descriptors are grouped into named presets for convenience.
# All descriptors listed here are available in rdkit.Chem.Descriptors.

DESCRIPTOR_GROUPS: Dict[str, List[str]] = {
    # Lipinski-style drug-likeness properties
    "lipinski": [
        "MolWt",
        "MolLogP",
        "NumHDonors",
        "NumHAcceptors",
        "TPSA",
        "NumRotatableBonds",
    ],
    # Extended physicochemical properties
    "physchem": [
        "MolWt",
        "ExactMolWt",
        "MolLogP",
        "MolMR",
        "TPSA",
        "NumHDonors",
        "NumHAcceptors",
        "NumRotatableBonds",
        "NumAromaticRings",
        "NumSaturatedRings",
        "NumAliphaticRings",
        "NumAromaticHeterocycles",
        "NumSaturatedHeterocycles",
        "NumAliphaticHeterocycles",
        "RingCount",
        "FractionCSP3",
        "HeavyAtomCount",
        "NHOHCount",
        "NOCount",
        "NumHeteroatoms",
        "NumValenceElectrons",
        "NumRadicalElectrons",
        "MaxPartialCharge",
        "MinPartialCharge",
        "MaxAbsPartialCharge",
        "MinAbsPartialCharge",
    ],
    # Topological / graph-theory indices
    "topological": [
        "BalabanJ",
        "BertzCT",
        "Chi0",
        "Chi0n",
        "Chi0v",
        "Chi1",
        "Chi1n",
        "Chi1v",
        "Chi2n",
        "Chi2v",
        "Chi3n",
        "Chi3v",
        "Chi4n",
        "Chi4v",
        "HallKierAlpha",
        "Ipc",
        "Kappa1",
        "Kappa2",
        "Kappa3",
        "LabuteASA",
        "PEOE_VSA1",
        "PEOE_VSA2",
        "PEOE_VSA3",
        "PEOE_VSA4",
        "PEOE_VSA5",
        "PEOE_VSA6",
        "PEOE_VSA7",
        "PEOE_VSA8",
        "PEOE_VSA9",
        "PEOE_VSA10",
        "PEOE_VSA11",
        "PEOE_VSA12",
        "PEOE_VSA13",
        "PEOE_VSA14",
        "SMR_VSA1",
        "SMR_VSA2",
        "SMR_VSA3",
        "SMR_VSA4",
        "SMR_VSA5",
        "SMR_VSA6",
        "SMR_VSA7",
        "SMR_VSA8",
        "SMR_VSA9",
        "SMR_VSA10",
        "SlogP_VSA1",
        "SlogP_VSA2",
        "SlogP_VSA3",
        "SlogP_VSA4",
        "SlogP_VSA5",
        "SlogP_VSA6",
        "SlogP_VSA7",
        "SlogP_VSA8",
        "SlogP_VSA9",
        "SlogP_VSA10",
        "SlogP_VSA11",
        "SlogP_VSA12",
        "EState_VSA1",
        "EState_VSA2",
        "EState_VSA3",
        "EState_VSA4",
        "EState_VSA5",
        "EState_VSA6",
        "EState_VSA7",
        "EState_VSA8",
        "EState_VSA9",
        "EState_VSA10",
        "EState_VSA11",
    ],
    # Full Mordred-like 200-descriptor set (RDKit built-in subset)
    "all": [],  # populated dynamically below
}

# Populate "all" dynamically at import time
try:
    from rdkit.Chem import Descriptors as _D  # type: ignore

    _ALL_RDKIT = [name for name, _ in _D.descList]
    DESCRIPTOR_GROUPS["all"] = _ALL_RDKIT
except Exception:
    DESCRIPTOR_GROUPS["all"] = (
        DESCRIPTOR_GROUPS["lipinski"]
        + DESCRIPTOR_GROUPS["physchem"]
        + DESCRIPTOR_GROUPS["topological"]
    )


# ---------------------------------------------------------------------------
# Fingerprint definitions
# ---------------------------------------------------------------------------

FP_TYPES = [
    "morgan2",  # Morgan radius-2 circular FP (ECFP4-like), bit vector
    "morgan3",  # Morgan radius-3 circular FP (ECFP6-like), bit vector
    "morgan2_count",  # Morgan radius-2 count vector
    "rdkit",  # RDKit path-based FP
    "maccs",  # MACCS 167-bit keys
    "topological",  # Topological torsion FP
    "atompair",  # Atom-pair FP
    "layered",  # Layered FP (substructure-aware)
    "pattern",  # Pattern FP (SMARTS-based)
]


def _mol_to_fp_array(mol, fp_type: str, nbits: int, radius: int):
    """Convert a single RDKit Mol to a numpy array for the requested FP type."""
    import numpy as np
    from rdkit.Chem import rdMolDescriptors  # type: ignore
    from rdkit import DataStructs  # type: ignore

    if fp_type in ("morgan2", "morgan3"):
        r = 2 if fp_type == "morgan2" else 3
        bv = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, radius=r, nBits=nbits)
        arr = np.zeros(nbits, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(bv, arr)
        return arr

    if fp_type == "morgan2_count":
        from rdkit.Chem.rdMolDescriptors import GetMorganFingerprint  # type: ignore

        fp = GetMorganFingerprint(mol, radius=2)
        cnts = fp.GetNonzeroElements()
        arr = np.zeros(nbits, dtype=np.int32)
        for idx, cnt in cnts.items():
            arr[idx % nbits] += cnt
        return arr

    if fp_type == "rdkit":
        from rdkit.Chem import RDKFingerprint  # type: ignore

        bv = RDKFingerprint(mol, fpSize=nbits)
        arr = np.zeros(nbits, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(bv, arr)
        return arr

    if fp_type == "maccs":
        from rdkit.Chem import MACCSkeys  # type: ignore

        bv = MACCSkeys.GenMACCSKeys(mol)
        # MACCS keys are always 167 bits; we return as-is regardless of nbits
        arr = np.zeros(167, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(bv, arr)
        return arr

    if fp_type == "topological":
        from rdkit.Chem.rdMolDescriptors import GetTopologicalTorsionFingerprint  # type: ignore

        fp = GetTopologicalTorsionFingerprint(mol)
        cnts = fp.GetNonzeroElements()
        arr = np.zeros(nbits, dtype=np.int32)
        for idx, cnt in cnts.items():
            arr[int(idx) % nbits] += cnt
        return arr

    if fp_type == "atompair":
        from rdkit.Chem.rdMolDescriptors import GetAtomPairFingerprint  # type: ignore

        fp = GetAtomPairFingerprint(mol)
        cnts = fp.GetNonzeroElements()
        arr = np.zeros(nbits, dtype=np.int32)
        for idx, cnt in cnts.items():
            arr[int(idx) % nbits] += cnt
        return arr

    if fp_type == "layered":
        from rdkit.Chem.rdmolops import LayeredFingerprint  # type: ignore

        bv = LayeredFingerprint(mol, fpSize=nbits)
        arr = np.zeros(nbits, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(bv, arr)
        return arr

    if fp_type == "pattern":
        from rdkit.Chem.rdmolops import PatternFingerprint  # type: ignore

        bv = PatternFingerprint(mol, fpSize=nbits)
        arr = np.zeros(nbits, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(bv, arr)
        return arr

    raise ValueError(f"Unknown fingerprint type: {fp_type!r}. Choose from: {FP_TYPES}")


# ---------------------------------------------------------------------------
# cmd_desc: compute physicochemical descriptors → .csv
# ---------------------------------------------------------------------------


def cmd_desc(args: argparse.Namespace) -> int:
    try:
        import pandas as pd  # type: ignore
        from rdkit import Chem  # type: ignore
        from rdkit.Chem import Descriptors  # type: ignore
    except ImportError as e:
        raise RuntimeError(f"Required package not found: {e}") from e

    # ---- Resolve input ----
    actual_smiles_col: str = (
        args.smiles_col
    )  # resolved later for CSV; default for other paths
    if args.smiles:
        raw_smiles = [args.smiles]
        in_path: Optional[Path] = None
        source_df: Optional["pd.DataFrame"] = None
    else:
        in_path = Path(args.file).expanduser().resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")
        if in_path.suffix.lower() == ".smi":
            raw_smiles = read_smiles_from_smi(in_path)
            source_df = None
        elif in_path.suffix.lower() == ".csv":
            raw_smiles, source_df, actual_smiles_col = read_smiles_from_csv(
                in_path, args.smiles_col
            )
        else:
            raise ValueError("--file only supports .csv or .smi")

    # ---- Resolve output ----
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else _default_out_for_input(in_path, "desc.csv").resolve()
    )
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_path.with_suffix(out_path.suffix + ".skipped.csv")
    )

    # ---- Validate SMILES ----
    valid_pairs, skipped = validate_smiles_with_idx(raw_smiles)
    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(
            f"[WARN] Found {len(skipped)} invalid/empty SMILES. "
            f"Skipped and logged to: {skipped_path}"
        )
    if not valid_pairs:
        raise RuntimeError("No valid SMILES available (all parsing failed or empty).")

    # ---- Resolve descriptor list ----
    preset = str(args.preset).lower()
    if args.descriptors:
        desc_names = [d.strip() for d in args.descriptors.split(",") if d.strip()]
    else:
        desc_names = list(
            dict.fromkeys(DESCRIPTOR_GROUPS.get(preset, DESCRIPTOR_GROUPS["physchem"]))
        )

    # Build lookup: name → function
    desc_fn_map = {name: fn for name, fn in Descriptors.descList}
    missing = [d for d in desc_names if d not in desc_fn_map]
    if missing:
        raise ValueError(
            f"Unknown descriptor(s): {missing}. "
            f"Run `rdkit_helper.py list-desc` to see all available descriptors."
        )

    # ---- Compute descriptors ----
    records = []
    for orig_idx, smi in valid_pairs:
        mol = Chem.MolFromSmiles(smi)
        row: Dict[str, object] = {"smiles": smi}
        for d in desc_names:
            try:
                val = desc_fn_map[d](mol)
                # Some descriptors return NaN for edge cases; keep as-is
                row[d] = val
            except Exception as e:
                row[d] = float("nan")
                _eprint(f"[WARN] Descriptor '{d}' failed for {smi!r}: {e}")
        records.append((orig_idx, row))

    out_rows = [r for _, r in records]
    out_df = pd.DataFrame(out_rows, columns=["smiles"] + desc_names)

    # Optionally merge back with source CSV columns
    if source_df is not None and not args.no_merge:
        valid_idxs = [i for i, _ in valid_pairs]
        src_subset = source_df.iloc[valid_idxs].reset_index(drop=True)
        # Drop the original SMILES column (using the resolved name) to avoid duplication
        if actual_smiles_col in src_subset.columns:
            src_subset = src_subset.drop(columns=[actual_smiles_col])
        out_df = pd.concat([out_df, src_subset.reset_index(drop=True)], axis=1)

    ensure_parent_dir(out_path)
    out_df.to_csv(out_path, index=False)

    print(f"[RESULT] desc_csv={str(out_path.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


# ---------------------------------------------------------------------------
# cmd_fp: compute molecular fingerprints → .npy (or .csv)
# ---------------------------------------------------------------------------


def cmd_fp(args: argparse.Namespace) -> int:
    try:
        import numpy as np  # type: ignore
        from rdkit import Chem  # type: ignore
    except ImportError as e:
        raise RuntimeError(f"Required package not found: {e}") from e

    # ---- Resolve input ----
    if args.smiles:
        raw_smiles = [args.smiles]
        in_path: Optional[Path] = None
        source_df = None
    else:
        in_path = Path(args.file).expanduser().resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")
        if in_path.suffix.lower() == ".smi":
            raw_smiles = read_smiles_from_smi(in_path)
            source_df = None
        elif in_path.suffix.lower() == ".csv":
            raw_smiles, source_df, _actual_smiles_col = read_smiles_from_csv(
                in_path, args.smiles_col
            )
        else:
            raise ValueError("--file only supports .csv or .smi")

    fp_type = str(args.type).lower()
    if fp_type not in FP_TYPES:
        raise ValueError(
            f"Unknown fingerprint type '{fp_type}'. Choose from: {FP_TYPES}"
        )

    nbits = int(args.nbits)
    fmt = str(args.format).lower()
    if fmt not in ("npy", "csv"):
        raise ValueError("--format must be 'npy' or 'csv'")

    # ---- Resolve output ----
    default_suffix = f"{fp_type}.{fmt}"
    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else _default_out_for_input(in_path, default_suffix).resolve()
    )
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_path.with_suffix(out_path.suffix + ".skipped.csv")
    )

    # ---- Validate SMILES ----
    valid_pairs, skipped = validate_smiles_with_idx(raw_smiles)
    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(
            f"[WARN] Found {len(skipped)} invalid/empty SMILES. "
            f"Skipped and logged to: {skipped_path}"
        )
    if not valid_pairs:
        raise RuntimeError("No valid SMILES available (all parsing failed or empty).")

    # ---- Compute fingerprints ----
    arrays: List[np.ndarray] = []
    valid_smiles_out: List[str] = []
    runtime_skipped: List[SmilesRecord] = []
    for orig_idx, smi in valid_pairs:
        mol = Chem.MolFromSmiles(smi)
        try:
            arr = _mol_to_fp_array(mol, fp_type, nbits, radius=2)
            arrays.append(arr)
            valid_smiles_out.append(smi)
        except Exception as e:
            runtime_skipped.append(
                SmilesRecord(orig_idx, smi, f"fp_failed:{type(e).__name__}:{e}")
            )
            _eprint(f"[WARN] FP computation failed for {smi!r}: {e}")

    all_skipped = skipped + runtime_skipped
    if runtime_skipped:
        write_skipped_csv(skipped_path, all_skipped)

    if not arrays:
        raise RuntimeError("Fingerprint computation failed: No results obtained.")

    mat = np.stack(arrays, axis=0)
    ensure_parent_dir(out_path)

    if fmt == "npy":
        np.save(out_path, mat)
        print(f"[RESULT] fp_npy={str(out_path.resolve())}")
    else:
        # CSV output: smiles + bit_0 ... bit_N-1
        import pandas as pd  # type: ignore

        ncols = mat.shape[1]
        col_names = [f"bit_{i}" for i in range(ncols)]
        df = pd.DataFrame(mat, columns=col_names)
        df.insert(0, "smiles", valid_smiles_out)
        df.to_csv(out_path, index=False)
        print(f"[RESULT] fp_csv={str(out_path.resolve())}")

    if all_skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


# ---------------------------------------------------------------------------
# cmd_list_desc: print available descriptors (grouped)
# ---------------------------------------------------------------------------


def cmd_list_desc(args: argparse.Namespace) -> int:
    try:
        from rdkit.Chem import Descriptors  # type: ignore

        all_names = [name for name, _ in Descriptors.descList]
    except Exception:
        all_names = []

    group = str(args.group).lower() if args.group else None
    if group and group not in DESCRIPTOR_GROUPS:
        raise ValueError(
            f"Unknown group '{group}'. Available groups: {list(DESCRIPTOR_GROUPS.keys())}"
        )

    if group:
        names = DESCRIPTOR_GROUPS[group]
        print(f"Descriptors in group '{group}' ({len(names)} total):")
        for n in names:
            print(f"  {n}")
    else:
        print(f"All available RDKit descriptors ({len(all_names)} total):")
        for n in all_names:
            print(f"  {n}")
        print()
        print("Built-in presets:")
        for g, members in DESCRIPTOR_GROUPS.items():
            if g == "all":
                print(f"  all        : all {len(members)} descriptors")
            else:
                print(
                    f"  {g:<12}: {len(members)} descriptors  "
                    f"({', '.join(members[:4])}{'...' if len(members) > 4 else ''})"
                )
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rdkit_helper.py",
        description=(
            "CLI wrapper for RDKit molecular descriptor and fingerprint extraction.\n"
            "Subcommands: desc, fp, list-desc"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--no-env",
        action="store_true",
        help="Do not print environment detection info",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    # ---- desc ----
    pd_ = sub.add_parser(
        "desc",
        help="Compute physicochemical descriptors, output as .csv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    g = pd_.add_mutually_exclusive_group(required=True)
    g.add_argument("--smiles", type=str, help="Single SMILES string input")
    g.add_argument("--file", type=str, help="Input file: .csv or .smi")
    pd_.add_argument(
        "--smiles-col", type=str, default="smiles", help="SMILES column name in CSV"
    )
    pd_.add_argument(
        "--preset",
        type=str,
        default="physchem",
        choices=list(DESCRIPTOR_GROUPS.keys()),
        help=(
            "Named descriptor preset. "
            "'lipinski' (6 desc), 'physchem' (25 desc), "
            "'topological' (56 desc), 'all' (all RDKit descriptors)"
        ),
    )
    pd_.add_argument(
        "--descriptors",
        type=str,
        default=None,
        help=(
            "Comma-separated list of specific descriptor names (overrides --preset). "
            "Use `list-desc` subcommand to see all available names."
        ),
    )
    pd_.add_argument(
        "--no-merge",
        action="store_true",
        help="Do not merge original CSV columns into output (only smiles + descriptors)",
    )
    pd_.add_argument(
        "--output", type=str, default=None, help="Output path for descriptor CSV"
    )
    pd_.add_argument(
        "--error-log", type=str, default=None, help="Path to log bad SMILES as CSV"
    )
    pd_.set_defaults(func=cmd_desc)

    # ---- fp ----
    pfp = sub.add_parser(
        "fp",
        help="Compute molecular fingerprints, output as .npy or .csv",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    g2 = pfp.add_mutually_exclusive_group(required=True)
    g2.add_argument("--smiles", type=str, help="Single SMILES string input")
    g2.add_argument("--file", type=str, help="Input file: .csv or .smi")
    pfp.add_argument(
        "--smiles-col", type=str, default="smiles", help="SMILES column name in CSV"
    )
    pfp.add_argument(
        "--type",
        type=str,
        default="morgan2",
        choices=FP_TYPES,
        help=(
            "Fingerprint type. "
            "morgan2/morgan3: ECFP4/ECFP6-style bit vectors; "
            "morgan2_count: Morgan count vector; "
            "rdkit: RDKit path-based; "
            "maccs: 167-bit MACCS keys (ignores --nbits); "
            "topological: topological torsion; "
            "atompair: atom-pair; "
            "layered: layered substructure; "
            "pattern: SMARTS pattern"
        ),
    )
    pfp.add_argument(
        "--nbits",
        type=int,
        default=2048,
        help="Number of bits for bit-vector fingerprints (ignored for maccs)",
    )
    pfp.add_argument(
        "--format",
        type=str,
        default="npy",
        choices=["npy", "csv"],
        help=(
            "Output format: 'npy' saves a numpy array of shape (N, nbits); "
            "'csv' saves smiles + bit_0...bit_{nbits-1} columns"
        ),
    )
    pfp.add_argument(
        "--output", type=str, default=None, help="Output path for fingerprint file"
    )
    pfp.add_argument(
        "--error-log", type=str, default=None, help="Path to log bad SMILES as CSV"
    )
    pfp.set_defaults(func=cmd_fp)

    # ---- list-desc ----
    pld = sub.add_parser(
        "list-desc",
        help="List available descriptor names and presets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    pld.add_argument(
        "--group",
        type=str,
        default=None,
        choices=list(DESCRIPTOR_GROUPS.keys()),
        help="Show descriptors in a specific preset group only",
    )
    pld.set_defaults(func=cmd_list_desc)

    return p


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "no_env", False):
        print_env()

    return int(args.func(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        _eprint("[ERROR] Interrupted.")
        raise
    except Exception as e:
        _eprint(f"[ERROR] {type(e).__name__}: {e}")
        if os.environ.get("RDKIT_HELPER_TRACE", "").strip() in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }:
            _eprint(traceback.format_exc())
        raise SystemExit(2)
