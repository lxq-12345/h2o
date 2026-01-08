# 程序名：gentrainsample.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
程序名：generate_train_samples_flex.py
功能：灵活识别硬盘监控样本字段，自动生成滞后特征及剩余寿命训练样本
"""
import pandas as pd
import configparser
import sys
import os
from sklearn.linear_model import LinearRegression
import numpy as np
import wcwidth
from typing import Dict, Any

try:
    import utils as _ut 
    print(f"    组件 utils OK")
except Exception as e:
    _ut = None
    print(f"⚠️ 未找到 util：{e}")

# ========== B方案：预测未来日期硬盘坏道数量 ==========
# B方案打印汇总。
def print_B_summary_func(df: pd.DataFrame, cfg: Dict[str, Any]):
    """
    B方案结果汇总打印函数。
    打印最终样本的关键信息：特征集、目标定义和样本数量。
    
    参数说明：
        df (pd.DataFrame): 最终生成的训练/测试样本DataFrame。
        cfg (Dict): 配置字典。
    """
    print("\n\n====================== 📈 B 方案样本汇总 (Target Value) ======================")
    
    # 1. 获取核心配置参数
    # lag_days_B 配置为列表，horizon_days_B 和 slope_window_B 配置为单整数
    lag_days = cfg["lag_days_B"]
    horizon_days = cfg["horizon_days_B"]
    slope_window = cfg["slope_window_B"]
    key_field = cfg["key_field"]
    target = cfg["target"]
    
    # 2. 统计样本数量
    total_samples = len(df)
    
    # 3. 筛选最终特征列 (排除 ID, Date, Target)
    id_cols = ['device_id', 'date']
    
    # 获取特征列：排除 ID, Date, Target
    feature_cols = [
        col for col in df.columns 
        if col not in id_cols and col != target
    ]
    
    # 4. 打印核心信息
    
    # 目标定义
    print(f"✅ 目标定义: 预测未来 {horizon_days} 天后的 **{key_field}** 值。")
    print(f"   目标标签: {target}")

    # 特征类型和数量
    print(f"\n🔬 特征集概览 ({len(feature_cols)} 个特征):")
    
    # 滞后特征 (Lag Features)
    lag_features_count = len([f for f in feature_cols if any(f.endswith(f'_lag{d}') for d in lag_days)])
    print(f"   - 滞后特征 (Lag Features): {lag_features_count} 个 (基于 {lag_days} 天)")

    # 增强特征 (Extended Features)
    extended_features_names = ['diff1', 'slope_recent']
    extended_features_count = len([f for f in feature_cols if f in extended_features_names])
    print(f"   - 增强特征 (Extended Features): {extended_features_count} 个")
    print(f"     ↳ (基于 {slope_window} 天滑动窗口计算 slope_recent)")

    # 5. 打印样本统计
    if target in df.columns:
        valid_samples = df[target].dropna().shape[0]
        missing_samples = total_samples - valid_samples
        
        print(f"\n📊 样本统计 (总记录数: {total_samples}):")
        print(f"   - **有效训练样本** (目标值非空): {valid_samples} 个")
        print(f"   - **待预测样本** (目标值缺失 <NA>): {missing_samples} 个 (每块硬盘最后 {horizon_days} 天)")
    else:
        # 测试模式下
        print(f"\n📊 样本统计 (总记录数: {total_samples}):")
        print("   - 处于测试模式，无目标值统计。")

    # 6. 打印特征列表 (简洁格式)
    print("\n📌 特征列表 (部分):")
    
    # 将特征列表按类型分组，便于阅读
    base_features = [f for f in feature_cols if not any(name in f for name in ['lag', 'diff', 'slope'])]
    lag_features = [f for f in feature_cols if 'lag' in f]
    extended_features = [f for f in feature_cols if any(name in f for name in ['diff', 'slope'])]
    
    def _print_list(title, items):
        if items:
            # 仅打印前5个特征，并标出总数
            print(f"   - {title} ({len(items)}): {', '.join(items[:5])}...")
    
    _print_list("基础特征", base_features)
    _print_list("增强特征", extended_features)
    _print_list("滞后特征", lag_features)
    
    print("======================================================================\n")

# B 方案函数 1: 目标特征生成 (已修正配置读取 Bug)
def add_B_target_feature_func(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    【B 方案目标生成】
    为每块硬盘的每一天，生成 horizon_n 天后的未来坏道数目标特征列。
    使用 shift(-N) 实现。    
    参数说明：
        df (pd.DataFrame) : 包含 'device_id', 'date', key_field 的 DataFrame。
        cfg (dict) : 配置字典，包含 'horizon_days_B' (单整数) 和 'target'。
    返回：
        新 DataFrame，增加目标特征列。
    """
    # BUG 修复：从 cfg 中直接获取 horizon_days_B 的整数值
    key_field = cfg["key_field"]
    device_id = cfg["device_id"]
    date = cfg["date"]
    horizon_n = cfg["horizon_days_B"] 
    target = cfg["target"]
    
    print(f"\n>> add_B_target_feature_func() (B方案目标生成)")
    print(f"   目标特征：{target} (即未来 {horizon_n} 天后的 {key_field} 值) .....")
    
    def _calc_target(group_df: pd.DataFrame) -> pd.DataFrame:
        """对每个硬盘组生成目标特征"""
        # 按照日期对当前硬盘的数据进行升序排序
        group_df = group_df.sort_values(date).reset_index(drop=True)
        
        # 核心逻辑：使用 shift(-horizon_n) 生成目标特征列。
        # shift(-N) 将 key_field 列向上平移 N 行（当前行的目标值是 N 天后的值）。
        # 由于数据末尾没有对应值，最后 N 行将自动填充 <NA>。
        group_df[target] = group_df[key_field].shift(-horizon_n)
        return group_df

    # 按 device_id 分组，并对每个组应用目标特征计算函数
    df_out = df.groupby(device_id, group_keys=False).apply(_calc_target)
    
    # 将目标列转换为 Pandas 可空整数类型 ('Int64')
    df_out[target] = df_out[target].astype('Int64')
    
    n_nan = df_out[target].isna().sum()
    print(f"   ✅ 目标特征生成完毕。总记录数：{len(df_out)}")
    print(f"   因前瞻天数不足被置为 <NA> 的样本数：{n_nan} (位于每块硬盘的最后 {horizon_n} 天)")
    return df_out

