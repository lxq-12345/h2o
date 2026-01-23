# H2O 硬盘坏道预测项目

## 项目目的

本项目使用 H2O AutoML 机器学习平台构建硬盘坏道（故障）预测模型，通过分析硬盘 SMART 监控指标（如坏道数量、已重映射扇区数等），实现对硬盘剩余寿命（RUL）和故障风险的预测。

### 核心功能
- **数据预处理**：支持 Excel 到 CSV 的数据格式转换，字段提取与数据清洗
- **样本生成**：从基础数据生成时间序列训练样本和测试样本
- **模型训练**：利用 H2O AutoML 自动化训练最优预测模型（支持 GBM、GLM 等算法）
- **故障预测**：对硬盘进行 A/B/C 三种方案的故障预测
- **模块化执行**：提供统一的命令行接口驱动完整的数据处理到预测工作流

---

## 目录说明

```
h2o/
├── README.md                          # 本文件
├── proj/                              # 主项目目录
│   ├── src/                           # 核心源代码目录
│   │   ├── data_prep.py              # 数据预处理脚本：Excel➜CSV 转换
│   │   ├── datapreproc.py            # 数据预处理：字段清洗与验证
│   │   ├── gen_samps.py              # 样本生成脚本：生成训练/测试样本
│   │   ├── train_automl.py           # 模型训练脚本：H2O AutoML 训练
│   │   ├── predictor.py              # 预测脚本：应用模型进行预测
│   │   ├── h2o_run.py                # 主控脚本：驱动完整工作流
│   │   ├── utils.py                  # 通用工具函数库
│   │   ├── history_param.py          # 历史参数管理
│   │   └── test.py / test2.py        # 测试脚本
│   ├── config/                        # 配置文件目录
│   │   ├── h2o_run.ini               # 主配置文件（路径、参数）
│   │   ├── data_prep.ini             # 数据预处理配置
│   │   ├── datapreproc.ini           # 数据预处理参数
│   │   └── train-automl.ini          # 模型训练参数
│   ├── data/                          # 原始输入数据目录
│   │   ├── base_samples_2.csv        # 基础训练样本
│   │   ├── base_samples.csv
│   │   ├── test_samples_base_2.csv   # 基础测试样本
│   │   └── test_samples_base.csv
│   ├── sample/                        # 处理后的样本数据目录
│   │   ├── train_samples_2_A.csv     # A 方案训练样本
│   │   ├── train_samples_2_B.csv     # B 方案训练样本
│   │   ├── train_samples_2_Atest.csv
│   │   └── test_samples_2_*.csv      # 各方案测试样本
│   ├── models/                        # 训练后的模型目录
│   │   ├── GBM_1_AutoML_1_20251213_A/
│   │   ├── GBM_4_AutoML_1_20251215_B/
│   │   └── ...（包含多个已训练的模型版本）
│   ├── log/                           # 运行日志目录
│   ├── app/                           # 应用程序相关目录
│   │   └── input/                    # 应用输入目录
│   └── scripts/                       # 执行脚本目录
│       └── run.sh                    # Shell 运行脚本
├── data/                              # 备用数据目录
├── bk/, bk2/, srcbk2/, srcbk3/       # 备份目录（旧版本代码）
└── docs/                              # 文档目录

```
---

## 运行方式

### 前置条件
- Python 3.7+
- 已安装依赖包：`h2o`, `pandas`, `numpy`, `scikit-learn` 等
- 原始数据文件位于 `data/` 目录

### 方案一：完整工作流（推荐）

使用主控脚本 `h2o_run.py` 一键执行整个流程：

```bash
cd proj
python src/h2o_run.py
```

该脚本将按顺序执行：
1. 数据预处理（如需要）
2. 样本生成
3. 模型训练
4. 故障预测

### 方案二：分步执行

#### 步骤 1：数据预处理（可选）
如需从 Excel 转换为 CSV 格式：

```bash
cd proj
python src/data_prep.py
```

#### 步骤 2：生成训练/测试样本

```bash
cd proj
python src/gen_samps.py
```

配置文件：`config/data_prep.ini` 和 `config/gentrainsamps.ini`

#### 步骤 3：训练预测模型

```bash
cd proj
python src/train_automl.py
```

配置文件：`config/train-automl.ini`

**参数说明：**
- `max_models`：最多训练模型数量（默认：10）
- `max_runtime_secs`：最长训练时间（秒）
- `seed`：随机种子（保证可重现性）
- `target_column`：预测目标列名

#### 步骤 4：模型预测

