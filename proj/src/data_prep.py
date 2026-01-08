# 程序名：data_prep.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Excel ➜ CSV 转换脚本（支持自定义字段抽取、自定义表头行数、统计报告）
# 作者：李小群，ChatGPT4.2/5.2
# 日期：2025年12月20日


import pandas as pd
from pathlib import Path
import sys
import os
import configparser

# ========== 软件项目环境目录 ==========
# 计算项目根目录（scripts/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
print(f">> PROJECT_ROOT = {PROJECT_ROOT}")
# 组装 src 目录路径
SRC_DIR = PROJECT_ROOT / "src"
print(f">> SRC_DIR = {SRC_DIR}")
# 将 src 目录加入模块搜索路径（若尚未加入）
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
# 将项目根目录加入模块搜索路径（若尚未加入）
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# ========== End of 软件项目环境目录 ==========

# CWD 切换至 h2o 根路径下
os.chdir(PROJECT_ROOT)
current_path = os.getcwd()
print(f">> 当前工作目录: {current_path}")

# ========== 配置区（可自定义输出列） ==========
HEADER_ROW = 1
SELECTED_FIELDS = ['device_id', 'date', 'bad_sectors', 'remapped_sectors']

# 打印 df 文件内容。
def print_df_structure(df: pd.DataFrame):
    print("\n========== 最终输出文件结构 ==========")
    print(f"记录数：{len(df)}")
    print(f"列数：{len(df.columns)}")
    print(f"列名：{', '.join(df.columns)}")

    print("\n[前 5 行数据]")
    print(df.head().to_string(index=False))

    print("=====================================")

