"""
# 程序名：utils.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import pandas as pd
import configparser
import sys
import os
import numpy as np
import wcwidth
from typing import Dict, Any, List
import glob
import re
import h2o
from datetime import date
from datetime import datetime

# ========== H2O 模型 ==========
# h2o 模型初始化。
def h2o_init_func(cfg):
    """
    初始化或连接 H2O 集群。
    """
    try:
        print(f">> h2o_init_func()")
        print("   H2Oxg初始化")        
        # 从配置中获取内存设置
        max_mem = cfg.get("h2o_max_mem", "10G") 
        # 直接调用 h2o.init() 启动或连接集群
        h2o.init(
            nthreads=-1,  # 使用所有可用 CPU 线程
            max_mem_size=max_mem, 
            verbose=False # 减少控制台输出
        )
    except Exception as e:
        print(f"❌ H2O 初始化失败: {e}")
        # 如果初始化失败，尝试安全关闭 H2O (防止进程残留)
        try:
             # 只有当集群对象存在时才尝试关闭
             if h2o.cluster():
                 h2o.cluster().shutdown(prompt=False)
        except Exception:
             pass 
 
# 加载 h2o 训练模型文件。
def h2o_load_model_func(cfg):
    """
    根据配置和当前模式，从模型目录中查找并加载最新的模型文件（H2O）。
    :param cfg: 配置字典，需包含 'model_dir' 和 'mode'
    :return: 加载好的 H2O 模型对象
    """
    print(f"\n>> h2o_load_model_func()")
    model_dir = cfg["model_save_dir"]
    mode = cfg["mode"].upper()
    # 查找所有以 _A/_B/_C 结尾的模型文件
    pattern = os.path.join(model_dir, f"*_{mode}")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"未找到 {mode} 方案的模型文件（目录: {model_dir}）")
    # 提取文件名中的日期，格式为 _YYYYMMDD_
    date_pattern = re.compile(r'_(\d{8})_[A-Z]$')
    def extract_date(file):
        base = os.path.basename(file)
        m = date_pattern.search(base)
        return int(m.group(1)) if m else 0
    # 按日期从大到小排序，取最新
    files_sorted = sorted(files, key=extract_date, reverse=True)
    latest_model_path = files_sorted[0]
    print(f"   选用模型文件: {latest_model_path}")
    # 加载 H2O 模型
    try:
        # 初始化 h2o 模型。
        h2o_init_func(cfg)
        # 加载模型。
        model = h2o.load_model(latest_model_path)
        print(f"   加载 {latest_model_path} 模型成功") 
    except Exception as e:
        raise RuntimeError(f"模型文件加载失败: {latest_model_path}\n错误信息: {e}")
    return model

# h2o 模型预测接口。
def h2o_predict_func(df: pd.DataFrame, model_h2o, cfg): 
    print(">> h2o_predict_func()")
    print("   样本的特征列 dtyp:")
    print(f"   ", df.dtypes)
    predict = cfg["predict"]
    # 自动选择所有数值型列作为初始特征集
    feature_cols = df.select_dtypes(include='number').columns.tolist()
    # 并转为 H2OFrame 格式，因为 H2O 模型只能识别 H2OFrame 类型的数据。 
    test_h2o = h2o.H2OFrame(df[feature_cols])
    # 用训练好的 leader 模型对 test_h2o 进行批量预测。
    # 这里并不需要手动遍历每一行，H2O 会自动对所有样本一行行计算预测值，
    # 返回的 preds_h2o 是 H2OFrame 格式的预测结果。    
    pred_h2o = model_h2o.predict(test_h2o) 
    # 将 H2OFrame 的预测结果转换为 pandas DataFrame（preds），
    # 这样方便后续处理和与原数据对齐。    
    df_pred = pred_h2o.as_data_frame()
    # 复制 df。
    df_result = df.reset_index(drop=True).copy()
    # 将后处理后的预测结果添加到新 DataFrame
    # 对预测值做标准化后处理步骤：
    # - clip(lower=0)：将所有预测结果限制为不小于0，防止出现负值（如剩余寿命天数、
    #   坏道数等业务要求非负的预测场景）。
    # - round(0)：将浮点预测结果四舍五入为整数，更贴合实际业务（如剩余天数应为整数）。
    # - astype(int)：将结果转为 int 类型，确保后续保存/分析时数据类型一致。
    df_result[predict] = df_pred["predict"].clip(lower=0).round(0).astype(int)
    # df 列表数据全部转换成Int。
    df_result = df_result.apply(lambda col: col.astype("Int64") if col.dtype == "float64" else col)
    # 返回完整结果集
    return df_result
# ========== H2O 模型结束 ==========

# ========== 特征处理 ==========
# 设置滞后特征项。
def add_lag_features_func(df: pd.DataFrame, lag_days: list[int], cfg: dict) -> pd.DataFrame:
    """
    功能： 
          为训练样本中的每个监控字段自动生成指定天数的“滞后特征”（lag features）。 
          滞后特征用于表示某个指标在过去 N 天的历史值，让模型能够看到趋势，而不仅是当前数值。 
    用途： 
          在时间序列预测（如硬盘未来坏道数预测）中，模型必须看到“过去几天的数据变化”， 
          才能判断增长趋势或恶化速度，因此滞后特征是最重要的特征工程之一。 
    特点： 
          1. 自动适配多个监控字段：不论有多少指标（如 bad_sectors、温度、IOPS），都会自动生成
             滞后列。 
          2. 按硬盘分组处理：每块硬盘独立做滞后，不会互相干扰。 
          3. 缺失值处理自然合理：前 lag 行没有足够历史，会自动生成缺失值（NaN）。 
          4. 可扩展性强：未来增加监控字段或增加滞后天数时，无需改代码。 
          5. 输出的滞后特征均为浮点数类型（float）。 
    返回： 
          一个包含所有滞后特征的新 DataFrame，可直接用于训练模型。
    """
    print("\n>> add_lag_features_func()")
    device_id = cfg["device_id"]
    date = cfg["date"]
    POH = "POH"

    # 为兼容未来样本中新增的监控字段（即使不在配置文件里），这里采用排除法确定监控字段集合。
    value_cols = [col for col in df.columns if col not in [device_id, date, POH]]
    print(f"   构建监控项(value_cols):{value_cols} 的滞后特征(lag_days):{lag_days}")
    # 保证排序。
    df = df.sort_values([device_id, date])
    # 遍历每个监控字段，生成其对应的多个滞后特征 
    # 遍历所有需要做滞后的监控字段（如 bad_sectors、temperature 等）， 
    # for循环的必要性：对每个字段分别生成它自己的滞后特征；这样当监控项增加时，代码无需改动。
    for col in value_cols:
        print(f"   当前监控项(col)：{col}")
        # 遍历所有需要生成的滞后天数（如 5 天、7 天、9 天）， 
        # 为当前监控字段逐个创建对应的滞后特征列。
        for lag in lag_days:
            # 构建滞后特征名称，监控项名+_lag+滞后项，例如 bad_sectors_lag3
            lag_col = f'{col}_lag{lag}'
            print(f"   生成滞后特征项(lag_col)：{lag_col}")
            # 生成滞后特征项
            # 按硬盘编号 device_id 分组后，对每个硬盘内部的【当前字段 col】做“向下平移 lag 行”操作。 
            # 这个平移效果就是：为每条记录找出它“lag 天之前”的数值，从而生成一个新的滞后特征列。 
            # 比如 lag=5，则新列 bad_sectors_lag5 表示：该硬盘在 5 天前（5 条记录前）的
            #  bad_sectors 数值。 前 lag 行因为没有足够的历史记录，会自动填为 NaN。
            df[lag_col] = df.groupby(device_id)[col].shift(lag)
            # 打印本次生成的新列内容
            # print(f" 新增滞后列(log_col)：{lag_col} 前5行：\n{df[[lag_col]].head(5)}") 
            # 类型转换 # shift() 会产生缺失值 NaN，使整列自动变成 float 类型； 
            # 但业务字段（如 bad_sectors）本质是整数，缺失值也应该是“整数的缺失”； 
            # 因此把列转换为 pandas 的可空整数类型 Int64，用 <NA> 表示缺失， 
            # 这样既能保持整数类型，又能正确记录缺失值，避免混入不必要的浮点数。
            df[lag_col] = df[lag_col].astype(float)
    print(f"\n   [生成滞后特征项列表(前5行数据)]")
    print(f"   ", df.head(5))        
    return df

# 检查最大滞后天数与应用测试数据时序序列长度
def check_min_sequence_length_func(df, cfg):
    """
    检查每个 device_id 硬盘的时间序列长度是否 >= 最大滞后天数 2 倍要求。
    :param df: 清洗后的 DataFrame，须包含 device_id 和 date 字段
    :param cfg: 配置，需有 lag_days_A/B/C
    """
    print(f">> check_min_sequence_length_func()")    
    device_id = cfg["device_id"]
    date = cfg["date"]
    mode = cfg["mode"].upper()    
    if device_id not in df.columns or date not in df.columns:
        print("  ⚠️  缺少 device_id 或 date 字段，跳过序列长度检查")
        return False 
    lag_days_key = f"lag_days_{mode}"
    if lag_days_key in cfg:
        val = cfg[lag_days_key]
        if isinstance(val, str):
            lag_days_list = [int(x.strip()) for x in val.split(",") if x.strip()]
        elif isinstance(val, (list, tuple)):
            lag_days_list = [int(x) for x in val]
        else:
            raise ValueError(f"{lag_days_key} 配置类型不支持: {type(val)}")
        # 最大滞后天数 * 2
        max_lag = max(lag_days_list) * 2
    else:
        print(f"  ⚠️  配置中未找到 {lag_days_key}，跳过序列长度检查")
        return False
    if max_lag <= 0:
        print(f"  ⚠️  滞后特征参数 {lag_days_key} 配置有误，跳过序列长度检查")
        return False    
    cnt_short = 0
    for did, g in df.groupby(device_id, sort=True):
        days = g[date].nunique()
        # 需要至少 max_lag + 1 条记录，才能构造最大滞后特征
        if days < max_lag + 1:
            print(f"  ⚠️  device_id={did} 的天数 {days} < 最大滞后天数 2 倍 {max_lag + 1}")
            cnt_short += 1
    if cnt_short > 0:
        print(f"有 {cnt_short} 块硬盘数据不足最大滞后天数 2 倍({max_lag + 1})，请检查原始数据。")
        return False
    else:
        print(f"   所有硬盘时间序列数据长度均满足最大滞后天数2倍要求（{max_lag + 1}天）")
        return True

# 获取硬盘 POH 折合天数
def get_hdd_used_days_func(row):
    #print("\n>> get_hdd_used_days_func()")    
    try:
        # pandas Series
        if isinstance(row, pd.Series):
            poh = float(row["POH"])
        else:
            # itertuples() 返回的 namedtuple
            poh = float(row.POH)
        return int(poh // 24)
    except Exception:
        return 0  

# 获取硬盘坏道 cp 检查点时的寿命天数。
def get_hdd_life_days_func(group_df: pd.DataFrame, device_id: int, cfg, cp_threshold: int) -> int:
    print("\n>> get_hdd_life_days_func()")
    key_field = cfg["key_field"]
    date = cfg["date"]
    fail_threshold = cp_threshold
    # 每个硬盘的开始日期
    start_date = group_df[date].min()
    # 1) 找出是否达到坏道阈值
    failure_rows = group_df[group_df[key_field] >= fail_threshold]
    # ==========================
    # 情况 1：达到了阈值 → 使用原本的寿命逻辑
    # ==========================
    if not failure_rows.empty:
        failure_date = failure_rows[date].min()
        life_days = (failure_date - start_date).days
        print(f"   HDD {device_id} 达到坏道 cp 阈值:{fail_threshold} → 寿命 {life_days} 天")
        return life_days
    # ==========================
    # 情况 2：未达到阈值 → 使用最大 bad_sectors 的 POH 作为寿命
    # ==========================
    # 找出坏道最大时的记录
    max_bad_row = group_df.loc[group_df[key_field].idxmax()]
    # 读取该行的 POH
    #max_poh = max_bad_row.POH
    max_poh = max_bad_row["POH"]
    # 折算为“使用天数”
    life_days = int(float(max_poh) // 24)
    print(f"   HDD {device_id} 未达到 cp 阈值:{fail_threshold} → 使用最大坏道点 POH={max_poh} → 寿命 {life_days} 天")
    return life_days  
# ========== 特征处理结束 ==========

# ========== 数据处理 ==========
# A 方案预测结果倒时修正。
def adjust_prediction_func(df, cfg):
    """
    A 方案预测结果倒计时修正：
    1. 指标不变：当天 RUL = 前一天 RUL - 1
    2. 指标突变：当天 RUL = 模型输出的 predict 值
    3. target 最小值限制为 0
    """
    print(f">> adjust_prediction_func()")
    # 从 cfg 获取字段名
    key_field = cfg.get("key_field")
    predict = cfg.get("predict")
    # 复制 df。
    df = df.copy()
    # key_field 与 target 变量不能为空。
    if key_field is None or predict is None:
        raise KeyError(f"cfg 中必须包含 {key_field} 与 {predict} 字段")
    # 检查 df 里是否真的有这些列
    missing_cols = []
    if key_field not in df.columns:
        missing_cols.append(key_field)
    if predict not in df.columns:
        missing_cols.append(predict)
    if missing_cols:
        raise KeyError(f"DataFrame 中缺少必须列：{missing_cols}")
    # 遍历 df 列表。
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        # 新硬盘开始 → 不倒计时
        if curr.device_id != prev.device_id:
            continue
        # 指标不变 → 做倒计时
        if curr[key_field] == prev[key_field]:
            # 当坏道数不变时，把当前天的预期值设为前一天的预期值减 1，并且确保不会低于 0
            df.loc[df.index[i], predict] = max(prev[predict] - 1, 0)
            continue
        # 当预期值指标突变 → 使用模型输出值（重置 RUL）
        df.loc[df.index[i], predict] = curr[predict]
    return df

# 打印预测结果队列
def print_pred_result_func(df, cfg):
    print(f"\n>> print_pred_result_func()")
    print(f'   {cfg["mode"]} 方案预测结果：')
    print(f" ", df.to_string(index=False))

# 清洗数据。
def clean_and_normalize_func(df, cfg):
    """
    对数据做基础清洗与标准化。
    包括：空值剔除、类型修正、生成 干净的 df。
    增加统计起止日期、总年数、硬盘数量。
    返回清洗后的 DataFrame。
    注：本清理不删除 POH 栏目数据
    """
    print("\n>> clean_and_normalize_func()")
    print("   正在清洗数据......")
    device_id = cfg["device_id"]
    date = cfg["date"]
    key_field = cfg["key_field"]
    # 去除所有字段全空的行
    df = df.dropna(how='all')
    # 主字段类型转换（如坏道数转 int）
    if key_field in df.columns:
        #df[key_field] = df[key_field].astype(int, errors="ignore")
        df[key_field] = pd.to_numeric(df[key_field], errors="coerce")
        df = df.dropna(subset=[key_field])
        df[key_field] = df[key_field].astype(int)
    # 日期字段标准化为 datetime
    if date in df.columns and not pd.api.types.is_datetime64_any_dtype(df[date]):
        df[date] = pd.to_datetime(df[date], errors="coerce")
        df = df.dropna(subset=[date])
    # 按主键去重
    pk = [c for c in [device_id, date] if c in df.columns]
    if pk:
        df = df.drop_duplicates(subset=pk, keep="first")
    # 打印部分清洗后数据
    print("   清洗后数据样例（前 5 行）：")
    print(df.head(5).to_string(index=False))
    print(f"   清洗后记录数量：{len(df)}")
    # 增加统计——日期范围和年数
    if date in df.columns:
        min_date = df[date].min()
        max_date = df[date].max()
        n_years = round((max_date - min_date).days / 365.25, 2)
        print(f"   数据日期范围：{min_date.strftime('%Y-%m-%d')} ～ {max_date.strftime('%Y-%m-%d')}，共约 {n_years} 年")
    # 统计硬盘数量和编号区间
    if device_id in df.columns:
        unique_ids = sorted(int(x) for x in df[device_id].unique())
        n_ids = len(unique_ids)
        if n_ids > 10:
            front = unique_ids[:5]
            tail = unique_ids[-5:]
            ids_str = ", ".join(map(str, front)) + ", ..., " + ", ".join(map(str, tail))
            print(f"   硬盘编号：{ids_str}")
        else:
            ids_str = ", ".join(map(str, unique_ids))
            print(f"   硬盘编号：{ids_str}")
        print(f"   硬盘总数：{n_ids}个")
    print("\n   清洗数据数据完毕")
    return df

# 检查测试数据验特征完整性
def check_test_file_func(df, cfg):
    print(">> check_test_file_func()")
    key_field = cfg["key_field"]
    device_id = cfg["device_id"]
    date = cfg["date"]
    id_columns = [device_id, date]
    try:
        # 检查 关键字段 key_field 列
        if key_field not in df.columns:
            print(f"❌ 测试集缺少关键字段 {key_field}")
            return None
        # 检查 ID 列
        for col in id_columns:
            if col not in df.columns:
                print(f"❌ 测试集缺少 ID 列：{col}")
                return None
        return df
    except Exception as e:
        print("❌ 测试数据处理失败，请检查文件内容或格式")
        print(f"[调试信息] {e}")
        return None
# ========== 数据处理结束 ==========

# ========== 文件处理 ==========
# 加载样本文件。
def load_file_func(cfg, file_path):
    """
    加载测试 / 预测样本文件。
    仅保留必要字段：device_id, date, key_field 及模型所需特征列。
    """
    print(f">> load_file_func()")    
    device_id = cfg["device_id"]
    date = cfg["date"]
    key_field = cfg["key_field"]
    print(f"   正在读取 {file_path} 文件数据......")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")
    # 读取文件
    if file_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    # 预测阶段：至少要保留这些列
    keep_cols = [device_id, date]
    if key_field in df.columns:
        keep_cols.append(key_field)
    # 防御式过滤（避免 KeyError）
    keep_cols = [c for c in keep_cols if c in df.columns]
    df = df[keep_cols]
    # 日期字段转 datetime
    if date in df.columns:
        df[date] = pd.to_datetime(df[date], errors="coerce")
    df = df.dropna(subset=[date])
    # 排序
    if device_id in df.columns:
        df = df.sort_values(by=[device_id, date])
    else:
        df = df.sort_values(by=[date])
    df = df.reset_index(drop=True)
    # 打印信息
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

# 定制文件路径名 + 模块后缀：_A, _B, _C 
def customize_file_path_func(cfg, file_path: str):
    print(f">> customize_file_path_func()")  
    if not file_path:
        raise ValueError("file_path 不能为空")
    mode = cfg["mode"]
    dirpath, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    file_name = f"{name}_{mode}{ext}"
    output_path = os.path.join(dirpath, file_name)
    return output_path

# 定制文件名：加日期 + 模块后缀
def customize_file_date_path_func(cfg, file_path: str) -> str:
    print(f">> customize_file_date_path_func()")     
    if not file_path:
        raise ValueError("file_path 不能为空")
    mode   = cfg.get("mode", "A")
    dirpath, filename = os.path.split(file_path)
    name, ext = os.path.splitext(filename)
    date_str = datetime.today().strftime("%Y%m%d")
    output_path = os.path.join(dirpath, f"{name}_{date_str}_{mode}{ext}")
    return output_path

# 打印配置参数。
def print_config_func(cfg):
    print(f">> print_config_func()") 
    print("\n  ========== 配置参数一览 ==========")
    max_len = max(len(str(k)) for k in cfg.keys())
    for k, v in cfg.items():
        print(f"  {k:<{max_len}} : {v}")
    print("  ==================================")

# 加载配置文件。
def load_config_func(config_path: str = 'config/h2o_run.ini') -> Dict[str, Any]:
    """
    加载并解析 h2o_run.ini 配置文件。
    所有变量名与配置文件保持一致，不做额外扩展。
    返回 cfg 字典，供后续数据处理使用。
    """
    print(f"\n>> load_config_func()")
    config = configparser.ConfigParser()
    
    # --- 辅助函数：处理逗号分隔的列表 ---
    def _get_list(section: str, option: str, type_func=str) -> List[Any]:
        """获取逗号分隔的字符串，并转换为指定类型的列表。"""
        # 获取字符串并去除空格
        value_str = config.get(section, option).replace(' ', '')
        # 分割并转换为指定类型
        return [type_func(item) for item in value_str.split(',') if item]
    # ---------------------------------
    
    # 检查配置文件是否存在
    print(f"  打开配置文件：{config_path}")
    if not os.path.exists(config_path):
        sys.stderr.write(f"\n❌ 配置文件未找到：{config_path}\n")
        sys.exit(1)
    try:
        # 读取配置文件
        config.read(config_path, encoding='utf-8')
        cfg: Dict[str, Any] = {} # 初始化配置字典

        # 1. [Title]
        section_name = 'Title'
        cfg['label'] = config.get(section_name, 'label')

        # 2. [Base_Path]
        section_name = 'Base_Path'
        cfg['raw_train_input_path'] = config.get(section_name, 'raw_train_input_path')
        cfg['raw_test_input_path'] = config.get(section_name, 'raw_test_input_path')

        # 3. [Sample_Path]
        section_name = 'Sample_Path'
        cfg['train_sample_path'] = config.get(section_name, 'train_sample_path')
        cfg['test_sample_path'] = config.get(section_name, 'test_sample_path')

        # 4. [After_Train_Path]
        section_name = 'After_Train_Path'
        cfg['static_path'] = config.get(section_name, 'static_path')
        cfg['prediction_path'] = config.get(section_name, 'prediction_path')
        cfg['feature_importance_path'] = config.get(section_name, 'feature_importance_path')
        cfg['model_save_dir'] = config.get(section_name, 'model_save_dir')

        # 5. [App_Path]
        section_name = 'App_Path'
        cfg['app_input_path'] = config.get(section_name, 'app_input_path')
        cfg['app_out_path'] = config.get(section_name, 'app_out_path')

        # 6. [Features]
        section_name = 'Features'
        cfg['device_id'] = config.get(section_name, 'device_id')
        cfg['date'] = config.get(section_name, 'date')       
        cfg['key_field'] = config.get(section_name, 'key_field')
        cfg['target'] = config.get(section_name, 'target')
        cfg['predict'] = config.get(section_name, 'predict')
        cfg['trend_feature'] = config.getint(section_name, 'trend_feature')

        # 7. [Make_Train_Sample]
        section_name = 'Make_Train_Sample'
        cfg['mode'] = config.get(section_name, 'mode')
        cfg['if_test'] = config.get(section_name, 'if_test').strip().lower() == 'true'
        cfg['lag_days_A'] = _get_list(section_name, 'lag_days_A', int)
        cfg['fail_threshold_A'] = config.getint(section_name, 'fail_threshold_A')
        cfg['lag_days_B'] = _get_list(section_name, 'lag_days_B', int)
        cfg['horizon_days_B'] = config.getint(section_name, 'horizon_days_B')
        cfg['slope_window_B'] = config.getint(section_name, 'slope_window_B')

        # 8. [Train_Automl]
        section_name = 'Train_Automl'
        cfg['if_clean'] = config.getint(section_name, 'if_clean')
        cfg['max_models'] = config.getint(section_name, 'max_models')
        cfg['max_runtime_secs'] = config.getint(section_name, 'max_runtime_secs')
        
        # 9. [App_predictor]
        section_name = 'App_predictor'
        cfg['h2o_max_mem'] = config.get(section_name, 'h2o_max_mem')

        # 动态配置参数。
        cfg["model_path"] = ""
        print("  ✅ 配置文件加载成功。")
        # 打印配置参数。
        print_config_func(cfg)
        return cfg

    except configparser.Error as e:
        # 捕获 configparser 自身的解析错误
        sys.stderr.write(f"\n❌ 配置文件解析错误 (configparser Error)：{e}\n")
        sys.exit(1)
    except Exception as e:
        # 捕获其他意外错误，例如类型转换错误
        sys.stderr.write(f"\n❌ 加载配置时发生意外错误：{e}\n")
        sys.exit(1)
# ========== 文件处理结束 ==========
