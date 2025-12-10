"""搜索相关的MCP工具"""
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from ..search_utils import (
    search_in_files,
    search_smali_method,
    search_smali_string,
    list_smali_classes,
    find_smali_class
)


def register_search_tools(server: Server):
    """注册搜索工具"""
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "search_text":
            result = search_in_files(
                directory=arguments["directory"],
                pattern=arguments["pattern"],
                file_extensions=arguments.get("file_extensions"),
                case_sensitive=arguments.get("case_sensitive", False),
                is_regex=arguments.get("is_regex", False),
                max_results=arguments.get("max_results", 100),
                context_lines=arguments.get("context_lines", 2)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "search_method":
            result = search_smali_method(
                directory=arguments["directory"],
                method_pattern=arguments["method_pattern"],
                max_results=arguments.get("max_results", 50)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "search_string":
            result = search_smali_string(
                directory=arguments["directory"],
                string_value=arguments["string_value"],
                max_results=arguments.get("max_results", 50)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "list_classes":
            result = list_smali_classes(directory=arguments["directory"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "find_class":
            result = find_smali_class(
                directory=arguments["directory"],
                class_name=arguments["class_name"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_text",
                description="在项目文件中搜索文本内容，支持正则表达式",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "搜索目录"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "搜索模式"
                        },
                        "file_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "文件扩展名过滤，如 [\".smali\", \".xml\"]"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "是否区分大小写"
                        },
                        "is_regex": {
                            "type": "boolean",
                            "description": "是否使用正则表达式"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数"
                        },
                        "context_lines": {
                            "type": "integer",
                            "description": "上下文行数"
                        }
                    },
                    "required": ["directory", "pattern"]
                }
            ),
            Tool(
                name="search_method",
                description="搜索smali方法调用，如 Landroid/util/Log;->d",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "项目目录"
                        },
                        "method_pattern": {
                            "type": "string",
                            "description": "方法调用模式"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数"
                        }
                    },
                    "required": ["directory", "method_pattern"]
                }
            ),
            Tool(
                name="search_string",
                description="搜索smali中的字符串常量",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "项目目录"
                        },
                        "string_value": {
                            "type": "string",
                            "description": "要搜索的字符串"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "最大结果数"
                        }
                    },
                    "required": ["directory", "string_value"]
                }
            ),
            Tool(
                name="list_classes",
                description="列出项目中所有的smali类",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "项目目录"
                        }
                    },
                    "required": ["directory"]
                }
            ),
            Tool(
                name="find_class",
                description="查找指定的smali类文件路径",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "项目目录"
                        },
                        "class_name": {
                            "type": "string",
                            "description": "类名，如 Lcom/example/MainActivity;"
                        }
                    },
                    "required": ["directory", "class_name"]
                }
            )
        ]
