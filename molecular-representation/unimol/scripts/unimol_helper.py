#!/usr/bin/env python
# /// script
# dependencies = [
#   "unimol-tools",
#   "torch",
#   "rdkit",
#   "pandas",
#   "numpy",
# ]
# ///

"""
unimol_helper.py

A minimal CLI wrapper for unimol-tools:

- repr    : Extract molecular representations (outputs .npy)
- train   : Train models (outputs model directory)
- predict : Property prediction (outputs .csv)

Design goal: Work with `uv run` to complete common molecular ML tasks in a single command,
printing absolute paths of result files/directories upon completion.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


def _eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def detect_env() -> dict:
    env = {
        "python": sys.version.replace("\n", " "),
        "executable": sys.executable,
        "cwd": str(Path.cwd().resolve()),
        "torch": None,
        "cuda_available": None,
        "cuda_device_count": None,
        "cuda_devices": None,
    }
    try:
        import torch  # type: ignore

        env["torch"] = getattr(torch, "__version__", None)
        env["cuda_available"] = bool(torch.cuda.is_available())
        env["cuda_device_count"] = int(torch.cuda.device_count())
        if env["cuda_available"] and env["cuda_device_count"]:
            names = []
            for i in range(env["cuda_device_count"]):
                try:
                    names.append(torch.cuda.get_device_name(i))
                except Exception:
                    names.append(f"cuda:{i}")
            env["cuda_devices"] = names
        else:
            env["cuda_devices"] = []
    except Exception as e:
        env["torch"] = f"unavailable ({type(e).__name__}: {e})"
        env["cuda_available"] = False
        env["cuda_device_count"] = 0
        env["cuda_devices"] = []
    return env


def print_env():
    env = detect_env()
    print("======== unimol_helper Environment Detection ========", flush=True)
    print(f"python          : {env['python']}", flush=True)
    print(f"executable      : {env['executable']}", flush=True)
    print(f"cwd             : {env['cwd']}", flush=True)
    print(f"torch           : {env['torch']}", flush=True)
    print(f"cuda_available  : {env['cuda_available']}", flush=True)
    print(f"cuda_device_cnt : {env['cuda_device_count']}", flush=True)
    if env["cuda_devices"]:
        for i, n in enumerate(env["cuda_devices"]):
            print(f"cuda_device[{i}] : {n}", flush=True)
    print("=====================================================", flush=True)


def _try_import_rdkit():
    try:
        from rdkit import Chem  # type: ignore

        return Chem
    except Exception:
        return None


@dataclass
class SmilesRecord:
    idx: int
    smiles: str
    error: str


def validate_smiles(smiles: Sequence[str]) -> Tuple[List[str], List[SmilesRecord]]:
    """
    Validate SMILES via RDKit. If RDKit is unavailable, only basic empty filtering is performed.
    To satisfy the 'bad SMILES won't crash' goal, it handles exceptions per entry.
    """
    Chem = _try_import_rdkit()
    valid: List[str] = []
    bad: List[SmilesRecord] = []
    for i, s in enumerate(smiles):
        s = (s or "").strip()
        if not s:
            bad.append(SmilesRecord(i, s, "empty_smiles"))
            continue
        if Chem is None:
            valid.append(s)
            continue
        try:
            mol = Chem.MolFromSmiles(s)
            if mol is None:
                bad.append(SmilesRecord(i, s, "rdkit_parse_failed"))
            else:
                valid.append(s)
        except Exception as e:
            bad.append(SmilesRecord(i, s, f"rdkit_exception:{type(e).__name__}:{e}"))
    return valid, bad


def validate_smiles_with_idx(
    smiles: Sequence[str],
) -> Tuple[List[Tuple[int, str]], List[SmilesRecord]]:
    Chem = _try_import_rdkit()
    valid: List[Tuple[int, str]] = []
    bad: List[SmilesRecord] = []
    for i, s in enumerate(smiles):
        s = (s or "").strip()
        if not s:
            bad.append(SmilesRecord(i, s, "empty_smiles"))
            continue
        if Chem is None:
            valid.append((i, s))
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
            # Common .smi format: "SMILES[ whitespace ]NAME"
            token = line.split()[0]
            smiles.append(token)
    return smiles


def read_smiles_from_csv(path: Path, smiles_col: str) -> List[str]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Reading .csv files requires pandas. Please install pandas in the environment."
        ) from e
    df = pd.read_csv(path)
    if smiles_col not in df.columns:
        # Fallback: check case-insensitive matches
        candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
        if candidates:
            smiles_col = candidates[0]
        else:
            raise ValueError(
                f"SMILES column '{smiles_col}' not found in CSV. Available columns: {list(df.columns)}"
            )
    return [str(x) for x in df[smiles_col].tolist()]


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
        return Path.cwd() / f"unimol_{suffix}"
    return in_path.with_suffix("").with_suffix(f".{suffix}")


def cmd_repr(args: argparse.Namespace) -> int:
    from unimol_tools import UniMolRepr  # type: ignore

    if args.smiles:
        raw_smiles = [args.smiles]
        in_path = None
    else:
        in_path = Path(args.file).expanduser().resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")
        if in_path.suffix.lower() == ".smi":
            raw_smiles = read_smiles_from_smi(in_path)
        elif in_path.suffix.lower() == ".csv":
            raw_smiles = read_smiles_from_csv(in_path, args.smiles_col)
        else:
            raise ValueError("--file only supports .csv or .smi")

    out_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else _default_out_for_input(in_path, "repr.npy").resolve()
    )
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_path.with_suffix(out_path.suffix + ".skipped.csv")
    )

    valid_pairs, skipped = validate_smiles_with_idx(raw_smiles)
    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(
            f"[WARN] Found {len(skipped)} invalid/empty SMILES. Skipped and logged to: {skipped_path}"
        )

    if not valid_pairs:
        raise RuntimeError("No valid SMILES available (all parsing failed or empty).")

    env = detect_env()
    if args.no_gpu:
        use_gpu = False
    elif args.use_gpu:
        use_gpu = True
    else:
        use_gpu = bool(env.get("cuda_available"))
    if use_gpu and not env.get("cuda_available"):
        _eprint("[WARN] CUDA not detected in current environment, falling back to CPU.")
        use_gpu = False

    repr_model = UniMolRepr(
        data_type="molecule", remove_hs=bool(args.remove_hs), use_gpu=use_gpu
    )

    import numpy as np  # type: ignore

    batch = int(args.batch_size)
    embs: List[np.ndarray] = []

    def safe_get_batch(pairs: Sequence[Tuple[int, str]]) -> List[np.ndarray]:
        smis = [s for _, s in pairs]
        try:
            d = repr_model.get_repr(list(smis))
            cls = d.get("cls_repr", [])
            return [np.asarray(x, dtype=np.float32) for x in cls]
        except Exception:
            # Fallback: Isolate entries to ensure "bad SMILES won't crash"
            out: List[np.ndarray] = []
            for orig_idx, s in pairs:
                try:
                    d1 = repr_model.get_repr([s])
                    cls1 = d1.get("cls_repr", [])
                    if not cls1:
                        raise RuntimeError("empty_cls_repr")
                    out.append(np.asarray(cls1[0], dtype=np.float32))
                except Exception as e:
                    skipped.append(
                        SmilesRecord(
                            orig_idx, s, f"unimol_repr_failed:{type(e).__name__}:{e}"
                        )
                    )
            return out

    for i in range(0, len(valid_pairs), batch):
        chunk = valid_pairs[i : i + batch]
        embs.extend(safe_get_batch(chunk))

    if len(embs) == 0:
        raise RuntimeError("Representation extraction failed: No embeddings obtained.")

    arr = np.stack(embs, axis=0).astype(np.float32, copy=False)
    ensure_parent_dir(out_path)
    np.save(out_path, arr)

    if skipped:
        write_skipped_csv(skipped_path, skipped)

    print(f"[RESULT] repr_npy={str(out_path.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    from unimol_tools import MolTrain  # type: ignore

    data_path = Path(args.input).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found: {data_path}")
    if data_path.suffix.lower() != ".csv":
        raise ValueError(
            "--input currently only supports .csv (containing smiles and target columns)"
        )

    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("Training requires pandas for CSV reading.") from e

    df = pd.read_csv(data_path)

    smiles_col = str(args.smiles_col)
    if smiles_col not in df.columns:
        candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
        if candidates:
            smiles_col = candidates[0]
        else:
            raise ValueError(
                f"SMILES column '{args.smiles_col}' not found in training CSV. Columns: {list(df.columns)}"
            )

    def _resolve_col(col_name: str, label: str) -> str:
        if col_name in df.columns:
            return col_name
        candidates = [c for c in df.columns if c.lower() == col_name.lower()]
        if candidates:
            return candidates[0]
        raise ValueError(
            f"{label} column '{col_name}' not found in training CSV. Columns: {list(df.columns)}"
        )

    is_multilabel = str(args.task) in {
        "multilabel_classification",
        "multilabel_regression",
    }
    target_cols: List[str]
    if is_multilabel:
        requested_cols: List[str] = []
        if args.target_cols:
            requested_cols = [
                x.strip() for x in str(args.target_cols).split(",") if x.strip()
            ]
        elif (
            str(args.target_col).strip()
            and str(args.target_col).strip().lower() != "target"
        ):
            requested_cols = [str(args.target_col).strip()]
        else:
            # Auto-detect common multilabel target naming patterns.
            # Exclude SMILES column even if its name starts with "target" unexpectedly.
            requested_cols = [
                c
                for c in df.columns
                if c != smiles_col
                and (c.lower() == "target" or c.lower().startswith("target_"))
            ]

        if not requested_cols:
            raise ValueError(
                "No target columns detected for multilabel task. "
                "Please provide --target-cols (comma-separated), e.g. --target-cols target_0,target_1."
            )

        resolved: List[str] = []
        seen = set()
        for c in requested_cols:
            rc = _resolve_col(c, "Target")
            if rc not in seen:
                seen.add(rc)
                resolved.append(rc)
        target_cols = resolved
    else:
        target_col = _resolve_col(str(args.target_col), "Target")
        target_cols = [target_col]

    env = detect_env()
    use_cuda = (not bool(args.no_cuda)) and bool(env.get("cuda_available"))
    if (not args.no_cuda) and (not env.get("cuda_available")):
        _eprint("[WARN] CUDA not detected, training will use CPU.")

    trainer = MolTrain(
        task=str(args.task),
        data_type="molecule",
        epochs=int(args.epochs),
        learning_rate=float(args.learning_rate),
        batch_size=int(args.batch_size),
        save_path=str(out_dir),
        smiles_col=smiles_col,
        target_cols=target_cols,
        smiles_check="filter",
        use_cuda=use_cuda,
        model_name=str(args.model_name),
        model_size=str(args.model_size),
        metrics=str(args.metrics),
    )
    trainer.fit(str(data_path))

    print(f"[RESULT] model_dir={str(out_dir.resolve())}")
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    from unimol_tools import MolPredict  # type: ignore

    model_dir = Path(args.model).expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(f"Model path not found: {model_dir}")

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input data not found: {in_path}")

    out_csv = Path(args.output).expanduser().resolve()
    ensure_parent_dir(out_csv)

    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("Prediction requires pandas.") from e

    if in_path.suffix.lower() == ".csv":
        df = pd.read_csv(in_path)
        smiles_col = str(args.smiles_col)
        if smiles_col not in df.columns:
            candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
            if candidates:
                smiles_col = candidates[0]
            else:
                raise ValueError(
                    f"SMILES column '{args.smiles_col}' not found in input CSV. Columns: {list(df.columns)}"
                )
        smiles_list = [str(x) for x in df[smiles_col].tolist()]
    elif in_path.suffix.lower() == ".smi":
        smiles_col = "smiles"
        smiles_list = read_smiles_from_smi(in_path)
        df = pd.DataFrame({smiles_col: smiles_list})
    else:
        raise ValueError("--input only supports .csv or .smi")

    valid_pairs, skipped = validate_smiles_with_idx(smiles_list)
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_csv.with_suffix(out_csv.suffix + ".skipped.csv")
    )
    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(
            f"[WARN] Found {len(skipped)} invalid/empty SMILES. Skipped and logged to: {skipped_path}"
        )

    if not valid_pairs:
        raise RuntimeError("No valid SMILES available (all parsing failed or empty).")

    valid_idxs = [i for i, _ in valid_pairs]
    valid_smiles = [s for _, s in valid_pairs]

    df_valid = df.iloc[valid_idxs].copy()
    df_valid[smiles_col] = valid_smiles
    predictor = MolPredict(load_model=str(model_dir))
    pred_input = df_valid[[smiles_col]]
    try:
        y_pred = predictor.predict(
            pred_input, save_path=None, metrics=str(args.metrics)
        )
    except ValueError as e:
        # Some unimol_tools versions reject DataFrame inputs in predict() despite
        # accepting CSV path strings. Fall back to a temporary CSV for compatibility.
        if "Unknown data type" not in str(e):
            raise
        import tempfile

        with tempfile.TemporaryDirectory(prefix="unimol_predict_") as td:
            tmp_csv = Path(td) / "predict_input.csv"
            pred_input.to_csv(tmp_csv, index=False)
            y_pred = predictor.predict(
                str(tmp_csv), save_path=None, metrics=str(args.metrics)
            )

    import numpy as np  # type: ignore

    # Standardize output to CSV: smiles + pred_* columns
    arr = np.asarray(y_pred)
    out_df = df_valid.copy()
    if arr.ndim == 1:
        out_df["pred"] = arr
    elif arr.ndim == 2 and arr.shape[1] == 1:
        out_df["pred"] = arr[:, 0]
    elif arr.ndim == 2:
        for j in range(arr.shape[1]):
            out_df[f"pred_{j}"] = arr[:, j]
    else:
        out_df["pred"] = arr.reshape(len(valid_smiles), -1)[:, 0]

    out_df.to_csv(out_csv, index=False)

    print(f"[RESULT] pred_csv={str(out_csv.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unimol_helper.py",
        description="General CLI wrapper for unimol-tools (repr/train/predict).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--no-env", action="store_true", help="Do not print environment detection info"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # repr
    pr = sub.add_parser(
        "repr", help="Extract molecular representations (embeddings), output as .npy"
    )
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--smiles", type=str, help="Single SMILES string input")
    g.add_argument("--file", type=str, help="Input file: .csv or .smi")
    pr.add_argument(
        "--smiles-col", type=str, default="smiles", help="SMILES column name in CSV"
    )
    pr.add_argument("--output", type=str, default=None, help="Output path for .npy")
    pr.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for representation extraction",
    )
    pr.add_argument("--use-gpu", action="store_true", help="Force GPU usage")
    pr.add_argument(
        "--no-gpu", action="store_true", help="Force CPU usage (disable GPU)"
    )
    pr.add_argument("--remove-hs", action="store_true", help="Remove explicit H atoms")
    pr.add_argument(
        "--error-log", type=str, default=None, help="Path to log bad SMILES as CSV"
    )
    pr.set_defaults(func=cmd_repr)

    # train
    pt = sub.add_parser("train", help="Train model, output model directory")
    pt.add_argument(
        "--task",
        type=str,
        required=True,
        choices=[
            "classification",
            "regression",
            "multilabel_classification",
            "multilabel_regression",
        ],
        help="Task type (including future-facing multilabel variants)",
    )
    pt.add_argument(
        "--input",
        type=str,
        required=True,
        help="Training CSV data (must contain smiles and target column(s))",
    )
    pt.add_argument(
        "--smiles-col", type=str, default="smiles", help="SMILES column name"
    )
    pt.add_argument(
        "--target-col", type=str, default="target", help="Target column name"
    )
    pt.add_argument(
        "--target-cols",
        type=str,
        default=None,
        help="Comma-separated target columns for multilabel tasks (e.g. target_0,target_1)",
    )
    pt.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    pt.add_argument(
        "--output", type=str, required=True, help="Output directory for model"
    )
    pt.add_argument("--batch-size", type=int, default=32, help="Batch size")
    pt.add_argument("--learning-rate", type=float, default=1e-4, help="Learning rate")
    pt.add_argument("--no-cuda", action="store_true", help="Force CPU usage")
    pt.add_argument(
        "--model-name",
        type=str,
        default="unimolv1",
        choices=["unimolv1", "unimolv2"],
        help="Model family",
    )
    pt.add_argument(
        "--model-size", type=str, default="84m", help="Model size for unimolv2"
    )
    pt.add_argument("--metrics", type=str, default="none", help="Evaluation metrics")
    pt.set_defaults(func=cmd_train)

    # predict
    pp = sub.add_parser("predict", help="Load model for inference, output as .csv")
    pp.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model directory or path (save_path from MolTrain)",
    )
    pp.add_argument("--input", type=str, required=True, help="Input data: .csv or .smi")
    pp.add_argument(
        "--smiles-col", type=str, default="smiles", help="SMILES column name in CSV"
    )
    pp.add_argument(
        "--output", type=str, required=True, help="Output path for prediction CSV"
    )
    pp.add_argument(
        "--metrics", type=str, default="none", help="Optional evaluation metrics"
    )
    pp.add_argument(
        "--error-log", type=str, default=None, help="Path to log bad SMILES as CSV"
    )
    pp.set_defaults(func=cmd_predict)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.no_env:
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
        if os.environ.get("UNIMOL_HELPER_TRACE", "").strip() in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }:
            _eprint(traceback.format_exc())
        raise SystemExit(2)
