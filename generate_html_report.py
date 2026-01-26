#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成H2O项目代码分析报告 (使用openpyxl/csv生成，然后转换)
"""
import os
from datetime import datetime

def create_html_report():
    """创建HTML报告（可在浏览器中打开并保存为Word）"""
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H2O硬盘坏道预测项目 - 代码分析报告</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.8;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #003366;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
            border-bottom: 3px solid #003366;
            padding-bottom: 15px;
        }
        h2 {
            color: #0066cc;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 5px solid #0066cc;
            padding-left: 10px;
            font-size: 20px;
        }
        h3 {
            color: #0099ff;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .timestamp {
            text-align: center;
            color: #888;
            font-size: 12px;
            margin-bottom: 30px;
        }
        .toc {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .toc h2 {
            border-left: none;
            padding-left: 0;
            margin-top: 0;
        }
        .toc ul {
            margin-left: 20px;
        }
        .toc li {
            margin: 8px 0;
            color: #0066cc;
        }
        p {
            margin-bottom: 12px;
            text-align: justify;
        }
        ul {
            margin-left: 30px;
            margin-bottom: 15px;
        }
        li {
            margin: 8px 0;
        }
        .architecture {
            background-color: #f0f8ff;
            padding: 15px;
            border-left: 4px solid #0066cc;
            margin: 15px 0;
            font-family: monospace;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #003366;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f0f0f0;
        }
        .program-section {
            background-color: #fafafa;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            border-left: 4px solid #0099ff;
        }
        .program-section h3 {
            margin-top: 0;
            color: #0066cc;
        }
        .strong {
            color: #003366;
            font-weight: bold;
        }
        .success {
            color: #00aa00;
            font-weight: bold;
        }
        .warning {
            color: #ff6600;
            font-weight: bold;
        }
        .info {
            background-color: #e8f4f8;
            padding: 10px;
            border-left: 3px solid #0099ff;
            margin: 10px 0;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 11px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            .container {
                max-width: none;
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 标题 -->
        <h1>📊 H2O 硬盘坏道预测项目 - 代码分析报告</h1>
        <div class="timestamp">生成时间：''' + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") + '''</div>

        <!-- 目录 -->
        <div class="toc">
            <h2>📑 目录</h2>
            <ul>
                <li>1. 项目整体架构</li>
                <li>2. 各程序功能详解</li>
                <li>3. 程序依赖关系图</li>
                <li>4. 数据流转过程</li>
                <li>5. 配置文件体系</li>
                <li>6. 核心设计模式</li>
                <li>7. 代码质量问题</li>
                <li>8. 项目强点</li>
                <li>9. 附录：程序统计</li>
            </ul>
        </div>

        <!-- 1. 项目整体架构 -->
        <h2>1. 项目整体架构</h2>
        <p>该项目是一个<span class="strong">模块化的机器学习系统</span>，包含11个Python程序，按功能分为以下<span class="strong">5个层级</span>：</p>
        <div class="architecture">主控层 (h2o_run.py)
    ↓
数据处理层 (data_prep.py, datapreproc.py, gen_samps.py)
    ↓
模型训练层 (train_automl.py)
    ↓
预测应用层 (predictor.py)
    ↓
辅助层 (utils.py, history_param.py, test.py, test2.py, train-automl2.py)</div>

        <!-- 2. 各程序功能详解 -->
        <h2>2. 各程序功能详解</h2>

        <div class="program-section">
            <h3>🔴 h2o_run.py (241行) - 系统总指挥</h3>
            <p><strong>角色：</strong>主控脚本，提供命令行界面</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li>初始化项目环境路径和模块搜索</li>
                <li>动态加载其他四个核心组件：gen_samps、train_automl、predictor、utils</li>
                <li>加载配置文件 (h2o_run.ini)</li>
                <li>顺序执行：样本生成 → 模型训练 → 故障预测</li>
            </ul>
            <p><strong>关键函数：</strong> clear_screen(), execute_component()</p>
            <p><strong>依赖：</strong> configparser, argparse, pathlib, gen_samps, train_automl, predictor, utils</p>
        </div>

        <div class="program-section">
            <h3>🟠 data_prep.py (407行) - 原始数据→CSV转换</h3>
            <p><strong>角色：</strong>数据预处理脚本</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li>读取Excel文件（支持自定义表头行数）</li>
                <li>字段抽取和数据验证</li>
                <li>按 device_id 和 date 排序</li>
                <li>生成POH（Power-On Hours）字段</li>
            </ul>
            <p><strong>关键函数：</strong> sort_func(), insert_poh_after_date_func(), print_df_structure()</p>
            <p><strong>输入/输出：</strong> Excel → CSV</p>
        </div>

        <div class="program-section">
            <h3>🟡 gen_samps.py (760行) - 特征工程的核心</h3>
            <p><strong>角色：</strong>样本生成脚本（最复杂的处理模块）</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li><strong>滞后特征</strong>（Lag Features）：基于配置的历史天数生成过去N天的特征值</li>
                <li><strong>增强特征</strong>（Extended Features）：计算差分、斜率等统计特征</li>
                <li><strong>目标标签生成</strong>：支持A/B/C三种预测方案</li>
                <li>生成训练样本和测试样本</li>
            </ul>
            <p><strong>关键函数：</strong> print_B_summary_func()</p>
            <p><strong>配置参数：</strong> lag_days_A/B, horizon_days_B, slope_window_B</p>
        </div>

        <div class="program-section">
            <h3>🟢 train_automl.py (279行) - 机器学习模型训练器</h3>
            <p><strong>角色：</strong>模型训练脚本</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li>初始化H2O集群</li>
                <li>加载训练样本</li>
                <li>配置AutoML参数并训练多个模型（GBM、GLM、XGBoost等）</li>
                <li>自动选择性能最好的模型（leader）</li>
                <li>保存模型和特征重要性</li>
                <li>使用测试样本验证模型</li>
            </ul>
            <p><strong>关键函数：</strong> save_feature_model_func(), test_model_func(), save_prediction_results_func()</p>
            <p><strong>配置参数：</strong> max_models, max_runtime_secs, seed</p>
        </div>

        <div class="program-section">
            <h3>🔵 predictor.py (143行) - 模型推理引擎</h3>
            <p><strong>角色：</strong>预测应用脚本</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li>加载历史训练的H2O模型</li>
                <li>为测试数据生成滞后特征（与训练时保持一致）</li>
                <li>调用模型进行预测</li>
                <li>对A方案预测结果进行调整（单调性约束）</li>
                <li>保存预测结果</li>
            </ul>
            <p><strong>关键函数：</strong> make_features_func(), predict_result_func(), save_prediction_results_func()</p>
        </div>

        <div class="program-section">
            <h3>🟣 utils.py (572行) - 全局工具函数库（核心公共库）</h3>
            <p><strong>角色：</strong>为其他所有模块提供通用工具函数</p>
            <p><strong>核心功能模块：</strong></p>
            <ul>
                <li><span class="strong">配置管理</span>：load_config_func()</li>
                <li><span class="strong">H2O模型操作</span>：h2o_init_func(), h2o_load_model_func(), h2o_predict_func()</li>
                <li><span class="strong">文件操作</span>：load_file_func(), customize_file_path_func()</li>
                <li><span class="strong">数据处理</span>：add_lag_features_func(), adjust_prediction_func()</li>
                <li><span class="strong">统计分析</span>：print_pred_result_func()</li>
            </ul>
            <p><span class="strong">被依赖程度</span>：☆☆☆☆☆（最高，被所有其他程序频繁调用）</p>
        </div>

        <div class="program-section">
            <h3>📋 history_param.py (129行) - 后处理和结果分析</h3>
            <p><strong>角色：</strong>预测结果的后处理和统计分析</p>
            <p><strong>核心功能：</strong></p>
            <ul>
                <li>加载预测结果文件</li>
                <li>删除滞后特征列（清理不需要的列）</li>
                <li>按硬盘聚合，保留坏道增长的关键记录</li>
                <li>按业务阈值筛选有效坏道阶段</li>
                <li>按坏道值进行统计分析</li>
            </ul>
        </div>

        <div class="program-section">
            <h3>🔄 train-automl2.py (197行) - 备选训练脚本</h3>
            <p><strong>特点：</strong>与 train_automl.py 类似但结构更简洁，直接在脚本内定义配置</p>
            <p><strong>用途：</strong>可能是早期版本或测试版本</p>
        </div>

        <div class="program-section">
            <h3>🧪 test.py、test2.py - 测试脚本</h3>
            <p><strong>特点：</strong>test.py 为空，test2.py 未被使用</p>
            <p><strong>用途：</strong>可能用于单元测试或组件测试</p>
        </div>

        <div class="program-section">
            <h3>📄 datapreproc.py (405行) - 数据预处理2</h3>
            <p><strong>特点：</strong>与 data_prep.py 基本相同，是冗余文件</p>
        </div>

        <!-- 3. 依赖关系 -->
        <h2>3. 程序依赖关系图</h2>
        <div class="architecture">h2o_run.py (主控)
  ├── → gen_samps.py (样本生成)
  │      └── → utils.py
  ├── → train_automl.py (模型训练)
  │      └── → utils.py
  ├── → predictor.py (预测应用)
  │      └── → utils.py
  └── → utils.py (工具库)

history_param.py (独立后处理)
  └── → utils.py

data_prep.py (可选的数据预处理)
datapreproc.py (冗余的数据预处理)
train-automl2.py (备选版本)
test.py, test2.py (测试脚本)</div>

        <!-- 4. 数据流转 -->
        <h2>4. 数据流转过程</h2>
        <div class="architecture">原始数据 (Excel/CSV)
    ↓
[data_prep.py] 格式转换
    ↓
base_samples_2.csv (原始样本)
    ↓
[gen_samps.py] 样本生成 + 特征工程
    ├→ train_samples_2_A.csv (A方案训练)
    ├→ train_samples_2_B.csv (B方案训练)
    └→ test_samples_2_A.csv (A方案测试)
    ↓
[train_automl.py] 模型训练
    ├→ models/GBM_X_AutoML_Y_*_MODE/
    └→ feature_importance_*.csv
    ↓
[predictor.py] 预测应用
    ├→ predictions_*.csv
    └→ app_out/*.csv
    ↓
[history_param.py] 后处理分析 (可选)
    └→ 统计报告</div>

        <!-- 5. 配置文件体系 -->
        <h2>5. 配置文件体系</h2>
        <table>
            <tr>
                <th>配置文件</th>
                <th>负责模块</th>
                <th>主要参数</th>
            </tr>
            <tr>
                <td>h2o_run.ini</td>
                <td>全局</td>
                <td>路径、模式(A/B/C)、目标列、内存配置</td>
            </tr>
            <tr>
                <td>data_prep.ini</td>
                <td>data_prep.py</td>
                <td>字段映射、输入输出路径</td>
            </tr>
            <tr>
                <td>train-automl.ini</td>
                <td>train_automl.py</td>
                <td>max_models、max_runtime_secs、seed</td>
            </tr>
            <tr>
                <td>datapreproc.ini</td>
                <td>datapreproc.py</td>
                <td>与data_prep.ini相同</td>
            </tr>
            <tr>
                <td>gentrainsamps.ini</td>
                <td>gen_samps.py</td>
                <td>lag_days、horizon_days、slope_window</td>
            </tr>
        </table>

        <!-- 6. 核心设计模式 -->
        <h2>6. 核心设计模式</h2>
        <ul>
            <li><strong>模块化设计</strong>：每个脚本独立负责一个功能</li>
            <li><strong>配置驱动</strong>：大量使用INI配置文件而非硬编码</li>
            <li><strong>工具库集中</strong>：utils.py 集中所有公共函数</li>
            <li><strong>多方案支持</strong>：A/B/C三种预测方案灵活切换</li>
            <li><strong>模型持久化</strong>：使用H2O原生格式保存模型，便于复用</li>
        </ul>

        <!-- 7. 代码质量问题 -->
        <h2>7. 代码质量问题</h2>
        <ul>
            <li><span class="warning">❌ 冗余代码</span>：data_prep.py 和 datapreproc.py 几乎完全相同</li>
            <li><span class="warning">❌ 重复功能</span>：train_automl.py 和 train-automl2.py 功能重复</li>
            <li><span class="warning">❌ 空文件</span>：test.py 为空，test2.py 未被使用</li>
            <li><span class="warning">❌ 注释不全</span>：某些函数缺乏详细的参数说明和返回值描述</li>
            <li><span class="warning">❌ 错误处理</span>：异常处理不够全面，某些关键函数缺少try-except</li>
        </ul>

        <!-- 8. 项目强点 -->
        <h2>8. 项目强点</h2>
        <ul>
            <li><span class="success">✓ 清晰的工作流程</span></li>
            <li><span class="success">✓ 模块化设计便于维护</span></li>
            <li><span class="success">✓ 支持多种预测方案</span></li>
            <li><span class="success">✓ 详细的日志输出</span></li>
            <li><span class="success">✓ 灵活的特征工程</span></li>
        </ul>

        <!-- 9. 附录 -->
        <h2>9. 附录：程序统计</h2>
        <table>
            <tr>
                <th>统计项目</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>总程序数</td>
                <td>11个</td>
            </tr>
            <tr>
                <td>代码总行数</td>
                <td>~3,200行</td>
            </tr>
            <tr>
                <td>主控脚本</td>
                <td>1个 (h2o_run.py)</td>
            </tr>
            <tr>
                <td>数据处理脚本</td>
                <td>3个</td>
            </tr>
            <tr>
                <td>模型训练脚本</td>
                <td>2个</td>
            </tr>
            <tr>
                <td>预测脚本</td>
                <td>1个</td>
            </tr>
            <tr>
                <td>工具库</td>
                <td>1个 (572行)</td>
            </tr>
            <tr>
                <td>后处理脚本</td>
                <td>1个</td>
            </tr>
            <tr>
                <td>测试脚本</td>
                <td>2个</td>
            </tr>
            <tr>
                <td>配置文件数</td>
                <td>5个</td>
            </tr>
            <tr>
                <td>最大单文件行数</td>
                <td>760行 (gen_samps.py)</td>
            </tr>
        </table>

        <div class="footer">
            <p>📄 H2O 硬盘坏道预测项目代码分析报告</p>
            <p>生成时间：''' + datetime.now().strftime("%Y年%m月%d日 %H:%M:%S") + '''</p>
            <p>本报告由自动化分析工具生成</p>
        </div>
    </div>
</body>
</html>'''
    
    output_path = r'd:\usr\百信公司项目\h2o\H2O项目代码分析报告.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ HTML报告已生成：{output_path}")
    return output_path

if __name__ == '__main__':
    create_html_report()
