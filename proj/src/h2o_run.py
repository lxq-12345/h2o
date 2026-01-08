# 程序名：h2o_run.py
# 功能：极简命令行界面，用于驱动样本制作、训练和应用测试流程。

import os
import sys
import subprocess # 仍然保留，但不再用于驱动主流程
import configparser
# 提供命令行参数解析能力
import argparse
# 提供面向对象的路径与文件操作
from pathlib import Path

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

# ========== h2o 项目包资源 ==========
print(f"    ✅ 加载项目组件")
# 生成训练样本与测试样本。
try:
    import gen_samps as _gen_samps
    print(f"    组件 gen_samps OK") # ✅ 修正了打印信息
except Exception as e:
    _gen_samps = None # ✅ 修正了变量名拼写
    print(f"⚠️ 未找到 gen_samps：{e}")
# 训练时间序列预测模型。
try:
    import train_automl as _train_automl
    print(f"    组件 train_automl OK")
except Exception as e:
    _train_automl = None
    print(f"⚠️ 未找到 train_automl：{e}")
# 应用预测接口
try:
    import predictor as _predict
    print(f"    组件 predict OK")
except Exception as e:
    _predict = None
    print(f"⚠️ 未找到 predict：{e}")
# 工具模块
try:
    import utils as _ut 
    print(f"    组件 utils OK")
except Exception as e:
    _ut = None
    print(f"⚠️ 未找到 util：{e}")
# ========== End of h2o 项目包资源 ==========

# CWD 切换至 h2o 根路径下
os.chdir(PROJECT_ROOT)
current_path = os.getcwd()
print(f">> 当前工作目录: {current_path}")

# 加载配置文件
# 注意：cfg 必须在全局范围或传递到所有需要它的函数中
if _ut:
    cfg = _ut.load_config_func() 
else:
    print("❌ 核心工具模块未加载，无法读取配置。")
    sys.exit(1)

input(f"\n  ...环境配置参数 按回车键继续...")

label = cfg["label"]

# ==============================================================================
# 0. 配置及路径定义 (已删除硬编码脚本名和动态配置文件名)
# ==============================================================================

# **动态配置文件和脚本文件名常量已删除**

# ==============================================================================
# 1. 辅助函数
# ==============================================================================

def clear_screen():
    """清空控制台界面"""
    os.system('cls' if os.name == 'nt' else 'clear')

# **update_dynamic_config 函数已删除，不再通过 INI 文件传递模式**

def execute_component(component_name: str, success: bool):
    """
    用于在调用组件接口后，显示运行结果。
    """
    print(f">>>>>>>>>>>> {'✅' if success else '❌'} 组件运行结束：{component_name} <<<<<<<<<<<<")
    if not success:
        input(" ...按回车键返回主菜单...")
    else:
        input("\n ...按回车键继续...")
    return success

# ==============================================================================
# 2. 菜单逻辑函数
# ==============================================================================
# 主菜单
def show_main_menu():
    """显示一级菜单"""
    clear_screen()
    print(f"=" * 40)
    print(f"     H2O 硬盘{label}预测项目管理器")
    print(f"=" * 40)
    print(f" 1. 样本制作 + 训练 (Gentrain + Train)")
    print(f" 2. 样本制作 (Gentrain Only)")
    print(f" 3. 训练 (Train Only)")
    print(f" 4. 应用预测 (Predictor)")
    print(f"-" * 40)
    print(f" 0. 退出")
    print(f"=" * 40)
    choice = input("请选择操作 (0-4): ").strip()
    return choice

# 二级菜单（输入方案选项）
def show_mode_menu(action_description: str):
    """显示 A, B 方案选择菜单"""
    clear_screen()
    print("=" * 40)
    print(f"      选择 {action_description} 方案")
    print("=" * 40)
    print(f" A. 方案 A：预测到达{label}检查点天数")
    print(f" B. 方案 B：预测到达检查点的{label}数")
    print("-" * 40)
    print(" R. 返回主菜单")
    print("=" * 40)
    choice = input("请选择方案 (A/B/R): ").strip().upper()
    return choice

