"""
目录文件清单扫描工具
自动扫描指定目录并导出文件清单
"""
# 模块说明：目录文件清单扫描工具，自动扫描指定目录并导出文件清单

# 导入用于解析命令行参数的模块
import argparse
# 导入用于写入CSV文件的模块
import csv
# 导入用于写入JSON文件的模块
import json
# 导入与Python解释器交互的模块（用于退出码）
import sys
# 导入Path类以便跨平台处理路径
from pathlib import Path
# 导入datetime以格式化时间戳
from datetime import datetime
# 导入日志模块
import logging


# 配置基础日志，设置日志级别和输出格式
logging.basicConfig(
    level=logging.INFO,  # 日志级别为 INFO
    format='%(levelname)s: %(message)s'  # 日志输出格式
)
# 创建模块级别的 logger 实例
logger = logging.getLogger(__name__)


# 函数: collect_file_info — 收集单个文件的信息
def collect_file_info(file_path):
    """
    收集单个文件的信息
    
    Args:
        file_path (Path): 文件路径对象
        
    Returns:
        dict: 包含文件信息的字典
    """
    try:
        # 获取文件的状态信息（size、ctime等）
        stat_info = file_path.stat()
        # 将创建时间（或状态时间）转换为 ISO 格式字符串
        created_time = datetime.fromtimestamp(stat_info.st_ctime).isoformat()

        # 获取文件扩展名，如果不存在则为空字符串
        file_ext = file_path.suffix if file_path.suffix else ""

        # 返回包含文件关键信息的字典
        return {
            'file_name': file_path.name,  # 文件名
            'file_path': str(file_path),  # 完整路径字符串
            'size_bytes': stat_info.st_size,  # 文件大小（字节）
            'file_ext': file_ext,  # 文件扩展名
            'created_time': created_time  # 创建时间（ISO 格式）
        }
    except (OSError, PermissionError) as e:
        # 如果无法访问文件则记录警告并返回 None
        logger.warning(f"无法访问文件 {file_path}: {e}")
        return None


# 函数: scan_directory — 扫描目录并收集文件信息
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
    # 将输入路径转换为 Path 对象
    input_path = Path(input_dir)

    # 如果路径不存在则抛出 FileNotFoundError
    if not input_path.exists():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    # 如果路径不是目录则抛出 NotADirectoryError
    if not input_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {input_dir}")

    # 尝试列出目录以验证权限，如果失败则抛出 PermissionError
    try:
        list(input_path.iterdir())
    except PermissionError:
        raise PermissionError(f"无权限访问目录: {input_dir}")

    # 用于收集文件信息的列表
    files_info = []

    # 选择 glob 模式，递归或非递归
    if recursive:
        glob_pattern = '**/*'
    else:
        glob_pattern = '*'

    # 遍历匹配的路径，收集文件信息
    try:
        for item in input_path.glob(glob_pattern):
            # 仅处理文件，跳过目录
            if item.is_file():
                file_info = collect_file_info(item)
                # 只有在成功收集信息时才加入列表
                if file_info:
                    files_info.append(file_info)
    except PermissionError as e:
        # 如果在扫描过程中遇到权限问题则抛出异常
        raise PermissionError(f"扫描目录时权限不足: {e}")

    # 将结果按文件路径排序，保证输出稳定
    files_info.sort(key=lambda x: x['file_path'])

    # 返回收集到的文件信息列表
    return files_info


# 函数: export_to_csv — 将文件信息导出为 CSV 文件
def export_to_csv(files_info, output_file):
    """
    将文件信息导出为CSV格式
    
    Args:
        files_info (list): 文件信息列表
        output_file (str): 输出文件路径
    """
    # 将输出路径包装为 Path 对象
    output_path = Path(output_file)

    # 确保输出目录存在（必要时创建）
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 定义 CSV 的列名顺序
    fieldnames = ['file_name', 'file_path', 'size_bytes', 'file_ext', 'created_time']

    try:
        # 打开目标文件并写入 CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()  # 写入表头
            writer.writerows(files_info)  # 写入多行数据
        # 记录日志表示成功生成 CSV
        logger.info(f"CSV文件已生成: {output_file} ({len(files_info)} 个文件)")
    except IOError as e:
        # 如果写入失败则抛出 IOError
        raise IOError(f"无法写入CSV文件 {output_file}: {e}")


# 函数: export_to_json — 将文件信息导出为 JSON 文件
def export_to_json(files_info, output_file):
    """
    将文件信息导出为JSON格式
    
    Args:
        files_info (list): 文件信息列表
        output_file (str): 输出文件路径
    """
    # 将输出路径转换为 Path 对象
    output_path = Path(output_file)

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 打开文件并写入 JSON，使用 ensure_ascii=False 保持中文
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(files_info, f, ensure_ascii=False, indent=2)
        # 记录生成 JSON 的日志
        logger.info(f"JSON文件已生成: {output_file} ({len(files_info)} 个文件)")
    except IOError as e:
        # 写入失败则抛出异常
        raise IOError(f"无法写入JSON文件 {output_file}: {e}")


# 函数: main — 程序入口，解析参数并触发扫描与导出流程
def main():
    """主函数"""
    # 创建参数解析器并设置说明与示例 epilog
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

    # 添加必填参数 --input_dir
    parser.add_argument(
        '--input_dir',
        required=True,
        help='要扫描的目录（必填）'
    )
    # 添加必填参数 --output_file
    parser.add_argument(
        '--output_file',
        required=True,
        help='输出文件路径（必填）'
    )

    # 添加可选参数 --recursive，用于控制是否递归扫描
    parser.add_argument(
        '--recursive',
        type=lambda x: x.lower() in ('true', '1', 'yes', 'y'),
        default=True,
        help='是否递归扫描子目录（默认: true）'
    )
    # 添加可选参数 --format，用于指定输出格式 csv 或 json
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='输出格式（默认: csv）'
    )

    # 解析命令行参数
    args = parser.parse_args()

    try:
        # 记录开始扫描的日志
        logger.info(f"开始扫描目录: {args.input_dir}")
        # 执行目录扫描，得到文件信息列表
        files_info = scan_directory(args.input_dir, recursive=args.recursive)
        # 记录找到的文件数量
        logger.info(f"找到 {len(files_info)} 个文件")

        # 根据参数选择导出为 JSON 或 CSV
        if args.format == 'json':
            export_to_json(files_info, args.output_file)
        else:  # csv
            export_to_csv(files_info, args.output_file)

        # 操作完成日志并返回成功码
        logger.info("操作完成")
        return 0

    except FileNotFoundError as e:
        # 找不到目录时记录错误并返回失败码
        logger.error(f"错误: {e}")
        return 1
    except NotADirectoryError as e:
        # 路径不是目录时记录错误并返回失败码
        logger.error(f"错误: {e}")
        return 1
    except PermissionError as e:
        # 权限问题记录错误并返回失败码
        logger.error(f"错误: {e}")
        return 1
    except IOError as e:
        # IO 错误记录并返回失败码
        logger.error(f"错误: {e}")
        return 1
    except Exception as e:
        # 捕获其他未预期错误并记录
        logger.error(f"未预期的错误: {e}")
        return 1


# 如果作为脚本直接运行，则调用 main 并以其返回码退出
if __name__ == "__main__":
    sys.exit(main())