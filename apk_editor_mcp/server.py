"""APK Editor MCP Server - 主入口"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import APKEDITOR_JAR, WORKSPACE_DIR, JAVA_PATH
from .apk_editor import (
    ensure_workspace,
    decode_apk,
    build_apk,
    merge_apk,
    refactor_apk,
    protect_apk,
    get_apk_info,
    sign_apk,
    verify_apk_signature,
    fast_manifest_read,
    fast_manifest_modify,
    fast_manifest_patch
)
from .file_utils import (
    list_directory,
    read_file,
    write_file,
    delete_file,
    copy_file,
    move_file,
    get_file_info,
    file_patch,
    file_insert
)
from .search_utils import (
    search_in_files,
    search_smali_method,
    search_smali_string,
    list_smali_classes,
    find_smali_class
)
from .smali_utils import (
    parse_smali_class,
    get_method_from_smali,
    replace_method_in_smali,
    insert_smali_code,
    generate_log_smali,
    generate_return_smali
)
from .fast_dex import (
    fast_dex_open,
    fast_dex_list_classes,
    fast_dex_get_class,
    fast_dex_get_method,
    fast_dex_modify_class,
    fast_dex_save,
    fast_dex_search_class,
    fast_dex_search_string,
    fast_dex_close,
    fast_dex_summary,
    fast_dex_get_paged,
    fast_dex_to_java,
    fast_dex_deobfuscate,
    fast_dex_decompile_package
)

# 创建服务器实例
server = Server("apk-editor-mcp")


def get_all_tools() -> list[Tool]:
    """获取所有工具定义"""
    return [
        # ===== APK操作工具 =====
        Tool(
            name="apk_decode",
            description="反编译APK文件到可编辑的目录结构（XML/JSON格式），支持smali代码查看",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "output_dir": {"type": "string", "description": "输出目录（可选）"},
                    "decode_type": {"type": "string", "enum": ["xml", "json", "raw"], "description": "反编译类型"},
                    "skip_dex": {"type": "boolean", "description": "跳过DEX反编译"},
                    "force": {"type": "boolean", "description": "强制覆盖"}
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
                    "project_dir": {"type": "string", "description": "项目目录路径"},
                    "output_apk": {"type": "string", "description": "输出APK路径（可选）"},
                    "force": {"type": "boolean", "description": "强制覆盖"}
                },
                "required": ["project_dir"]
            }
        ),
        Tool(
            name="apk_merge",
            description="合并分割的APK文件（XAPK, APKM, APKS等）为单个APK",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {"type": "string", "description": "输入目录或文件路径"},
                    "output_apk": {"type": "string", "description": "输出APK路径（可选）"},
                    "force": {"type": "boolean", "description": "强制覆盖"}
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
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "output_apk": {"type": "string", "description": "输出APK路径（可选）"},
                    "force": {"type": "boolean", "description": "强制覆盖"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="apk_protect",
            description="保护/混淆APK资源文件，防止反编译",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "output_apk": {"type": "string", "description": "输出APK路径（可选）"},
                    "force": {"type": "boolean", "description": "强制覆盖"}
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
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "verbose": {"type": "boolean", "description": "详细模式"},
                    "show_resources": {"type": "boolean", "description": "显示资源列表"},
                    "show_permissions": {"type": "boolean", "description": "显示权限列表"},
                    "show_activities": {"type": "boolean", "description": "显示Activity列表"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="apk_sign",
            description="签名APK文件（默认使用debug.keystore，支持自定义keystore）",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "output_path": {"type": "string", "description": "输出路径（可选，默认添加_signed后缀）"},
                    "keystore": {"type": "string", "description": "keystore路径（可选，默认debug.keystore）"},
                    "keystore_pass": {"type": "string", "description": "keystore密码"},
                    "key_alias": {"type": "string", "description": "key别名"},
                    "key_pass": {"type": "string", "description": "key密码"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="apk_verify",
            description="验证APK签名是否有效",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="fast_manifest_read",
            description="快速读取APK中的AndroidManifest.xml",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="fast_manifest_modify",
            description="快速修改APK中的AndroidManifest.xml并重新打包",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "new_manifest": {"type": "string", "description": "新的AndroidManifest.xml内容"},
                    "output_path": {"type": "string", "description": "输出路径（可选）"}
                },
                "required": ["apk_path", "new_manifest"]
            }
        ),
        Tool(
            name="fast_manifest_patch",
            description="快速修补AndroidManifest.xml（正则替换）",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"},
                    "patches": {"type": "array", "description": "补丁列表 [{find: pattern, replace: replacement}]", "items": {"type": "object"}},
                    "output_path": {"type": "string", "description": "输出路径（可选）"}
                },
                "required": ["apk_path", "patches"]
            }
        ),
        
        # ===== 文件操作工具 =====
        Tool(
            name="file_list",
            description="列出目录内容，显示文件和文件夹",
            inputSchema={
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "目录路径"},
                    "recursive": {"type": "boolean", "description": "是否递归列出子目录"},
                    "include_size": {"type": "boolean", "description": "是否包含文件大小信息"}
                },
                "required": ["dir_path"]
            }
        ),
        Tool(
            name="file_read",
            description="读取文件内容（文本或二进制预览）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "encoding": {"type": "string", "description": "文件编码，默认utf-8"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="file_write",
            description="写入文件内容（完整覆盖）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                    "encoding": {"type": "string", "description": "文件编码，默认utf-8"}
                },
                "required": ["file_path", "content"]
            }
        ),
        Tool(
            name="file_patch",
            description="精准替换文件中的内容（查找并替换）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "old_string": {"type": "string", "description": "要替换的原内容"},
                    "new_string": {"type": "string", "description": "替换后的新内容"},
                    "replace_all": {"type": "boolean", "description": "是否替换所有匹配（默认只替换第一个）"},
                    "encoding": {"type": "string", "description": "文件编码，默认utf-8"}
                },
                "required": ["file_path", "old_string", "new_string"]
            }
        ),
        Tool(
            name="file_insert",
            description="在文件中插入内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件路径"},
                    "position": {"type": "string", "enum": ["start", "end", "before", "after"], "description": "插入位置"},
                    "content": {"type": "string", "description": "要插入的内容"},
                    "anchor": {"type": "string", "description": "锚点字符串（position为before/after时需要）"},
                    "encoding": {"type": "string", "description": "文件编码，默认utf-8"}
                },
                "required": ["file_path", "position", "content"]
            }
        ),
        Tool(
            name="file_delete",
            description="删除文件或目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文件或目录路径"}
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
                    "src": {"type": "string", "description": "源路径"},
                    "dst": {"type": "string", "description": "目标路径"},
                    "overwrite": {"type": "boolean", "description": "是否覆盖已存在的文件"}
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
                    "src": {"type": "string", "description": "源路径"},
                    "dst": {"type": "string", "description": "目标路径"},
                    "overwrite": {"type": "boolean", "description": "是否覆盖已存在的文件"}
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
                    "file_path": {"type": "string", "description": "文件或目录路径"}
                },
                "required": ["file_path"]
            }
        ),
        
        # ===== 搜索工具 =====
        Tool(
            name="search_text",
            description="在项目文件中搜索文本内容，支持正则表达式",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索目录"},
                    "pattern": {"type": "string", "description": "搜索模式"},
                    "file_extensions": {"type": "array", "items": {"type": "string"}, "description": "文件扩展名过滤"},
                    "case_sensitive": {"type": "boolean", "description": "是否区分大小写"},
                    "is_regex": {"type": "boolean", "description": "是否使用正则表达式"},
                    "max_results": {"type": "integer", "description": "最大结果数"},
                    "context_lines": {"type": "integer", "description": "上下文行数"}
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
                    "directory": {"type": "string", "description": "项目目录"},
                    "method_pattern": {"type": "string", "description": "方法调用模式"},
                    "max_results": {"type": "integer", "description": "最大结果数"}
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
                    "directory": {"type": "string", "description": "项目目录"},
                    "string_value": {"type": "string", "description": "要搜索的字符串"},
                    "max_results": {"type": "integer", "description": "最大结果数"}
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
                    "directory": {"type": "string", "description": "项目目录"}
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
                    "directory": {"type": "string", "description": "项目目录"},
                    "class_name": {"type": "string", "description": "类名，如 Lcom/example/MainActivity;"}
                },
                "required": ["directory", "class_name"]
            }
        ),
        
        # ===== Smali工具 =====
        Tool(
            name="smali_parse",
            description="解析smali类文件，提取类名、方法、字段等信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "smali文件路径"}
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
                    "file_path": {"type": "string", "description": "smali文件路径"},
                    "method_name": {"type": "string", "description": "方法名"}
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
                    "file_path": {"type": "string", "description": "smali文件路径"},
                    "method_name": {"type": "string", "description": "方法名"},
                    "new_method_body": {"type": "string", "description": "新的方法体"}
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
                    "file_path": {"type": "string", "description": "smali文件路径"},
                    "method_name": {"type": "string", "description": "方法名"},
                    "code": {"type": "string", "description": "要插入的smali代码"},
                    "position": {"type": "string", "enum": ["start", "end"], "description": "插入位置"}
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
                    "tag": {"type": "string", "description": "Log TAG"},
                    "message": {"type": "string", "description": "Log消息"},
                    "register": {"type": "string", "description": "使用的寄存器，默认v0"}
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
                    "return_type": {"type": "string", "description": "返回类型：V, Z, I, J, L..."},
                    "value": {"type": "string", "description": "返回值（可选）"}
                },
                "required": ["return_type"]
            }
        ),
        
        # ===== 快速DEX编辑工具（内存操作，不解包）=====
        Tool(
            name="fast_dex_open",
            description="【快速】打开APK加载DEX到内存（不解包，秒开）",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "APK文件路径"}
                },
                "required": ["apk_path"]
            }
        ),
        Tool(
            name="fast_dex_list_classes",
            description="【快速】列出所有类（从内存读取）",
            inputSchema={
                "type": "object",
                "properties": {
                    "dex_name": {"type": "string", "description": "指定DEX名称（可选）"}
                }
            }
        ),
        Tool(
            name="fast_dex_get_class",
            description="【快速】获取单个类的smali代码（按需反编译）",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名，如 Lcom/example/VipInfo;"}
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="fast_dex_modify_class",
            description="【快速】修改类的smali代码（内存操作）",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名"},
                    "smali_code": {"type": "string", "description": "新的smali代码"}
                },
                "required": ["class_name", "smali_code"]
            }
        ),
        Tool(
            name="fast_dex_save",
            description="【快速】保存修改到APK",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "输出路径（可选）"}
                }
            }
        ),
        Tool(
            name="fast_dex_search_class",
            description="【快速】搜索类名",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "搜索模式（正则）"}
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="fast_dex_close",
            description="【快速】关闭DEX编辑器",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="fast_dex_summary",
            description="【快速】获取类摘要（方法列表、字段列表、代码长度）- 先用这个看结构",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名，如 Lcom/example/VipInfo;"}
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="fast_dex_get_paged",
            description="【快速】分页获取smali代码（避免超token）",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名"},
                    "offset": {"type": "integer", "description": "偏移量（默认0）"},
                    "limit": {"type": "integer", "description": "限制长度（默认10000字符）"}
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="fast_dex_to_java",
            description="【快速】smali转Java代码（需要jadx）",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名"}
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="fast_dex_deobfuscate",
            description="【快速】反混淆并转Java（自动重命名混淆名称）",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {"type": "string", "description": "类名"}
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="fast_dex_decompile_package",
            description="【快速】批量反编译包下所有类",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "包名模式，如 com.example.*"}
                },
                "required": ["pattern"]
            }
        ),
        
        # ===== 系统工具 =====
        Tool(
            name="get_workspace",
            description="获取当前工作目录信息",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用工具"""
    result = {}
    
    try:
        # APK操作
        if name == "apk_decode":
            result = decode_apk(
                apk_path=arguments["apk_path"],
                output_dir=arguments.get("output_dir"),
                decode_type=arguments.get("decode_type", "xml"),
                skip_dex=arguments.get("skip_dex", False),
                force=arguments.get("force", True)
            )
        elif name == "apk_build":
            result = build_apk(
                project_dir=arguments["project_dir"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
        elif name == "apk_merge":
            result = merge_apk(
                input_path=arguments["input_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
        elif name == "apk_refactor":
            result = refactor_apk(
                apk_path=arguments["apk_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
        elif name == "apk_protect":
            result = protect_apk(
                apk_path=arguments["apk_path"],
                output_apk=arguments.get("output_apk"),
                force=arguments.get("force", True)
            )
        elif name == "apk_info":
            result = get_apk_info(
                apk_path=arguments["apk_path"],
                verbose=arguments.get("verbose", False),
                show_resources=arguments.get("show_resources", False),
                show_permissions=arguments.get("show_permissions", False),
                show_activities=arguments.get("show_activities", False)
            )
        elif name == "apk_sign":
            result = sign_apk(
                apk_path=arguments["apk_path"],
                output_path=arguments.get("output_path"),
                keystore=arguments.get("keystore"),
                keystore_pass=arguments.get("keystore_pass"),
                key_alias=arguments.get("key_alias"),
                key_pass=arguments.get("key_pass")
            )
        elif name == "apk_verify":
            result = verify_apk_signature(apk_path=arguments["apk_path"])
        elif name == "fast_manifest_read":
            result = fast_manifest_read(apk_path=arguments["apk_path"])
            # 格式化显示
            if result.get("success") and result.get("manifest"):
                return [TextContent(type="text", text=f"```xml\n{result['manifest']}\n```")]
        elif name == "fast_manifest_modify":
            result = fast_manifest_modify(
                apk_path=arguments["apk_path"],
                new_manifest=arguments["new_manifest"],
                output_path=arguments.get("output_path")
            )
        elif name == "fast_manifest_patch":
            result = fast_manifest_patch(
                apk_path=arguments["apk_path"],
                patches=arguments["patches"],
                output_path=arguments.get("output_path")
            )
        
        # 文件操作
        elif name == "file_list":
            result = list_directory(
                dir_path=arguments["dir_path"],
                recursive=arguments.get("recursive", False),
                include_size=arguments.get("include_size", True)
            )
        elif name == "file_read":
            result = read_file(
                file_path=arguments["file_path"],
                encoding=arguments.get("encoding", "utf-8")
            )
        elif name == "file_write":
            result = write_file(
                file_path=arguments["file_path"],
                content=arguments["content"],
                encoding=arguments.get("encoding", "utf-8")
            )
        elif name == "file_patch":
            result = file_patch(
                file_path=arguments["file_path"],
                old_string=arguments["old_string"],
                new_string=arguments["new_string"],
                replace_all=arguments.get("replace_all", False),
                encoding=arguments.get("encoding", "utf-8")
            )
        elif name == "file_insert":
            result = file_insert(
                file_path=arguments["file_path"],
                position=arguments["position"],
                content=arguments["content"],
                anchor=arguments.get("anchor", ""),
                encoding=arguments.get("encoding", "utf-8")
            )
        elif name == "file_delete":
            result = delete_file(file_path=arguments["file_path"])
        elif name == "file_copy":
            result = copy_file(
                src=arguments["src"],
                dst=arguments["dst"],
                overwrite=arguments.get("overwrite", False)
            )
        elif name == "file_move":
            result = move_file(
                src=arguments["src"],
                dst=arguments["dst"],
                overwrite=arguments.get("overwrite", False)
            )
        elif name == "file_info":
            result = get_file_info(file_path=arguments["file_path"])
        
        # 搜索
        elif name == "search_text":
            result = search_in_files(
                directory=arguments["directory"],
                pattern=arguments["pattern"],
                file_extensions=arguments.get("file_extensions"),
                case_sensitive=arguments.get("case_sensitive", False),
                is_regex=arguments.get("is_regex", False),
                max_results=arguments.get("max_results", 100),
                context_lines=arguments.get("context_lines", 2)
            )
        elif name == "search_method":
            result = search_smali_method(
                directory=arguments["directory"],
                method_pattern=arguments["method_pattern"],
                max_results=arguments.get("max_results", 50)
            )
        elif name == "search_string":
            result = search_smali_string(
                directory=arguments["directory"],
                string_value=arguments["string_value"],
                max_results=arguments.get("max_results", 50)
            )
        elif name == "list_classes":
            result = list_smali_classes(directory=arguments["directory"])
        elif name == "find_class":
            result = find_smali_class(
                directory=arguments["directory"],
                class_name=arguments["class_name"]
            )
        
        # Smali操作
        elif name == "smali_parse":
            file_result = read_file(arguments["file_path"])
            if file_result["success"]:
                result = parse_smali_class(file_result["content"])
                result["success"] = True
            else:
                result = file_result
        elif name == "smali_get_method":
            file_result = read_file(arguments["file_path"])
            if file_result["success"]:
                result = get_method_from_smali(file_result["content"], arguments["method_name"])
            else:
                result = file_result
        elif name == "smali_replace_method":
            file_result = read_file(arguments["file_path"])
            if file_result["success"]:
                result = replace_method_in_smali(
                    file_result["content"],
                    arguments["method_name"],
                    arguments["new_method_body"]
                )
                if result["success"]:
                    write_result = write_file(arguments["file_path"], result["content"])
                    result["write_success"] = write_result["success"]
            else:
                result = file_result
        elif name == "smali_insert_code":
            file_result = read_file(arguments["file_path"])
            if file_result["success"]:
                result = insert_smali_code(
                    file_result["content"],
                    arguments["method_name"],
                    arguments["code"],
                    arguments.get("position", "start")
                )
                if result["success"]:
                    write_result = write_file(arguments["file_path"], result["content"])
                    result["write_success"] = write_result["success"]
            else:
                result = file_result
        elif name == "smali_gen_log":
            code = generate_log_smali(
                arguments["tag"],
                arguments["message"],
                arguments.get("register", "v0")
            )
            result = {"success": True, "code": code}
        elif name == "smali_gen_return":
            code = generate_return_smali(
                arguments["return_type"],
                arguments.get("value")
            )
            result = {"success": True, "code": code}
        
        # 快速DEX编辑
        elif name == "fast_dex_open":
            result = fast_dex_open(arguments["apk_path"])
        elif name == "fast_dex_list_classes":
            result = fast_dex_list_classes(arguments.get("dex_name"))
        elif name == "fast_dex_get_class":
            result = fast_dex_get_class(arguments["class_name"])
            # 将smali代码格式化显示
            if result.get("success") and result.get("data", {}).get("smali"):
                smali = result["data"]["smali"]
                # 返回格式化的smali代码
                return [TextContent(type="text", text=f"```smali\n{smali}\n```")]
        elif name == "fast_dex_modify_class":
            result = fast_dex_modify_class(arguments["class_name"], arguments["smali_code"])
        elif name == "fast_dex_save":
            result = fast_dex_save(arguments.get("output_path"))
        elif name == "fast_dex_search_class":
            result = fast_dex_search_class(arguments["pattern"])
        elif name == "fast_dex_close":
            result = fast_dex_close()
        elif name == "fast_dex_summary":
            result = fast_dex_summary(arguments["class_name"])
        elif name == "fast_dex_get_paged":
            result = fast_dex_get_paged(
                arguments["class_name"],
                arguments.get("offset", 0),
                arguments.get("limit", 10000)
            )
            # 格式化显示
            if result.get("success") and result.get("data", {}).get("smali"):
                data = result["data"]
                header = f"# 偏移: {data['offset']}, 长度: {data['length']}/{data['totalLength']}, 还有更多: {data['hasMore']}\n"
                return [TextContent(type="text", text=f"```smali\n{header}{data['smali']}\n```")]
        elif name == "fast_dex_to_java":
            result = fast_dex_to_java(arguments["class_name"])
            # 格式化显示Java代码
            if result.get("success") and result.get("data", {}).get("java"):
                java = result["data"]["java"]
                return [TextContent(type="text", text=f"```java\n{java}\n```")]
        elif name == "fast_dex_deobfuscate":
            result = fast_dex_deobfuscate(arguments["class_name"])
            if result.get("success") and result.get("data", {}).get("java"):
                java = result["data"]["java"]
                return [TextContent(type="text", text=f"```java\n// 反混淆后:\n{java}\n```")]
        elif name == "fast_dex_decompile_package":
            result = fast_dex_decompile_package(arguments["pattern"])
        
        # 系统
        elif name == "get_workspace":
            result = {
                "success": True,
                "workspace_dir": WORKSPACE_DIR,
                "apkeditor_jar": APKEDITOR_JAR,
                "java_path": JAVA_PATH
            }
        
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}
    
    except Exception as e:
        result = {"success": False, "error": str(e)}
    
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def run_server():
    """运行MCP服务器"""
    ensure_workspace()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """主入口"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
