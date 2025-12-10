"""Smali代码处理工具"""
import re
from pathlib import Path
from typing import Optional


def parse_smali_class(content: str) -> dict:
    """
    解析smali类文件内容
    
    Args:
        content: smali文件内容
    
    Returns:
        dict: 解析后的类信息
    """
    result = {
        "class_name": "",
        "super_class": "",
        "source_file": "",
        "interfaces": [],
        "fields": [],
        "methods": []
    }
    
    lines = content.split("\n")
    current_method = None
    method_lines = []
    
    for line in lines:
        line = line.strip()
        
        # 类名
        if line.startswith(".class"):
            match = re.search(r"\.class\s+.*?(L[\w/$]+;)", line)
            if match:
                result["class_name"] = match.group(1)
        
        # 父类
        elif line.startswith(".super"):
            match = re.search(r"\.super\s+(L[\w/$]+;)", line)
            if match:
                result["super_class"] = match.group(1)
        
        # 源文件
        elif line.startswith(".source"):
            match = re.search(r'\.source\s+"([^"]+)"', line)
            if match:
                result["source_file"] = match.group(1)
        
        # 接口
        elif line.startswith(".implements"):
            match = re.search(r"\.implements\s+(L[\w/$]+;)", line)
            if match:
                result["interfaces"].append(match.group(1))
        
        # 字段
        elif line.startswith(".field"):
            match = re.search(r"\.field\s+(\S+)\s+(\S+):(\S+)", line)
            if match:
                result["fields"].append({
                    "access": match.group(1),
                    "name": match.group(2),
                    "type": match.group(3)
                })
        
        # 方法开始
        elif line.startswith(".method"):
            match = re.search(r"\.method\s+(.+?)\s+(\S+)\(([^)]*)\)(\S+)", line)
            if match:
                current_method = {
                    "access": match.group(1),
                    "name": match.group(2),
                    "params": match.group(3),
                    "return_type": match.group(4),
                    "full_signature": line,
                    "start_line": len(method_lines)
                }
                method_lines = [line]
        
        # 方法结束
        elif line.startswith(".end method"):
            if current_method:
                method_lines.append(line)
                current_method["body"] = "\n".join(method_lines)
                current_method["line_count"] = len(method_lines)
                result["methods"].append(current_method)
                current_method = None
                method_lines = []
        
        # 方法体
        elif current_method:
            method_lines.append(line)
    
    return result


def get_method_from_smali(content: str, method_name: str) -> dict:
    """
    从smali内容中提取指定方法
    
    Args:
        content: smali文件内容
        method_name: 方法名
    
    Returns:
        dict: {"success": bool, "method": str, "error": str}
    """
    try:
        lines = content.split("\n")
        in_method = False
        method_lines = []
        
        for i, line in enumerate(lines):
            if f".method" in line and method_name in line:
                in_method = True
                method_lines = [line]
                start_line = i + 1
            elif in_method:
                method_lines.append(line)
                if line.strip() == ".end method":
                    return {
                        "success": True,
                        "method": "\n".join(method_lines),
                        "start_line": start_line,
                        "end_line": i + 1,
                        "error": ""
                    }
        
        return {
            "success": False,
            "method": "",
            "error": f"Method not found: {method_name}"
        }
    
    except Exception as e:
        return {"success": False, "method": "", "error": str(e)}


def replace_method_in_smali(
    content: str,
    method_name: str,
    new_method_body: str
) -> dict:
    """
    替换smali中的方法
    
    Args:
        content: smali文件内容
        method_name: 方法名
        new_method_body: 新的方法体
    
    Returns:
        dict: {"success": bool, "content": str, "error": str}
    """
    try:
        lines = content.split("\n")
        result_lines = []
        in_method = False
        method_replaced = False
        
        for line in lines:
            if f".method" in line and method_name in line:
                in_method = True
                result_lines.append(new_method_body)
                method_replaced = True
            elif in_method:
                if line.strip() == ".end method":
                    in_method = False
                # 跳过旧方法体
            else:
                result_lines.append(line)
        
        if not method_replaced:
            return {
                "success": False,
                "content": "",
                "error": f"Method not found: {method_name}"
            }
        
        return {
            "success": True,
            "content": "\n".join(result_lines),
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


def insert_smali_code(
    content: str,
    method_name: str,
    code_to_insert: str,
    position: str = "start"  # "start", "end", or line number
) -> dict:
    """
    在smali方法中插入代码
    
    Args:
        content: smali文件内容
        method_name: 方法名
        code_to_insert: 要插入的代码
        position: 插入位置 ("start", "end", 或行号)
    
    Returns:
        dict: {"success": bool, "content": str, "error": str}
    """
    try:
        lines = content.split("\n")
        result_lines = []
        in_method = False
        method_found = False
        locals_line_idx = -1
        
        for i, line in enumerate(lines):
            result_lines.append(line)
            
            if f".method" in line and method_name in line:
                in_method = True
                method_found = True
            
            elif in_method:
                # 找到 .locals 行后插入（start位置）
                if position == "start" and line.strip().startswith(".locals"):
                    result_lines.append(code_to_insert)
                
                elif line.strip() == ".end method":
                    if position == "end":
                        # 在.end method前插入
                        result_lines.insert(-1, code_to_insert)
                    in_method = False
        
        if not method_found:
            return {
                "success": False,
                "content": "",
                "error": f"Method not found: {method_name}"
            }
        
        return {
            "success": True,
            "content": "\n".join(result_lines),
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


def generate_log_smali(tag: str, message: str, register: str = "v0") -> str:
    """
    生成Log.d的smali代码
    
    Args:
        tag: Log tag
        message: Log message
        register: 使用的寄存器
    
    Returns:
        str: smali代码
    """
    return f'''
    const-string {register}, "{tag}"
    const-string {register.replace("0", "1")}, "{message}"
    invoke-static {{{register}, {register.replace("0", "1")}}}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I
'''


def generate_return_smali(return_type: str, value: str = None) -> str:
    """
    生成return语句的smali代码
    
    Args:
        return_type: 返回类型 (V, Z, I, J, F, D, L...)
        value: 返回值
    
    Returns:
        str: smali代码
    """
    if return_type == "V":
        return "    return-void"
    elif return_type == "Z":
        # boolean
        val = "0x1" if value == "true" else "0x0"
        return f"    const/4 v0, {val}\n    return v0"
    elif return_type in ["I", "S", "B", "C"]:
        # int, short, byte, char
        return f"    const v0, {value or '0x0'}\n    return v0"
    elif return_type == "J":
        # long
        return f"    const-wide v0, {value or '0x0'}\n    return-wide v0"
    elif return_type.startswith("L") or return_type.startswith("["):
        # object or array
        if value == "null":
            return "    const/4 v0, 0x0\n    return-object v0"
        return "    return-object v0"
    else:
        return "    return-void"
