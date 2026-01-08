# 文件名：train-automl.py
# 功能：使用 H2O AutoML 训练硬盘剩余寿命预测模型（支持模块化配置、训练、预测与结果保存）

import h2o
import pandas as pd
import configparser
import sys
import os
from h2o.automl import H2OAutoML
import re

try:
    import utils as _ut 
    print(f"    组件 utils OK")
except Exception as e:
    _ut = None
    print(f"⚠️ 未找到 util：{e}")

# ========== 测试模块 ==========
# 保存测试结果。
def save_prediction_results_func(df_preds, cfg):
    # 模型预测路径增加模式后缀：A，B，C 模式后缀。
    print(">> save_prediction_results_func()")    
    path = cfg["prediction_path"]
    prediction_path = _ut.customize_file_path_func(cfg, path)
    # 保存文件。
    df_preds.to_csv(prediction_path, index=False)
    print(f"✅ 预测结果已保存：{prediction_path}")    

# 测试模块。
def test_model_func(leader, cfg):
    print(">> test_model_func()")
    path = cfg["test_sample_path"]
    # 给出测试文件正确路径名。
    test_sample_path = _ut.customize_file_path_func(cfg, path)
    print(f"  测试文件路径（test_sample_path）： {test_sample_path}")    
    # 加载应用数据    
    df_test = _ut.load_file_func(cfg, test_sample_path)
    # 检查文件。
    df_test = _ut.check_test_file_func(df_test, cfg)
    # 预测
    df_preds = _ut.h2o_predict_func(df_test, leader, cfg)
    # 保存预测结果（含 ID + key_field + predict）
    save_prediction_results_func(df_preds, cfg)
    print(">> 测试流程已完成")
# ========== 测试模块结束 ==========

# ========== 训练模块 ==========
# 保存最佳模型权重文件和特征重要性文件。
def save_feature_model_func(aml, cfg):
    print(f">> save_feature_model_func()")
    model_save_dir = cfg["model_save_dir"]
    mode = cfg["mode"]
    path = cfg["feature_importance_path"]
    # 特征重要性路径增加模式后缀：A，B，C 模式后缀。
    feature_importance_path = _ut.customize_file_path_func(cfg, path)
    # 从 AutoML 训练器中获取最佳模型（排名第 1 的模型）。
    # AutoML 会自动训练多个模型（GBM、XGBoost、DRF、GLM 等），
    # 并根据 RMSE 等指标进行排序。aml.leader 始终代表性能最好的那个模型。
    leader = aml.leader
    try:
        varimp = leader.varimp(use_pandas=True)
        varimp.to_csv(feature_importance_path, index=False)
        print(f"   ✅ 特征重要性文件保存路径：{feature_importance_path}")
        # 以原始模型文件名的形式保存模型文件。
        path = h2o.save_model(model=leader, path=model_save_dir, force=True)
        print(f"   原始模型路径path: {path}")
        # 拆分目录、文件名和扩展名
        dir_name, filename = os.path.split(path)
        base, ext = os.path.splitext(filename)  # ext 多为 .zip 或 .bin
        # 去除文件名base的最后一个随机数字戳，例如：base = "GBM_1_AutoML_1_20251209_151027"
        # 去掉 _ + 5~6 位数字（H2O 的随机戳） 
        base_ = re.sub(r'_\d{5,6}$', '', base)
        new_filename = f"{base_}_{mode}{ext}"
        # 拼写新文件全路径名。
        final_path = os.path.join(dir_name, new_filename)
        # 将保存的文件原名，改为新文件名、
        os.rename(path, final_path)
        # 将模型路径保持到配置中。        
        cfg["model_path"] = final_path
        print(f"   ✅ 最佳模型保存路径：{final_path}")
    except Exception as e:
        print(f"❌ 模型或特征重要性保存失败，请检查输出路径：{e}")