# B 方案函数 2: 增强特征生成
def add_extended_features_func(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    【B 方案特征增强 - 性能优化版】
    扩展特征工程，增加以下特征：
      - diff1:        最近一次坏道数差分
      - slope_recent: 近N天坏道增长斜率 (使用【滚动平均日增长量】近似替代)    
    参数说明：
        df (pd.DataFrame) : 输入的 DataFrame。
        cfg (dict) : 配置字典，包含 key_field 和 'slope_window_B' (单整数)。
    返回：
        新 DataFrame，增加 diff1 和 slope_recent 特征列。
    """
    print(f"\n>> add_extended_features_func() (B方案特征增强 - 性能优化版)")
    device_id = cfg["device_id"]
    date = cfg["date"]
    key_field = cfg["key_field"]    
    # 从配置中获取 slope_window_B 的整数值
    # slope_window_B 定义了计算短期恶化趋势（斜率）所回顾的历史天数。
    slope_window = cfg["slope_window_B"]    
    print(f"   使用的斜率计算窗口 (slope_window_B): {slope_window} 天")    
    def _calc_extended_features(group: pd.DataFrame) -> pd.DataFrame:
        """
        对每个硬盘组进行特征计算（完全矢量化）
        直接调用外部函数变量：date，key_field
        """
        group = group.sort_values(date).reset_index(drop=True)
        # 最近一次差分 (diff1)
        group["diff1"] = group[key_field].diff().fillna(0).astype('Int64')
        # 趋势特征：slope_recent (滚动平均日增长量近似斜率)
        daily_growth = group[key_field].diff()        
        # 计算过去 slope_window 天每日增长量的均值，捕捉短期恶化速率
        group["slope_recent"] = daily_growth.rolling(
            window=slope_window, 
            min_periods=1 
        ).mean()
        return group
    # 按 device_id 分组，并应用特征计算函数
    df_out = df.groupby(device_id, group_keys=False).apply(_calc_extended_features)
    df_out["slope_recent"] = df_out["slope_recent"].astype(float)
    print(f"   增强特征生成完毕。新增特征列: diff1, slope_recent")
    return df_out

# B 方案函数 3: 主流程函数 (已修正配置读取 Bug)
def build_B_func(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    B方案主流程函数：构建预测未来坏道数的时序样本。
    
    核心步骤：
    1. 生成【通用滞后特征】(lag_days)
    2. 生成【增强特征】(diff1, slope_recent)
    3. 生成【前瞻目标特征】(Target: horizon_days_B 天后的 key_field)
    
    参数说明：
        df (pd.DataFrame) : 原始输入数据。
        cfg (dict) : 包含 B 方案配置参数的字典。
    返回：
        最终可用于训练/预测的 DataFrame。
    """
    print(f"\n=======================================================")
    print(f">> build_B_func() (B方案样本制作主流程)")
    
    # 从配置中获取参数
    lag_days = cfg["lag_days_B"] 
    horizon_days_B_val = cfg["horizon_days_B"] 
    slope_window_B_val = cfg["slope_window_B"]
    target_col = cfg["target"] 

    print(f"   配置概览：")
    print(f"   目标：预测未来 {horizon_days_B_val} 天的坏道数")
    print(f"   特征：使用 {lag_days} 天滞后特征")
    print(f"   增强特征：使用 {slope_window_B_val} 天滚动窗口计算趋势（斜率）")
    
    # 生成滞后特征
    df = _ut.add_lag_features_func(df, lag_days, cfg)     
    # 扩展特征工程：新增 diff1 和 slope_recent
    df = add_extended_features_func(df, cfg)    
    # 生成目标特征 (仅在非测试模式下)
    if not cfg.get("if_test", False):
        df = add_B_target_feature_func(df, cfg)
    else:
        print("\n   [测试模式] 跳过目标特征生成。")
    print(f"\n   B 方案样本生成主流程完成。总记录数: {len(df)}")
    # 调整列顺序，将目标列移到最后（如果存在）
    if target_col in df.columns and df.columns.tolist()[-1] != target_col:
        cols = [col for col in df.columns if col != target_col] + [target_col]
        df = df[cols]        
    # 调用 B 方案汇总打印函数 (如果存在)
    if 'print_B_summary_func' in globals():
        print_B_summary_func(df, cfg)
    # 打印最终样本文件的前 5 个记录 (新增要求)
    print("\n\n📄 最终训练/预测样本 (前 5 条记录):")
    # 使用 to_string(index=False) 保持格式清晰
    print(df.head(5).to_string(index=False))
    return df
# ========== B方案：预测未来日期硬盘坏道数量结束 ==========

# ========== A方案：预测硬盘剩余寿命 ==========
# 为 A 方案生成目标特征 remaining_life_days
def add_A_target_feature_func(df, cfg):
    """
    按硬盘分组，为每块硬盘计算寿命天数，并为每条记录生成剩余寿命特征
    remaining_life_days。
    """
    print("\n>> add_A_target_feature_func()")
    # 目标特征项名字
    target = cfg["target"]
    device_id = cfg["device_id"]
    date = cfg["date"]
    fail_threshold = cfg["fail_threshold_A"]
    output_rows = []     
    # 遍历每一块硬盘（按 device_id 分组），group_df 是当前分组（hd_id）硬盘的全部记录， 
    # 这样能保证每块硬盘的寿命和剩余寿命都独立计算、互不影响
    for device_id, group_df in df.groupby(device_id):
        # 先按日期排序，保证计算顺序与时间一致 
        group_df = group_df.sort_values(by=date) 
        # 获取当前硬盘组的最小日期。 
        #start_date = group_df['date'].min() 
        # 获取硬盘不可用时的寿命天数。 
        life_days = _ut.get_hdd_life_days_func(group_df, device_id, cfg, fail_threshold)
        #print(f"   硬盘 {device_id}：启用日 = {start_date}, 寿命天数 = {life_days}")
        # 遍历当前硬盘组内的每一条记录，为每一天都计算并生成剩余寿命
        # itertuples() 返回 namedtuple，不是 Series。
        # namedtuple 用属性访问：row.POH、row.date；不能用 row["POH"]。
        # iterrows() 才会返回 Series（那时才能用 row["POH"]）。
        # 记忆要点：itertuples → row.POH；iterrows → row["POH"]。
        for row in group_df.itertuples(index=False):
            # 计算硬盘当前记录的使用累计天数（从启用日到当前日期的天数差） 
            used_days = _ut.get_hdd_used_days_func(row)
            #used_days2 = (row.date - start_date).days             
            #print(f"   used_days = {used_days}, used_days2 = {used_days2} ")
            # 计算当前记录的剩余寿命（寿命天数减去已用天数） 
            remaining = life_days - used_days 
            # 将当前记录转换为字典格式，便于后面添加新字段
            new_row = dict(row._asdict())
            # 新增target字段 remaining_life_days，赋值为刚计算的剩余寿命 
            new_row[target] = remaining 
            # 把带有剩余寿命的新记录加入输出列表 
            output_rows.append(new_row)
    # 将所有硬盘所有新记录的字典列表，合并生成新的 DataFrame，作为最终结果
    result_df = pd.DataFrame(output_rows)
    print("\n   [生成目标特征项列表(前5行数据)]")
    print(result_df.head(5))
    return result_df

# 为A方案生成趋势特征。
def add_trend_features_func(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """
    为每块硬盘生成趋势特征：
      - diff1, diff3, diff7
      - slope7: 7天线性回归斜率
      - rolling_mean7, rolling_std7
      - remaining_margin: 距离坏道阈值(34 - bad)
    """
    print("\n>> add_trend_features_func()")

    key = cfg["key_field"]
    fail_threshold_A = cfg["fail_threshold_A"]

    # 按硬盘分组，确保不同硬盘不会串
    def _calc_trend(group):
        # ==== diff 系列 ====
        group[f"{key}_diff1"] = group[key] - group[key].shift(1)
        group[f"{key}_diff3"] = group[key] - group[key].shift(3)
        group[f"{key}_diff7"] = group[key] - group[key].shift(7)

        # ==== rolling mean / std ====
        group[f"{key}_mean7"] = group[key].rolling(7, min_periods=1).mean()
        group[f"{key}_std7"]  = group[key].rolling(7, min_periods=1).std()

        # ==== slope7：7 日线性回归斜率 ====
        import numpy as np
        from sklearn.linear_model import LinearRegression

        slope_list = []
        arr = group[key].values.reshape(-1, 1)

        for i in range(len(group)):
            if i < 6:
                slope_list.append(np.nan)
                continue
            window = arr[i-6:i+1]  # 最近7天
            x = np.arange(7).reshape(-1, 1)
            model = LinearRegression().fit(x, window)
            slope_list.append(model.coef_[0][0])

        group[f"{key}_slope7"] = slope_list

        # ==== 距离阈值 margin ====
        group["remaining_margin"] = fail_threshold_A - group[key]

        return group

    df = df.groupby("device_id", group_keys=False).apply(_calc_trend)

    # 全部转成可空整数或浮点（自动）
    return df

# A方案主函数
def build_A_func(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """
    主流程：
    1. 生成滞后特征
    2. 生成增强特征   
    3. 生成目标特征（如剩余寿命标签）
       调整目标特征项顺序到最后一列
    4. 去除样本中的 POH 字段数据。
    """
    print(">> build_A_func()")
    lag_days = cfg["lag_days_A"]
    # 生成滞后特征
    df = _ut.add_lag_features_func(df, lag_days, cfg)
    # 趋势特征（新增）
    #df = add_trend_features_func(df, cfg)
    if not cfg["if_test"]:
        # 生成目标特征
        df = add_A_target_feature_func(df, cfg)
    return df
# ========== A方案：预测硬盘剩余寿命结束 ==========

# ========== 公共部分函数 =========
# 宽字符对齐函数（中文=2宽度）
def align(text, width):
    """
    用于在终端中对齐中英文混合字符。
    width：希望的可视宽度（英文=1，中文=2）
    """
    text = str(text)
    text_width = sum(wcwidth.wcwidth(c) for c in text)
    pad = width - text_width
    return text + " " * max(0, pad)

# 统计信息 注：本统计适合与硬盘坏道预测，如果更改其他指标预测，本函数将不适用。
def print_dataset_statistics_func(df: pd.DataFrame, cfg):
    """
    打印数据集统计信息（硬盘级别）并输出 CSV 到 out/ 目录。
    增强内容：
        - 宽字符对齐（align）
        - 波动率 5 档统计
        - 全局硬盘坏道统计（总数 / 最大坏道 / 平均 / 中位 / 占比）
        - 新增：月变化斜率、总体变化斜率
    """
    print(">> print_dataset_statistics_func()")

    static_path = cfg["static_path"]
    device_id_col = cfg["device_id"]
    date = cfg["date"]
    key_field = cfg["key_field"]

    print("\n==============================================")
    print("📊 数据集统计信息列表 (print_dataset_statistics_func)")
    print("==============================================")

    # 统计函数不负责清洗数据，date 必须已是 datetime
    if date not in df.columns:
        raise ValueError(f"缺少日期字段 {date}")
    if not pd.api.types.is_datetime64_any_dtype(df[date]):
        raise ValueError(f"{date} 字段不是 datetime 类型，请先执行 clean_and_normalize_func")

    os.makedirs(os.path.dirname(static_path), exist_ok=True)

    csv_rows = []
    fluctuations = []
    max_bad_list = []  # 用于整体坏道统计

    # ==========================
    # 新表头（使用 align，保持间距）
    # ==========================
    header = (
        align("硬盘ID", 8) +
        align("记录数", 8) +
        align("日期跨度", 20) +
        align("总天数", 8) +
        align("最大坏道数", 12) +
        align("平均月增", 10) +
        align("最大月增", 10) +
        align("波动率", 8) +
        align("月变化斜率", 12) +
        align("总体变化斜率", 12)
    )
    print(header)
    print("-" * len(header))

    # ==========================
    # 遍历每块硬盘
    # ==========================
    for did, group in df.groupby(device_id_col):

        group_sorted = group.sort_values(date)

        n_records = len(group_sorted)
        start_date = group_sorted[date].min()
        end_date = group_sorted[date].max()
        total_days = (end_date - start_date).days
        max_bad = group_sorted[key_field].max()
        max_bad_list.append(max_bad)

        # 月增长分析
        group_sorted = group_sorted.copy()
        group_sorted["month"] = group_sorted[date].dt.to_period("M")
        month_end = group_sorted.groupby("month")[key_field].last()
        month_growth = month_end.diff().dropna()

        if len(month_growth) > 0:
            avg_growth = month_growth.mean()
            max_growth_val = month_growth.max()
            min_growth_val = month_growth.min()
            fluctuation = ((max_growth_val - min_growth_val) / avg_growth) if avg_growth else np.nan

            # 月变化斜率
            month_days = (month_end.index[-1].end_time - month_end.index[0].start_time).days
            month_slope = (
                (month_end.iloc[-1] - month_end.iloc[0]) / month_days
                if month_days > 0 else np.nan
            )
        else:
            avg_growth = max_growth_val = fluctuation = month_slope = np.nan

        # 总体变化斜率
        total_slope = (
            (group_sorted[key_field].iloc[-1] - group_sorted[key_field].iloc[0]) / total_days
            if total_days > 0 else np.nan
        )

        if not np.isnan(fluctuation):
            fluctuations.append(fluctuation)

        # 打印单行
        print(
            align(did, 8) +
            align(n_records, 8) +
            align(f"{start_date.date()}~{end_date.date()}", 24) +
            align(total_days, 8) +
            align(max_bad, 12) +
            align(f"{avg_growth:.2f}", 10) +
            align(f"{max_growth_val:.2f}", 10) +
            align(f"{fluctuation:.2f}", 8) +
            align(f"{month_slope:.4f}", 12) +
            align(f"{total_slope:.4f}", 12)
        )

        # 写入 CSV
        csv_rows.append({
            "device_id": did,
            "records": n_records,
            "date_range": f"{start_date.date()}~{end_date.date()}",
            "total_days": total_days,
            "max_bad": max_bad,
            "avg_growth": round(avg_growth, 4) if not np.isnan(avg_growth) else "",
            "max_growth": round(max_growth_val, 4) if not np.isnan(max_growth_val) else "",
            "fluctuation": round(fluctuation, 4) if not np.isnan(fluctuation) else "",
            "month_slope": round(month_slope, 6) if not np.isnan(month_slope) else "",
            "total_slope": round(total_slope, 6) if not np.isnan(total_slope) else "",
        })

    # 写 CSV
    pd.DataFrame(csv_rows).to_csv(static_path, index=False, encoding="utf-8-sig")
    print("\n📁 已生成统计文件：", static_path)

    # ==========================
    # 全局硬盘坏道统计
    # ==========================
    print("\n--------------------------------------------")
    print("📊 硬盘整体坏道统计（基于全部硬盘）")

    max_bad_array = np.array(max_bad_list)
    total_hdd = len(max_bad_array)
    max_bad_global = int(max_bad_array.max())
    mean_bad = round(float(max_bad_array.mean()), 2)
    median_bad = float(np.median(max_bad_array))

    cnt_below = sum(max_bad_array <= median_bad)
    cnt_above = sum(max_bad_array > median_bad)

    print(f"\n硬盘总数：{total_hdd}")
    print(f"📌 全部硬盘最大坏道数：    {max_bad_global}")
    print(f"📌 全部硬盘最大坏道平均数：{mean_bad}")
    print(f"📌 全部硬盘最大坏道中位数：{median_bad}")

    print(f"\n📌 高于中位数的硬盘占比：  {cnt_above / total_hdd * 100:.1f}%  （{cnt_above} 块）")
    print(f"📌 低于等于中位数的硬盘占比：{cnt_below / total_hdd * 100:.1f}%  （{cnt_below} 块）")

    # ==========================
    # 波动率五档统计
    # ==========================
    print("\n--------------------------------------------")
    print("📊 波动率占比统计（基于全部硬盘）")

    total_f = len(fluctuations)

    def pct(cnt):
        return (cnt / total_f * 100) if total_f > 0 else 0.0

    cnt_a = sum(f < 0.2 for f in fluctuations)
    cnt_b = sum(0.2 <= f < 0.5 for f in fluctuations)
    cnt_c = sum(0.5 <= f < 1.0 for f in fluctuations)
    cnt_d = sum(1.0 <= f < 2.0 for f in fluctuations)
    cnt_e = sum(f >= 2.0 for f in fluctuations)

    print(f"\nA档 (0.0 - 0.2) ：{pct(cnt_a):.1f}%  （{cnt_a} 块） → 增长最稳定")
    print(f"B档 (0.2 - 0.5) ：{pct(cnt_b):.1f}%  （{cnt_b} 块） → 轻微波动")
    print(f"C档 (0.5 - 1.0) ：{pct(cnt_c):.1f}%  （{cnt_c} 块） → 中度波动")
    print(f"D档 (1.0 - 2.0) ：{pct(cnt_d):.1f}%  （{cnt_d} 块） → 明显非线性")
    print(f"E档 (>= 2.0)    ：{pct(cnt_e):.1f}%  （{cnt_e} 块） → 跳变强烈")

    print(f"\n📌 光滑硬盘占比：{pct(cnt_a):.1f}%  （{cnt_a} 块）")
    print(
        f"📌 非光滑硬盘占比：{pct(cnt_b + cnt_c + cnt_d + cnt_e):.1f}%  "
        f"（{cnt_b + cnt_c + cnt_d + cnt_e} 块）"
    )
    print("\n📌 注：波动率越低，坏道增长越平滑；波动率越高，坏道增长越不稳定。")
    print("--------------------------------------------\n")

# 定制输出文件名
def customize_file_path(cfg):
    # 判断输出是测试文件还是训练文件。
    mode = cfg["mode"]
    if cfg["if_test"]:
        filepath = cfg["test_sample_path"]
    else:
        filepath = cfg["train_sample_path"]
    # 将文件全路径分解为目录和文件
    dirpath, filename = os.path.split(filepath)
    # 将文件名分解为文件名与文件后缀
    name, ext = os.path.splitext(filename)
    # 在文件名中加入不同处理方案的后缀。
    file_name = f"{name}_{mode}{ext}"
    output_path = os.path.join(dirpath, file_name)
    # 输出定制好的文件全路径
    return output_path

# 保存新的数据项组成训练样本数据。
def save_output_func(df: pd.DataFrame, cfg):
    print("\n>> save_output_func()")
    date = cfg["date"]
    # 修正日期格式（保持为 datetime 类型）
    if date in df.columns:
        df[date] = pd.to_datetime(df[date], errors='coerce')
    # 定制输出文件名
    output_path = customize_file_path(cfg)
    # 保存前，格式化日期列为字符串（只用于输出）
    df_to_save = df.copy()
    if date in df_to_save.columns:
        df_to_save[date] = df_to_save[date].dt.strftime('%Y-%m-%d') 
    # 将数据保存到输出文件
    df_to_save.to_csv(output_path, index=False, na_rep='NaN')
    # 显示新文件的特性
    print(f"   [输出文件列结构]")
    print(f"   总列数：{len(df.columns)}")
    print(f"   列名称：{', '.join(df.columns)}")
    print(f"   [输出文件记录统计]")
    print(f"   记录数：{len(df)}")
    print(f"   [输出文件前5行数据]")
    preview = df_to_save.head().copy()  
    preview = preview.astype(object).where(pd.notnull(preview), 'NaN')
    print(preview.to_string(index=False))
    print(f"✅ 成功生成样本，输出文件：{output_path}\n")

# 加载基础样本文件。
def load_basedata_file_func(cfg):
    """
    从配置中指定的 input_path 中读取原始数据。
    返回按列提取、日期格式化、按硬盘与日期排序后的 DataFrame。
    """
    print(f"\n>> load_basedata_file_func()")    
    device_id = cfg["device_id"]
    date = cfg["date"]
    if cfg["if_test"]:
        input_path = cfg["raw_test_input_path"]
    else:
        input_path = cfg["raw_train_input_path"]
    print(f"   正在读取 {input_path} 文件数据......")
    # 读取文件（自动判断 Excel 或 CSV）
    if input_path.lower().endswith(".xlsx") or input_path.lower().endswith(".xls"):
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)
    # 日期字段转为 datetime
    if date in df.columns:
        df[date] = pd.to_datetime(df[date], errors="coerce")
    # 排序
    if device_id in df.columns:
        df = df.sort_values(by=[device_id, date])
    else:
        df = df.sort_values(by=[date])
    df = df.reset_index(drop=True)
    # 打印输出输入文件信息 
    print(f"\n   [输入文件列结构]")
    print(f"   总列数：{len(df.columns)}")
    print(f"   列名称：{', '.join(df.columns)}")
    print(f"   [输入文件记录统计]")
    print(f"   总记录数：{len(df)}")
    print(f"   空值统计：\n{df.isnull().sum()}")
    print(f"   [打印文件前5行数据]")
    print(df.head(5).to_string(index=False)) 
    print(f"\n   数据读取完毕")
    return df

# 分析与清理原始样本数据。
def clean_raw_sample_func(cfg):
    print(f"\n>> clean_raw_sample_func()") 
    trend_feature = cfg["trend_feature"]
    key_field = cfg["key_field"]
    # 读取基础样本数据文件
    df = load_basedata_file_func(cfg)
    # 清洗数据。
    df = _ut.clean_and_normalize_func(df, cfg)
    if trend_feature == 0:
        print(f"   单调型增长样本数据")
        if key_field == "bad_sectors":
            # 统计。
            print_dataset_statistics_func(df, cfg) 
    else:
        print(f"   波动趋势样本数据，数据特征统计打印未开发！ TBD")
        pass
    return df

# 生成训练样本或测试样本。
def gen_samples_func(df, cfg):
    print(">> gen_samples_func()  ")
    if not cfg["if_test"]:
        input(f"  ..... 继续生成训练样本数据 ..... 单击回车键继续")
    else:
        input(f"  ..... 继续生成测试样本数据 ..... 单击回车键继续")
    # 执行样本生成方案。
    if "A" in cfg["mode"]:
        # 调用 A 方案，预测硬盘剩余寿命。
        df_final = build_A_func(df, cfg)
    elif "B" in cfg["mode"]:
        # 调用 B 方案，预测几天后天硬盘坏道数量为 N 。
        df_final = build_B_func(df, cfg)
    elif "C" in cfg["mode"]:
        # 调用 C 方案，预测硬盘从当日开始达到指定坏道数需要几天。
        df_final = build_C_func(df, cfg)
    else:
        pass # 待扩展。
    # 删除样本列表中的 POH 字段数据，它在训练样本中，严重影响训练效果。      
    if "POH" in df_final.columns:
        df_final = df_final.drop(columns=["POH"])
    # 调用保存新的数据项组成训练样本数据。
    save_output_func(df_final, cfg)        
# ========== 公共部分函数结束 =========

# 组件标准接口
def run_func(cfg): 
    print(">> run_func()  ")
    try:
        if cfg["if_test"] == "": 
            cfg['if_test'] = False
            # 分析与清理原始训练样本数据。
            df = clean_raw_sample_func(cfg)    
            # 生成训练样本。
            gen_samples_func(df, cfg)
            cfg['if_test'] = True
            # 分析与清理原始测试样本数据。
            df = clean_raw_sample_func(cfg)    
            # 生成测试样本。
            gen_samples_func(df, cfg) 
            # 恢复原状。 
            cfg['if_test'] = ""
        elif cfg["if_test"] == False:
            # 分析与清理原始训练样本数据。
            df = clean_raw_sample_func(cfg)    
            # 生成训练样本。
            gen_samples_func(df, cfg)
        elif cfg["if_test"] == True:
            # 分析与清理原始测试样本数据。
            df = clean_raw_sample_func(cfg)    
            # 生成测试样本。
            gen_samples_func(df, cfg)                     
        return True 
    except Exception as e:
        # 捕获整个流程中的任何异常
        print(f"❌ 样本制作流程中发生严重错误，已中断：{e}")
        return False

# 主函数功能
def main_func():
    print(">> main_func()")
    # 读入配置文件
    cfg = _ut.load_config_func()
    # 读取基础样本数据文件
    df = load_basedata_file_func(cfg)
    # 清洗数据。
    df = _ut.clean_and_normalize_func(df, cfg)
    # 统计。
    print_dataset_statistics_func(df, cfg)
    if not cfg["if_test"]:
        input(f"  ..... 继续生成训练样本数据 ..... 单击回车键继续")
    else:
        input(f"  ..... 继续生成测试样本数据 ..... 单击回车键继续")
    # 执行样本生成方案。
    if "A" in cfg["mode"]:
        # 调用 A 方案，预测硬盘剩余寿命。
        df_final = build_A_func(df, cfg)
    elif "B" in cfg["mode"]:
        # 调用 B 方案，预测几天后天硬盘坏道数量为 N 。
        df_final = build_B_func(df, cfg)
    else:
        pass # 待扩展。
    # 删除样本列表中的 POH 字段数据，它在训练样本中，严重影响训练效果。      
    if "POH" in df_final.columns:
        df_final = df_final.drop(columns=["POH"])
    # 调用保存新的数据项组成训练样本数据。
    save_output_func(df_final, cfg)
# 重新入口。
if __name__ == '__main__':
    main_func()
