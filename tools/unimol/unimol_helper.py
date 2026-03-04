#!/usr/bin/env python
"""
unimol_helper.py

一个极简但健壮的 unimol-tools 标准化 CLI 封装：

- repr    : 提取分子表征（输出 .npy）
- train   : 训练模型（输出模型目录）
- predict : 性质预测（输出 .csv）

设计目标：配合 `uv run` 以单行命令完成常见分子 ML 任务，并在结束时打印结果文件/目录的绝对路径。
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


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
    print("======== unimol_helper 环境探测 ========", flush=True)
    print(f"python          : {env['python']}", flush=True)
    print(f"executable      : {env['executable']}", flush=True)
    print(f"cwd             : {env['cwd']}", flush=True)
    print(f"torch           : {env['torch']}", flush=True)
    print(f"cuda_available  : {env['cuda_available']}", flush=True)
    print(f"cuda_device_cnt : {env['cuda_device_count']}", flush=True)
    if env["cuda_devices"]:
        for i, n in enumerate(env["cuda_devices"]):
            print(f"cuda_device[{i}] : {n}", flush=True)
    print("=======================================", flush=True)


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
    用 RDKit 做语法级校验。若 RDKit 不可用，则仅做简单空串过滤，并将其余交由 unimol_tools；
    但为了满足“坏 SMILES 不崩溃”，repr/predict 会在 unimol_tools 抛错时自动降级到逐条隔离。
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


def validate_smiles_with_idx(smiles: Sequence[str]) -> Tuple[List[Tuple[int, str]], List[SmilesRecord]]:
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
            # 常见 .smi 格式: "SMILES[ whitespace ]NAME"
            token = line.split()[0]
            smiles.append(token)
    return smiles


def read_smiles_from_csv(path: Path, smiles_col: str) -> List[str]:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "读取 .csv 需要 pandas。请在隔离环境中安装 pandas 后重试。"
        ) from e
    df = pd.read_csv(path)
    if smiles_col not in df.columns:
        # 兜底：允许常见大小写
        candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
        if candidates:
            smiles_col = candidates[0]
        else:
            raise ValueError(
                f"CSV 中不存在 smiles 列 '{smiles_col}'，实际列名: {list(df.columns)}"
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
            raise FileNotFoundError(f"输入文件不存在: {in_path}")
        if in_path.suffix.lower() == ".smi":
            raw_smiles = read_smiles_from_smi(in_path)
        elif in_path.suffix.lower() == ".csv":
            raw_smiles = read_smiles_from_csv(in_path, args.smiles_col)
        else:
            raise ValueError("--file 仅支持 .csv 或 .smi")

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
        _eprint(f"[WARN] 发现 {len(skipped)} 条非法/空 SMILES，已跳过并记录到: {skipped_path}")

    if not valid_pairs:
        raise RuntimeError("没有可用的有效 SMILES（全部解析失败或为空）。")

    env = detect_env()
    if args.no_gpu:
        use_gpu = False
    elif args.use_gpu:
        use_gpu = True
    else:
        use_gpu = bool(env.get("cuda_available"))
    if use_gpu and not env.get("cuda_available"):
        _eprint("[WARN] 当前环境未检测到可用 CUDA，已自动回退到 CPU。")
        use_gpu = False

    repr_model = UniMolRepr(data_type="molecule", remove_hs=bool(args.remove_hs), use_gpu=use_gpu)

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
            # 降级：逐条隔离，保证“坏 SMILES 不崩溃”
            out: List[np.ndarray] = []
            for orig_idx, s in pairs:
                try:
                    d1 = repr_model.get_repr([s])
                    cls1 = d1.get("cls_repr", [])
                    if not cls1:
                        raise RuntimeError("empty_cls_repr")
                    out.append(np.asarray(cls1[0], dtype=np.float32))
                except Exception as e:
                    skipped.append(SmilesRecord(orig_idx, s, f"unimol_repr_failed:{type(e).__name__}:{e}"))
            return out

    for i in range(0, len(valid_pairs), batch):
        chunk = valid_pairs[i : i + batch]
        embs.extend(safe_get_batch(chunk))

    if len(embs) == 0:
        raise RuntimeError("表征提取失败：没有得到任何 embedding。")

    arr = np.stack(embs, axis=0).astype(np.float32, copy=False)
    ensure_parent_dir(out_path)
    np.save(out_path, arr)

    # 若在 unimol_tools 阶段也有跳过，补写一次日志
    if skipped:
        # idx 为原始输入的行号（--smiles 场景 idx=0）
        write_skipped_csv(skipped_path, skipped)

    print(f"[RESULT] repr_npy={str(out_path.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    from unimol_tools import MolTrain  # type: ignore

    data_path = Path(args.input).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"训练数据不存在: {data_path}")
    if data_path.suffix.lower() != ".csv":
        raise ValueError("--input 目前仅支持 .csv（包含 smiles 与 target 列）")

    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 简单预检查列名，避免 unimol_tools 内部报错不易定位
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("训练需要 pandas 读取 CSV。") from e

    df = pd.read_csv(data_path)
    if args.smiles_col not in df.columns:
        raise ValueError(
            f"训练 CSV 中不存在 SMILES 列 '{args.smiles_col}'，实际列名: {list(df.columns)}"
        )
    if args.target_col not in df.columns:
        raise ValueError(
            f"训练 CSV 中不存在 target 列 '{args.target_col}'，实际列名: {list(df.columns)}"
        )

    env = detect_env()
    use_cuda = (not bool(args.no_cuda)) and bool(env.get("cuda_available"))
    if (not args.no_cuda) and (not env.get("cuda_available")):
        _eprint("[WARN] 未检测到可用 CUDA，训练将使用 CPU。")

    trainer = MolTrain(
        task=str(args.task),
        data_type="molecule",
        epochs=int(args.epochs),
        learning_rate=float(args.learning_rate),
        batch_size=int(args.batch_size),
        save_path=str(out_dir),
        smiles_col=str(args.smiles_col),
        target_cols=[str(args.target_col)],
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
        raise FileNotFoundError(f"模型路径不存在: {model_dir}")

    in_path = Path(args.input).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"输入数据不存在: {in_path}")

    out_csv = Path(args.output).expanduser().resolve()
    ensure_parent_dir(out_csv)

    # 读取为 DataFrame，做 SMILES 校验与过滤，避免 unimol_tools 因坏 SMILES 直接崩溃
    try:
        import pandas as pd  # type: ignore
    except Exception as e:
        raise RuntimeError("predict 需要 pandas。") from e

    if in_path.suffix.lower() == ".csv":
        df = pd.read_csv(in_path)
        smiles_col = str(args.smiles_col)
        if smiles_col not in df.columns:
            candidates = [c for c in df.columns if c.lower() == smiles_col.lower()]
            if candidates:
                smiles_col = candidates[0]
            else:
                raise ValueError(
                    f"输入 CSV 中不存在 smiles 列 '{args.smiles_col}'，实际列名: {list(df.columns)}"
                )
        smiles_list = [str(x) for x in df[smiles_col].tolist()]
    elif in_path.suffix.lower() == ".smi":
        smiles_col = "smiles"
        smiles_list = read_smiles_from_smi(in_path)
        df = pd.DataFrame({smiles_col: smiles_list})
    else:
        raise ValueError("--input 仅支持 .csv 或 .smi")

    valid_pairs, skipped = validate_smiles_with_idx(smiles_list)
    skipped_path = (
        Path(args.error_log).expanduser().resolve()
        if args.error_log
        else out_csv.with_suffix(out_csv.suffix + ".skipped.csv")
    )
    if skipped:
        write_skipped_csv(skipped_path, skipped)
        _eprint(f"[WARN] 发现 {len(skipped)} 条非法/空 SMILES，已跳过并记录到: {skipped_path}")

    if not valid_pairs:
        raise RuntimeError("没有可用的有效 SMILES（全部解析失败或为空）。")

    valid_idxs = [i for i, _ in valid_pairs]
    valid_smiles = [s for _, s in valid_pairs]
    # 保留原始 CSV 的其它列（若有），便于下游 agent 对齐样本；.smi 场景下 df 只有 smiles 列
    df_valid = df.iloc[valid_idxs].copy()
    df_valid[smiles_col] = valid_smiles
    predictor = MolPredict(load_model=str(model_dir))
    y_pred = predictor.predict(df_valid[[smiles_col]], save_path=None, metrics=str(args.metrics))

    import numpy as np  # type: ignore

    # 统一输出为 CSV：smiles + pred_* 列
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
        # 极端情况：让 numpy 展平成 1 列
        out_df["pred"] = arr.reshape(len(valid_smiles), -1)[:, 0]

    out_df.to_csv(out_csv, index=False)

    print(f"[RESULT] pred_csv={str(out_csv.resolve())}")
    if skipped:
        print(f"[RESULT] skipped_csv={str(skipped_path.resolve())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unimol_helper.py",
        description="unimol-tools 的通用 CLI 封装（repr/train/predict）。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # 环境探测：按需求默认打印（便于 agent 判断是否启用 GPU）
    p.add_argument("--no-env", action="store_true", help="不打印环境探测信息（默认会打印）")
    sub = p.add_subparsers(dest="cmd", required=True)

    # repr
    pr = sub.add_parser("repr", help="提取分子表征（embedding），输出 .npy")
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--smiles", type=str, help="单个 SMILES 字符串输入")
    g.add_argument("--file", type=str, help="输入文件：.csv 或 .smi")
    pr.add_argument("--smiles-col", type=str, default="smiles", help="CSV 中 SMILES 列名")
    pr.add_argument("--output", type=str, default=None, help="输出 .npy 路径")
    pr.add_argument("--batch-size", type=int, default=64, help="表征提取 batch size")
    pr.add_argument("--use-gpu", action="store_true", help="强制启用 GPU")
    pr.add_argument("--no-gpu", action="store_true", help="强制使用 CPU（禁用 GPU）")
    pr.add_argument("--remove-hs", action="store_true", help="移除显式 H（传给 unimol_tools）")
    pr.add_argument("--error-log", type=str, default=None, help="坏 SMILES 记录 CSV 路径")
    pr.set_defaults(func=cmd_repr)

    # train
    pt = sub.add_parser("train", help="训练模型，输出模型目录")
    pt.add_argument("--task", type=str, required=True, choices=["classification", "regression"], help="任务类型")
    pt.add_argument("--input", type=str, required=True, help="训练数据 CSV（需包含 smiles 与 target 列）")
    pt.add_argument("--smiles-col", type=str, default="smiles", help="SMILES 列名")
    pt.add_argument("--target-col", type=str, default="target", help="target 列名")
    pt.add_argument("--epochs", type=int, default=100, help="训练轮数")
    pt.add_argument("--output", type=str, required=True, help="输出模型目录")
    pt.add_argument("--batch-size", type=int, default=32, help="batch size")
    pt.add_argument("--learning-rate", type=float, default=1e-4, help="学习率")
    pt.add_argument("--no-cuda", action="store_true", help="强制使用 CPU")
    pt.add_argument("--model-name", type=str, default="unimolv1", choices=["unimolv1", "unimolv2"], help="模型族")
    pt.add_argument("--model-size", type=str, default="84m", help="unimolv2 模型大小")
    pt.add_argument("--metrics", type=str, default="none", help="评估指标（传给 unimol_tools）")
    pt.set_defaults(func=cmd_train)

    # predict
    pp = sub.add_parser("predict", help="加载模型进行推理，输出 .csv")
    pp.add_argument("--model", type=str, required=True, help="模型目录或模型路径（MolTrain 的 save_path）")
    pp.add_argument("--input", type=str, required=True, help="输入数据：.csv 或 .smi")
    pp.add_argument("--smiles-col", type=str, default="smiles", help="CSV 中 SMILES 列名")
    pp.add_argument("--output", type=str, required=True, help="输出预测 CSV 路径")
    pp.add_argument("--metrics", type=str, default="none", help="评估指标（可选）")
    pp.add_argument("--error-log", type=str, default=None, help="坏 SMILES 记录 CSV 路径")
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
        # 需要可定位时，打开环境变量 UNIMOL_HELPER_TRACE=1
        if os.environ.get("UNIMOL_HELPER_TRACE", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
            _eprint(traceback.format_exc())
        raise SystemExit(2)

