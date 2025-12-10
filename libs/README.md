# Libs 目录

此目录需要放置以下jar文件（由于文件过大未上传到GitHub）：

## 必需文件

| 文件 | 说明 | 下载地址 |
|------|------|----------|
| `APKEditor.jar` | APK编辑核心 | [APKEditor Releases](https://github.com/AlanTse1314/AKDTv-APKEditor/releases) |
| `dex-editor.jar` | DEX编辑器 | 从 `../java-core` 构建生成 |
| `apksigner.jar` | APK签名工具 | Android SDK build-tools |

## 可选文件

| 文件 | 说明 | 下载地址 |
|------|------|----------|
| `baksmali.jar` | Smali反编译 | [smali Releases](https://github.com/JesusFreke/smali/releases) |
| `smali.jar` | Smali编译 | [smali Releases](https://github.com/JesusFreke/smali/releases) |

## 获取步骤

### 1. APKEditor.jar
```bash
# 下载最新版本
wget https://github.com/AlanTse1314/AKDTv-APKEditor/releases/download/v1.4.1/APKEditor.jar
```

### 2. dex-editor.jar
```bash
cd ../java-core
./gradlew shadowJar
cp build/libs/dex-editor.jar ../libs/
```

### 3. apksigner.jar
```bash
# Windows: 从Android SDK复制
copy "%LOCALAPPDATA%\Android\Sdk\build-tools\<version>\lib\apksigner.jar" .

# Linux/Mac
cp ~/Android/Sdk/build-tools/<version>/lib/apksigner.jar .
```

## 目录结构

```
libs/
├── README.md              # 本文件
├── APKEditor.jar          # 7MB
├── dex-editor.jar         # 14MB
├── apksigner.jar          # 1MB
├── baksmali.jar           # 1.2MB (可选)
├── smali.jar              # 0.9MB (可选)
└── jadx/                  # jadx工具目录 (可选)
```
