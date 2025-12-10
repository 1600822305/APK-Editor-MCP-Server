"""APKEditor.jar 封装"""
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from .config import APKEDITOR_JAR, JAVA_PATH, DEFAULT_TIMEOUT, WORKSPACE_DIR
import zipfile
import re


def ensure_workspace():
    """确保工作目录存在"""
    Path(WORKSPACE_DIR).mkdir(parents=True, exist_ok=True)
    return WORKSPACE_DIR


def run_apkeditor(args: list[str], timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    运行APKEditor命令
    
    Args:
        args: APKEditor参数列表
        timeout: 超时时间
    
    Returns:
        dict: {"success": bool, "output": str, "error": str}
    """
    if not Path(APKEDITOR_JAR).exists():
        return {
            "success": False,
            "output": "",
            "error": f"APKEditor.jar not found at: {APKEDITOR_JAR}"
        }
    
    cmd = [JAVA_PATH, "-jar", APKEDITOR_JAR] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
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
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


def decode_apk(
    apk_path: str,
    output_dir: Optional[str] = None,
    decode_type: str = "xml",
    skip_dex: bool = False,
    force: bool = True
) -> dict:
    """
    反编译APK
    
    Args:
        apk_path: APK文件路径
        output_dir: 输出目录（可选）
        decode_type: 反编译类型 [xml, json, raw]
        skip_dex: 是否跳过DEX反编译
        force: 是否强制覆盖
    
    Returns:
        dict: 执行结果
    """
    args = ["d", "-t", decode_type, "-i", apk_path]
    
    if output_dir:
        args.extend(["-o", output_dir])
    
    if skip_dex:
        args.append("-dex")
    
    if force:
        args.append("-f")
    
    return run_apkeditor(args)


def build_apk(
    project_dir: str,
    output_apk: Optional[str] = None,
    force: bool = True
) -> dict:
    """
    构建APK
    
    Args:
        project_dir: 项目目录
        output_apk: 输出APK路径（可选）
        force: 是否强制覆盖
    
    Returns:
        dict: 执行结果
    """
    args = ["b", "-i", project_dir]
    
    if output_apk:
        args.extend(["-o", output_apk])
    
    if force:
        args.append("-f")
    
    return run_apkeditor(args)


def merge_apk(
    input_path: str,
    output_apk: Optional[str] = None,
    force: bool = True
) -> dict:
    """
    合并分割的APK
    
    Args:
        input_path: 输入目录或文件
        output_apk: 输出APK路径（可选）
        force: 是否强制覆盖
    
    Returns:
        dict: 执行结果
    """
    args = ["m", "-i", input_path]
    
    if output_apk:
        args.extend(["-o", output_apk])
    
    if force:
        args.append("-f")
    
    return run_apkeditor(args)


def refactor_apk(
    apk_path: str,
    output_apk: Optional[str] = None,
    force: bool = True
) -> dict:
    """
    反资源混淆
    
    Args:
        apk_path: APK文件路径
        output_apk: 输出APK路径（可选）
        force: 是否强制覆盖
    
    Returns:
        dict: 执行结果
    """
    args = ["x", "-i", apk_path]
    
    if output_apk:
        args.extend(["-o", output_apk])
    
    if force:
        args.append("-f")
    
    return run_apkeditor(args)


def protect_apk(
    apk_path: str,
    output_apk: Optional[str] = None,
    force: bool = True
) -> dict:
    """
    保护/混淆APK
    
    Args:
        apk_path: APK文件路径
        output_apk: 输出APK路径（可选）
        force: 是否强制覆盖
    
    Returns:
        dict: 执行结果
    """
    args = ["p", "-i", apk_path]
    
    if output_apk:
        args.extend(["-o", output_apk])
    
    if force:
        args.append("-f")
    
    return run_apkeditor(args)


def get_apk_info(
    apk_path: str,
    verbose: bool = False,
    show_resources: bool = False,
    show_permissions: bool = False,
    show_activities: bool = False
) -> dict:
    """
    获取APK信息
    
    Args:
        apk_path: APK文件路径
        verbose: 详细模式
        show_resources: 显示资源
        show_permissions: 显示权限
        show_activities: 显示Activity
    
    Returns:
        dict: 执行结果
    """
    args = ["info", "-i", apk_path]
    
    if verbose:
        args.append("-v")
    
    if show_resources:
        args.append("-resources")
    
    if show_permissions:
        args.append("-permissions")
    
    if show_activities:
        args.append("-activities")
    
    return run_apkeditor(args)


def find_apksigner_jar() -> Optional[str]:
    """查找内嵌的apksigner.jar"""
    # 优先使用内嵌的jar
    script_dir = Path(__file__).parent.parent
    embedded_jar = script_dir / "libs" / "apksigner.jar"
    if embedded_jar.exists():
        return str(embedded_jar)
    return None


def find_apksigner() -> Optional[str]:
    """查找apksigner路径"""
    # 常见路径
    possible_paths = [
        # Windows Android SDK
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\build-tools"),
        os.path.expandvars(r"%ANDROID_HOME%\build-tools"),
        os.path.expandvars(r"%ANDROID_SDK_ROOT%\build-tools"),
        # Linux/Mac
        os.path.expanduser("~/Android/Sdk/build-tools"),
        "/usr/local/android-sdk/build-tools",
    ]
    
    for base_path in possible_paths:
        if not os.path.exists(base_path):
            continue
        # 查找最新版本
        try:
            versions = sorted(os.listdir(base_path), reverse=True)
            for version in versions:
                apksigner = os.path.join(base_path, version, "apksigner.bat" if os.name == "nt" else "apksigner")
                if os.path.exists(apksigner):
                    return apksigner
        except:
            pass
    
    # 尝试直接使用命令（如果在PATH中）
    return "apksigner"


def get_debug_keystore() -> tuple[str, str, str, str]:
    """获取debug keystore路径和密码"""
    keystore = os.path.expanduser("~/.android/debug.keystore")
    if not os.path.exists(keystore):
        # Windows路径
        keystore = os.path.expandvars(r"%USERPROFILE%\.android\debug.keystore")
    
    return keystore, "android", "androiddebugkey", "android"


def sign_apk(
    apk_path: str,
    output_path: Optional[str] = None,
    keystore: Optional[str] = None,
    keystore_pass: Optional[str] = None,
    key_alias: Optional[str] = None,
    key_pass: Optional[str] = None
) -> dict:
    """
    签名APK
    
    Args:
        apk_path: APK文件路径
        output_path: 输出路径（可选，默认覆盖原文件或添加_signed后缀）
        keystore: keystore路径（可选，默认使用debug.keystore）
        keystore_pass: keystore密码
        key_alias: key别名
        key_pass: key密码
    
    Returns:
        dict: {"success": bool, "output": str, "error": str, "signed_apk": str}
    """
    if not os.path.exists(apk_path):
        return {
            "success": False,
            "output": "",
            "error": f"APK not found: {apk_path}",
            "signed_apk": ""
        }
    
    # 使用debug keystore如果未指定
    if not keystore:
        keystore, keystore_pass, key_alias, key_pass = get_debug_keystore()
    
    if not os.path.exists(keystore):
        return {
            "success": False,
            "output": "",
            "error": f"Keystore not found: {keystore}. Please create debug.keystore first.",
            "signed_apk": ""
        }
    
    # 确定输出路径
    if not output_path:
        base, ext = os.path.splitext(apk_path)
        if base.endswith("_unsigned"):
            output_path = base.replace("_unsigned", "_signed") + ext
        else:
            output_path = f"{base}_signed{ext}"
    
    # 优先使用内嵌的apksigner.jar
    apksigner_jar = find_apksigner_jar()
    
    if apksigner_jar:
        # 使用内嵌jar
        cmd = [
            JAVA_PATH, "-jar", apksigner_jar, "sign",
            "--ks", keystore,
            "--ks-pass", f"pass:{keystore_pass}",
            "--ks-key-alias", key_alias,
            "--key-pass", f"pass:{key_pass}",
            "--out", output_path,
            apk_path
        ]
    else:
        # 使用系统apksigner
        apksigner = find_apksigner()
        cmd = [
            apksigner, "sign",
            "--ks", keystore,
            "--ks-pass", f"pass:{keystore_pass}",
            "--ks-key-alias", key_alias,
            "--key-pass", f"pass:{key_pass}",
            "--out", output_path,
            apk_path
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout or "APK signed successfully",
                "error": "",
                "signed_apk": output_path
            }
        else:
            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr or "Unknown error",
                "signed_apk": ""
            }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "apksigner not found. Please install Android SDK build-tools.",
            "signed_apk": ""
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "signed_apk": ""
        }


def verify_apk_signature(apk_path: str) -> dict:
    """
    验证APK签名
    
    Args:
        apk_path: APK文件路径
    
    Returns:
        dict: {"success": bool, "verified": bool, "output": str, "error": str}
    """
    if not os.path.exists(apk_path):
        return {
            "success": False,
            "verified": False,
            "output": "",
            "error": f"APK not found: {apk_path}"
        }
    
    # 优先使用内嵌的apksigner.jar
    apksigner_jar = find_apksigner_jar()
    
    if apksigner_jar:
        cmd = [JAVA_PATH, "-jar", apksigner_jar, "verify", "-v", apk_path]
    else:
        apksigner = find_apksigner()
        cmd = [apksigner, "verify", "-v", apk_path]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": True,
            "verified": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except FileNotFoundError:
        return {
            "success": False,
            "verified": False,
            "output": "",
            "error": "apksigner not found"
        }
    except Exception as e:
        return {
            "success": False,
            "verified": False,
            "output": "",
            "error": str(e)
        }


def fast_manifest_read(apk_path: str) -> dict:
    """
    快速读取APK中的AndroidManifest.xml
    使用APKEditor解码后读取
    
    Args:
        apk_path: APK文件路径
    
    Returns:
        dict: {"success": bool, "manifest": str, "error": str}
    """
    if not os.path.exists(apk_path):
        return {
            "success": False,
            "manifest": "",
            "error": f"APK not found: {apk_path}"
        }
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="manifest_")
    
    try:
        # 使用APKEditor解码（只解码manifest）
        result = run_apkeditor([
            "d", "-t", "xml", "-i", apk_path, "-o", temp_dir, "-f"
        ], timeout=60)
        
        if not result["success"]:
            return {
                "success": False,
                "manifest": "",
                "error": result.get("error", "Failed to decode APK")
            }
        
        # 读取AndroidManifest.xml
        manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
        if not os.path.exists(manifest_path):
            # 尝试其他可能的路径
            for root, dirs, files in os.walk(temp_dir):
                if "AndroidManifest.xml" in files:
                    manifest_path = os.path.join(root, "AndroidManifest.xml")
                    break
        
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_content = f.read()
            return {
                "success": True,
                "manifest": manifest_content,
                "error": "",
                "temp_dir": temp_dir  # 保留临时目录用于修改
            }
        else:
            return {
                "success": False,
                "manifest": "",
                "error": "AndroidManifest.xml not found in decoded APK"
            }
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": False,
            "manifest": "",
            "error": str(e)
        }


def fast_manifest_modify(
    apk_path: str,
    new_manifest: str,
    output_path: Optional[str] = None
) -> dict:
    """
    快速修改APK中的AndroidManifest.xml
    
    Args:
        apk_path: APK文件路径
        new_manifest: 新的AndroidManifest.xml内容
        output_path: 输出路径（可选）
    
    Returns:
        dict: {"success": bool, "output_apk": str, "error": str}
    """
    if not os.path.exists(apk_path):
        return {
            "success": False,
            "output_apk": "",
            "error": f"APK not found: {apk_path}"
        }
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="manifest_mod_")
    
    try:
        # 1. 解码APK
        result = run_apkeditor([
            "d", "-t", "xml", "-i", apk_path, "-o", temp_dir, "-f"
        ], timeout=120)
        
        if not result["success"]:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False,
                "output_apk": "",
                "error": f"Failed to decode APK: {result.get('error', '')}"
            }
        
        # 2. 找到并修改AndroidManifest.xml
        manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
        if not os.path.exists(manifest_path):
            for root, dirs, files in os.walk(temp_dir):
                if "AndroidManifest.xml" in files:
                    manifest_path = os.path.join(root, "AndroidManifest.xml")
                    break
        
        if not os.path.exists(manifest_path):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False,
                "output_apk": "",
                "error": "AndroidManifest.xml not found"
            }
        
        # 写入新的manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(new_manifest)
        
        # 3. 重新构建APK
        if not output_path:
            base, ext = os.path.splitext(apk_path)
            output_path = f"{base}_manifest_modified{ext}"
        
        result = run_apkeditor([
            "b", "-i", temp_dir, "-o", output_path, "-f"
        ], timeout=180)
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result["success"]:
            return {
                "success": True,
                "output_apk": output_path,
                "error": ""
            }
        else:
            return {
                "success": False,
                "output_apk": "",
                "error": f"Failed to build APK: {result.get('error', '')}"
            }
    
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": False,
            "output_apk": "",
            "error": str(e)
        }


def fast_manifest_patch(
    apk_path: str,
    patches: list[dict],
    output_path: Optional[str] = None
) -> dict:
    """
    快速修补AndroidManifest.xml（正则替换）
    
    Args:
        apk_path: APK文件路径
        patches: 补丁列表 [{"find": "pattern", "replace": "replacement"}, ...]
        output_path: 输出路径（可选）
    
    Returns:
        dict: {"success": bool, "output_apk": str, "patches_applied": int, "error": str}
    """
    # 先读取manifest
    read_result = fast_manifest_read(apk_path)
    if not read_result["success"]:
        return {
            "success": False,
            "output_apk": "",
            "patches_applied": 0,
            "error": read_result["error"]
        }
    
    manifest = read_result["manifest"]
    patches_applied = 0
    
    # 应用补丁
    for patch in patches:
        find = patch.get("find", "")
        replace = patch.get("replace", "")
        if find:
            new_manifest = re.sub(find, replace, manifest)
            if new_manifest != manifest:
                patches_applied += 1
                manifest = new_manifest
    
    if patches_applied == 0:
        return {
            "success": True,
            "output_apk": "",
            "patches_applied": 0,
            "error": "No patches matched"
        }
    
    # 修改manifest
    modify_result = fast_manifest_modify(apk_path, manifest, output_path)
    modify_result["patches_applied"] = patches_applied
    return modify_result
