# h2o_run.py 程序说明

文件路径：proj/src/h2o_run.py

## 一、概述

`h2o_run.py` 是项目的交互式命令行驱动器（CLI），用于加载并协调项目核心组件（样本生成、模型训练、预测与工具模块），通过菜单引导用户执行样本制作、训练和预测流程，适用于手工或半自动运行场景。

## 二、设计目标

- 以最小依赖实现交互式流程调度。
- 将 `proj/src` 与项目根路径加入 `sys.path` 以便导入内部模块。
- 按组件接口 `run_func(cfg)` 调用各功能模块，统一用户交互与结果提示。

## 三、依赖

- Python 标准库：`os`, `sys`, `subprocess`, `configparser`, `argparse`, `pathlib`。
- 项目内部模块（位于 `proj/src`）：`gen_samps`, `train_automl`, `predictor`, `utils`。这些模块应实现约定接口（例如 `run_func(cfg)`）。

## 四、主要全局变量

- `PROJECT_ROOT`：通过 `Path(__file__).resolve().parents[1]` 计算得出项目根目录。
- `SRC_DIR`：项目 `src` 目录路径（`PROJECT_ROOT / "src"`），会被插入 `sys.path`。
- `cfg`：通过 `utils.load_config_func()` 加载的配置对象（运行时必须存在）。

## 五、主要功能函数与职责

- `clear_screen()`：跨平台清空终端（Windows 使用 `cls`，其它系统使用 `clear`）。
- `execute_component(component_name: str, success: bool)`：统一显示组件执行结果，成功或失败后提示用户按回车继续或返回。
- `show_main_menu()`：显示主菜单并读取用户选择（1-4/0）。
- `show_mode_menu(action_description: str)`：显示 A/B 方案选择菜单（返回 `A`/`B`/`R`）。
- `run_sample_gen_train()`：菜单项“样本制作 + 训练”，先调用 `gen_samps.run_func(cfg)` 生成样本，成功后调用 `train_automl.run_func(cfg)` 训练模型。
- `run_sample_gen()`：菜单项“样本制作”，在 A/B 模式下可选择生成训练集或测试集并调用 `gen_samps.run_func(cfg)`。
- `run_training()`：菜单项“训练”，调用 `train_automl.run_func(cfg)` 进行训练（使用训练集）。
- `run_prediction()`：菜单项“应用预测”，调用 `predictor.run_func(cfg)` 执行预测流程。
- `main_func()`：主循环，基于用户选择分发到上述各子流程并支持退出。

## 六、执行流程（高层）

1. 计算 `PROJECT_ROOT` 与 `SRC_DIR`，并将两者路径插入 `sys.path`，确保可以导入内部模块。
2. 导入项目组件并打印加载状态（若组件不可用则记录并在后续阻断或提示）。
3. 切换当前工作目录到 `PROJECT_ROOT`（`os.chdir(PROJECT_ROOT)`)。 
4. 使用 `utils.load_config_func()` 读取配置到 `cfg`；若 `utils` 未加载则退出程序。
5. 进入交互式主菜单，根据用户输入调用对应模块，并用 `execute_component` 显示运行结果和等待用户确认。

## 七、错误处理与前提条件

- 脚本假设 `gen_samps`, `train_automl`, `predictor`, `utils` 等模块存在并实现约定接口（例如 `run_func(cfg)`)。
- 若导入任何核心模块失败，脚本会在初始化阶段打印提示信息并在主循环前阻止继续运行（或在运行时出现错误）。
- 组件内部需自行处理其 I/O、权限或模型训练相关的异常；本脚本仅做流程调度与基本用户交互。

## 八、改进建议

- 增加非交互式命令行参数（通过 `argparse`）以支持脚本化或 CI 自动运行，例如 `--mode sample_train --auto`。
- 将组件加载与诊断封装为函数并返回结构化状态，便于单元测试和自动化检查。
- 把初始化时的 `print` 输出替换为 `logging`，并增加 `--quiet`/`--verbose` 控制项。
- 增加超时与异常回滚策略，防止组件错误导致主流程卡死。

## 九、运行示例

在项目根或任意路径运行：

```powershell
python proj/src/h2o_run.py
```

随后按交互菜单提示选择操作。

---

文件已保存为：`proj/doc/h2o_run程序文件.md`。