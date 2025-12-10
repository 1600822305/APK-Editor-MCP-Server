"""文件操作相关的MCP工具"""
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from ..file_utils import (
    list_directory,
    read_file,
    write_file,
    delete_file,
    copy_file,
    move_file,
    get_file_info
)


def register_file_tools(server: Server):
    """注册文件操作工具"""
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "file_list":
            result = list_directory(
                dir_path=arguments["dir_path"],
                recursive=arguments.get("recursive", False),
                include_size=arguments.get("include_size", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_read":
            result = read_file(
                file_path=arguments["file_path"],
                encoding=arguments.get("encoding", "utf-8")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_write":
            result = write_file(
                file_path=arguments["file_path"],
                content=arguments["content"],
                encoding=arguments.get("encoding", "utf-8")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_delete":
            result = delete_file(file_path=arguments["file_path"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_copy":
            result = copy_file(
                src=arguments["src"],
                dst=arguments["dst"],
                overwrite=arguments.get("overwrite", False)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_move":
            result = move_file(
                src=arguments["src"],
                dst=arguments["dst"],
                overwrite=arguments.get("overwrite", False)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "file_info":
            result = get_file_info(file_path=arguments["file_path"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="file_list",
                description="列出目录内容，显示文件和文件夹",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dir_path": {
                            "type": "string",
                            "description": "目录路径"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "是否递归列出子目录"
                        },
                        "include_size": {
                            "type": "boolean",
                            "description": "是否包含文件大小信息"
                        }
                    },
                    "required": ["dir_path"]
                }
            ),
            Tool(
                name="file_read",
                description="读取文件内容",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "文件编码，默认utf-8"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="file_write",
                description="写入文件内容",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "文件编码，默认utf-8"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            ),
            Tool(
                name="file_delete",
                description="删除文件或目录",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件或目录路径"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="file_copy",
                description="复制文件或目录",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "src": {
                            "type": "string",
                            "description": "源路径"
                        },
                        "dst": {
                            "type": "string",
                            "description": "目标路径"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "是否覆盖已存在的文件"
                        }
                    },
                    "required": ["src", "dst"]
                }
            ),
            Tool(
                name="file_move",
                description="移动文件或目录",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "src": {
                            "type": "string",
                            "description": "源路径"
                        },
                        "dst": {
                            "type": "string",
                            "description": "目标路径"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "是否覆盖已存在的文件"
                        }
                    },
                    "required": ["src", "dst"]
                }
            ),
            Tool(
                name="file_info",
                description="获取文件或目录的详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件或目录路径"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
