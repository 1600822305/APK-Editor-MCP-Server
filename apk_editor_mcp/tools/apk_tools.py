"""APK操作相关的MCP工具"""
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

from ..apk_editor import (
    decode_apk,
    build_apk,
    merge_apk,
    refactor_apk,
    protect_apk,
    get_apk_info
)


def register_apk_tools(server: Server):
    """注册APK操作工具"""
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name == "apk_decode":
            result = decode_apk(
                apk_path=arguments["apk_path"],
                output_dir=arguments.get("output_dir"),
                decode_type=arguments.get("decode_type", "xml"),
                skip_dex=arguments.get("skip_dex", False),
                force=arguments.get("force", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "apk_build":
            result = build_apk(
                project_dir=arguments["project_dir"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "apk_merge":
            result = merge_apk(
                input_path=arguments["input_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "apk_refactor":
            result = refactor_apk(
                apk_path=arguments["apk_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "apk_protect":
            result = protect_apk(
                apk_path=arguments["apk_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        elif name == "apk_info":
            result = get_apk_info(
                apk_path=arguments["apk_path"],
                verbose=arguments.get("verbose", False),
                show_resources=arguments.get("show_resources", False),
                show_permissions=arguments.get("show_permissions", False),
                show_activities=arguments.get("show_activities", False)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="apk_decode",
                description="反编译APK文件到可编辑的目录结构（XML/JSON格式）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_path": {
                            "type": "string",
                            "description": "APK文件路径"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "输出目录（可选）"
                        },
                        "decode_type": {
                            "type": "string",
                            "enum": ["xml", "json", "raw"],
                            "description": "反编译类型，默认xml"
                        },
                        "skip_dex": {
                            "type": "boolean",
                            "description": "跳过DEX反编译（只复制原始DEX）"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "强制覆盖已存在的输出目录"
                        }
                    },
                    "required": ["apk_path"]
                }
            ),
            Tool(
                name="apk_build",
                description="从反编译的目录构建APK文件（支持DEX缓存，速度快）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_dir": {
                            "type": "string",
                            "description": "项目目录路径"
                        },
                        "output_apk": {
                            "type": "string",
                            "description": "输出APK路径（可选）"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "强制覆盖已存在的输出文件"
                        }
                    },
                    "required": ["project_dir"]
                }
            ),
            Tool(
                name="apk_merge",
                description="合并分割的APK文件（XAPK, APKM, APKS等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "输入目录或文件路径"
                        },
                        "output_apk": {
                            "type": "string",
                            "description": "输出APK路径（可选）"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "强制覆盖"
                        }
                    },
                    "required": ["input_path"]
                }
            ),
            Tool(
                name="apk_refactor",
                description="反资源混淆，恢复被混淆的资源名称",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_path": {
                            "type": "string",
                            "description": "APK文件路径"
                        },
                        "output_apk": {
                            "type": "string",
                            "description": "输出APK路径（可选）"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "强制覆盖"
                        }
                    },
                    "required": ["apk_path"]
                }
            ),
            Tool(
                name="apk_protect",
                description="保护/混淆APK资源文件",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_path": {
                            "type": "string",
                            "description": "APK文件路径"
                        },
                        "output_apk": {
                            "type": "string",
                            "description": "输出APK路径（可选）"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "强制覆盖"
                        }
                    },
                    "required": ["apk_path"]
                }
            ),
            Tool(
                name="apk_info",
                description="获取APK信息（包名、版本、权限、Activity等）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_path": {
                            "type": "string",
                            "description": "APK文件路径"
                        },
                        "verbose": {
                            "type": "boolean",
                            "description": "详细模式"
                        },
                        "show_resources": {
                            "type": "boolean",
                            "description": "显示资源列表"
                        },
                        "show_permissions": {
                            "type": "boolean",
                            "description": "显示权限列表"
                        },
                        "show_activities": {
                            "type": "boolean",
                            "description": "显示Activity列表"
                        }
                    },
                    "required": ["apk_path"]
                }
            )
        ]
