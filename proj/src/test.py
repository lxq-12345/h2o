#!/usr/bin/env python3
get_file_info(file_path: Path) -> Optional[Dict[str, Any]]
获取单个文件的基本信息并以字典形式返回。
参数：
    file_path (Path): 要读取信息的文件路径对象。
返回：
    dict 或 None：成功时返回包含以下键的字典：
        - "file_name": 文件名（不含路径）
        - "file_path": 文件的完整路径（字符串）
        - "size_bytes": 文件大小（字节）
        - "file_ext": 文件扩展名（若无则空字符串）
        - "created_time": 创建时间（ISO 8601 字符串）
    如果因权限或 I/O 错误无法访问文件，返回 None 并将警告信息打印到 stderr。
行为与异常：
    捕获并处理 OSError/IOError，打印警告信息而不抛出异常。
scan_directory(input_dir: Path, recursive: bool) -> List[Dict[str, Any]]
扫描指定目录并收集其中所有文件的信息列表（通过 get_file_info 获取单文件信息）。
参数：
    input_dir (Path): 要扫描的目录路径（会先检查是否存在且为目录）。
    recursive (bool): 是否递归扫描子目录；True 使用 rglob("**/*")，False 使用 glob("*")。
返回：
    List[Dict[str, Any]]: 按 "file_path" 字段排序的文件信息字典列表。
行为与异常：
    - 若输入目录不存在或不是目录，打印错误信息到 stderr 并调用 sys.exit(1)。
    - 若权限不足，打印错误信息到 stderr 并调用 sys.exit(1)。
    - 仅对实际文件调用 get_file_info，忽略目录条目；跳过无法访问的文件（get_file_info 返回 None）。
export_csv(file_list: List[Dict[str, Any]], output_file: Path) -> None
将文件信息列表导出为 CSV 文件。
参数：
    file_list (List[Dict[str, Any]]): 要导出的文件信息字典列表（应包含与字段名对应的键）。
    output_file (Path): 输出 CSV 文件的目标路径；会在必要时创建父目录。
行为与异常：
    - 使用固定表头 ["file_name","file_path","size_bytes","file_ext","created_time"] 写入 CSV。
    - 文件以 UTF-8 编码写入并包含表头。
    - 写入成功时打印成功信息；若发生 I/O 错误，打印错误到 stderr 并调用 sys.exit(1)。
export_json(file_list: List[Dict[str, Any]], output_file: Path) -> None
将文件信息列表导出为 JSON 文件（UTF-8 编码，含缩进且不转义非 ASCII 字符）。
参数：
    file_list (List[Dict[str, Any]]): 要导出的文件信息字典列表。
    output_file (Path): 输出 JSON 文件的目标路径；会在必要时创建父目录。
行为与异常：
    - 使用 json.dump 写入，indent=2，ensure_ascii=False，以便可读且保留中文等字符。
    - 写入成功时打印成功信息；若发生 I/O 错误，打印错误到 stderr 并调用 sys.exit(1)。
main() -> None
命令行入口函数：解析参数、扫描目录并导出文件清单（CSV 或 JSON）。
行为：
    - 使用 argparse 定义并解析参数：
        --input_dir (required): 要扫描的目录路径
        --output_file (required): 导出文件路径
        --recursive / --no-recursive: 是否递归扫描（默认递归）
        --format: 输出格式，"csv" 或 "json"（默认 "csv"）
    - 将输入路径和输出路径转换为 Path.resolve()。
    - 调用 scan_directory 获取文件列表并打印找到的文件数量。
    - 根据 --format 调用 export_csv 或 export_json 导出结果。
    - 在流程中将关键操作和状态打印到 stdout，以便用户了解进度与结果。
# -*- coding: utf-8 -*-
"""
文件清单导出工具
自动扫描目录并导出文件信息列表（支持 CSV 和 JSON 格式）
"""

import argparse
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径对象
        
    Returns:
        包含文件信息的字典
    """
    try:
        stat_info = file_path.stat()
        # 获取创建时间，转换为 ISO 8601 格式
        created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        
        # 获取文件扩展名
        file_ext = file_path.suffix if file_path.suffix else ""
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "size_bytes": stat_info.st_size,
            "file_ext": file_ext,
            "created_time": created_time
        }
    except (OSError, IOError) as e:
        print(f"警告：无法访问文件 {file_path}：{e}", file=sys.stderr)
        return None


def scan_directory(input_dir: Path, recursive: bool) -> List[Dict[str, Any]]:
    """
    扫描目录并收集文件信息
    
    Args:
        input_dir: 要扫描的目录路径
        recursive: 是否递归扫描子目录
        
    Returns:
        文件信息列表
    """
    file_list = []
    
    try:
        # 检查目录是否存在
        if not input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在：{input_dir}")
        
        if not input_dir.is_dir():
            raise NotADirectoryError(f"路径不是一个目录：{input_dir}")
        
        # 使用 glob 或 rglob 遍历文件
        pattern = "**/*" if recursive else "*"
        for item in input_dir.glob(pattern):
            # 只处理文件，不处理目录
            if item.is_file():
                file_info = get_file_info(item)
                if file_info is not None:
                    file_list.append(file_info)
        
        # 按 file_path 排序
        file_list.sort(key=lambda x: x["file_path"])
        
        return file_list
    
    except FileNotFoundError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"错误：权限不足，无法访问目录 {input_dir}：{e}", file=sys.stderr)
        sys.exit(1)


def export_csv(file_list: List[Dict[str, Any]], output_file: Path) -> None:
    """
    导出为 CSV 格式
    
    Args:
        file_list: 文件信息列表
        output_file: 输出文件路径
    """
    try:
        # 创建输出目录（如果不存在）
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 定义 CSV 表头
        fieldnames = ["file_name", "file_path", "size_bytes", "file_ext", "created_time"]
        
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(file_list)
        
        print(f"成功导出 CSV 文件：{output_file}")
    
    except IOError as e:
        print(f"错误：无法写入输出文件 {output_file}：{e}", file=sys.stderr)
        sys.exit(1)


def export_json(file_list: List[Dict[str, Any]], output_file: Path) -> None:
    """
    导出为 JSON 格式
    
    Args:
        file_list: 文件信息列表
        output_file: 输出文件路径
    """
    try:
        # 创建输出目录（如果不存在）
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(file_list, f, indent=2, ensure_ascii=False)
        
        print(f"成功导出 JSON 文件：{output_file}")
    
    except IOError as e:
        print(f"错误：无法写入输出文件 {output_file}：{e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主函数"""
    # 配置命令行参数
    parser = argparse.ArgumentParser(
        description="自动扫描目录并导出文件清单",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python test.py --input_dir ./data --output_file ./output.csv
  python test.py --input_dir ./data --output_file ./output.json --format json --no-recursive
        """
    )
    
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
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="递归扫描子目录（默认：True）"
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
        help="输出格式（默认：csv）"
    )
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 转换路径为 Path 对象
    input_dir = Path(args.input_dir).resolve()
    output_file = Path(args.output_file).resolve()
    
    # 扫描目录
    print(f"正在扫描目录：{input_dir}")
    print(f"递归扫描：{args.recursive}")
    file_list = scan_directory(input_dir, args.recursive)
    
    print(f"找到 {len(file_list)} 个文件")
    
    # 导出文件清单
    if args.format == "json":
        export_json(file_list, output_file)
    else:  # 默认 csv
        export_csv(file_list, output_file)


if __name__ == "__main__":
    main()
