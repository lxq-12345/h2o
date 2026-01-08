#!/bin/bash
# 进入工程根目录（proj），如果已在proj可忽略
cd "$(dirname "$0")"

# 切换到工程根目录
cd ..

# 创建日志目录
mkdir -p log

# 启动主流程脚本
python3 src/h2o_run.py 

