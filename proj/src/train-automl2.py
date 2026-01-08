# 文件名：train-automl.py
# 功能：使用 H2O AutoML 训练硬盘剩余寿命预测模型（支持模块化配置、训练、预测与结果保存）

import h2o
import pandas as pd
import configparser
import sys
import os
from h2o.automl import H2OAutoML

# 配置读取函数
def load_train_config_func(config_path: str = 'train-automl.ini') -> tuple:
    print(">> 执行配置加载函数 load_train_config_func()")
    print(f"读取配置文件：{config_path}")
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        print(f"❌ 配置文件未找到：{os.path.abspath(config_path)}")
        sys.exit(1)
    try:
        config.read(config_path, encoding='utf-8')
        train_file = config.get('Paths', 'train_file').strip()
        test_file = config.get('Paths', 'test_file').strip()
        output_feature_importance = config.get('Paths', 'output_feature_importance').strip()
        output_prediction_file = config.get('Paths', 'output_prediction_file').strip()
        model_save_path = config.get('Paths', 'model_save_path').strip()
        target_column = config.get('Columns', 'target_column').strip()
        id_columns = [x.strip() for x in config.get('Columns', 'id_columns').split(',')]
        max_models = int(config.get('Automl', 'max_models'))
        max_runtime_secs = int(config.get('Automl', 'max_runtime_secs'))
        print("配置内容：")
        print(f"  训练文件路径 ：{train_file}")
        print(f"  测试文件路径 ：{test_file}")
        print(f"  输出预测路径 ：{output_prediction_file}")
        print(f"  特征重要性路径：{output_feature_importance}")
        print(f"  模型保存路径 ：{model_save_path}")
        print(f"  目标列         ：{target_column}")
        print(f"  ID列           ：{id_columns}")
        print(f"  最大模型数     ：{max_models}")
        print(f"  最长训练秒数   ：{max_runtime_secs}")
        return (train_file, test_file, output_feature_importance, output_prediction_file,
                model_save_path, target_column, id_columns, max_models, max_runtime_secs)
    except Exception as e:
        print("❌ 配置文件读取失败，请检查格式和字段")
        print(f"[调试信息] {e}")
        sys.exit(1)

# 保存模型和特征重要性
def save_artifacts(leader, output_feature_importance, model_save_path):
    try:
        varimp = leader.varimp(use_pandas=True)
        varimp.to_csv(output_feature_importance, index=False)
        print(f">> ✅ 特征重要性保存：{output_feature_importance}")
        path = h2o.save_model(model=leader, path=model_save_path, force=True)
        print(f">> ✅ 模型保存路径：{path}")
    except Exception:
        print("❌ 模型或特征重要性保存失败，请检查输出路径")

# 预测并保存结果
def predict_and_save(leader, test_df, feature_cols, id_columns, output_prediction_file):
    try:
        # 预测。
        preds = leader.predict(h2o.H2OFrame(test_df[feature_cols])).as_data_frame(use_multi_thread=True)
        preds = preds.round(0).astype(int)  # ✅ 四舍五入并转为整数
        preds['predict'] = preds['predict'].clip(lower=0)  # ✅ 保证预测为非负寿命
        for col in id_columns + ['bad_sectors']:
            if col not in test_df.columns:
                print(f"❌ 测试集缺字段：{col}")
                return
        meta_df = test_df[id_columns + ['bad_sectors']].reset_index(drop=True)
        result_df = pd.concat([meta_df, preds], axis=1)
        result_df.to_csv(output_prediction_file, index=False)
        print(f">> ✅ 预测结果保存：{output_prediction_file}")
    except Exception:
        print("❌ 模型预测或结果保存出错，请检查测试数据格式和字段")

# 模型性能评价 
def evaluate_model_func(aml):
    try:
        print(">> 模型排行榜：")
        leaderboard = aml.leaderboard.as_data_frame(use_multi_thread=True)
        print(leaderboard.head(5))
        leader_model = aml.leader
        perf = leader_model.model_performance()
        print(f">> 最佳模型性能：")
        print(f"  RMSE: {perf.rmse():.3f}")
        print(f"  MAE : {perf.mae():.3f}")
        print(f"  R²  : {perf.r2():.3f}")
    except Exception:
        print("⚠️ 无法输出模型性能，请检查 AutoML 是否训练成功")		
		
