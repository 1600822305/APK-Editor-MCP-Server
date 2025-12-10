# APK Editor MCP Server 安装说明

## 1. 下载 APKEditor.jar

从 GitHub 下载最新版本：
https://github.com/REAndroid/APKEditor/releases

将 `APKEditor-xxx.jar` 重命名为 `APKEditor.jar` 并放入 `libs/` 目录

## 2. 安装 Python 依赖

```bash
cd apk-editor-mcp-python
pip install -e .
```

或者直接安装依赖：
```bash
pip install mcp
```

## 3. 配置环境变量（可选）

```bash
# APKEditor.jar 路径
export APKEDITOR_JAR=/path/to/APKEditor.jar

# 工作目录
export APK_WORKSPACE=/path/to/workspace

# Java 路径（如果不在PATH中）
export JAVA_HOME=/path/to/java
```

## 4. 在 Windsurf/Claude 中配置 MCP

编辑 MCP 配置文件，添加：

```json
{
  "mcpServers": {
    "apk-editor": {
      "command": "python",
      "args": ["-m", "apk_editor_mcp.server"],
      "cwd": "K:/Cherry/androidmtmangebg/apk-editor-mcp-python"
    }
  }
}
```

或者使用 uv：
```json
{
  "mcpServers": {
    "apk-editor": {
      "command": "uv",
      "args": ["run", "python", "-m", "apk_editor_mcp.server"],
      "cwd": "K:/Cherry/androidmtmangebg/apk-editor-mcp-python"
    }
  }
}
```

## 5. 可用工具列表

### APK 操作
- `apk_decode` - 反编译APK
- `apk_build` - 构建APK（带缓存）
- `apk_merge` - 合并分割APK
- `apk_refactor` - 反资源混淆
- `apk_protect` - 资源保护
- `apk_info` - 获取APK信息

### 文件操作
- `file_list` - 列出目录
- `file_read` - 读取文件
- `file_write` - 写入文件
- `file_delete` - 删除文件
- `file_copy` - 复制文件
- `file_move` - 移动文件
- `file_info` - 文件信息

### 搜索
- `search_text` - 文本搜索
- `search_method` - 方法调用搜索
- `search_string` - 字符串常量搜索
- `list_classes` - 列出所有类
- `find_class` - 查找类文件

### Smali 操作
- `smali_parse` - 解析smali类
- `smali_get_method` - 获取方法代码
- `smali_replace_method` - 替换方法
- `smali_insert_code` - 插入代码
- `smali_gen_log` - 生成Log代码
- `smali_gen_return` - 生成return代码
