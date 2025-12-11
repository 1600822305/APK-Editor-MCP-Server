"""资源文件操作工具"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict
from .apk_editor import run_apkeditor
import tempfile
import shutil


def find_resource_dir(project_path: str) -> Optional[str]:
    """
    查找资源目录
    
    Args:
        project_path: 项目路径（已解码的APK目录）
    
    Returns:
        资源目录路径
    """
    possible_paths = [
        os.path.join(project_path, "res"),
        os.path.join(project_path, "resources", "res"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def read_strings_xml(
    project_path: str,
    language: str = ""
) -> dict:
    """
    读取strings.xml
    
    Args:
        project_path: 项目路径
        language: 语言代码（空为默认，如 zh-rCN, en）
    
    Returns:
        dict: {"success": bool, "strings": dict, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {
            "success": False,
            "strings": {},
            "error": f"Resource directory not found in: {project_path}"
        }
    
    # 确定values目录
    if language:
        values_dir = os.path.join(res_dir, f"values-{language}")
        if not os.path.exists(values_dir):
            values_dir = os.path.join(res_dir, "values")
    else:
        values_dir = os.path.join(res_dir, "values")
    
    strings_path = os.path.join(values_dir, "strings.xml")
    
    if not os.path.exists(strings_path):
        return {
            "success": False,
            "strings": {},
            "error": f"strings.xml not found: {strings_path}"
        }
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        strings = {}
        for string_elem in root.findall(".//string"):
            name = string_elem.get("name")
            value = string_elem.text or ""
            if name:
                strings[name] = value
        
        return {
            "success": True,
            "strings": strings,
            "count": len(strings),
            "file_path": strings_path,
            "error": ""
        }
    except ET.ParseError as e:
        return {
            "success": False,
            "strings": {},
            "error": f"XML parse error: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "strings": {},
            "error": str(e)
        }


def modify_string(
    project_path: str,
    string_name: str,
    new_value: str,
    language: str = ""
) -> dict:
    """
    修改strings.xml中的字符串
    
    Args:
        project_path: 项目路径
        string_name: 字符串名称
        new_value: 新值
        language: 语言代码
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "error": "Resource directory not found"}
    
    if language:
        values_dir = os.path.join(res_dir, f"values-{language}")
        if not os.path.exists(values_dir):
            values_dir = os.path.join(res_dir, "values")
    else:
        values_dir = os.path.join(res_dir, "values")
    
    strings_path = os.path.join(values_dir, "strings.xml")
    
    if not os.path.exists(strings_path):
        return {"success": False, "error": f"strings.xml not found: {strings_path}"}
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        found = False
        for string_elem in root.findall(".//string"):
            if string_elem.get("name") == string_name:
                string_elem.text = new_value
                found = True
                break
        
        if not found:
            return {"success": False, "error": f"String not found: {string_name}"}
        
        tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        
        return {
            "success": True,
            "modified": string_name,
            "new_value": new_value,
            "file_path": strings_path,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_modify_strings(
    project_path: str,
    modifications: Dict[str, str],
    language: str = ""
) -> dict:
    """
    批量修改strings.xml
    
    Args:
        project_path: 项目路径
        modifications: {string_name: new_value, ...}
        language: 语言代码
    
    Returns:
        dict: {"success": bool, "modified_count": int, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "modified_count": 0, "error": "Resource directory not found"}
    
    if language:
        values_dir = os.path.join(res_dir, f"values-{language}")
        if not os.path.exists(values_dir):
            values_dir = os.path.join(res_dir, "values")
    else:
        values_dir = os.path.join(res_dir, "values")
    
    strings_path = os.path.join(values_dir, "strings.xml")
    
    if not os.path.exists(strings_path):
        return {"success": False, "modified_count": 0, "error": "strings.xml not found"}
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        modified_count = 0
        for string_elem in root.findall(".//string"):
            name = string_elem.get("name")
            if name in modifications:
                string_elem.text = modifications[name]
                modified_count += 1
        
        tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        
        return {
            "success": True,
            "modified_count": modified_count,
            "total_requested": len(modifications),
            "error": ""
        }
    except Exception as e:
        return {"success": False, "modified_count": 0, "error": str(e)}


def read_colors_xml(project_path: str) -> dict:
    """
    读取colors.xml
    
    Args:
        project_path: 项目路径
    
    Returns:
        dict: {"success": bool, "colors": dict, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "colors": {}, "error": "Resource directory not found"}
    
    colors_path = os.path.join(res_dir, "values", "colors.xml")
    
    if not os.path.exists(colors_path):
        return {"success": False, "colors": {}, "error": "colors.xml not found"}
    
    try:
        tree = ET.parse(colors_path)
        root = tree.getroot()
        
        colors = {}
        for color_elem in root.findall(".//color"):
            name = color_elem.get("name")
            value = color_elem.text or ""
            if name:
                colors[name] = value
        
        return {
            "success": True,
            "colors": colors,
            "count": len(colors),
            "file_path": colors_path,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "colors": {}, "error": str(e)}


def modify_color(
    project_path: str,
    color_name: str,
    new_value: str
) -> dict:
    """
    修改colors.xml中的颜色
    
    Args:
        project_path: 项目路径
        color_name: 颜色名称
        new_value: 新颜色值（如 #FF0000）
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "error": "Resource directory not found"}
    
    colors_path = os.path.join(res_dir, "values", "colors.xml")
    
    if not os.path.exists(colors_path):
        return {"success": False, "error": "colors.xml not found"}
    
    try:
        tree = ET.parse(colors_path)
        root = tree.getroot()
        
        found = False
        for color_elem in root.findall(".//color"):
            if color_elem.get("name") == color_name:
                color_elem.text = new_value
                found = True
                break
        
        if not found:
            return {"success": False, "error": f"Color not found: {color_name}"}
        
        tree.write(colors_path, encoding="utf-8", xml_declaration=True)
        
        return {
            "success": True,
            "modified": color_name,
            "new_value": new_value,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_in_resources(
    project_path: str,
    search_text: str,
    resource_types: Optional[List[str]] = None
) -> dict:
    """
    在资源文件中搜索文本
    
    Args:
        project_path: 项目路径
        search_text: 搜索文本
        resource_types: 资源类型列表，如 ["string", "color", "dimen"]
    
    Returns:
        dict: {"success": bool, "results": list, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "results": [], "error": "Resource directory not found"}
    
    if resource_types is None:
        resource_types = ["string", "color", "dimen", "style"]
    
    results = []
    
    # 遍历所有values目录
    for item in os.listdir(res_dir):
        if item.startswith("values"):
            values_dir = os.path.join(res_dir, item)
            if os.path.isdir(values_dir):
                for xml_file in os.listdir(values_dir):
                    if xml_file.endswith(".xml"):
                        xml_path = os.path.join(values_dir, xml_file)
                        try:
                            tree = ET.parse(xml_path)
                            root = tree.getroot()
                            
                            for res_type in resource_types:
                                for elem in root.findall(f".//{res_type}"):
                                    name = elem.get("name", "")
                                    value = elem.text or ""
                                    
                                    if search_text.lower() in name.lower() or search_text.lower() in value.lower():
                                        results.append({
                                            "type": res_type,
                                            "name": name,
                                            "value": value,
                                            "file": os.path.relpath(xml_path, project_path),
                                            "values_folder": item
                                        })
                        except:
                            pass
    
    return {
        "success": True,
        "results": results,
        "count": len(results),
        "error": ""
    }


def list_resource_files(project_path: str) -> dict:
    """
    列出所有资源文件
    
    Args:
        project_path: 项目路径
    
    Returns:
        dict: {"success": bool, "files": dict, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "files": {}, "error": "Resource directory not found"}
    
    files = {}
    
    for item in os.listdir(res_dir):
        item_path = os.path.join(res_dir, item)
        if os.path.isdir(item_path):
            files[item] = []
            for f in os.listdir(item_path):
                files[item].append(f)
    
    return {
        "success": True,
        "files": files,
        "res_dir": res_dir,
        "error": ""
    }


def read_xml_resource(
    project_path: str,
    resource_path: str
) -> dict:
    """
    读取任意XML资源文件
    
    Args:
        project_path: 项目路径
        resource_path: 资源相对路径（如 values/strings.xml）
    
    Returns:
        dict: {"success": bool, "content": str, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "content": "", "error": "Resource directory not found"}
    
    full_path = os.path.join(res_dir, resource_path)
    
    if not os.path.exists(full_path):
        return {"success": False, "content": "", "error": f"File not found: {resource_path}"}
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "file_path": full_path,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


def modify_xml_resource(
    project_path: str,
    resource_path: str,
    new_content: str
) -> dict:
    """
    修改任意XML资源文件
    
    Args:
        project_path: 项目路径
        resource_path: 资源相对路径
        new_content: 新内容
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "error": "Resource directory not found"}
    
    full_path = os.path.join(res_dir, resource_path)
    
    if not os.path.exists(full_path):
        return {"success": False, "error": f"File not found: {resource_path}"}
    
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return {
            "success": True,
            "file_path": full_path,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_string(
    project_path: str,
    string_name: str,
    string_value: str,
    language: str = ""
) -> dict:
    """
    添加新字符串到strings.xml
    
    Args:
        project_path: 项目路径
        string_name: 字符串名称
        string_value: 字符串值
        language: 语言代码
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "error": "Resource directory not found"}
    
    if language:
        values_dir = os.path.join(res_dir, f"values-{language}")
        if not os.path.exists(values_dir):
            values_dir = os.path.join(res_dir, "values")
    else:
        values_dir = os.path.join(res_dir, "values")
    
    strings_path = os.path.join(values_dir, "strings.xml")
    
    if not os.path.exists(strings_path):
        return {"success": False, "error": "strings.xml not found"}
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        # 检查是否已存在
        for string_elem in root.findall(".//string"):
            if string_elem.get("name") == string_name:
                return {"success": False, "error": f"String already exists: {string_name}"}
        
        # 添加新字符串
        new_elem = ET.SubElement(root, "string")
        new_elem.set("name", string_name)
        new_elem.text = string_value
        
        tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        
        return {
            "success": True,
            "added": string_name,
            "value": string_value,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_string(
    project_path: str,
    string_name: str,
    language: str = ""
) -> dict:
    """
    从strings.xml删除字符串
    
    Args:
        project_path: 项目路径
        string_name: 字符串名称
        language: 语言代码
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    res_dir = find_resource_dir(project_path)
    if not res_dir:
        return {"success": False, "error": "Resource directory not found"}
    
    if language:
        values_dir = os.path.join(res_dir, f"values-{language}")
        if not os.path.exists(values_dir):
            values_dir = os.path.join(res_dir, "values")
    else:
        values_dir = os.path.join(res_dir, "values")
    
    strings_path = os.path.join(values_dir, "strings.xml")
    
    if not os.path.exists(strings_path):
        return {"success": False, "error": "strings.xml not found"}
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        found = False
        for string_elem in root.findall(".//string"):
            if string_elem.get("name") == string_name:
                root.remove(string_elem)
                found = True
                break
        
        if not found:
            return {"success": False, "error": f"String not found: {string_name}"}
        
        tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        
        return {
            "success": True,
            "deleted": string_name,
            "error": ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
