"""搜索工具"""
import re
from pathlib import Path
from typing import Optional


def search_in_files(
    directory: str,
    pattern: str,
    file_extensions: Optional[list[str]] = None,
    case_sensitive: bool = False,
    is_regex: bool = False,
    max_results: int = 100,
    context_lines: int = 2
) -> dict:
    """
    在文件中搜索内容
    
    Args:
        directory: 搜索目录
        pattern: 搜索模式
        file_extensions: 文件扩展名过滤 (如 [".smali", ".xml"])
        case_sensitive: 是否区分大小写
        is_regex: 是否使用正则表达式
        max_results: 最大结果数
        context_lines: 上下文行数
    
    Returns:
        dict: {"success": bool, "results": list, "error": str}
    """
    try:
        path = Path(directory)
        if not path.exists():
            return {"success": False, "results": [], "error": f"Directory not found: {directory}"}
        
        # 编译搜索模式
        flags = 0 if case_sensitive else re.IGNORECASE
        if is_regex:
            regex = re.compile(pattern, flags)
        else:
            regex = re.compile(re.escape(pattern), flags)
        
        results = []
        files_searched = 0
        
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # 扩展名过滤
            if file_extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in file_extensions]:
                    continue
            
            # 跳过二进制文件
            if file_path.suffix.lower() in [".dex", ".so", ".png", ".jpg", ".gif", ".zip", ".apk"]:
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")
                
                for i, line in enumerate(lines):
                    if regex.search(line):
                        # 获取上下文
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = lines[start:end]
                        
                        results.append({
                            "file": str(file_path.relative_to(path)),
                            "line_number": i + 1,
                            "line": line.strip(),
                            "context": context
                        })
                        
                        if len(results) >= max_results:
                            return {
                                "success": True,
                                "results": results,
                                "total_found": len(results),
                                "files_searched": files_searched,
                                "truncated": True,
                                "error": ""
                            }
                
                files_searched += 1
            
            except Exception:
                continue
        
        return {
            "success": True,
            "results": results,
            "total_found": len(results),
            "files_searched": files_searched,
            "truncated": False,
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "results": [], "error": str(e)}


def search_smali_method(
    directory: str,
    method_pattern: str,
    max_results: int = 50
) -> dict:
    """
    搜索smali方法调用
    
    Args:
        directory: smali目录
        method_pattern: 方法模式 (如 "Landroid/util/Log;->d")
        max_results: 最大结果数
    
    Returns:
        dict: {"success": bool, "results": list, "error": str}
    """
    return search_in_files(
        directory=directory,
        pattern=method_pattern,
        file_extensions=[".smali"],
        case_sensitive=True,
        is_regex=False,
        max_results=max_results
    )


def search_smali_string(
    directory: str,
    string_value: str,
    max_results: int = 50
) -> dict:
    """
    搜索smali中的字符串常量
    
    Args:
        directory: smali目录
        string_value: 字符串值
        max_results: 最大结果数
    
    Returns:
        dict: {"success": bool, "results": list, "error": str}
    """
    # smali中字符串格式: const-string vX, "xxx"
    pattern = f'const-string.*"{re.escape(string_value)}"'
    
    return search_in_files(
        directory=directory,
        pattern=pattern,
        file_extensions=[".smali"],
        case_sensitive=True,
        is_regex=True,
        max_results=max_results
    )


def list_smali_classes(directory: str) -> dict:
    """
    列出所有smali类
    
    Args:
        directory: 项目目录
    
    Returns:
        dict: {"success": bool, "classes": list, "error": str}
    """
    try:
        path = Path(directory)
        if not path.exists():
            return {"success": False, "classes": [], "error": f"Directory not found: {directory}"}
        
        classes = []
        
        # 查找所有smali目录
        smali_dirs = list(path.glob("smali*"))
        
        for smali_dir in smali_dirs:
            for smali_file in smali_dir.rglob("*.smali"):
                # 从路径推断类名
                rel_path = smali_file.relative_to(smali_dir)
                class_name = "L" + str(rel_path).replace("\\", "/").replace(".smali", "") + ";"
                
                classes.append({
                    "class_name": class_name,
                    "file_path": str(smali_file.relative_to(path)),
                    "smali_dir": smali_dir.name
                })
        
        return {
            "success": True,
            "classes": classes,
            "total": len(classes),
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "classes": [], "error": str(e)}


def find_smali_class(directory: str, class_name: str) -> dict:
    """
    查找指定的smali类文件
    
    Args:
        directory: 项目目录
        class_name: 类名 (如 "Lcom/example/MainActivity;")
    
    Returns:
        dict: {"success": bool, "file_path": str, "error": str}
    """
    try:
        path = Path(directory)
        if not path.exists():
            return {"success": False, "file_path": "", "error": f"Directory not found: {directory}"}
        
        # 转换类名为文件路径
        # Lcom/example/MainActivity; -> com/example/MainActivity.smali
        if class_name.startswith("L") and class_name.endswith(";"):
            class_path = class_name[1:-1] + ".smali"
        else:
            class_path = class_name.replace(".", "/") + ".smali"
        
        # 在所有smali目录中查找
        smali_dirs = list(path.glob("smali*"))
        
        for smali_dir in smali_dirs:
            file_path = smali_dir / class_path
            if file_path.exists():
                return {
                    "success": True,
                    "file_path": str(file_path),
                    "relative_path": str(file_path.relative_to(path)),
                    "smali_dir": smali_dir.name,
                    "error": ""
                }
        
        return {
            "success": False,
            "file_path": "",
            "error": f"Class not found: {class_name}"
        }
    
    except Exception as e:
        return {"success": False, "file_path": "", "error": str(e)}
