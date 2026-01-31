#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
目录文件清单扫描工具
自动扫描指定目录并导出文件清单
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from datetime import datetime
import logging


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def collect_file_info(file_path):
    """
    收集单个文件的信息
    
    Args:
        file_path (Path): 文件路径对象
        
    Returns:
        dict: 包含文件信息的字典
    """
    try:
        stat_info = file_path.stat()
        # 获取创建时间（Windows）或修改时间（Linux/Mac）
        created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        
        # 获取文件扩展名
        file_ext = file_path.suffix if file_path.suffix else ""
        
        return {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'size_bytes': stat_info.st_size,
            'file_ext': file_ext,
            'created_time': created_time
        }
    except (OSError, PermissionError) as e:
        logger.warning(f"无法访问文件 {file_path}: {e}")
        return None


def scan_directory(input_dir, recursive=True):
    """
    扫描目录并收集文件信息
    
    Args:
        input_dir (str): 输入目录路径
        recursive (bool): 是否递归扫描子目录
        
    Returns:
        list: 文件信息列表
        
    Raises:
        FileNotFoundError: 目录不存在
        PermissionError: 无权限访问目录
    """
    input_path = Path(input_dir)
    
    # 验证目录存在性
    if not input_path.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {input_dir}")
    
    # 验证目录权限
    try:
        list(input_path.iterdir())
    except PermissionError:
        raise PermissionError(f"无权限访问目录: {input_dir}")
    
    # 扫描文件
    files_info = []
    
    if recursive:
        glob_pattern = '**/*'
    else:
        glob_pattern = '*'
    
    try:
        for item in input_path.glob(glob_pattern):
            # 只处理文件，跳过目录
            if item.is_file():
                file_info = collect_file_info(item)
                if file_info:
                    files_info.append(file_info)
    except PermissionError as e:
        raise PermissionError(f"扫描目录时权限不足: {e}")
    
    # 按file_path排序
    files_info.sort(key=lambda x: x['file_path'])
    
    return files_info


def export_to_csv(files_info, output_file):
    """
    将文件信息导出为CSV格式
    
    Args:
        files_info (list): 文件信息列表
        output_file (str): 输出文件路径
    """
    output_path = Path(output_file)
    
    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # CSV列名
    fieldnames = ['file_name', 'file_path', 'size_bytes', 'file_ext', 'created_time']
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(files_info)
        logger.info(f"CSV文件已生成: {output_file} ({len(files_info)} 个文件)")
    except IOError as e:
        raise IOError(f"无法写入CSV文件 {output_file}: {e}")


def export_to_json(files_info, output_file):
    """
    将文件信息导出为JSON格式
    
    Args:
        files_info (list): 文件信息列表
        output_file (str): 输出文件路径
    """
    output_path = Path(output_file)
    
    # 创建输出目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(files_info, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON文件已生成: {output_file} ({len(files_info)} 个文件)")
    except IOError as e:
        raise IOError(f"无法写入JSON文件 {output_file}: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='自动扫描目录并导出文件清单',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s --input_dir ./data --output_file list.csv
  %(prog)s --input_dir ./data --output_file list.json --format json
  %(prog)s --input_dir ./data --output_file list.csv --recursive false
        '''
    )
    
    # 必填参数
    parser.add_argument(
        '--input_dir',
        required=True,
        help='要扫描的目录（必填）'
    )
    parser.add_argument(
        '--output_file',
        required=True,
        help='输出文件路径（必填）'
    )
    
    # 可选参数
    parser.add_argument(
        '--recursive',
        type=lambda x: x.lower() in ('true', '1', 'yes', 'y'),
        default=True,
        help='是否递归扫描子目录（默认: true）'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='输出格式（默认: csv）'
    )
    
    args = parser.parse_args()
    
    try:
        # 扫描目录
        logger.info(f"开始扫描目录: {args.input_dir}")
        files_info = scan_directory(args.input_dir, recursive=args.recursive)
        logger.info(f"找到 {len(files_info)} 个文件")
        
        # 导出文件
        if args.format == 'json':
            export_to_json(files_info, args.output_file)
        else:  # csv
            export_to_csv(files_info, args.output_file)
        
        logger.info("操作完成")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"错误: {e}")
        return 1
    except NotADirectoryError as e:
        logger.error(f"错误: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"错误: {e}")
        return 1
    except IOError as e:
        logger.error(f"错误: {e}")
        return 1
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())