# 样本制作 + 训练
def run_sample_gen_train():
    """一级菜单 1：样本制作 + 训练"""
    while True:
        mode = show_mode_menu("样本制作 + 训练")
        cfg["mode"] = mode        
        if mode in ('A', 'B'):
            # 1. 制作训练样本 (if_test=False)
            print(f"\n>>>>>>>>>>>> 🚀 启动组件：_gen_sample (Mode: {mode}) <<<<<<<<<<<<")
            cfg["if_test"] = False
            # 调用生成样本程序的组件接口。
            success_gen = _gen_samps.run_func(cfg) 
            execute_component("_gen_samps", success_gen)
            if success_gen:
                # 2. 执行训练
                print(f"\n>>>>>>>>>>>> 🚀 启动组件：train_automl (Mode: {mode}) <<<<<<<<<<<<")
                # 调用训练程序的组件接口。
                success_train = _train_automl.run_func(cfg)
                execute_component("_train_automl", success_train)
            break
        elif mode == 'R':
            break

# 样本制作
def run_sample_gen():
    """一级菜单 2：样本制作"""
    while True:
        mode = show_mode_menu("样本制作")
        cfg["mode"] = mode  
        if mode in ('A', 'B'):
            # 区分生成训练集还是测试集
            sub_choice = input("请选择样本类型 (T: 训练集 / S: 测试集): ").strip().upper()
            is_test = sub_choice == 'S'            
            type_str = '测试集' if is_test else '训练集'
            print(f"\n>>>>>>>>>>>> 🚀 _gen_sample (Mode: {mode}, Type: {type_str}) <<<<<<<<<<<<")
            # 赋值
            cfg["if_test"] = is_test
            # 调用组件接口
            success_gen = _gen_samps.run_func(cfg)
            execute_component("_gen_samps", success_gen)
            break
        elif mode == 'R':
            break

# 训练
def run_training():
    """一级菜单 3：训练"""
    while True:
        mode = show_mode_menu("训练")
        cfg["mode"] = mode  
        if mode in ('A', 'B'):
            # 训练总是使用训练集样本 (if_test=False)
            print(f"\n>>>>>>>>>>>> 🚀 启动组件：train_automl (Mode: {mode}) <<<<<<<<<<<<")
            # 调用组件接口
            success_train = _train_automl.run_func(cfg)
            execute_component("_train_automl", success_train)
            break
        elif mode == 'R':
            break

# 应用预测
def run_prediction():
    """一级菜单 4：应用测试 (预测)"""
    while True:
        mode = show_mode_menu("应用测试")
        cfg["mode"] = mode  
        if mode in ('A', 'B'):
            print(f"\n>>>>>>>>>>>> 🚀 启动组件： predict (Mode: {mode}) <<<<<<<<<<<<")
            success_pred = _predict.run_func(cfg)
            execute_component("_predict", success_pred)
            break
        elif mode == 'R':
            break
  # ==============================================================================
# 3. 主程序循环
# ==============================================================================

def main_func():
    while True:
        choice = show_main_menu()
        
        if choice == '1':
            run_sample_gen_train()
        elif choice == '2':
            run_sample_gen()
        elif choice == '3':
            run_training()
        elif choice == '4':
            run_prediction()
        elif choice == '0':
            print("程序退出。再见！")
            break
        else:
            print("\n无效的选择，请重新输入。")
            input("按回车键继续...")

if __name__ == '__main__':
    # 检查核心组件是否存在，以防止运行时错误
    if not (_gen_samps and _train_automl and _predict and _ut):
        print("\n❌ 警告：核心组件缺失，无法启动主循环。请检查导入错误。")
    else:
        main_func()