# 训练 AutoML 模型
def train_automl(train_df, target_column, feature_cols, max_models, max_runtime_secs):
    try:
        train_h2o = h2o.H2OFrame(train_df)
        train_h2o[target_column] = train_h2o[target_column].asnumeric()

        print("train_h2o 表头字段名：")
        print(train_h2o.columns)

        print(">> AutoML 正在训练中...")
        aml = H2OAutoML(
            max_models=max_models,
            max_runtime_secs=max_runtime_secs,
            seed=1234,
            stopping_metric="RMSE",
            exclude_algos=["StackedEnsemble"]
        )
        aml.train(
            x=feature_cols, 
            y=target_column, 
            training_frame=train_h2o
        )
        print(">> AutoML 训练完成")
        return aml
    except Exception:
        print("❌ 模型训练出错，请检查训练数据格式和参数设置")
        sys.exit(1)

# 训练模块：加载训练数据、提取特征、训练模型
def train_model_func(train_file, target_column, id_columns, max_models, max_runtime_secs):
    print("train_model_func")
    try:
        print(f">> 加载训练数据：{train_file}")
        df = pd.read_csv(train_file)
        print(f"✅ 训练数据共 {len(df)} 条记录，字段数：{len(df.columns)}")
        if target_column not in df.columns:
            print(f"❌ 缺少目标列：{target_column}")
            return None, None
        feature_cols = df.select_dtypes(include='number').columns.tolist()

        print("   df 的 feature_cols 特征列:")
        print("  ",feature_cols)  # 输出选择的特征列名列表  

        for col in id_columns + [target_column]:
            if col in feature_cols:
                feature_cols.remove(col)

        print("   选择的 feature_cols 特征列:")
        print("  ",feature_cols)  # 输出选择的特征列名列表  

        print("   target_column 特征列:")
        print("  ", target_column)  # 输出选择的特征列名列表  

        aml = train_automl(df, target_column, feature_cols, max_models, max_runtime_secs)
        # 模型性能评价 
        evaluate_model_func(aml)
        leader = aml.leader
        return leader, feature_cols
    except Exception as e:
        print("❌ 模型训练失败，请检查训练数据格式或特征列设置")
        print(f"[调试信息] {e}")
        return None, None

# 测试模块：加载测试数据并校验特征完整性
def test_model_func(test_file, feature_cols):
    print("test_model_func")
    try:
        print(f">> 加载测试数据：{test_file}")
        df_test = pd.read_csv(test_file)
        used_test_cols = [col for col in feature_cols if col in df_test.columns]
        missing = set(feature_cols) - set(used_test_cols)
        if missing:
            print(f"❌ 测试集缺少特征列：{missing}")
            return None, None
        return df_test, used_test_cols
    except Exception as e:
        print("❌ 测试数据处理失败，请检查文件内容或格式")
        print(f"[调试信息] {e}")
        return None, None

# 主函数：调用模块执行训练、测试、预测保存流程
def main_func():
    print("main_func()")
    print("================= 启动硬盘寿命预测程序 =================")
    try:
        print(f">> 初始化 h2o")
        h2o.init(max_mem_size="4G",nthreads=4)
        (train_file, test_file, output_feature_importance, output_prediction_file,
         model_save_path, target_column, id_columns, max_models, max_runtime_secs) = load_train_config_func()
        leader, feature_cols = train_model_func(train_file, target_column, id_columns, max_models, max_runtime_secs)
        if leader is None:
            return
        df_test, used_test_cols = test_model_func(test_file, feature_cols)
        if df_test is None:
            return
        predict_and_save(leader, df_test, used_test_cols, id_columns, output_prediction_file)
        save_artifacts(leader, output_feature_importance, model_save_path)
        h2o.cluster().shutdown()
    except Exception as e:
        print("❌ 程序执行失败，请检查配置、文件路径和数据格式")
        print(f"[调试信息] {e}")
        sys.exit(1)

# 程序入口
if __name__ == '__main__':
    main_func()
