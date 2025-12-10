"""配置文件"""
import os
from pathlib import Path

# APKEditor.jar 路径（需要用户配置或自动查找）
APKEDITOR_JAR = os.environ.get(
    "APKEDITOR_JAR", 
    str(Path(__file__).parent.parent / "libs" / "APKEditor.jar")
)

# 工作目录
WORKSPACE_DIR = os.environ.get(
    "APK_WORKSPACE",
    str(Path(__file__).parent.parent / "workspace")
)

# Java路径
JAVA_PATH = os.environ.get("JAVA_HOME", "java")
if JAVA_PATH != "java" and not JAVA_PATH.endswith("java"):
    JAVA_PATH = str(Path(JAVA_PATH) / "bin" / "java")

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 300

# 最大文件大小（用于读取）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
