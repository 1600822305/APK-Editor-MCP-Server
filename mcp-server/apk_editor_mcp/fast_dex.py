"""
快速DEX编辑器 - Python包装器
调用 dex-editor.jar 实现内存级DEX编辑
"""
import os
import json
import subprocess
from typing import Optional, Dict, List, Any
from pathlib import Path

# 获取JAR路径
SCRIPT_DIR = Path(__file__).parent.parent
DEX_EDITOR_JAR = os.environ.get(
    "DEX_EDITOR_JAR",
    str(SCRIPT_DIR / "libs" / "dex-editor.jar")
)
JAVA_PATH = os.environ.get("JAVA_PATH", "java")


class FastDexEditor:
    """快速DEX编辑器 - 保持进程通信"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
    
    def _ensure_process(self):
        """确保进程在运行"""
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen(
                [JAVA_PATH, "-jar", DEX_EDITOR_JAR],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # 忽略stderr
                text=True,
                bufsize=1
            )
    
    def _send_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """发送命令并获取响应"""
        self._ensure_process()
        
        request = {"command": command, "args": args or []}
        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            
            # 读取多行JSON响应
            lines = []
            brace_count = 0
            started = False
            
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                # 计算花括号
                for ch in line:
                    if ch == '{':
                        brace_count += 1
                        started = True
                    elif ch == '}':
                        brace_count -= 1
                
                if started:
                    lines.append(line)
                
                # 当花括号配对完成时，JSON结束
                if started and brace_count == 0:
                    break
            
            if not lines:
                return {"success": False, "error": "No response from dex-editor"}
            
            response_text = "".join(lines)
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON parse error: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open(self, apk_path: str) -> Dict[str, Any]:
        """打开APK文件"""
        return self._send_command("open", [apk_path])
    
    def list_classes(self, dex_name: str = None) -> Dict[str, Any]:
        """列出所有类"""
        args = [dex_name] if dex_name else []
        return self._send_command("list_classes", args)
    
    def get_class(self, class_name: str) -> Dict[str, Any]:
        """获取类的smali代码"""
        return self._send_command("get_class", [class_name])
    
    def get_method(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """获取方法的smali代码"""
        return self._send_command("get_method", [class_name, method_name])
    
    def modify_class(self, class_name: str, smali_code: str) -> Dict[str, Any]:
        """修改类的smali代码"""
        return self._send_command("modify_class", [class_name, smali_code])
    
    def save(self, output_path: str = None) -> Dict[str, Any]:
        """保存修改"""
        args = [output_path] if output_path else []
        return self._send_command("save", args)
    
    def search_class(self, pattern: str) -> Dict[str, Any]:
        """搜索类"""
        return self._send_command("search_class", [pattern])
    
    def search_string(self, text: str) -> Dict[str, Any]:
        """搜索字符串"""
        return self._send_command("search_string", [text])
    
    def get_class_summary(self, class_name: str) -> Dict[str, Any]:
        """获取类摘要（方法列表、字段列表、代码长度）"""
        return self._send_command("summary", [class_name])
    
    def get_class_paged(self, class_name: str, offset: int = 0, limit: int = 0) -> Dict[str, Any]:
        """分页获取smali代码"""
        return self._send_command("get_paged", [class_name, str(offset), str(limit)])
    
    def to_java(self, class_name: str) -> Dict[str, Any]:
        """smali转Java"""
        return self._send_command("to_java", [class_name])
    
    def set_jadx_path(self, path: str) -> Dict[str, Any]:
        """设置jadx路径"""
        return self._send_command("set_jadx", [path])
    
    def close(self):
        """关闭编辑器"""
        if self.process is not None:
            try:
                self._send_command("close")
                self.process.terminate()
            except:
                pass
            self.process = None
    
    def __del__(self):
        self.close()


# 单例实例
_editor: Optional[FastDexEditor] = None


def get_editor() -> FastDexEditor:
    """获取编辑器单例"""
    global _editor
    if _editor is None:
        _editor = FastDexEditor()
    return _editor


# ===== MCP工具函数 =====

def fast_dex_open(apk_path: str) -> Dict[str, Any]:
    """快速打开APK（不解包，直接加载DEX到内存）"""
    editor = get_editor()
    # 自动设置jadx路径
    jadx_path = os.environ.get("JADX_PATH")
    if jadx_path:
        editor.set_jadx_path(jadx_path)
    return editor.open(apk_path)


def fast_dex_list_classes(dex_name: str = None) -> Dict[str, Any]:
    """列出所有类（从内存中读取，无需文件）"""
    return get_editor().list_classes(dex_name)


def fast_dex_get_class(class_name: str) -> Dict[str, Any]:
    """获取单个类的smali代码（按需反编译）"""
    return get_editor().get_class(class_name)


def fast_dex_get_method(class_name: str, method_name: str) -> Dict[str, Any]:
    """获取单个方法的smali代码"""
    return get_editor().get_method(class_name, method_name)


def fast_dex_modify_class(class_name: str, smali_code: str) -> Dict[str, Any]:
    """修改类的smali代码（内存操作）"""
    return get_editor().modify_class(class_name, smali_code)


def fast_dex_save(output_path: str = None) -> Dict[str, Any]:
    """保存修改到APK"""
    return get_editor().save(output_path)


def fast_dex_search_class(pattern: str) -> Dict[str, Any]:
    """搜索类名"""
    return get_editor().search_class(pattern)


def fast_dex_search_string(text: str) -> Dict[str, Any]:
    """搜索字符串"""
    return get_editor().search_string(text)


def fast_dex_close() -> Dict[str, Any]:
    """关闭编辑器"""
    get_editor().close()
    return {"success": True}


def fast_dex_summary(class_name: str) -> Dict[str, Any]:
    """获取类摘要（方法列表、字段、代码长度）"""
    return get_editor().get_class_summary(class_name)


def fast_dex_get_paged(class_name: str, offset: int = 0, limit: int = 10000) -> Dict[str, Any]:
    """分页获取smali代码"""
    return get_editor().get_class_paged(class_name, offset, limit)


def fast_dex_to_java(class_name: str) -> Dict[str, Any]:
    """smali转Java代码"""
    return get_editor().to_java(class_name)


def fast_dex_deobfuscate(class_name: str) -> Dict[str, Any]:
    """反混淆并转Java"""
    return get_editor()._send_command("deobf", [class_name])


def fast_dex_decompile_package(pattern: str) -> Dict[str, Any]:
    """批量反编译包"""
    return get_editor()._send_command("batch_decompile", [pattern])
