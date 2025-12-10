"""Smali代码操作相关的MCP工具"""
from mcp.server import Server
from mcp.types import Tool, TextContent
import json
from pathlib import Path

from ..smali_utils import (
    parse_smali_class,
    get_method_from_smali,
    replace_method_in_smali,
    insert_smali_code,
    generate_log_smali,
    generate_return_smali
)
from ..file_utils import read_file, write_file


def register_smali_tools(server: Server):
    """注册Smali操作工具"""
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "smali_parse":
            # 先读取文件
            file_result = read_file(arguments["file_path"])
            if not file_result["success"]:
                return [TextContent(type="text", text=json.dumps(file_result, indent=2, ensure_ascii=False))]
            
            result = parse_smali_class(file_result["content"])
            result["success"] = True
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "smali_get_method":
            file_result = read_file(arguments["file_path"])
            if not file_result["success"]:
                return [TextContent(type="text", text=json.dumps(file_result, indent=2, ensure_ascii=False))]
            
            result = get_method_from_smali(
                content=file_result["content"],
                method_name=arguments["method_name"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "smali_replace_method":
            file_result = read_file(arguments["file_path"])
            if not file_result["success"]:
                return [TextContent(type="text", text=json.dumps(file_result, indent=2, ensure_ascii=False))]
            
            result = replace_method_in_smali(
                content=file_result["content"],
                method_name=arguments["method_name"],
                new_method_body=arguments["new_method_body"]
            )
            
            if result["success"]:
                # 写回文件
                write_result = write_file(arguments["file_path"], result["content"])
                result["write_success"] = write_result["success"]
                if not write_result["success"]:
                    result["error"] = write_result["error"]
            
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "smali_insert_code":
            file_result = read_file(arguments["file_path"])
            if not file_result["success"]:
                return [TextContent(type="text", text=json.dumps(file_result, indent=2, ensure_ascii=False))]
            
            result = insert_smali_code(
                content=file_result["content"],
                method_name=arguments["method_name"],
                code_to_insert=arguments["code"],
                position=arguments.get("position", "start")
            )
            
            if result["success"]:
                write_result = write_file(arguments["file_path"], result["content"])
                result["write_success"] = write_result["success"]
                if not write_result["success"]:
                    result["error"] = write_result["error"]
            
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "smali_gen_log":
            code = generate_log_smali(
                tag=arguments["tag"],
                message=arguments["message"],
                register=arguments.get("register", "v0")
            )
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "code": code
            }, indent=2, ensure_ascii=False))]
        
        elif name == "smali_gen_return":
            code = generate_return_smali(
                return_type=arguments["return_type"],
                value=arguments.get("value")
            )
            return [TextContent(type="text", text=json.dumps({
                "success": True,
                "code": code
            }, indent=2, ensure_ascii=False))]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="smali_parse",
                description="解析smali类文件，提取类名、方法、字段等信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "smali文件路径"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="smali_get_method",
                description="从smali文件中提取指定方法的代码",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "smali文件路径"
                        },
                        "method_name": {
                            "type": "string",
                            "description": "方法名"
                        }
                    },
                    "required": ["file_path", "method_name"]
                }
            ),
            Tool(
                name="smali_replace_method",
                description="替换smali文件中的方法实现",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "smali文件路径"
                        },
                        "method_name": {
                            "type": "string",
                            "description": "方法名"
                        },
                        "new_method_body": {
                            "type": "string",
                            "description": "新的方法体（完整的.method到.end method）"
                        }
                    },
                    "required": ["file_path", "method_name", "new_method_body"]
                }
            ),
            Tool(
                name="smali_insert_code",
                description="在smali方法中插入代码",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "smali文件路径"
                        },
                        "method_name": {
                            "type": "string",
                            "description": "方法名"
                        },
                        "code": {
                            "type": "string",
                            "description": "要插入的smali代码"
                        },
                        "position": {
                            "type": "string",
                            "enum": ["start", "end"],
                            "description": "插入位置：start(方法开头) 或 end(return前)"
                        }
                    },
                    "required": ["file_path", "method_name", "code"]
                }
            ),
            Tool(
                name="smali_gen_log",
                description="生成Log.d调用的smali代码",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tag": {
                            "type": "string",
                            "description": "Log TAG"
                        },
                        "message": {
                            "type": "string",
                            "description": "Log消息"
                        },
                        "register": {
                            "type": "string",
                            "description": "使用的寄存器，默认v0"
                        }
                    },
                    "required": ["tag", "message"]
                }
            ),
            Tool(
                name="smali_gen_return",
                description="生成return语句的smali代码",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "return_type": {
                            "type": "string",
                            "description": "返回类型：V(void), Z(boolean), I(int), J(long), L...(对象)"
                        },
                        "value": {
                            "type": "string",
                            "description": "返回值（可选）"
                        }
                    },
                    "required": ["return_type"]
                }
            )
        ]