# 打印最佳模型信息。
def print_leader_info(leader, cfg):
    """打印最佳模型的 5 类关键信息（面向一般用户）"""
    # 模型名称 + 算法类型
    print(f">> print_leader_info()")    
    print("\n   ========== 最佳训练模型 ==========")
    print(f'   模型名称：{cfg["model_path"]}')
    print(f"   模型算法：{leader.algo}")
    # 模型性能
    perf = leader.model_performance()
    print(f"\n   模型性能指标")
    print(f"   RMSE：{perf.rmse():.3f}")
    print(f"   MAE ：{perf.mae():.3f}")
    print(f"   R²  ：{perf.r2():.3f}")
    # 特征重要性 Top 10
    print("\n   特征重要性（Top 10）")
    try:
        varimp = leader.varimp(use_pandas=True)
        for i, row in varimp.head(10).iterrows():
            print(f"   {i+1}. {row['variable']}  (importance = {row['relative_importance']:.3f})")
    except Exception as e:
        print("   ⚠️ 该模型不支持特征重要性（如 GLM 或部分 DL 模型）")
        print(f"[调试信息] {e}")
    # 模型保存路径
    print("\n   模型保存路径：", cfg["model_path"]) 
    print("   =================================\n")

# 模型性能评价 
def evaluate_model_func(aml, cfg):
    print(f">> evaluate_model_func()")
    try:
        print("   模型排行榜：")
        leaderboard = aml.leaderboard.as_data_frame(use_multi_thread=True)
        #print(leaderboard.head(5))
        print(leaderboard)
        print(f"   共训练模型数量：{len(leaderboard)}")
        # 打印最佳模型信息。
        print_leader_info(aml.leader, cfg)
        # 返回最佳模型对象实例。
        return aml.leader
    except Exception as e:
        print("⚠️ 无法输出模型性能，请检查 AutoML 是否训练成功")
        print(f"[调试信息] {e}")
        return None

# 训练 AutoML 模型
def train_automl_func(train_df, cfg):
    print(f">> train_automl_func()") 
    # 配置参数
    device_id = cfg["device_id"]
    date = cfg["date"]
    target = cfg["target"]    
    max_models = cfg["max_models"]
    max_runtime_secs = cfg["max_runtime_secs"]
    max_mem = cfg.get("h2o_max_mem", "10G")  
    id_columns = [device_id, date]         
    try:  
        # 打印 train_df 的所有列名
        print("   train_df 列名信息:")
        print("  ", train_df.columns.tolist())  # 输出所有列名
        # 自动选择所有数值型列作为初始特征集
        feature_cols = train_df.select_dtypes(include='number').columns.tolist()
        # 删除 feature_cols 中的id_columns + [target]
        for col in id_columns + [target]:
            if col in feature_cols:
                feature_cols.remove(col)
        # 初始化 H2O 引擎（启动 H2O 服务器）        
        print("   初始化 H2O 引擎...")
        _ut.h2o_init_func(cfg)
        # 将 pandas DataFrame 转换为 H2OFrame（H2O 模型要求的格式）
        train_h2o = h2o.H2OFrame(train_df)
        # 确保目标列为数值型（必须）；H2O 回归模型只能预测 numeric 类型
        train_h2o[target] = train_h2o[target].asnumeric()
        # 创建 AutoML 对象，准备开始自动训练, 实例化AutoML 训练器对象
        aml = H2OAutoML(
            max_models=max_models,                 # 限制最多训练多少个模型
            max_runtime_secs=max_runtime_secs,     # 或限制总训练时间（秒）
            seed=1234,                             # 固定随机种子，保证结果可复现
            stopping_metric="RMSE",                # 使用 RMSE 作为模型选择标准
            exclude_algos=["XGBoost", "StackedEnsemble"] # 排除堆叠模型以加快训练
        )
        # 打印显示训练数据
        print(f"\n   训练数据集：feature_cols, target, train_h2o:")        
        print(f"   feature_cols 特征列:")
        print(f"  ",feature_cols)  
        print(f"   target 特征列:")
        print(f"  ", target)  # 输出选择的特征列名列表    
        print(f"   train_h2o 训练样本数据字段名：")        
        print(f"  ", train_h2o.columns)
        print(f"   train_h2o 训练样本特征类型:")
        print(f"  ", train_h2o.types)
        # 开始训练：AutoML 会自动训练多种模型并选出表现最好的模型
        print(f'\n   AutoML {cfg["mode"]} 方案正在训练中...')
        aml.train(
            x=feature_cols,              # 输入特征列名
            y=target,                    # 输出目标列名
            training_frame=train_h2o     # H2OFrame 格式的训练数据
        )
        print("   AutoML 训练完成")
        # 返回训练器对象。
        return aml
    except Exception as e:
        print("❌ 模型训练出错，请检查训练数据格式和参数设置")
        print(f"[调试信息] {e}")

