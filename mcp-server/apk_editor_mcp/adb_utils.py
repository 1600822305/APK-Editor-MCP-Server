"""ADB工具集成"""
import subprocess
import os
import re
from pathlib import Path
from typing import Optional, List


def find_adb() -> Optional[str]:
    """查找adb路径"""
    # 常见路径
    possible_paths = [
        # Windows
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
        os.path.expandvars(r"%ANDROID_HOME%\platform-tools\adb.exe"),
        # Linux/Mac
        os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
        "/usr/local/bin/adb",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 尝试PATH中的adb
    return "adb"


def run_adb(args: List[str], timeout: int = 30) -> dict:
    """
    运行ADB命令
    
    Args:
        args: ADB参数列表
        timeout: 超时时间
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    adb = find_adb()
    cmd = [adb] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Command timed out after {timeout} seconds"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "adb not found. Please install Android SDK platform-tools."
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


def list_devices() -> dict:
    """
    列出所有连接的设备
    
    Returns:
        dict: {"success": bool, "devices": list, "error": str}
    """
    result = run_adb(["devices", "-l"])
    
    if not result["success"]:
        return {
            "success": False,
            "devices": [],
            "error": result["error"]
        }
    
    devices = []
    lines = result["output"].strip().split("\n")[1:]  # 跳过第一行标题
    
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                
                # 解析设备信息
                info = {"id": device_id, "status": status}
                
                # 提取model、device等信息
                for part in parts[2:]:
                    if ":" in part:
                        key, value = part.split(":", 1)
                        info[key] = value
                
                devices.append(info)
    
    return {
        "success": True,
        "devices": devices,
        "count": len(devices),
        "error": ""
    }


def install_apk(
    apk_path: str,
    device_id: Optional[str] = None,
    replace: bool = True,
    grant_permissions: bool = True
) -> dict:
    """
    安装APK
    
    Args:
        apk_path: APK文件路径
        device_id: 设备ID（可选，如果只有一个设备）
        replace: 是否替换已安装的应用
        grant_permissions: 是否自动授予权限
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    if not os.path.exists(apk_path):
        return {
            "success": False,
            "output": "",
            "error": f"APK not found: {apk_path}"
        }
    
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    args.append("install")
    
    if replace:
        args.append("-r")
    
    if grant_permissions:
        args.append("-g")
    
    args.append(apk_path)
    
    result = run_adb(args, timeout=120)
    
    # 检查是否安装成功
    if result["success"] and "Success" in result["output"]:
        return {
            "success": True,
            "output": result["output"],
            "error": ""
        }
    else:
        return {
            "success": False,
            "output": result["output"],
            "error": result["error"] or result["output"]
        }


def uninstall_app(package_name: str, device_id: Optional[str] = None) -> dict:
    """
    卸载应用
    
    Args:
        package_name: 包名
        device_id: 设备ID
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    args.extend(["uninstall", package_name])
    
    result = run_adb(args)
    
    if result["success"] and "Success" in result["output"]:
        return {
            "success": True,
            "output": result["output"],
            "error": ""
        }
    else:
        return result


def get_logcat(
    device_id: Optional[str] = None,
    filter_tag: Optional[str] = None,
    lines: int = 100,
    clear: bool = False
) -> dict:
    """
    获取logcat日志
    
    Args:
        device_id: 设备ID
        filter_tag: 过滤标签
        lines: 行数
        clear: 是否先清空日志
    
    Returns:
        dict: {"success": bool, "logs": str, "error": str}
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    if clear:
        run_adb(args + ["logcat", "-c"])
    
    args.append("logcat")
    args.extend(["-d", "-t", str(lines)])
    
    if filter_tag:
        args.append(f"{filter_tag}:*")
    
    result = run_adb(args, timeout=10)
    
    return {
        "success": result["success"],
        "logs": result["output"],
        "error": result["error"]
    }


def take_screenshot(
    output_path: str,
    device_id: Optional[str] = None
) -> dict:
    """
    截图
    
    Args:
        output_path: 输出路径
        device_id: 设备ID
    
    Returns:
        dict: {"success": bool, "screenshot_path": str, "error": str}
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    # 在设备上截图
    device_path = "/sdcard/screenshot.png"
    args.extend(["shell", "screencap", "-p", device_path])
    
    result = run_adb(args)
    if not result["success"]:
        return {
            "success": False,
            "screenshot_path": "",
            "error": result["error"]
        }
    
    # 拉取到本地
    pull_args = []
    if device_id:
        pull_args.extend(["-s", device_id])
    
    pull_args.extend(["pull", device_path, output_path])
    
    result = run_adb(pull_args)
    
    if result["success"]:
        return {
            "success": True,
            "screenshot_path": output_path,
            "error": ""
        }
    else:
        return {
            "success": False,
            "screenshot_path": "",
            "error": result["error"]
        }


def get_device_info(device_id: Optional[str] = None) -> dict:
    """
    获取设备信息
    
    Args:
        device_id: 设备ID
    
    Returns:
        dict: 设备信息
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    info = {}
    
    # 获取Android版本
    result = run_adb(args + ["shell", "getprop", "ro.build.version.release"])
    if result["success"]:
        info["android_version"] = result["output"].strip()
    
    # 获取设备型号
    result = run_adb(args + ["shell", "getprop", "ro.product.model"])
    if result["success"]:
        info["model"] = result["output"].strip()
    
    # 获取设备品牌
    result = run_adb(args + ["shell", "getprop", "ro.product.brand"])
    if result["success"]:
        info["brand"] = result["output"].strip()
    
    # 获取SDK版本
    result = run_adb(args + ["shell", "getprop", "ro.build.version.sdk"])
    if result["success"]:
        info["sdk_version"] = result["output"].strip()
    
    # 获取CPU架构
    result = run_adb(args + ["shell", "getprop", "ro.product.cpu.abi"])
    if result["success"]:
        info["cpu_abi"] = result["output"].strip()
    
    return {
        "success": True,
        "info": info,
        "error": ""
    }


def list_installed_packages(
    device_id: Optional[str] = None,
    filter_text: Optional[str] = None
) -> dict:
    """
    列出已安装的应用
    
    Args:
        device_id: 设备ID
        filter_text: 过滤文本
    
    Returns:
        dict: {"success": bool, "packages": list, "error": str}
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    args.extend(["shell", "pm", "list", "packages"])
    
    if filter_text:
        args.append(filter_text)
    
    result = run_adb(args)
    
    if not result["success"]:
        return {
            "success": False,
            "packages": [],
            "error": result["error"]
        }
    
    packages = []
    for line in result["output"].strip().split("\n"):
        if line.startswith("package:"):
            packages.append(line.replace("package:", "").strip())
    
    return {
        "success": True,
        "packages": packages,
        "count": len(packages),
        "error": ""
    }


def clear_app_data(
    package_name: str,
    device_id: Optional[str] = None
) -> dict:
    """
    清除应用数据
    
    Args:
        package_name: 包名
        device_id: 设备ID
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    args = []
    if device_id:
        args.extend(["-s", device_id])
    
    args.extend(["shell", "pm", "clear", package_name])
    
    result = run_adb(args)
    
    if result["success"] and "Success" in result["output"]:
        return {
            "success": True,
            "output": result["output"],
            "error": ""
        }
    else:
        return result
