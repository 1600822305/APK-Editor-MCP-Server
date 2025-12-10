# APK Editor MCP

一个强大的 Android APK 逆向工程 MCP (Model Context Protocol) 服务器，支持 APK 反编译、修改、重打包，以及快速 DEX 内存编辑。

## 特性

- **快速 DEX 编辑** - 内存操作，无需解包，秒级打开大型 APK
- **Smali 转 Java** - 内置 jadx-core，一键反编译
- **智能搜索** - 搜索类名、字符串、方法调用
- **实时修改** - 直接修改 smali 代码并保存
- **批量操作** - 批量反编译整个包

## 安装

### 前置要求

- Python 3.10+
- Java 17+
- [APKEditor.jar](https://github.com/AlanTse1314/AKDTv-APKEditor)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/your-repo/apk-editor-mcp.git
cd apk-editor-mcp

# 安装依赖
pip install -e .

# 配置 Windsurf/Cursor MCP
```

### MCP 配置

在 `~/.codeium/windsurf/mcp_config.json` 中添加：

```json
{
  "mcpServers": {
    "apk-editor": {
      "command": "python",
      "args": ["K:/path/to/APK-Editor-MCP-Server/mcp-server/run_server.py"]
    }
  }
}
```

## 工具列表

### 快速 DEX 编辑器 (推荐)

| 工具 | 说明 |
|------|------|
| `fast_dex_open` | 打开 APK 加载 DEX 到内存（秒开） |
| `fast_dex_list_classes` | 列出所有类 |
| `fast_dex_search_class` | 搜索类名（支持正则） |
| `fast_dex_get_class` | 获取类的 smali 代码 |
| `fast_dex_summary` | 获取类摘要（方法列表、代码长度） |
| `fast_dex_get_paged` | 分页获取 smali（避免超 token） |
| `fast_dex_modify_class` | 修改类的 smali 代码 |
| `fast_dex_save` | 保存修改到 APK |
| `fast_dex_to_java` | smali 转 Java 代码 |
| `fast_dex_deobfuscate` | 反混淆并转 Java |
| `fast_dex_decompile_package` | 批量反编译包下所有类 |
| `fast_dex_close` | 关闭编辑器 |

### APK 操作

| 工具 | 说明 |
|------|------|
| `apk_decode` | 反编译 APK 到目录 |
| `apk_build` | 从目录构建 APK |
| `apk_info` | 获取 APK 信息 |
| `apk_sign` | **签名 APK（默认debug.keystore）** |
| `apk_verify` | 验证 APK 签名 |
| `fast_manifest_read` | **快速读取 AndroidManifest.xml** |
| `fast_manifest_modify` | **快速修改 AndroidManifest.xml** |
| `fast_manifest_patch` | **快速修补 Manifest（正则替换）** |
| `apk_merge` | 合并分割 APK (XAPK/APKS) |
| `apk_protect` | 保护/混淆 APK 资源 |
| `apk_refactor` | 反资源混淆 |

### 文件操作

| 工具 | 说明 |
|------|------|
| `file_list` | 列出目录内容 |
| `file_read` | 读取文件 |
| `file_write` | 写入文件 |
| `file_copy` | 复制文件 |
| `file_move` | 移动文件 |
| `file_delete` | 删除文件 |

### Smali 操作

| 工具 | 说明 |
|------|------|
| `smali_parse` | 解析 smali 文件结构 |
| `smali_get_method` | 提取指定方法 |
| `smali_replace_method` | 替换方法实现 |
| `smali_insert_code` | 在方法中插入代码 |
| `smali_gen_log` | 生成 Log.d 调用代码 |
| `smali_gen_return` | 生成 return 语句代码 |

### 搜索工具

| 工具 | 说明 |
|------|------|
| `search_text` | 搜索文本内容 |
| `search_string` | 搜索 smali 字符串常量 |
| `search_method` | 搜索方法调用 |
| `find_class` | 查找类文件路径 |
| `list_classes` | 列出所有 smali 类 |

## 使用示例

### 快速破解 VIP

```python
# 1. 打开 APK
fast_dex_open("app.apk")

# 2. 搜索 VIP 相关类
fast_dex_search_class("VipInfo")

# 3. 查看类结构
fast_dex_summary("Lcom/example/VipInfo;")

# 4. 获取并查看代码
fast_dex_to_java("Lcom/example/VipInfo;")

# 5. 修改 isVip 方法返回 true
fast_dex_modify_class("Lcom/example/VipInfo;", new_smali_code)

# 6. 保存
fast_dex_save("app_cracked.apk")
```

### 搜索字符串

```python
# 搜索登录相关
fast_dex_search_string("login")
fast_dex_search_string("password")
```

### 批量反编译

```python
# 反编译整个包
fast_dex_decompile_package("com.example.app.*")
```

## 项目结构

```
APK-Editor-MCP-Server/
├── mcp-server/           # Python MCP 服务器
│   ├── apk_editor_mcp/
│   │   ├── server.py     # MCP 服务器主文件
│   │   ├── fast_dex.py   # 快速 DEX 编辑器
│   │   ├── apk_editor.py # APK 操作工具
│   │   ├── file_utils.py # 文件操作
│   │   ├── smali_utils.py# Smali 操作
│   │   └── search_utils.py # 搜索工具
│   ├── run_server.py     # 启动脚本
│   └── requirements.txt
├── java-core/            # Kotlin/Java DEX 编辑核心
│   ├── src/main/kotlin/
│   │   └── com/apkeditor/dex/
│   │       ├── DexEditor.kt  # DEX 编辑器核心
│   │       └── Main.kt       # 命令行入口
│   ├── build.gradle.kts
│   └── build/libs/
│       └── dex-editor.jar    # 编译产物
├── libs/
│   ├── APKEditor.jar     # APK 编辑核心
│   ├── dex-editor.jar    # DEX 编辑器（内置 jadx-core）
│   └── apksigner.jar     # APK 签名工具
└── README.md
```

## 技术栈

- **Python** - MCP 服务器
- **Kotlin** - DEX 编辑器核心
- **dexlib2/smali** - DEX 操作库
- **jadx-core** - Java 反编译
- **APKEditor** - APK 打包工具

## License

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