```bash
cd proj
python src/predictor.py
```

配置文件：`config/h2o_run.ini`

**参数说明：**
- `mode`：预测模式（A/B/C）
- `model_path`：使用的模型路径
- `test_sample_path`：测试样本路径

### 配置文件说明

主配置文件：`proj/config/h2o_run.ini`

```ini
[Base_Path]
# 原始数据输入路径
raw_train_input_path = data/base_samples_2.csv
raw_test_input_path = data/test_samples_base_2.csv

[Sample_Path]
# 样本输出路径
train_sample_path = sample/train_samples_2.csv
test_sample_path = sample/test_samples_2.csv

[After_Train_Path]
# 模型和预测结果输出路径
model_path = models/
prediction_path = out/predictions.csv

[Train_Config]
# 训练参数
max_models = 10
max_runtime_secs = 3600
seed = 42
```

---

## 输入输出

### 输入数据格式

#### 原始数据（CSV）
```
device_id,date,bad_sectors,remapped_sectors,...
HD001,2025-01-01,0,5,...
HD001,2025-01-02,0,5,...
...
```

**必要字段：**
- `device_id`：硬盘编号（唯一标识）
- `date`：采集日期（yyyy-mm-dd 格式）
- `bad_sectors`：坏道数量（SMART 指标）
- `remapped_sectors`：已重映射扇区数（可选）

#### 样本数据（生成后）
```
device_id,date,bad_sectors_t0,bad_sectors_t1,...,bad_sectors_t7,label
HD001,2025-01-09,0,0,0,0,0,0,0,0,0
...
```

### 输出数据

#### 模型训练输出
- **模型文件**：`models/GBM_X_AutoML_Y_YYYYMMDD_MODE/`
  - H2O 二进制模型格式（可直接加载预测）
  
- **统计报告**：`out/dataset_statistics.csv`
  ```
  dataset_name,row_count,column_count,null_count,...
  train_samples_2_A,5000,10,0,...
  ```

#### 预测输出
- **预测结果**：`out/predictions_YYYYMMDD_MODE.csv`
  ```
  device_id,date,prediction,probability,...
  HD001,2025-02-15,1,0.85,...
  HD002,2025-02-15,0,0.15,...
  ```

---

## 常见问题

### Q1：如何修改预测目标或特征列？

**A：** 修改配置文件中的相关参数：
- `data_prep.ini`：`selected_fields` 字段指定要提取的列
- `train-automl.ini`：`target_column` 指定预测目标（如 `label`）
- `h2o_run.ini`：`feature_columns` 指定模型输入特征

### Q2：训练过程出现内存不足错误

**A：** 
1. 减小 `max_models` 参数（训练模型数量）
2. 减小样本集大小（在 `gen_samps.py` 中调整样本生成参数）
3. 增加系统虚拟内存或运行内存

### Q3：模型预测准确度不理想

**A：**
1. 检查输入数据质量（是否存在异常值、缺失值）
2. 扩大训练样本规模
3. 调整 `train-automl.ini` 中的训练参数：
   - 增加 `max_runtime_secs` 以获得更好的模型
   - 调整特征工程参数

### Q4：如何加载已训练的模型进行预测？

**A：** 在 `h2o_run.ini` 中指定 `model_path`，例如：
```ini
[After_Train_Path]
model_path = models/GBM_4_AutoML_1_20251215_B/
```

然后运行：
```bash
python src/predictor.py
```

### Q5：数据格式不规范导致处理失败

**A：** 检查以下事项：
- 日期格式是否为 `yyyy-mm-dd`
- CSV 编码是否为 UTF-8
- 是否包含所有必要字段
- 数值字段是否含有非数字字符

运行 `data_prep.py` 和 `datapreproc.py` 进行数据清洗。

### Q6：如何切换不同的预测模式（A/B/C）？

**A：** 修改 `h2o_run.ini` 中的 `mode` 参数：
```ini
[Run_Config]
mode = A  # 或 B/C
```

每种模式对应不同的样本和训练配置。

### Q7：如何查看训练过程日志？

**A：** 日志保存在 `proj/log/` 目录，运行脚本时也会在控制台输出详细的执行信息。

---

## 技术栈

- **H2O AutoML**：自动化机器学习框架
- **Pandas/NumPy**：数据处理与分析
- **Python 3.7+**：编程语言
- **scikit-learn**：机器学习库（评估指标）

## 联系方式

项目作者：李小群（ChatGPT 协助开发）
日期：2025年12月

---

*最后更新：2026年1月23日*
