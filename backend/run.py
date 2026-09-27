#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from main import main
    main()