# 排序功函数 
def sort_func(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n>> sort_func(...)")
    """
        对DataFrame按 device_id 升序、date 升序排序, 并重置索引
    """
    print(f"文件硬盘ID+时间排序处理")  
    df_sorted = df.sort_values(
        by=['device_id', 'date'],
        ascending=[True, True],
        na_position='last'
    ).reset_index(drop=True)
    return df_sorted

# 根据日期生成 power-on hours (POH) 字段。
def insert_poh_after_date_func(df: pd.DataFrame) -> pd.DataFrame:
    """
    添加 POH（power-on hours）字段，并且保证 POH 紧跟在 date 字段之后。
    """
    # 计算 POH（先确保日期排序）
    df = df.sort_values("date")
    df["POH"] = (df["date"] - df["date"].min()).dt.days * 24
    # 重新排列列顺序：date 后面是 POH
    cols = df.columns.tolist()
    if "date" in cols and "POH" in cols:
        date_index = cols.index("date")
        # 先去掉 POH，再插入 date 后面
        cols.remove("POH")
        cols.insert(date_index + 1, "POH")
    return df[cols]

# excel格式文件转换成csv格式文件函数
def excel_to_csv_func(input_file: str) -> None:
    print(f"\n>> excel_to_csv_func(...)")
    """
        读入excel文件转换成CSV数据。
    """
    try:
        input_path = os.path.abspath(input_file)
        print(f"\n{'='*10} 输入文件分析 {'='*10}")
        print(f"输入文件路径：{input_path}")
        # 1. 读取Excel
        df_raw = pd.read_excel(
            input_file,
            header=HEADER_ROW-1,
            dtype=str,
            engine='openpyxl'
        )
        print("\n[输入文件列结构]")
        print(f"总列数：{len(df_raw.columns)}")
        print(f"列名称：{', '.join(df_raw.columns)}")
        print(f"\n[输入文件记录统计]")
        print(f"总记录数：{df_raw.shape[0]}")
        print(f"空行检测：{df_raw.isnull().all(axis=1).sum()}")
        print("\n[列数据类型]")
        print(df_raw.dtypes.to_string())
        # 2. 强制转换日期列
        df_raw['date'] = pd.to_datetime(df_raw['date'], errors='coerce')
        # 3. 调用排序函数
        df_raw = sort_func(df_raw)
        print("\n[输入文件前5行数据]")
        print(df_raw.head().to_string(index=False))
        # 4. 返回df_raw
        return df_raw
    except Exception as e:
        sys.stderr.write(f"\n{'='*10} 错误追踪 {'='*10}")
        sys.stderr.write(f"\n❌ 错误类型：{type(e).__name__}")
        sys.stderr.write(f"\n❌ 错误详情：{str(e)}\n")
        return pd.DataFrame()

# 清洗单个硬盘数据 
def clean_one_disk_func(g: pd.DataFrame) -> pd.DataFrame:
    """
    对单块硬盘的数据进行清洗处理：
    - 去重（每个日期保留最后一条）
    - 时间序列补全（reindex）
    - 前向填充（ffill）
    - 自动恢复所有字段，并将整型数值列强制转为 int 类型（避免小数点）
    """
    #print(f"\n>> clean_one_disk_func(...)")
    try:
        #print(f"\n{'='*10} 清洗文件：去重与补全 {'='*10}")
        device_id = g.name  # 获取硬盘编号（groupby 分组的 key）
        original_df = g.sort_values('date')  # 按日期排序，确保后续逻辑有序
        # 1. 去重记录打印
        duplicate_dates = (  # 找出哪些日期在原始数据中重复出现
            original_df[original_df.duplicated(subset='date', keep='last')]['date']
            .dropna()
            .unique()
            .tolist()
        )
        if duplicate_dates:
            print(f"\n [去重记录] 硬盘 {device_id} 存在重复日期 {len(duplicate_dates)} 个：")
            for d in duplicate_dates[:10]:  # 最多打印前10个重复日期详情
                dup_rows = original_df[original_df['date'] == d]  # 获取重复行
                print(f"  - 日期 {d} 有 {len(dup_rows)} 条记录，保留最后一条，丢弃 {len(dup_rows)-1} 条")
        else:
            #print(f"\n [去重记录] 硬盘 {device_id} 没有重复日期")
            pass
        # 2. 去重 & 设置 index
        df_dedup = original_df.drop_duplicates(subset='date', keep='last').set_index('date')  # 每天保留最后一条，设置日期为索引
        # 3. 保存字段名
        value_columns = [col for col in df_dedup.columns if col != 'device_id']  # 除 device_id 外，保留所有原始字段名
        # 4. 补全日期
        date_range = pd.date_range(  # 创建从最早到最晚的完整日期序列
            start=df_dedup.index.min().floor('D'),
            end=df_dedup.index.max().ceil('D'),
            freq='D'
        )
        completed_df = df_dedup.reindex(date_range)  # 对日期进行补全，缺失日期填 NaN
        # 5. 补全信息打印
        filled_dates = sorted(set(date_range) - set(df_dedup.index))  # 找出补全的那些日期
        if filled_dates:
            print(f"\n [补全记录] 硬盘 {device_id} 补全缺失日期 {len(filled_dates)} 个：")
            for d in filled_dates[:10]:  # 最多打印前10个补全日期
                print(f"  - 补全日期：{d.date()}")
        else:
            #print(f"\n [补全记录] 硬盘 {device_id} 无需补全，日期连续完整")
            pass
        # 6. 填充 + 恢复列结构
        processed = (
            completed_df
            .ffill()  # 前向填充空值
            .reset_index()  # 恢复日期索引为普通列
            .rename(columns={'index': 'date'})  # 将 index 列名改回 date
        )
        # 7. 插入 device_id 列
        if 'device_id' not in processed.columns:
            processed.insert(0, 'device_id', device_id)  # 插入 device_id 列作为第一列
        # 8. 强制整型转换
        for col in value_columns:  # 遍历所有指标字段
            if pd.api.types.is_numeric_dtype(processed[col]):  # 是数值型列
                if processed[col].isnull().sum() == 0:  # 且无缺失值
                    processed[col] = processed[col].astype(int)  # 转换为 int（去掉小数点）
        # 9. 返回最终结果
        return processed[['device_id', 'date'] + value_columns]  # 保证列顺序固定且完整
    except Exception as e:
        sys.stderr.write(f"\n❌ 清洗失败 device_id={g.name}: {str(e)}\n")  # 报错打印硬盘编号
        return pd.DataFrame()  # 返回空数据，防止程序崩溃

# 清洗多个硬盘数据
def clean_all_disks_func(df: pd.DataFrame) -> pd.DataFrame:
    """
    清洗多个硬盘，只返回 df_clean，不写文件。
    """
    print(f"\n>> clean_all_disks_func(...)")

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    df_clean = df.groupby('device_id', group_keys=False).apply(
        clean_one_disk_func,
        include_groups=False
    )

    print("\n[清洗后前5行]")
    print(df_clean.head().to_string(index=False))

    return df_clean

# 字段抽取与输出新文件函数
def extract_data_func(df_raw: pd.DataFrame, selected_fields: list[str]) -> pd.DataFrame:
    print("\n>> extract_data_func(...)")

    # 1. 字段校验
    missing = [col for col in selected_fields if col not in df_raw.columns]
    if missing:
        raise ValueError(f"❌ 缺失字段：{missing}")
    # 2. 抽取字段
    df_extract = df_raw[selected_fields].copy()
    # 3. 数值字段转换
    numeric_cols = df_extract.apply(lambda x: pd.to_numeric(x, errors='coerce').notnull().all())
    numeric_cols = numeric_cols[numeric_cols].index.tolist()
    if numeric_cols:
        df_extract[numeric_cols] = df_extract[numeric_cols].apply(pd.to_numeric, errors='coerce')
    # 4. 日期字段转换
    if 'date' in df_extract.columns:
        df_extract['date'] = pd.to_datetime(df_extract['date'], errors='coerce')
        # 保持 bad_sectors 在最后
        cols = [c for c in df_extract.columns if c != 'bad_sectors'] + ['bad_sectors']
        df_extract = df_extract[cols]
    # 输出结构信息（不写文件）
    print(f"\n[抽取后列结构] 列数：{len(df_extract.columns)}")
    print(f"列名：{', '.join(df_extract.columns)}")
    print(f"\n[抽取后前5行数据]")
    print(df_extract.head().to_string(index=False))
    return df_extract

# 保存最终清洗后文件
def save_file_conf(df_clean: pd.DataFrame, cfg: dict) -> None:
    """
    保存最终清洗后文件到 cfg['output_file']。
    只负责存盘，不做数据处理。
    """
    print("\n>> save_file_conf(...)")

    output_file = cfg["output_file"]

    if df_clean is None or df_clean.empty:
        sys.stderr.write("\n❌ save_file_conf：df_clean 为空，未保存文件\n")
        return

    try:
        # 保存为 CSV UTF-8 带 BOM
        df_clean.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d",
            float_format="%.0f"
        )

        print(f"\n💾 文件已成功保存：{os.path.abspath(output_file)}")
        print(f"📏 记录数：{len(df_clean)}")
        print(f"📄 列数：{len(df_clean.columns)}")
        print(f"📚 列名：{', '.join(df_clean.columns)}\n")

    except Exception as e:
        sys.stderr.write(f"\n❌ 保存文件失败：{e}\n")

