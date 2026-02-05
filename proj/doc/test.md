# test.py 使用说明

文件路径：[proj/src/test.py](proj/src/test.py)

## 概述

`test.py` 是一个目录文件清单扫描工具，自动扫描指定目录并导出文件清单（CSV 或 JSON）。适用于在本地文件系统中快速生成文件元数据清单，用于审计或数据准备。

## 依赖

- Python 标准库：`argparse`, `csv`, `json`, `sys`, `pathlib.Path`, `datetime`, `logging`。
- 无外部第三方依赖。

## 主要功能与接口

- `collect_file_info(file_path)`
  - 功能：收集单个文件的元信息（文件名、完整路径、大小、扩展名、创建时间）。
  - 参数：`file_path`（`Path` 对象）。
  - 返回：包含文件信息的 `dict`，若无法访问返回 `None`。

- `scan_directory(input_dir, recursive=True)`
  - 功能：扫描指定目录并返回文件信息列表。
  - 参数：`input_dir`（字符串或可传给 `Path` 的对象），`recursive`（是否递归子目录，默认 True）。
  - 行为：
    - 将 `input_dir` 转为 `Path` 对象并验证存在性与目录类型。
    - 通过 `glob` 模式 `**/*`（递归）或 `*`（非递归）遍历项，仅对文件调用 `collect_file_info`。
    - 捕获并上抛权限相关异常；最终按 `file_path` 排序并返回列表。
  - 返回：`list[dict]`，每项为文件信息字典。
  - 可能抛出：`FileNotFoundError`, `NotADirectoryError`, `PermissionError`。

- `export_to_csv(files_info, output_file)`
  - 功能：将文件信息列表写为 CSV 文件。
  - 参数：`files_info`（列表），`output_file`（目标路径）。
  - 行为：创建输出目录（如不存在），写入带表头的 CSV。
  - 可能抛出：`IOError`（写入失败）。

- `export_to_json(files_info, output_file)`
  - 功能：将文件信息列表写为 JSON 文件（UTF-8，保留中文）。
  - 参数：同上。
  - 可能抛出：`IOError`。

- `main()`
  - 功能：命令行入口，解析参数并触发扫描与导出。
  - 支持参数：
    - `--input_dir`（必填）
    - `--output_file`（必填）
    - `--recursive`（可选，接受 true/1/yes/y）
    - `--format`（可选，`csv` 或 `json`，默认 `csv`）
  - 行为：根据 `--format` 调用对应导出函数，并通过日志输出进度与错误。

## 使用示例

在命令行运行：

```powershell
python proj/src/test.py --input_dir ./data --output_file list.csv
python proj/src/test.py --input_dir ./data --output_file list.json --format json
```

## 日志与错误处理

- 使用 `logging` 输出信息与错误（默认级别 INFO）。
- 对于单文件访问失败，`collect_file_info` 会记录警告并跳过该文件；对目录不存在或权限问题，`scan_directory` 会抛出异常并由 `main` 捕获打印错误码。

## 建议改进

- 增加 `--exclude` 与 `--include` 参数以支持按模式过滤文件类型。
- 支持按多字段排序（例如按大小或创建时间）。
- 增加并行扫描以提升大目录的性能（例如使用线程池按块处理）。

---

文件已保存为 `proj/doc/test.md`。如需我将该说明插入到 `proj/src/test.py` 文件头或提交到 git，请告诉我。