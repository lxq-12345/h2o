# 文件名：history_param.py 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 作者：李小群，ChatGPT5.1
# 日期：2025年12月20日

import pandas as pd
from pathlib import Path
import math

# 计算项目根目录（scripts/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 通用工具
try:
    import utils as _ut
    print("    组件 utils OK.")
except ImportError:
    print("❌ 导入 utils 失败。请确保 utils.py 文件存在。")
    sys.exit(1)

# 读取预测结果文件。
def load_prediction_file_func(cfg):
    print(">> load_prediction_file_func()")
    return pd.read_csv(cfg["prediction_file"])

# 删除训练阶段遗留的滞后特征列。
def drop_lag_features_func(df, cfg):
    print(">> drop_lag_features_func()")
    cols = [c for c in cfg["lag_columns"] if c in df.columns]
    return df.drop(columns=cols)

# 按硬盘收敛，仅保留坏道增长的关键记录。
def converge_by_device_func(df, cfg):
    print(">> converge_by_device_func()")

    device_col = cfg["device_id"]
    date_col = cfg["date"]
    bad_col = cfg["bad_sectors"]

    kept = []

    for _, g in df.groupby(device_col):
        g = g.sort_values(date_col)
        prev_bad = None
        for _, row in g.iterrows():
            cur_bad = row[bad_col]
            if prev_bad is None or cur_bad > prev_bad:
                kept.append(row)
                prev_bad = cur_bad

    return pd.DataFrame(kept)

# 按业务阈值筛选有效坏道阶段。
def filter_by_business_threshold_func(df, cfg):
    print(">> filter_by_business_threshold_func()")
    return df[df[cfg["bad_sectors"]] >= cfg["min_bad_sectors"]]

# 按坏道值对全部硬盘预测结果进行统计。
def aggregate_by_bad_sectors_func(df, cfg):
    print(">> aggregate_by_bad_sectors_func()")

    bad_col = cfg["bad_sectors"]
    pred_col = cfg["predict"]

    rows = []
    for bad_val, g in df.groupby(bad_col):
        preds = g[pred_col].dropna()
        if preds.empty:
            continue

        mean_val = int(math.floor(preds.mean()))
        median_val = int(math.floor(preds.median()))

        # 关键规则：一旦预期为 0，立即退出统计
        if mean_val == 0 or median_val == 0:
            print(f"   stop at bad_sectors={bad_val}, predict=0")
            break

        rows.append({
            bad_col: bad_val,
            "predict_mean": mean_val,
            "predict_median": median_val
        })
    df_stats = pd.DataFrame(rows).sort_values(bad_col)

    # 打印汇总信息
    # 打印每个 bad_sectors 分组的统计结果
    print(f'  坏道距离坏道阈值 {cfg["fail_threshold_A"]} 预期天数历史表')
    print(f"",df_stats.to_string(index=False))
    print(f"  记录总数： {len(df_stats)}")
    return df_stats

# 保存统计结果到文件。
def save_statistics_result_func(df, cfg):
    print(">> save_statistics_result_func()")
    df.to_csv(cfg["output_path"], index=False)
    print(f'  历史表保存到{cfg["output_path"]}')

# 主流程控制。
def main_func(cfg):
    print(">> main_func()")
    df = load_prediction_file_func(cfg)
    df = drop_lag_features_func(df, cfg)
    df = converge_by_device_func(df, cfg)
    df = filter_by_business_threshold_func(df, cfg)
    df_stats = aggregate_by_bad_sectors_func(df, cfg)
    save_statistics_result_func(df_stats, cfg)
    return df_stats

if __name__ == "__main__":
    cfg = {
        "prediction_file": "../out/predictions_automl_20251218_A.csv",
        "output_path": "../out/bad_sector_stats.csv",
        "device_id": "device_id",
        "date": "date",
        "bad_sectors": "bad_sectors",
        "predict": "predict",
        "lag_columns": [
            "bad_sectors_lag5",
            "bad_sectors_lag7",
            "bad_sectors_lag9"
        ],
        "fail_threshold_A" : 34,
        "min_bad_sectors": 20
    }
    # 调用主控函数
    main_func(cfg)