# 文件处理
def df_proc_file_func(df_raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    print("\n>> df_proc_file_func(...)")

    enable_poh = cfg.get("poh", 0)

    # ========== 情况③：只加 POH，不做任何清洗/抽取 ==========
    if enable_poh == 2:
        print("🔶 模式：仅添加 POH，不进行抽取和清洗")
        df_raw = df_raw.sort_values("date")
        df_raw = insert_poh_after_date_func(df_raw)
        return df_raw

    # ========== 正常流程 ==========
    # 抽取字段
    df_extract = extract_data_func(df_raw, cfg["selected_fields"])

    # 清洗硬盘序列
    df_clean = clean_all_disks_func(df_extract)

    # ========== 情况②：在清洗后添加 POH ==========
    if enable_poh == 1:
        print("🔵 模式：清洗后添加 POH 字段")
        df_clean = (
            df_clean
            .groupby("device_id", group_keys=False)
            .apply(lambda g: insert_poh_after_date_func(g.copy()))
        )
    return df_clean

# 加载原始训练/测试样本文件
def load_sample_file_func(cfg: dict) -> pd.DataFrame:
    """
    加载原始训练/测试样本文件：
        - 自动识别 CSV / Excel
        - 统一输出文件基本信息
        - 返回 DataFrame (df_raw)
    """
    print("\n>> load_sample_file_func(...)")

    input_file = cfg["input_file"]
    ext = os.path.splitext(input_file)[1].lower()

    print(f"📄 输入文件：{input_file}")
    print(f"📦 文件类型：{ext}")

    # ========== CSV ==========
    if ext == ".csv":
        df_raw = pd.read_csv(input_file)

        print(f"\n{'='*10} 输入文件分析 {'='*10}")
        print(f"记录数：{len(df_raw)}")
        print(f"列数：{len(df_raw.columns)}")
        print(f"列名：{', '.join(df_raw.columns)}")

        # 日期字段类型识别
        if "date" in df_raw.columns:
            df_raw["date"] = pd.to_datetime(df_raw["date"], errors="coerce")

        print("\n[前5行数据]")
        print(df_raw.head().to_string(index=False))

        return df_raw

    # ========== Excel ==========
    elif ext in [".xlsx", ".xls"]:
        print("📘 检测为 Excel 文件，调用 excel_to_csv_func(...) 进行读取与预处理")
        df_raw = excel_to_csv_func(input_file)
        return df_raw

    # ========== Unsupported ==========
    else:
        print(f"❌ 不支持的文件格式：{ext}")
        sys.exit(1)

# 读取配置文件
def load_config_func(config_path: str = 'config/datapreproc.ini') -> dict:
    print(">> load_config_func(...)")

    config = configparser.ConfigParser()
    abs_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        sys.stderr.write(f"\n❌ 没有找到配置文件：{abs_path}\n")
        sys.exit(1)

    try:
        config.read(config_path, encoding='utf-8')

        # IOFile 部分
        inputfile = config.get("IOFile", "input_file").strip()
        outputfile = config.get("IOFile", "output_file").strip()

        # Features 部分
        selectedfields_raw = config.get("Features", "selected_fields").strip()
        selectedfields = [x.strip() for x in selectedfields_raw.split(",")]

        poh_mode = config.getint("Features", "poh", fallback=0)

        # cfg 字典（你的要求：不要类，只用 dict）
        cfg = {
            "input_file": inputfile,
            "output_file": outputfile,
            "selected_fields": selectedfields,
            "poh": poh_mode,
        }

        # 打印 cfg
        print("\n[CFG 配置内容]")
        for k, v in cfg.items():
            print(f"  {k}: {v}")

        return cfg

    except Exception as e:
        sys.stderr.write(f"\n❌ 配置文件读取失败：{e}\n")
        sys.exit(1)

# main函数
def process_main_func():
    print(f"\n>> process_main_func(....)\n")
    # 加载配置文件。
    cfg = load_config_func();
    # 加载原始训练或测试样本文件。
    df_raw = load_sample_file_func(cfg)  
    # 处理文件
    df_clean = df_proc_file_func(df_raw, cfg) 
    # 打印最终文件
    print_df_structure(df_clean)   
    # 文件存盘
    save_file_conf(df_clean, cfg)

# ========== 主入口 ==========
if __name__ == "__main__":
    # 调用main函数。
    process_main_func()
