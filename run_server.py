#!/usr/bin/env python
"""直接运行MCP服务器的脚本"""
import sys
import os

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 切换工作目录
os.chdir(SCRIPT_DIR)

# 添加到Python路径
sys.path.insert(0, SCRIPT_DIR)

# 设置环境变量
os.environ.setdefault("APKEDITOR_JAR", os.path.join(SCRIPT_DIR, "libs", "APKEditor.jar"))
os.environ.setdefault("DEX_EDITOR_JAR", os.path.join(SCRIPT_DIR, "libs", "dex-editor.jar"))
os.environ.setdefault("APK_WORKSPACE", os.path.join(SCRIPT_DIR, "workspace"))
os.environ.setdefault("JADX_PATH", os.path.join(SCRIPT_DIR, "libs", "jadx", "bin", "jadx.bat"))
os.environ.setdefault("WORKSPACE_DIR", SCRIPT_DIR)

from apk_editor_mcp.server import main

if __name__ == "__main__":
    main()