# 训练模块：加载训练数据、提取特征、训练模型
def train_model_func(cfg):
    print(f">> train_model_func()")
    path = cfg["train_sample_path"]
    model_dir = cfg["model_save_dir"]
    output_feature_importance_path = cfg["feature_importance_path"]
    target = cfg["target"]
    device_id = cfg["device_id"]
    date = cfg["date"]
    clean_file = cfg["if_clean"]
    id_columns = [device_id, date] 

    # 获取训练样本路径名，加模块后缀：_A, _B, _C
    train_sample_path = _ut.customize_file_path_func(cfg, path)    
    # 检查文件是否存在。
    if not os.path.exists(train_sample_path):
        # ❌ 如果文件不存在，则打印错误信息并退出程序
        sys.stderr.write(f"\n❌ 错误：训练样本文件未找到！路径：{train_sample_path}\n")
        return None, None
    try:
        print(f"   加载训练数据：{train_sample_path}")
        df = pd.read_csv(train_sample_path)
        print(f"   训练数据共 {len(df)} 条记录，字段数：{len(df.columns)}")
        # 显示表头字段名
        #print("   字段名列表：", list(df.columns))
        if target not in df.columns:
            print(f"❌ 缺少目标列：{target}")
            return None, None
        if clean_file == 0:
            # 清空模型目录。
            rm_dir_files_func(model_dir)
            # 清空输出文件目录。
            out_path = os.path.dirname(output_feature_importance_path)
            rm_dir_files_func(out_path)
        # 调用训练模型。
        aml = train_automl_func(df, cfg)
        # 保存特征+模型文件。
        save_feature_model_func(aml, cfg)
        # 模型性能评价 
        leader = evaluate_model_func(aml, cfg)
        # aml.leader 表示 AutoML 自动选出的“最佳模型”。
        # AutoML 会训练很多模型（GBM、XGBoost、RF 等），
        # 并根据误差指标自动排序，选出表现最好的那个。
        # 返回最佳模型与特征栏目              
        return leader
    except Exception as e:
        print("❌ 模型训练失败，请检查训练数据格式或特征列设置")
        print(f"[调试信息] {e}")
        return None, None
# ========== 训练模块结束 ==========

# ========== 基础模块 ==========
# 删除目标目录的文件
def rm_dir_files_func(files_dir):
    print(f">> rm_dir_files_func()")    
    for fname in os.listdir(files_dir):
        fpath = os.path.join(files_dir, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)

# 模块标准接口
def run_func(cfg):
    print(f">> run_func()")      
    try:
        # 调用训练模块。
        leader = train_model_func(cfg)
        if leader is None:
            return False
        input(f" ... 训练完毕，按回车键继续测试...")
        # 调用测试模型。
        test_model_func(leader, cfg)
        # 关闭h2o。
        h2o.cluster().shutdown()
        return True
    except Exception as e:
        print("❌ 程序执行失败，请检查配置、文件路径和数据格式")
        print(f"[调试信息] {e}")
        return False

# 主函数：调用模块执行训练、测试、预测保存流程
def main_func():
    print(">> main_func()")
    print("   ========== 启动硬盘坏道时间序列预测训练程序 ==========")
    cfg = _ut.load_config_func()
    run_func(cfg)
# ========== 基础模块结束 ==========
# 程序入口
if __name__ == '__main__':
    main_func()
