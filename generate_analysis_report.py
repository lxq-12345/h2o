#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成H2O项目代码分析报告Word文档
"""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime

def set_cell_background(cell, fill):
    """设置表格单元格背景色"""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), fill)
    cell._element.get_or_add_tcPr().append(shading_elm)

def create_report():
    """创建Word报告"""
    doc = Document()
    
    # 标题
    title = doc.add_heading('H2O 硬盘坏道预测项目 - 代码分析报告', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_format = title.runs[0]
    title_format.font.size = Pt(24)
    title_format.font.bold = True
    title_format.font.color.rgb = RGBColor(0, 51, 102)
    
    # 生成时间
    timestamp = doc.add_paragraph()
    timestamp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    timestamp_run = timestamp.add_run(f'生成日期：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}')
    timestamp_run.font.size = Pt(11)
    timestamp_run.font.color.rgb = RGBColor(128, 128, 128)
    
    doc.add_paragraph()  # 空行
    
    # 目录
    doc.add_heading('📑 目录', 1)
    toc_items = [
        '1. 项目整体架构',
        '2. 各程序功能详解',
        '3. 程序依赖关系图',
        '4. 数据流转过程',
        '5. 配置文件体系',
        '6. 核心设计模式',
        '7. 代码质量问题',
        '8. 项目强点'
    ]
    for item in toc_items:
        p = doc.add_paragraph(item, style='List Bullet')
    
    doc.add_page_break()
    
    # 1. 项目整体架构
    doc.add_heading('1. 项目整体架构', 1)
    doc.add_paragraph('该项目是一个模块化的机器学习系统，包含11个Python程序，按功能分为以下5个层级：')
    
    arch = doc.add_paragraph()
    arch_text = '''主控层 (h2o_run.py)
    ↓
数据处理层 (data_prep.py, datapreproc.py, gen_samps.py)
    ↓
模型训练层 (train_automl.py)
    ↓
预测应用层 (predictor.py)
    ↓
辅助层 (utils.py, history_param.py, test.py, test2.py, train-automl2.py)'''
    arch.text = arch_text
    arch.style = 'List Bullet'
    arch.paragraph_format.left_indent = Inches(0.5)
    
    # 2. 各程序功能详解
    doc.add_heading('2. 各程序功能详解', 1)
    
    programs = [
        {
            'name': 'h2o_run.py (241行)',
            'role': '系统总指挥',
            'functions': [
                '初始化项目环境路径和模块搜索',
                '动态加载其他四个核心组件',
                '加载配置文件',
                '顺序执行：样本生成 → 模型训练 → 故障预测'
            ]
        },
        {
            'name': 'data_prep.py (407行)',
            'role': '原始数据→CSV转换',
            'functions': [
                '读取Excel文件（支持自定义表头行数）',
                '字段抽取和数据验证',
                '按 device_id 和 date 排序',
                '生成POH（Power-On Hours）字段'
            ]
        },
        {
            'name': 'gen_samps.py (760行)',
            'role': '特征工程的核心',
            'functions': [
                '生成滞后特征（Lag Features）',
                '计算增强特征（diff、slope等）',
                '生成A/B/C三种预测方案的目标标签',
                '生成训练和测试样本'
            ]
        },
        {
            'name': 'train_automl.py (279行)',
            'role': '机器学习模型训练器',
            'functions': [
                '初始化H2O集群',
                '加载训练样本',
                '配置AutoML参数并训练多个模型',
                '自动选择性能最好的模型',
                '保存模型和特征重要性'
            ]
        },
        {
            'name': 'predictor.py (143行)',
            'role': '模型推理引擎',
            'functions': [
                '加载历史训练的H2O模型',
                '为测试数据生成滞后特征',
                '调用模型进行预测',
                '对A方案预测结果进行调整',
                '保存预测结果'
            ]
        },
        {
            'name': 'utils.py (572行)',
            'role': '全局工具函数库（核心公共库）',
            'functions': [
                '配置管理：load_config_func()',
                'H2O模型操作：h2o_init_func(), h2o_load_model_func()',
                '文件操作：load_file_func(), customize_file_path_func()',
                '数据处理：add_lag_features_func(), adjust_prediction_func()',
                '统计分析：print_pred_result_func()'
            ]
        },
        {
            'name': 'history_param.py (129行)',
            'role': '后处理和结果分析',
            'functions': [
                '加载预测结果文件',
                '删除滞后特征列',
                '按硬盘聚合关键记录',
                '按业务阈值筛选',
                '按坏道值进行统计分析'
            ]
        }
    ]
    
    for prog in programs:
        doc.add_heading(prog['name'], 2)
        
        # 角色和功能
        p = doc.add_paragraph()
        p.add_run('角色：').bold = True
        p.add_run(prog['role'])
        
        doc.add_paragraph('核心功能：', style='List Bullet')
        for func in prog['functions']:
            doc.add_paragraph(func, style='List Bullet 2')
    
    # 3. 依赖关系
    doc.add_heading('3. 程序依赖关系图', 1)
    
    dep_text = '''h2o_run.py (主控)
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
test.py, test2.py (测试脚本)'''
    
    dep_para = doc.add_paragraph(dep_text)
    dep_para.style = 'Normal'
    dep_para.paragraph_format.left_indent = Inches(0.3)
    
    # 4. 数据流转过程
    doc.add_heading('4. 数据流转过程', 1)
    
    data_flow = '''原始数据 (Excel/CSV)
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
    └→ 统计报告'''
    
    flow_para = doc.add_paragraph(data_flow)
    flow_para.style = 'Normal'
    flow_para.paragraph_format.left_indent = Inches(0.3)
    
    # 5. 配置文件体系
    doc.add_heading('5. 配置文件体系', 1)
    
    table = doc.add_table(rows=6, cols=3)
    table.style = 'Light Grid Accent 1'
    
    # 表头
    header_cells = table.rows[0].cells
    headers = ['配置文件', '负责模块', '主要参数']
    for i, header_text in enumerate(headers):
        header_cells[i].text = header_text
        for paragraph in header_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # 表格数据
    configs = [
        ('h2o_run.ini', '全局', '路径、模式(A/B/C)、目标列、内存配置'),
        ('data_prep.ini', 'data_prep.py', '字段映射、输入输出路径'),
        ('train-automl.ini', 'train_automl.py', 'max_models、max_runtime_secs、seed'),
        ('datapreproc.ini', 'datapreproc.py', '与data_prep.ini相同'),
        ('gentrainsamps.ini', 'gen_samps.py', 'lag_days、horizon_days、slope_window'),
    ]
    
    for i, (cfg, module, params) in enumerate(configs, 1):
        row_cells = table.rows[i].cells
        row_cells[0].text = cfg
        row_cells[1].text = module
        row_cells[2].text = params
    
    # 6. 核心设计模式
    doc.add_heading('6. 核心设计模式', 1)
    
    patterns = [
        '模块化设计：每个脚本独立负责一个功能',
        '配置驱动：大量使用INI配置文件而非硬编码',
        '工具库集中：utils.py 集中所有公共函数',
        '多方案支持：A/B/C三种预测方案灵活切换',
        '模型持久化：使用H2O原生格式保存模型，便于复用'
    ]
    
    for pattern in patterns:
        doc.add_paragraph(pattern, style='List Bullet')
    
    # 7. 代码质量问题
    doc.add_heading('7. 代码质量问题', 1)
    
    issues = [
        '冗余代码：data_prep.py 和 datapreproc.py 几乎完全相同',
        '重复功能：train_automl.py 和 train-automl2.py 功能重复',
        '空文件：test.py 为空，test2.py 未被使用',
        '注释不全：某些函数缺乏详细的参数说明和返回值描述',
        '错误处理：异常处理不够全面，某些关键函数缺少try-except'
    ]
    
    for issue in issues:
        doc.add_paragraph(issue, style='List Bullet')
    
    # 8. 项目强点
    doc.add_heading('8. 项目强点', 1)
    
    strengths = [
        '✓ 清晰的工作流程',
        '✓ 模块化设计便于维护',
        '✓ 支持多种预测方案',
        '✓ 详细的日志输出',
        '✓ 灵活的特征工程'
    ]
    
    for strength in strengths:
        doc.add_paragraph(strength, style='List Bullet')
    
    # 页脚
    doc.add_page_break()
    doc.add_heading('附录：程序统计', 1)
    
    summary_table = doc.add_table(rows=13, cols=2)
    summary_table.style = 'Light Grid Accent 1'
    
    summary_data = [
        ('统计项目', '数值'),
        ('总程序数', '11个'),
        ('代码总行数', '~3,200行'),
        ('主控脚本', '1个 (h2o_run.py)'),
        ('数据处理脚本', '3个'),
        ('模型训练脚本', '2个'),
        ('预测脚本', '1个'),
        ('工具库', '1个 (572行)'),
        ('后处理脚本', '1个'),
        ('测试脚本', '2个'),
        ('配置文件数', '5个'),
        ('最大单文件行数', '760行 (gen_samps.py)')
    ]
    
    for i, (label, value) in enumerate(summary_data):
        row_cells = summary_table.rows[i].cells
        row_cells[0].text = label
        row_cells[1].text = value
        if i == 0:
            for cell in row_cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
    
    # 保存
    output_path = r'd:\usr\百信公司项目\h2o\H2O项目代码分析报告.docx'
    doc.save(output_path)
    print(f"✅ Word文档已生成：{output_path}")
    return output_path

if __name__ == '__main__':
    create_report()
