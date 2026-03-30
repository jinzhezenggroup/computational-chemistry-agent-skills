#!/usr/bin/env python
# /// script
# dependencies = [
#   "rdkit",
#   "pandas",
# ]
# ///

"""
rdkit_conf_helper.py

A minimal CLI wrapper for RDKit conformer generation:

- conf  : Generate 3D conformers (with 2D fallback) and write to SDF or XYZ

Design goal: Work with `uv run` to complete common molecular geometry generation
tasks in a single command, printing absolute paths of result files upon completion.

3D generation pipeline per molecule:
  1. Parse SMILES -> RDKit Mol
  2. Add hydrogens (--add-hs, default on)
  3. Embed 3D coordinates via ETKDG (ETKDGv3 by default)
  4. Optionally minimize with MMFF94s or UFF force field (--ff)
  5. If 3D embedding fails -> fall back to 2D layout (Compute2DCoords),
     print a [WARN] line, and record in the fallback log CSV

Bad/illegal SMILES are skipped entirely and logged to *.skipped.csv (no crash).
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


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
        "pandas": None,
    }
    for pkg, mod in (("rdkit", "rdkit"), ("pandas", "pandas")):
        try:
            import importlib

            m = importlib.import_module(mod)
            env[pkg] = getattr(m, "__version__", "installed")
        except Exception as e:
            env[pkg] = f"unavailable ({type(e).__name__}: {e})"
    return env


def print_env():
    env = detect_env()
    print("======== rdkit_conf_helper Environment Detection ========", flush=True)
    print(f"python  : {env['python']}", flush=True)
    print(f"exe     : {env['executable']}", flush=True)
    print(f"cwd     : {env['cwd']}", flush=True)
    print(f"rdkit   : {env['rdkit']}", flush=True)
    print(f"pandas  : {env['pandas']}", flush=True)
    print("=========================================================", flush=True)


# ---------------------------------------------------------------------------
# SMILES I/O and validation
# ---------------------------------------------------------------------------


@dataclass
class SmilesRecord:
    idx: int
    smiles: str
    error: str


@dataclass
class ConformerResult:
    idx: int
    smiles: str
    name: str
    dim: int  # 3 = 3D success, 2 = 2D fallback
    ff: str  # force field used, or "none" / "2d_fallback"
    note: str = ""


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


def read_smiles_from_smi(path: Path) -> List[Tuple[str, str]]:
    """Return list of (smiles, name). Name is the second token or 'mol_{i}'."""
    entries: List[Tuple[str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            smi = parts[0]
            name = parts[1] if len(parts) > 1 else f"mol_{i}"
            entries.append((smi, name))
    return entries


def read_smiles_from_csv(
    path: Path, smiles_col: str, name_col: Optional[str]
) -> Tuple[List[Tuple[str, str]], str]:
    """Return (list of (smiles, name), actual_smiles_col)."""
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("Reading .csv files requires pandas.") from e

    df = pd.read_csv(path)

    # Resolve SMILES column (case-insensitive fallback)
    if smiles_col not in df.columns:
        candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
        if candidates:
            smiles_col = candidates[0]
        else:
            raise ValueError(
                f"SMILES column '{smiles_col}' not found in CSV. "
                f"Available columns: {list(df.columns)}"
            )

    # Resolve optional name column
    actual_name_col: Optional[str] = None
    if name_col:
        if name_col in df.columns:
            actual_name_col = name_col
        else:
            candidates = [c for c in df.columns if c.lower() == name_col.lower()]
            if candidates:
                actual_name_col = candidates[0]
            else:
                _eprint(
                    f"[WARN] Name column '{name_col}' not found in CSV; "
                    f"falling back to row-index names."
                )

    entries: List[Tuple[str, str]] = []
    for i, row in df.iterrows():
        smi = str(row[smiles_col])
        if actual_name_col:
            name = str(row[actual_name_col])
        else:
            name = f"mol_{i}"
        entries.append((smi, name))

    return entries, smiles_col


def ensure_parent_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def write_skipped_csv(path: Path, rows: Sequence[SmilesRecord]):
    ensure_parent_dir(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "smiles", "error"])
        for r in rows:
            w.writerow([r.idx, r.smiles, r.error])


def write_fallback_csv(path: Path, rows: Sequence[ConformerResult]):
    ensure_parent_dir(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "smiles", "name", "dim", "ff", "note"])
        for r in rows:
            w.writerow([r.idx, r.smiles, r.name, r.dim, r.ff, r.note])


def _default_out_for_input(in_path: Optional[Path], suffix: str) -> Path:
    if in_path is None:
        return Path.cwd() / f"rdkit_conf_{suffix}"
    return in_path.with_suffix("").with_suffix(f".{suffix}")


def _positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return ivalue


# ---------------------------------------------------------------------------
# Core conformer generation logic
# ---------------------------------------------------------------------------


def _smiles_to_mol_with_hs(smiles: str, add_hs: bool):
    """Parse SMILES and optionally add explicit hydrogens. Return RDKit Mol."""
    from rdkit import Chem  # type: ignore

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit failed to parse SMILES: {smiles!r}")
    # Sanitize is implicit in MolFromSmiles, but ensure aromaticity perception
    Chem.SanitizeMol(mol)
    if add_hs:
        mol = Chem.AddHs(mol)
    return mol


def _embed_3d_multi(
    mol, num_confs: int, random_seed: int, max_attempts: int, use_random_coords: bool
) -> bool:
    """
    Embed ``num_confs`` conformers via EmbedMultipleConfs.
    Tries ETKDGv3 -> ETKDGv2 -> ETDG -> ETDG+randomCoords as a fallback chain.
    Returns True if at least one conformer was successfully embedded.
    """
    from rdkit.Chem import AllChem  # type: ignore

    def _set_embedding_limits(params) -> None:
        # RDKit renamed this knob in newer releases. Support both spellings.
        if hasattr(params, "maxAttempts"):
            params.maxAttempts = max_attempts
        elif hasattr(params, "maxIterations"):
            params.maxIterations = max_attempts

    for etkg_version in (3, 2, 1):
        try:
            if etkg_version == 3:
                params = AllChem.ETKDGv3()
            elif etkg_version == 2:
                params = AllChem.ETKDGv2()
            else:
                params = AllChem.ETDG()
            params.randomSeed = random_seed
            _set_embedding_limits(params)
            if use_random_coords:
                params.useRandomCoords = True
            ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=params)
            if len(ids) > 0:
                return True
            # Clear any partial results before next attempt
            for cid in mol.GetConformers():
                mol.RemoveConformer(cid.GetId())
        except Exception:
            continue

    # Last resort: random coordinate embedding
    try:
        params = AllChem.ETKDGv3()
        params.randomSeed = random_seed
        _set_embedding_limits(params)
        params.useRandomCoords = True
        ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=params)
        if len(ids) > 0:
            return True
    except Exception:
        pass

    return False


def _optimize_ff_conf(mol, conf_id: int, ff: str) -> Tuple[bool, str, Optional[float]]:
    """
    Run force-field optimization on a single conformer (``conf_id``).
    Returns (success, ff_name_used, energy).
    Energy is in kcal/mol for MMFF94s and in the UFF internal unit for UFF.
    Returns None for energy if optimization was skipped or failed.
    """
    from rdkit.Chem import AllChem  # type: ignore

    if ff == "none":
        return True, "none", None

    if ff in ("mmff", "mmff94s"):
        try:
            props = AllChem.MMFFGetMoleculeProperties(mol, mmffVariant="MMFF94s")
            if props is not None:
                ff_obj = AllChem.MMFFGetMoleculeForceField(mol, props, confId=conf_id)
                if ff_obj is not None:
                    ff_obj.Minimize()
                    energy = ff_obj.CalcEnergy()
                    return True, "mmff94s", energy
        except Exception:
            pass
        _eprint("[WARN] MMFF94s unavailable for this molecule, trying UFF.")

    if ff in ("uff", "mmff", "mmff94s"):
        try:
            ff_obj = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id)
            if ff_obj is not None:
                ff_obj.Minimize()
                energy = ff_obj.CalcEnergy()
                return True, "uff", energy
        except Exception:
            pass

    _eprint(
        f"[WARN] Force-field optimization failed (ff={ff!r}); keeping unoptimized geometry."
    )
    return False, "none", None


def _make_2d_fallback(smiles: str, add_hs: bool):
    """
    Generate a 2D layout as a last resort.
    Returns a mol with 2D coordinates (Z=0 for all atoms).
    """
    from rdkit import Chem  # type: ignore
    from rdkit.Chem import AllChem  # type: ignore

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Cannot parse SMILES even for 2D fallback: {smiles!r}")
    Chem.SanitizeMol(mol)
    if add_hs:
        mol = Chem.AddHs(mol)
    AllChem.Compute2DCoords(mol)
    return mol


def generate_conformer(
    smiles: str,
    add_hs: bool,
    ff: str,
    num_confs: int,
    random_seed: int,
    max_attempts: int,
    use_random_coords: bool,
) -> Tuple[object, int, str, str]:
    """
    Full pipeline: multi-conformer 3D embedding -> FF minimization per conformer
    -> keep lowest-energy conformer -> 2D fallback on total failure.

    Steps:
      1. Embed ``num_confs`` conformers via EmbedMultipleConfs (ETKDGv3 with fallbacks).
      2. Optimize every successfully embedded conformer with the chosen force field.
      3. Select the conformer with the lowest force-field energy; if FF is 'none',
         keep the first successfully embedded conformer.
      4. Strip all other conformers from the mol so the returned object has exactly one.
      5. If all 3D embedding attempts fail, fall back to Compute2DCoords.

    Returns:
        (mol, dim, ff_used, note)
        dim    : 3 if 3D succeeded, 2 if fell back to 2D
        ff_used: force-field name used, "none", or "2d_fallback"
        note   : human-readable status string including conformer counts
    """

    mol = _smiles_to_mol_with_hs(smiles, add_hs)

    # --- Attempt multi-conformer 3D embedding ---
    ok_3d = _embed_3d_multi(
        mol, num_confs, random_seed, max_attempts, use_random_coords
    )

    if ok_3d:
        conf_ids = [c.GetId() for c in mol.GetConformers()]
        n_embedded = len(conf_ids)

        if ff == "none":
            # No optimization: keep the first conformer
            best_id = conf_ids[0]
            ff_used = "none"
            note = f"3d_ok;embedded={n_embedded};kept=first;ff=none"
        else:
            # Optimize every conformer and collect energies
            energies: List[Tuple[float, int]] = []  # (energy, conf_id)
            ff_used = "none"
            for cid in conf_ids:
                ok, ff_name, energy = _optimize_ff_conf(mol, cid, ff)
                if ok and energy is not None:
                    energies.append((energy, cid))
                    ff_used = (
                        ff_name  # last successful ff name (all should be the same)
                    )

            if energies:
                energies.sort(key=lambda x: x[0])
                best_energy, best_id = energies[0]
                note = (
                    f"3d_ok;embedded={n_embedded};"
                    f"optimized={len(energies)};best_energy={best_energy:.4f};ff={ff_used}"
                )
            else:
                # Optimization failed for all; fall back to first embedded conformer
                best_id = conf_ids[0]
                ff_used = "none"
                note = f"3d_ok;embedded={n_embedded};opt_failed;kept=first"

        # Retain only the best conformer
        for cid in conf_ids:
            if cid != best_id:
                mol.RemoveConformer(cid)

        return mol, 3, ff_used, note

    # --- All 3D attempts failed: 2D fallback ---
    _eprint(
        f"[WARN] 3D embedding failed for SMILES {smiles!r}; "
        f"falling back to 2D layout (Z=0)."
    )
    mol2d = _make_2d_fallback(smiles, add_hs)
    return mol2d, 2, "2d_fallback", "3d_failed_used_2d"


# ---------------------------------------------------------------------------
# SDF / XYZ writers
# ---------------------------------------------------------------------------


def _mol_to_sdf_block(mol, name: str) -> str:
    from rdkit import Chem  # type: ignore

    mol.SetProp("_Name", name)
    return Chem.MolToMolBlock(mol)


def _mol_to_xyz_block(mol, name: str) -> str:
    """Write a minimal XYZ block (no velocity). Requires conformer."""

    conf = mol.GetConformer(0)
    atoms = [mol.GetAtomWithIdx(i) for i in range(mol.GetNumAtoms())]
    lines = [str(len(atoms)), name]
    for atom in atoms:
        pos = conf.GetAtomPosition(atom.GetIdx())
        lines.append(
            f"{atom.GetSymbol():<4s}  {pos.x:12.6f}  {pos.y:12.6f}  {pos.z:12.6f}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# cmd_conf
# ---------------------------------------------------------------------------


def cmd_conf(args: argparse.Namespace) -> int:
    if importlib.util.find_spec("rdkit") is None:
        raise RuntimeError("RDKit not available")

    # ---- Resolve input ----
    if args.smiles:
        raw_entries: List[Tuple[str, str]] = [(args.smiles, args.name or "mol_0")]
        in_path: Optional[Path] = None
    else:
        in_path = Path(args.file).expanduser().resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")
        if in_path.suffix.lower() == ".smi":
            raw_entries = read_smiles_from_smi(in_path)
        elif in_path.suffix.lower() == ".csv":
            raw_entries, _ = read_smiles_from_csv(
                in_path, args.smiles_col, args.name_col
            )
        else:
            raise ValueError("--file only supports .csv or .smi")

    # ---- Resolve output ----
    fmt = str(args.format).lower()
    if fmt not in ("sdf", "xyz"):
        raise ValueError("--format must be 'sdf' or 'xyz'")

    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else _default_out_for_input(in_path, fmt).resolve()
    )
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_path.with_suffix(out_path.suffix + ".skipped.csv")
    )
    fallback_path = (
        Path(args.fallback_log).expanduser().resolve()
        if args.fallback_log
        else out_path.with_suffix(out_path.suffix + ".fallback.csv")
    )

    # ---- Validate SMILES ----
    raw_smiles = [smi for smi, _ in raw_entries]
    valid_pairs, skipped = validate_smiles_with_idx(raw_smiles)

    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(
            f"[WARN] Found {len(skipped)} invalid/empty SMILES. "
            f"Skipped and logged to: {skipped_path}"
        )
    if not valid_pairs:
        raise RuntimeError("No valid SMILES available (all parsing failed or empty).")

    # ---- Generate conformers ----
    results: List[ConformerResult] = []
    fallbacks: List[ConformerResult] = []

    ensure_parent_dir(out_path)

    # Open output file for streaming write
    out_handle = out_path.open("w", encoding="utf-8")
    try:
        for orig_idx, smi in valid_pairs:
            _, mol_name = raw_entries[orig_idx]

            try:
                mol, dim, ff_used, note = generate_conformer(
                    smiles=smi,
                    add_hs=not args.no_hs,
                    ff=str(args.ff),
                    num_confs=int(args.num_confs),
                    random_seed=int(args.seed),
                    max_attempts=int(args.max_attempts),
                    use_random_coords=bool(args.use_random_coords),
                )
            except Exception as e:
                skipped.append(
                    SmilesRecord(orig_idx, smi, f"conf_failed:{type(e).__name__}:{e}")
                )
                _eprint(f"[WARN] Conformer generation failed for {smi!r}: {e}")
                continue

            # Write to output
            try:
                if fmt == "sdf":
                    block = _mol_to_sdf_block(mol, mol_name)
                    out_handle.write(block)
                    out_handle.write("\n$$$$\n")
                else:
                    block = _mol_to_xyz_block(mol, mol_name)
                    out_handle.write(block)
                    out_handle.write("\n")
            except Exception as e:
                _eprint(f"[WARN] Failed to write conformer for {smi!r}: {e}")
                skipped.append(
                    SmilesRecord(orig_idx, smi, f"write_failed:{type(e).__name__}:{e}")
                )
                continue

            rec = ConformerResult(
                idx=orig_idx,
                smiles=smi,
                name=mol_name,
                dim=dim,
                ff=ff_used,
                note=note,
            )
            results.append(rec)

            if dim == 2:
                fallbacks.append(rec)
    finally:
        out_handle.close()

    # ---- Write logs ----
    if skipped:
        write_skipped_csv(skipped_path, skipped)

    if fallbacks:
        write_fallback_csv(fallback_path, fallbacks)
        _eprint(
            f"[WARN] {len(fallbacks)} molecule(s) used 2D fallback. "
            f"Logged to: {fallback_path}"
        )

    # ---- Summary ----
    n_3d = sum(1 for r in results if r.dim == 3)
    n_2d = sum(1 for r in results if r.dim == 2)
    n_skip = len(skipped)
    print(
        f"[INFO] Done: {n_3d} 3D, {n_2d} 2D-fallback, {n_skip} skipped "
        f"(total input: {len(raw_entries)})",
        flush=True,
    )

    print(f"[RESULT] conf_{fmt}={str(out_path.resolve())}")
    if fallbacks:
        print(f"[RESULT] fallback_csv={str(fallback_path.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")

    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rdkit_conf_helper.py",
        description=(
            "CLI wrapper for RDKit 3D/2D conformer generation.\n"
            "Attempts 3D embedding (ETKDGv3) with optional FF minimization;\n"
            "falls back to 2D layout on failure and logs the affected molecules."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--no-env",
        action="store_true",
        help="Do not print environment detection info",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    # ---- conf ----
    pc = sub.add_parser(
        "conf",
        help="Generate conformers, output as SDF or XYZ",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    g = pc.add_mutually_exclusive_group(required=True)
    g.add_argument("--smiles", type=str, help="Single SMILES string input")
    g.add_argument("--file", type=str, help="Input file: .csv or .smi")
    pc.add_argument(
        "--smiles-col",
        type=str,
        default="smiles",
        help="SMILES column name in CSV",
    )
    pc.add_argument(
        "--name-col",
        type=str,
        default=None,
        help=(
            "Column name to use as molecule name in CSV "
            "(written to SDF/XYZ header; defaults to row-index names)"
        ),
    )
    pc.add_argument(
        "--name",
        type=str,
        default=None,
        help="Molecule name when using --smiles (default: 'mol_0')",
    )
    pc.add_argument(
        "--format",
        type=str,
        default="sdf",
        choices=["sdf", "xyz"],
        help="Output format: 'sdf' (multi-molecule V2000 SDF) or 'xyz' (concatenated XYZ blocks)",
    )
    pc.add_argument(
        "--num-confs",
        type=_positive_int,
        default=10,
        help=(
            "Number of conformers to sample per molecule via EmbedMultipleConfs. "
            "All conformers are optimized with the chosen force field and the "
            "lowest-energy one is kept. Set to 1 to skip multi-sampling."
        ),
    )
    pc.add_argument(
        "--ff",
        type=str,
        default="mmff94s",
        choices=["none", "mmff94s", "mmff", "uff"],
        help=(
            "Force field for geometry optimization after 3D embedding. "
            "'mmff94s' (default) -> falls back to 'uff' if unavailable; "
            "'none' skips optimization entirely"
        ),
    )
    pc.add_argument(
        "--no-hs",
        action="store_true",
        help="Do not add explicit hydrogens before embedding (not recommended for 3D accuracy)",
    )
    pc.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for ETKDG embedding (use -1 for non-deterministic)",
    )
    pc.add_argument(
        "--max-attempts",
        type=_positive_int,
        default=100,
        help="Maximum number of embedding attempts per molecule",
    )
    pc.add_argument(
        "--use-random-coords",
        action="store_true",
        help="Use random initial coordinates in ETKDG (can help for large / macrocyclic molecules)",
    )
    pc.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (.sdf or .xyz)",
    )
    pc.add_argument(
        "--error-log",
        type=str,
        default=None,
        help="Path for CSV log of SMILES that were skipped entirely",
    )
    pc.add_argument(
        "--fallback-log",
        type=str,
        default=None,
        help="Path for CSV log of molecules that fell back to 2D (default: <output>.fallback.csv)",
    )
    pc.set_defaults(func=cmd_conf)

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
        if os.environ.get("RDKIT_CONF_HELPER_TRACE", "").strip() in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }:
            _eprint(traceback.format_exc())
        raise SystemExit(2)
