# 文件名：predictor.py
# 功能：使用 H2O AutoML 训练模型预测硬盘 A/B/C 3种方案预期目标。
#import matplotlib
#matplotlib.use('Agg')  # 使用无头后端，避免 GUI 出错
#import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import numpy as np
import os
import sys
import glob
import re
import h2o

# 计算项目根目录（scripts/ 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 通用工具
try:
    import utils as _ut
    print("    组件 utils OK.")
except ImportError:
    print("❌ 导入 utils 失败。请确保 utils.py 文件存在。")
    sys.exit(1)

# 预测数据处理结果。
def predict_result_func(df_pred: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    根据模式分派给具体的预测函数。
    """
    print(f">> predic_result_func()")    
    mode = cfg["mode"] 
    device_id = cfg["device_id"]
    date = cfg["date"]
    key_field = cfg["key_field"]
    predict = cfg["predict"]
    # 去除滞后数据中滞后工程的变量只保留如下有业务意义的变量栏。    
    cols_keep = [device_id, date, key_field, predict]
    df_pred = df_pred[cols_keep]
    if 'A' in mode:
        # A 方案单调坏道增长 调整预测 
        df_adjust = _ut.adjust_prediction_func(df_pred, cfg)
    elif 'B' in mode:
        df_adjust = df_pred
    # 打印预测
    _ut.print_pred_result_func(df_adjust, cfg)
    return df_adjust

# 保存预测结果。
def save_prediction_results_func(df_preds, cfg):
    # 模型预测路径增加模式后缀：A，B，C 模式后缀。
    print(f">> save_prediction_results_func()")    
    path = cfg["app_out_path"]
    prediction_path = _ut.customize_file_date_path_func(cfg, path)
    # 保存文件。
    df_preds.to_csv(prediction_path, index=False)
    print(f"✅ 预测结果已保存：{prediction_path}")  

# 制作特征项。
def make_features_func(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    根据 cfg["mode"] 动态生成预测所需的特征。
    """
    print(f">> make_features_func()")
    mode = cfg["mode"]
    print(f">> 正在为 Mode {mode} 应用数据生成滞后特征...")
    if mode == 'A':
        lag_feature = cfg['lag_days_A']
    elif mode == 'B':
        lag_feature = cfg['lag_days_B']
    else:
        raise ValueError(f"❌ 未知的预测模式: {mode}")
    try:
        # 制作滞后特征。  
        df_feat = _ut.add_lag_features_func(df, lag_feature, cfg)
        print(f"✅ 特征制作完成，结果数据行数: {len(df_feat)}")
        if mode == 'C':
            hdd2validcp = _ut.get_valid_cp_func(df_feat, cfg)
            #print(f"   批量展开所有有效样本 ...")
            df_feat = _ut.expand_samples_by_cp_func(df, hdd2validcp)
        # 删除 df_feat 列表中含有“NaN”内容的行记录
        df_clean = df_feat.dropna()
        return df_clean       
    except Exception as e:
        print(f"❌ 制作特征项： {e}")
        raise 

# 模块通用接口。
def run_func(cfg):
    # 数据加载
    print(f">> run_func()")
    try:
        # 加载模型文件。
        model_h2o = _ut.h2o_load_model_func(cfg)
        # 加载应用数据
        df_raw = _ut.load_file_func(cfg, cfg["app_input_path"])
        if df_raw is None or len(df_raw) == 0:
            print("❌ 加载的数据为空，终止执行")
            return
        # 校验与清洗
        df_clean = _ut.clean_and_normalize_func(df_raw, cfg)
        if df_clean is None or len(df_clean) == 0:
            print("❌ 清洗后的数据为空，终止执行")
            return        
        # 检查每块硬盘数据长度
        ok = _ut.check_min_sequence_length_func(df_clean, cfg)
        if not ok:
            print("❌ 数据不满足最小序列长度要求，跳过当前数据集")
            return 
        # 滞后特征制作
        df_feat = make_features_func(df_clean, cfg)
        # 预测
        df_pred = _ut.h2o_predict_func(df_feat, model_h2o, cfg)
        # 预测结果处理
        df_result = predict_result_func(df_pred, cfg)
        # 打印预测结果。
        print(f"   预测输出数据列表栏目名：")
        print(f"   ", df_result.columns.tolist())  # 输出所有列名
        # 保存预测结果。
        save_prediction_results_func(df_result, cfg)
        return True
    except Exception as e:
        print(f"❌ 应用数据预测失败: {e}")
        return False

# 主入口函数
def main_func() -> pd.DataFrame:
    """
    [主函数] 驱动应用预测流程。
    """
    # CWD 切换至 h2o 根路径下
    os.chdir(PROJECT_ROOT)
    current_path = os.getcwd()
    print(f">> 当前工作目录: {current_path}")
    # 加载配置
    cfg = _ut.load_config_func()
    # 执行模块通用接口。
    run_func(cfg)

# 示例：如何使用这个函数 (在 h2o_run.py 中调用)
if __name__ == '__main__':
    main_func()
