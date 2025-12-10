"""文件操作工具"""
import os
import shutil
from pathlib import Path
from typing import Optional
from .config import MAX_FILE_SIZE, WORKSPACE_DIR


def list_directory(
    dir_path: str,
    recursive: bool = False,
    include_size: bool = True
) -> dict:
    """
    列出目录内容
    
    Args:
        dir_path: 目录路径
        recursive: 是否递归
        include_size: 是否包含文件大小
    
    Returns:
        dict: {"success": bool, "files": list, "error": str}
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            return {"success": False, "files": [], "error": f"Path not found: {dir_path}"}
        
        if not path.is_dir():
            return {"success": False, "files": [], "error": f"Not a directory: {dir_path}"}
        
        files = []
        iterator = path.rglob("*") if recursive else path.iterdir()
        
        for item in iterator:
            rel_path = str(item.relative_to(path))
            file_info = {
                "name": item.name,
                "path": rel_path,
                "is_dir": item.is_dir(),
                "type": "directory" if item.is_dir() else item.suffix.lstrip(".")
            }
            
            if include_size and item.is_file():
                file_info["size"] = item.stat().st_size
            
            files.append(file_info)
        
        # 排序：目录在前，然后按名称
        files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return {"success": True, "files": files, "error": ""}
    
    except Exception as e:
        return {"success": False, "files": [], "error": str(e)}


def read_file(
    file_path: str,
    encoding: str = "utf-8",
    max_size: int = MAX_FILE_SIZE
) -> dict:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 编码
        max_size: 最大读取大小
    
    Returns:
        dict: {"success": bool, "content": str, "error": str}
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "content": "", "error": f"File not found: {file_path}"}
        
        if not path.is_file():
            return {"success": False, "content": "", "error": f"Not a file: {file_path}"}
        
        size = path.stat().st_size
        if size > max_size:
            return {
                "success": False, 
                "content": "", 
                "error": f"File too large: {size} bytes (max: {max_size})"
            }
        
        # 尝试读取文本
        try:
            content = path.read_text(encoding=encoding)
            return {"success": True, "content": content, "error": "", "binary": False}
        except UnicodeDecodeError:
            # 二进制文件，返回hex预览
            content = path.read_bytes()[:1024]
            hex_preview = content.hex(" ", 1)
            return {
                "success": True, 
                "content": f"[Binary file, hex preview]:\n{hex_preview}", 
                "error": "",
                "binary": True
            }
    
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> dict:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码
        create_dirs: 是否创建父目录
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    try:
        path = Path(file_path)
        
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding=encoding)
        return {"success": True, "error": ""}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_file(file_path: str) -> dict:
    """
    删除文件或目录
    
    Args:
        file_path: 文件或目录路径
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"Path not found: {file_path}"}
        
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        
        return {"success": True, "error": ""}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def copy_file(src: str, dst: str, overwrite: bool = False) -> dict:
    """
    复制文件或目录
    
    Args:
        src: 源路径
        dst: 目标路径
        overwrite: 是否覆盖
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        
        if dst_path.exists() and not overwrite:
            return {"success": False, "error": f"Destination exists: {dst}"}
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if src_path.is_dir():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)
        
        return {"success": True, "error": ""}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def move_file(src: str, dst: str, overwrite: bool = False) -> dict:
    """
    移动文件或目录
    
    Args:
        src: 源路径
        dst: 目标路径
        overwrite: 是否覆盖
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        
        if dst_path.exists() and not overwrite:
            return {"success": False, "error": f"Destination exists: {dst}"}
        
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dst_path.exists():
            if dst_path.is_dir():
                shutil.rmtree(dst_path)
            else:
                dst_path.unlink()
        
        shutil.move(str(src_path), str(dst_path))
        return {"success": True, "error": ""}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_file_info(file_path: str) -> dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        dict: 文件信息
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"Path not found: {file_path}"}
        
        stat = path.stat()
        
        return {
            "success": True,
            "info": {
                "name": path.name,
                "path": str(path.absolute()),
                "is_dir": path.is_dir(),
                "is_file": path.is_file(),
                "size": stat.st_size,
                "extension": path.suffix,
                "modified": stat.st_mtime,
                "created": stat.st_ctime
            },
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def file_patch(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
    encoding: str = "utf-8"
) -> dict:
    """
    精准替换文件中的内容
    
    Args:
        file_path: 文件路径
        old_string: 要替换的原内容
        new_string: 替换后的新内容
        replace_all: 是否替换所有匹配（默认只替换第一个）
        encoding: 文件编码
    
    Returns:
        dict: {"success": bool, "replaced_count": int, "error": str}
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "replaced_count": 0, "error": f"File not found: {file_path}"}
        
        if not path.is_file():
            return {"success": False, "replaced_count": 0, "error": f"Not a file: {file_path}"}
        
        # 读取文件内容
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        
        # 检查是否找到要替换的内容
        if old_string not in content:
            return {
                "success": False, 
                "replaced_count": 0, 
                "error": f"String not found in file"
            }
        
        # 计算替换次数
        count = content.count(old_string)
        
        # 执行替换
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replaced_count = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replaced_count = 1
        
        # 写回文件
        with open(path, "w", encoding=encoding) as f:
            f.write(new_content)
        
        return {
            "success": True,
            "replaced_count": replaced_count,
            "total_matches": count,
            "error": ""
        }
    
    except Exception as e:
        return {"success": False, "replaced_count": 0, "error": str(e)}


def file_insert(
    file_path: str,
    position: str,
    content: str,
    anchor: str = "",
    encoding: str = "utf-8"
) -> dict:
    """
    在文件中插入内容
    
    Args:
        file_path: 文件路径
        position: 插入位置 - "start", "end", "before", "after"
        content: 要插入的内容
        anchor: 锚点字符串（position为before/after时需要）
        encoding: 文件编码
    
    Returns:
        dict: {"success": bool, "error": str}
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # 读取文件内容
        with open(path, "r", encoding=encoding) as f:
            file_content = f.read()
        
        # 根据位置插入
        if position == "start":
            new_content = content + file_content
        elif position == "end":
            new_content = file_content + content
        elif position == "before":
            if not anchor:
                return {"success": False, "error": "anchor required for 'before' position"}
            if anchor not in file_content:
                return {"success": False, "error": "Anchor not found"}
            new_content = file_content.replace(anchor, content + anchor, 1)
        elif position == "after":
            if not anchor:
                return {"success": False, "error": "anchor required for 'after' position"}
            if anchor not in file_content:
                return {"success": False, "error": "Anchor not found"}
            new_content = file_content.replace(anchor, anchor + content, 1)
        else:
            return {"success": False, "error": f"Invalid position: {position}"}
        
        # 写回文件
        with open(path, "w", encoding=encoding) as f:
            f.write(new_content)
        
        return {"success": True, "error": ""}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
