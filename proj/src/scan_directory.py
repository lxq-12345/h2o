#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
程序名：scan_directory.py
功能：自动扫描目录并导出文件清单（支持 CSV 和 JSON 格式）
"""

import argparse
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="自动扫描目录并导出文件清单"
    )
    
    # 必填参数
    parser.add_argument(
        "--input_dir",
        required=True,
        help="要扫描的目录（必填）"
    )
    parser.add_argument(
        "--output_file",
        required=True,
        help="输出文件路径（必填）"
    )
    
    # 可选参数
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="是否递归扫描子目录（默认：True）"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="不递归扫描子目录"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="输出格式：csv 或 json（默认：csv）"
    )
    
    return parser.parse_args()


def validate_input_dir(input_dir: str) -> Path:
    """
    验证输入目录的有效性
    
    Args:
        input_dir: 输入目录路径字符串
    
    Returns:
        Path 对象
    
    Raises:
        SystemExit: 如果目录不存在或无权限
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"❌ 错误：输入目录不存在：{input_path}", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.is_dir():
        print(f"❌ 错误：输入路径不是目录：{input_path}", file=sys.stderr)
        sys.exit(1)
    
    # 检查读权限
    try:
        list(input_path.iterdir())
    except PermissionError:
        print(f"❌ 错误：无权限访问目录：{input_path}", file=sys.stderr)
        sys.exit(1)
    
    return input_path


def create_output_dir(output_file: str) -> Path:
    """
    创建输出文件的父目录（如果不存在）
    
    Args:
        output_file: 输出文件路径字符串
    
    Returns:
        Path 对象
    
    Raises:
        SystemExit: 如果创建目录失败
    """
    output_path = Path(output_file)
    parent_dir = output_path.parent
    
    try:
        parent_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ 错误：无法创建输出目录 {parent_dir}：{e}", file=sys.stderr)
        sys.exit(1)
    
    return output_path


def scan_directory(input_path: Path, recursive: bool) -> List[Dict[str, Any]]:
    """
    扫描目录并收集文件信息
    
    Args:
        input_path: 输入目录的 Path 对象
        recursive: 是否递归扫描
    
    Returns:
        文件信息列表，每项为字典
    """
    files_info = []
    
    try:
        # 选择扫描方式
        if recursive:
            file_paths = input_path.rglob("*")
        else:
            file_paths = input_path.glob("*")
        
        # 收集文件信息
        for file_path in file_paths:
            # 跳过目录，只处理文件
            if not file_path.is_file():
                continue
            
            try:
                # 获取文件基本信息
                stat_info = file_path.stat()
                size_bytes = stat_info.st_size
                
                # 创建时间（使用 st_mtime，因为 st_birthtime 在 Linux 不可用）
                # 为了跨平台兼容，使用修改时间作为替代
                created_time = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                # 文件扩展名
                file_ext = file_path.suffix  # 如 .py，无扩展名则为 ""
                
                # 构造信息字典
                file_info = {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "size_bytes": size_bytes,
                    "file_ext": file_ext,
                    "created_time": created_time
                }
                
                files_info.append(file_info)
            
            except (OSError, ValueError) as e:
                print(f"⚠️  警告：无法读取文件信息 {file_path}：{e}", file=sys.stderr)
                continue
    
    except Exception as e:
        print(f"❌ 错误：扫描目录失败：{e}", file=sys.stderr)
        sys.exit(1)
    
    # 按 file_path 排序
    files_info.sort(key=lambda x: x["file_path"])
    
    return files_info


def export_to_csv(files_info: List[Dict[str, Any]], output_path: Path) -> None:
    """
    导出文件信息为 CSV 格式
    
    Args:
        files_info: 文件信息列表
        output_path: 输出文件路径
    """
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["file_name", "file_path", "size_bytes", "file_ext", "created_time"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 写表头
            writer.writeheader()
            
            # 写数据行
            writer.writerows(files_info)
        
        print(f"✅ 成功：文件清单已导出到 {output_path}")
        print(f"   共包含 {len(files_info)} 个文件")
    
    except Exception as e:
        print(f"❌ 错误：导出 CSV 失败：{e}", file=sys.stderr)
        sys.exit(1)


def export_to_json(files_info: List[Dict[str, Any]], output_path: Path) -> None:
    """
    导出文件信息为 JSON 格式
    
    Args:
        files_info: 文件信息列表
        output_path: 输出文件路径
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(files_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功：文件清单已导出到 {output_path}")
        print(f"   共包含 {len(files_info)} 个文件")
    
    except Exception as e:
        print(f"❌ 错误：导出 JSON 失败：{e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 验证输入目录
    input_path = validate_input_dir(args.input_dir)
    
    # 创建输出目录
    output_path = create_output_dir(args.output_file)
    
    # 扫描目录
    print(f"🔍 正在扫描目录：{input_path}")
    print(f"   递归模式：{'是' if args.recursive else '否'}")
    files_info = scan_directory(input_path, args.recursive)
    
    if not files_info:
        print("⚠️  警告：未找到任何文件")
    
    # 导出结果
    if args.format == "csv":
        export_to_csv(files_info, output_path)
    elif args.format == "json":
        export_to_json(files_info, output_path)


if __name__ == "__main__":
    main()
