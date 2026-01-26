#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动文件搜索程序
遍历指定目录，收集文件信息并导出到输出文件
"""

# 命令行参数解析（解析用户传入的 --input_dir 和 --output_file）
import argparse
# 访问系统相关功能（用于写错误到 stderr、退出程序等）
import sys
# CSV 读写支持（用于将文件信息写入 CSV 输出文件）
import csv
# Path 类用于路径操作、遍历文件系统
from pathlib import Path
# 处理和格式化日期时间（用于文件创建时间的格式化）
from datetime import datetime
import argparse
import sys
import csv
from pathlib import Path

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动文件搜索程序
遍历指定目录，收集文件信息并导出到输出文件
"""

# 导入所需模块


# 获取文件信息
def get_file_info(file_path: Path) -> dict:
    try:
        stat_info = file_path.stat()
        file_name = file_path.name                     # 文件名
        file_size = stat_info.st_size                  # 文件大小（字节）
        file_ext = file_path.suffix or "无扩展名"      # 文件类型/扩展名
        created_time = datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")  # 文件创建日期（ISO 8601 格式）
        return {
            "文件名": file_name,
            "文件大小(字节)": file_size,
            "文件类型": file_ext,
            "创建日期": created_time
        }
    except (OSError, IOError) as e:
        print(f"警告：无法访问文件 {file_path}：{e}", file=sys.stderr)
        return None


# 递归遍历目录并收集文件信息
def scan_directory(input_dir: Path) -> list:
    file_list = []  # 存放收集到的文件信息
    try:
        # 检查目录是否存在
        if not input_dir.exists():
            raise FileNotFoundError(f"目录不存在：{input_dir}")
        if not input_dir.is_dir():
            raise NotADirectoryError(f"路径不是一个目录：{input_dir}")
        # 递归遍历所有文件
        for item in input_dir.rglob("*"):
            if item.is_file():  # 只处理文件，不处理目录
                file_info = get_file_info(item)
                if file_info is not None:
                    file_list.append(file_info)
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


# 保存文件信息到输出文件
def save_to_file(file_list: list, output_file: Path) -> None:
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)  # 创建输出目录（如果不存在）
        fieldnames = ["文件名", "文件大小(字节)", "文件类型", "创建日期"]  # CSV 表头
        with open(output_file, "w", newline="", encoding="utf-8") as f:  # 写入 CSV 文件
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(file_list)
        print(f"✓ 成功扫描并保存文件清单")
        print(f"  输出文件：{output_file}")
        print(f"  文件总数：{len(file_list)}")
    except IOError as e:
        print(f"错误：无法写入输出文件 {output_file}：{e}", file=sys.stderr)
        sys.exit(1)


# 主函数
def main():
    parser = argparse.ArgumentParser(
        description="自动搜索文件程序 - 遍历目录并导出文件清单",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python test2.py --input_dir ./data --output_file ./file_list.csv
  python test2.py --input_dir d:\\projects\\data --output_file output.csv
        """
    )  # 命令行参数解析器
    parser.add_argument(
        "--input_dir",
        required=True,
        help="文件目录名（必填）"
    )
    parser.add_argument(
        "--output_file",
        required=True,
        help="输出文件路径（必填）"
    )
    args = parser.parse_args()  # 解析命令行参数
    input_dir = Path(args.input_dir).resolve()    # 转换输入路径为 Path 对象
    output_file = Path(args.output_file).resolve()  # 转换输出路径为 Path 对象
    print(f"正在扫描目录：{input_dir}")  # 打印扫描目录信息
    # 遍历目录
    file_list = scan_directory(input_dir)
    # 保存文件清单到输出文件
    save_to_file(file_list, output_file)


if __name__ == "__main__":
    main()
# 获取文件信息
def get_file_info(file_path: Path) -> dict:
    try:
        stat_info = file_path.stat()
        # 文件名
        file_name = file_path.name
        # 文件大小（字节）
        file_size = stat_info.st_size
        # 文件类型/扩展名
        file_ext = file_path.suffix if file_path.suffix else "无扩展名"
        # 文件创建日期（ISO 8601 格式）
        created_time = datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "文件名": file_name,
            "文件大小(字节)": file_size,
            "文件类型": file_ext,
            "创建日期": created_time
        }
    except (OSError, IOError) as e:
        print(f"警告：无法访问文件 {file_path}：{e}", file=sys.stderr)
        return None


# 递归遍历目录并收集文件信息
def scan_directory(input_dir: Path) -> list:
    file_list = []
    try:
        # 检查目录是否存在
        if not input_dir.exists():
            raise FileNotFoundError(f"目录不存在：{input_dir}")
        if not input_dir.is_dir():
            raise NotADirectoryError(f"路径不是一个目录：{input_dir}")
        # 递归遍历所有文件
        for item in input_dir.rglob("*"):
            # 只处理文件，不处理目录
            if item.is_file():
                file_info = get_file_info(item)
                if file_info is not None:
                    file_list.append(file_info)
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


# 保存文件信息到输出文件
def save_to_file(file_list: list, output_file: Path) -> None:
    try:
        # 创建输出目录（如果不存在）
        output_file.parent.mkdir(parents=True, exist_ok=True)
        # 定义 CSV 表头
        fieldnames = ["文件名", "文件大小(字节)", "文件类型", "创建日期"]
        # 写入 CSV 文件
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(file_list)
        print(f"✓ 成功扫描并保存文件清单")
        print(f"  输出文件：{output_file}")
        print(f"  文件总数：{len(file_list)}")
    except IOError as e:
        print(f"错误：无法写入输出文件 {output_file}：{e}", file=sys.stderr)
        sys.exit(1)


# 主函数
def main():
    # 配置命令行参数
    parser = argparse.ArgumentParser(
        description="自动搜索文件程序 - 遍历目录并导出文件清单",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python test2.py --input_dir ./data --output_file ./file_list.csv
  python test2.py --input_dir d:\\projects\\data --output_file output.csv
        """
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="文件目录名（必填）"
    )
    parser.add_argument(
        "--output_file",
        required=True,
        help="输出文件路径（必填）"
    )
    # 解析命令行参数
    args = parser.parse_args()
    # 转换路径为 Path 对象
    input_dir = Path(args.input_dir).resolve()
    output_file = Path(args.output_file).resolve()
    # 遍历目录
    print(f"正在扫描目录：{input_dir}")
    file_list = scan_directory(input_dir)
    # 保存文件清单到输出文件
    save_to_file(file_list, output_file)


if __name__ == "__main__":
    main()
