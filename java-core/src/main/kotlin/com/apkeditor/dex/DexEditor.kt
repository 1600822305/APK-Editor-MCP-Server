package com.apkeditor.dex

import com.android.tools.smali.dexlib2.DexFileFactory
import com.android.tools.smali.dexlib2.Opcodes
import com.android.tools.smali.dexlib2.iface.ClassDef
import com.android.tools.smali.dexlib2.iface.DexFile
import com.android.tools.smali.dexlib2.iface.Method
import com.android.tools.smali.dexlib2.writer.io.FileDataStore
import com.android.tools.smali.dexlib2.writer.pool.DexPool
import com.android.tools.smali.baksmali.Baksmali
import com.android.tools.smali.baksmali.BaksmaliOptions
import com.android.tools.smali.smali.Smali
import com.android.tools.smali.smali.SmaliOptions
import com.android.tools.smali.dexlib2.util.MethodUtil
import jadx.api.JadxArgs
import jadx.api.JadxDecompiler
import java.io.File
import java.io.StringWriter
import java.util.zip.ZipEntry
import java.util.zip.ZipFile
import java.util.zip.ZipOutputStream

/**
 * 快速DEX编辑器 - 内存操作，不生成大量文件
 */
class DexEditor {
    private var apkPath: String? = null
    private var dexFiles: MutableMap<String, DexFile> = mutableMapOf()
    private var modifiedClasses: MutableMap<String, ClassDef> = mutableMapOf()
    private var opcodes: Opcodes = Opcodes.getDefault()
    
    /**
     * 打开APK文件，加载所有DEX到内存
     */
    fun openApk(path: String): Result<Map<String, Int>> {
        return try {
            apkPath = path
            dexFiles.clear()
            modifiedClasses.clear()
            
            val zipFile = ZipFile(File(path))
            val dexEntries = zipFile.entries().asSequence()
                .filter { it.name.endsWith(".dex") }
                .toList()
            
            val result = mutableMapOf<String, Int>()
            
            for (entry in dexEntries) {
                val tempFile = File.createTempFile("dex_", ".dex")
                tempFile.deleteOnExit()
                
                zipFile.getInputStream(entry).use { input ->
                    tempFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                
                val dexFile = DexFileFactory.loadDexFile(tempFile, opcodes)
                dexFiles[entry.name] = dexFile
                result[entry.name] = dexFile.classes.size
                
                tempFile.delete()
            }
            
            zipFile.close()
            Result.success(result)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 列出所有类（不反编译，只返回类名）
     */
    fun listClasses(dexName: String? = null): Result<List<ClassInfo>> {
        return try {
            val classes = mutableListOf<ClassInfo>()
            
            val targetDexFiles = if (dexName != null) {
                dexFiles.filter { it.key == dexName }
            } else {
                dexFiles
            }
            
            for ((name, dexFile) in targetDexFiles) {
                for (classDef in dexFile.classes) {
                    classes.add(ClassInfo(
                        className = classDef.type,
                        dexName = name,
                        accessFlags = classDef.accessFlags,
                        superClass = classDef.superclass,
                        methodCount = classDef.methods.count(),
                        fieldCount = classDef.fields.count()
                    ))
                }
            }
            
            Result.success(classes)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取指定类的smali代码（按需反编译）
     */
    fun getClassSmali(className: String): Result<String> {
        return try {
            // 先检查是否有修改过的版本
            modifiedClasses[className]?.let { classDef ->
                return Result.success(classDefToSmali(classDef))
            }
            
            // 在所有DEX中查找类
            for ((_, dexFile) in dexFiles) {
                val classDef = dexFile.classes.find { it.type == className }
                if (classDef != null) {
                    val smali = classDefToSmali(classDef)
                    return Result.success(smali)
                }
            }
            
            Result.failure(Exception("Class not found: $className"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取指定方法的smali代码
     */
    fun getMethodSmali(className: String, methodName: String): Result<String> {
        return try {
            val classDef = findClass(className) 
                ?: return Result.failure(Exception("Class not found: $className"))
            
            val method = classDef.methods.find { it.name == methodName }
                ?: return Result.failure(Exception("Method not found: $methodName"))
            
            val smali = methodToSmali(method)
            Result.success(smali)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取类的简要信息（方法列表、字段列表、代码长度）
     */
    fun getClassSummary(className: String): Result<ClassSummary> {
        return try {
            val classDef = findClass(className)
                ?: return Result.failure(Exception("Class not found: $className"))
            
            val smali = getClassSmali(className).getOrNull() ?: ""
            
            val methods = classDef.methods.map { method ->
                val params = method.parameterTypes.joinToString(", ")
                MethodSummary(
                    name = method.name,
                    params = params,
                    returnType = method.returnType,
                    accessFlags = method.accessFlags,
                    isVirtual = !MethodUtil.isDirect(method)
                )
            }
            
            val fields = classDef.fields.map { field ->
                FieldSummary(
                    name = field.name,
                    type = field.type,
                    accessFlags = field.accessFlags
                )
            }
            
            Result.success(ClassSummary(
                className = className,
                superClass = classDef.superclass,
                interfaces = classDef.interfaces.toList(),
                methodCount = methods.size,
                fieldCount = fields.size,
                smaliLength = smali.length,
                methods = methods,
                fields = fields
            ))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取类的smali代码（支持分页/限制长度）
     */
    fun getClassSmaliPaged(className: String, offset: Int = 0, limit: Int = 0): Result<PagedSmali> {
        return try {
            val fullSmali = getClassSmali(className).getOrNull()
                ?: return Result.failure(Exception("Class not found: $className"))
            
            val totalLength = fullSmali.length
            
            if (limit <= 0) {
                Result.success(PagedSmali(
                    smali = fullSmali,
                    offset = 0,
                    length = totalLength,
                    totalLength = totalLength,
                    hasMore = false
                ))
            } else {
                val endIndex = minOf(offset + limit, totalLength)
                val content = fullSmali.substring(offset, endIndex)
                Result.success(PagedSmali(
                    smali = content,
                    offset = offset,
                    length = content.length,
                    totalLength = totalLength,
                    hasMore = endIndex < totalLength
                ))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // jadx路径（可通过setJadxPath设置）
    private var jadxPath: String? = null
    
    fun setJadxPath(path: String) {
        jadxPath = path
    }
    
    /**
     * smali转Java（使用内嵌jadx-core）
     */
    fun smaliToJava(className: String): Result<String> {
        return try {
            val classDef = findClass(className)
                ?: return Result.failure(Exception("Class not found: $className"))
            
            // 创建临时DEX文件
            val tempDex = File.createTempFile("decompile_", ".dex")
            tempDex.deleteOnExit()
            
            val dexPool = DexPool(opcodes)
            dexPool.internClass(classDef)
            dexPool.writeTo(FileDataStore(tempDex))
            
            // 使用内嵌jadx反编译
            val javaCode = decompileWithJadxCore(tempDex, className)
            
            tempDex.delete()
            
            Result.success(javaCode)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 使用内嵌jadx-core反编译
     */
    private fun decompileWithJadxCore(dexFile: File, className: String): String {
        return try {
            val args = JadxArgs().apply {
                setInputFile(dexFile)
                isSkipResources = true
                isShowInconsistentCode = true
            }
            
            JadxDecompiler(args).use { jadx ->
                jadx.load()
                
                // 查找类
                val javaClass = jadx.classes.find { 
                    it.fullName == className.substring(1, className.length - 1).replace("/", ".")
                }
                
                if (javaClass != null) {
                    javaClass.code
                } else {
                    // 返回所有类的代码
                    jadx.classes.firstOrNull()?.code 
                        ?: "// No classes found in decompiled output"
                }
            }
        } catch (e: Exception) {
            "// Decompile error: ${e.message}\n// Stack trace:\n${e.stackTraceToString()}"
        }
    }
    
    /**
     * 反混淆并反编译到Java（自动重命名混淆名称）
     */
    fun deobfuscateToJava(className: String): Result<String> {
        return try {
            val classDef = findClass(className)
                ?: return Result.failure(Exception("Class not found: $className"))
            
            val tempDex = File.createTempFile("deobf_", ".dex")
            tempDex.deleteOnExit()
            
            val dexPool = DexPool(opcodes)
            dexPool.internClass(classDef)
            dexPool.writeTo(FileDataStore(tempDex))
            
            val args = JadxArgs().apply {
                setInputFile(tempDex)
                isSkipResources = true
                isShowInconsistentCode = true
                // 启用反混淆
                isDeobfuscationOn = true
                deobfuscationMinLength = 2
                deobfuscationMaxLength = 64
                // 使用Kotlin方法名重命名变量
                useKotlinMethodsForVarNames = JadxArgs.UseKotlinMethodsForVarNames.APPLY
            }
            
            val code = JadxDecompiler(args).use { jadx ->
                jadx.load()
                jadx.classes.firstOrNull()?.code ?: "// No code generated"
            }
            
            tempDex.delete()
            Result.success(code)
        } catch (e: Exception) {
            // 返回错误信息而不是抛出异常
            Result.success("// Deobfuscation error: ${e.message}\n// Try using to_java instead")
        }
    }
    
    /**
     * 批量反编译包下所有类（限制数量避免数据过大）
     */
    fun decompilePackage(packagePattern: String, maxClasses: Int = 10): Result<PackageDecompileResult> {
        return try {
            val regex = Regex(packagePattern.replace(".", "/").replace("*", ".*"))
            
            // 收集匹配的类
            val matchedClasses = mutableListOf<ClassDef>()
            for ((_, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    if (regex.containsMatchIn(classDef.type)) {
                        matchedClasses.add(classDef)
                    }
                }
            }
            
            if (matchedClasses.isEmpty()) {
                return Result.success(PackageDecompileResult(
                    totalMatched = 0,
                    decompiled = 0,
                    classes = emptyMap(),
                    truncated = false
                ))
            }
            
            val truncated = matchedClasses.size > maxClasses
            val toDecompile = matchedClasses.take(maxClasses)
            
            // 创建包含匹配类的临时DEX
            val tempDex = File.createTempFile("batch_", ".dex")
            tempDex.deleteOnExit()
            
            val dexPool = DexPool(opcodes)
            toDecompile.forEach { dexPool.internClass(it) }
            dexPool.writeTo(FileDataStore(tempDex))
            
            val args = JadxArgs().apply {
                setInputFile(tempDex)
                isSkipResources = true
                isShowInconsistentCode = true
            }
            
            val results = mutableMapOf<String, String>()
            JadxDecompiler(args).use { jadx ->
                jadx.load()
                for (javaClass in jadx.classes) {
                    results[javaClass.fullName] = javaClass.code
                }
            }
            
            tempDex.delete()
            Result.success(PackageDecompileResult(
                totalMatched = matchedClasses.size,
                decompiled = results.size,
                classes = results,
                truncated = truncated
            ))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 使用jadx反编译DEX到Java
     */
    private fun decompileWithJadx(dexFile: File, className: String): String? {
        return try {
            val outputDir = File.createTempFile("jadx_", "").apply {
                delete()
                mkdirs()
                deleteOnExit()
            }
            
            // 调用jadx (优先使用jar，否则使用命令)
            val jadxJar = this@DexEditor.jadxPath 
                ?: System.getenv("JADX_JAR") 
                ?: System.getenv("JADX_PATH")
            
            val processBuilder = if (jadxJar != null && jadxJar.endsWith(".jar")) {
                // 直接调用jar的CLI主类
                ProcessBuilder("java", "-cp", jadxJar, "jadx.cli.JadxCLI", "-d", outputDir.absolutePath, dexFile.absolutePath)
            } else if (jadxJar != null && jadxJar.endsWith(".bat")) {
                // Windows bat脚本 - 查找对应的jar
                val jadxDir = File(jadxJar).parentFile.parentFile
                val jadxAllJar = File(jadxDir, "lib/jadx-1.5.0-all.jar")
                if (jadxAllJar.exists()) {
                    ProcessBuilder("java", "-cp", jadxAllJar.absolutePath, "jadx.cli.JadxCLI", "-d", outputDir.absolutePath, dexFile.absolutePath)
                } else {
                    ProcessBuilder("cmd", "/c", jadxJar, "-d", outputDir.absolutePath, dexFile.absolutePath)
                }
            } else if (jadxJar != null) {
                ProcessBuilder(jadxJar, "-d", outputDir.absolutePath, dexFile.absolutePath)
            } else {
                ProcessBuilder("jadx", "-d", outputDir.absolutePath, dexFile.absolutePath)
            }
            
            // 设置JADX_HOME避免加载用户插件
            val jadxHome = jadxJar?.let { 
                if (it.endsWith(".jar")) File(it).parentFile.parentFile.absolutePath
                else if (it.endsWith(".bat")) File(it).parentFile.parentFile.absolutePath
                else null
            }
            
            val process = processBuilder.apply {
                if (jadxHome != null) {
                    environment()["JADX_HOME"] = jadxHome
                }
            }
                .redirectErrorStream(true)
                .start()
            
            // 读取输出
            val output = process.inputStream.bufferedReader().readText()
            val exitCode = process.waitFor()
            
            if (exitCode == 0) {
                // 查找生成的Java文件
                val javaFileName = className.substring(1, className.length - 1).replace("/", File.separator) + ".java"
                val javaFile = File(outputDir, javaFileName)
                
                if (javaFile.exists()) {
                    val content = javaFile.readText()
                    outputDir.deleteRecursively()
                    content
                } else {
                    // 尝试查找sources目录
                    val sourcesDir = File(outputDir, "sources")
                    val altJavaFile = File(sourcesDir, javaFileName)
                    if (altJavaFile.exists()) {
                        val content = altJavaFile.readText()
                        outputDir.deleteRecursively()
                        content
                    } else {
                        // 递归查找所有Java文件
                        val allFiles = outputDir.walkTopDown().filter { it.extension == "java" }.toList()
                        if (allFiles.isNotEmpty()) {
                            val content = allFiles.first().readText()
                            outputDir.deleteRecursively()
                            content
                        } else {
                            outputDir.deleteRecursively()
                            "// jadx output dir: ${outputDir.absolutePath}\n// Files: ${outputDir.walkTopDown().toList()}\n// Output: $output"
                        }
                    }
                }
            } else {
                outputDir.deleteRecursively()
                "// jadx failed with exit code $exitCode\n// Command: $jadxJar\n// Output: $output"
            }
        } catch (e: Exception) {
            "// Exception: ${e.message}"
        }
    }
    
    /**
     * 修改类的smali代码
     */
    fun modifyClass(className: String, newSmali: String): Result<Boolean> {
        return try {
            // 获取原来的smali（用于撤销）
            val oldSmali = getClassSmali(className).getOrNull()
            
            // 自动存档
            if (autoCheckpoint) {
                autoCheckpointCounter++
                createCheckpoint("auto_$autoCheckpointCounter")
            }
            
            // 将smali编译为ClassDef
            val tempDir = File.createTempFile("smali_", "").apply { 
                delete()
                mkdirs()
                deleteOnExit()
            }
            
            val smaliFile = File(tempDir, className.substring(1, className.length - 1) + ".smali")
            smaliFile.parentFile?.mkdirs()
            smaliFile.writeText(newSmali)
            
            // 使用临时dex文件来编译smali
            val tempDex = File.createTempFile("smali_out_", ".dex")
            tempDex.deleteOnExit()
            
            val options = SmaliOptions()
            options.outputDexFile = tempDex.absolutePath
            
            val success = Smali.assemble(options, tempDir.absolutePath)
            
            if (!success) {
                return Result.failure(Exception("Failed to assemble smali"))
            }
            
            // 加载编译后的dex
            val dexFile = DexFileFactory.loadDexFile(tempDex, opcodes)
            val newClassDef = dexFile.classes.firstOrNull()
                ?: return Result.failure(Exception("Failed to compile smali"))
            
            modifiedClasses[className] = newClassDef
            
            // 记录历史（用于撤销）
            recordHistory(HistoryAction(
                type = "modify",
                className = className,
                oldSmali = oldSmali,
                newSmali = newSmali
            ))
            
            // 清理临时文件
            tempDir.deleteRecursively()
            tempDex.delete()
            
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 保存修改到APK
     */
    fun save(outputPath: String? = null): Result<String> {
        return try {
            val srcApk = apkPath ?: return Result.failure(Exception("No APK opened"))
            val dstApk = outputPath ?: srcApk.replace(".apk", "_modified.apk")
            
            val srcFile = File(srcApk)
            val dstFile = File(dstApk)
            
            ZipFile(srcFile).use { zipIn ->
                ZipOutputStream(dstFile.outputStream()).use { zipOut ->
                    // 复制非DEX文件
                    for (entry in zipIn.entries()) {
                        if (!entry.name.endsWith(".dex")) {
                            zipOut.putNextEntry(ZipEntry(entry.name))
                            zipIn.getInputStream(entry).copyTo(zipOut)
                            zipOut.closeEntry()
                        }
                    }
                    
                    // 写入修改后的DEX
                    for ((dexName, dexFile) in dexFiles) {
                        val dexPool = DexPool(opcodes)
                        
                        for (classDef in dexFile.classes) {
                            // 跳过已删除的类
                            if (deletedClasses.contains(classDef.type)) continue
                            // 检查是否有修改
                            val finalClass = modifiedClasses[classDef.type] ?: classDef
                            dexPool.internClass(finalClass)
                        }
                        
                        val tempDex = File.createTempFile("dex_out_", ".dex")
                        tempDex.deleteOnExit()
                        
                        dexPool.writeTo(FileDataStore(tempDex))
                        
                        zipOut.putNextEntry(ZipEntry(dexName))
                        tempDex.inputStream().copyTo(zipOut)
                        zipOut.closeEntry()
                        
                        tempDex.delete()
                    }
                }
            }
            
            Result.success(dstApk)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 搜索类
     */
    fun searchClass(pattern: String): Result<List<String>> {
        return try {
            val results = mutableListOf<String>()
            val regex = Regex(pattern, RegexOption.IGNORE_CASE)
            
            for ((_, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    if (regex.containsMatchIn(classDef.type)) {
                        results.add(classDef.type)
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 搜索字符串
     */
    fun searchString(text: String): Result<List<StringSearchResult>> {
        return try {
            val results = mutableListOf<StringSearchResult>()
            
            for ((dexName, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    for (method in classDef.methods) {
                        val impl = method.implementation ?: continue
                        for (instruction in impl.instructions) {
                            val str = instruction.toString()
                            if (str.contains(text)) {
                                results.add(StringSearchResult(
                                    className = classDef.type,
                                    methodName = method.name,
                                    dexName = dexName,
                                    context = str
                                ))
                            }
                        }
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 搜索方法调用处 - MT管理器核心功能
     */
    fun searchMethodCalls(methodPattern: String): Result<List<MethodCallResult>> {
        return try {
            val results = mutableListOf<MethodCallResult>()
            val pattern = methodPattern.lowercase()
            
            for ((dexName, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    for (method in classDef.methods) {
                        val impl = method.implementation ?: continue
                        for (instruction in impl.instructions) {
                            val instrStr = instruction.toString()
                            if (instrStr.contains("invoke") && instrStr.lowercase().contains(pattern)) {
                                results.add(MethodCallResult(
                                    callerClass = classDef.type,
                                    callerMethod = method.name,
                                    callInstruction = instrStr,
                                    dexName = dexName
                                ))
                            }
                        }
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 查找子类/实现类 - 用于查找重写方法
     */
    fun findSubclasses(className: String): Result<List<String>> {
        return try {
            val results = mutableListOf<String>()
            
            for ((_, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    // 检查父类
                    if (classDef.superclass == className) {
                        results.add(classDef.type)
                    }
                    // 检查实现的接口
                    if (classDef.interfaces.contains(className)) {
                        results.add(classDef.type)
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 搜索字段引用
     */
    fun searchFieldRefs(fieldPattern: String): Result<List<FieldRefResult>> {
        return try {
            val results = mutableListOf<FieldRefResult>()
            val pattern = fieldPattern.lowercase()
            
            for ((dexName, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    for (method in classDef.methods) {
                        val impl = method.implementation ?: continue
                        for (instruction in impl.instructions) {
                            val instrStr = instruction.toString()
                            if ((instrStr.contains("iget") || instrStr.contains("iput") ||
                                 instrStr.contains("sget") || instrStr.contains("sput")) &&
                                instrStr.lowercase().contains(pattern)) {
                                results.add(FieldRefResult(
                                    className = classDef.type,
                                    methodName = method.name,
                                    instruction = instrStr,
                                    dexName = dexName
                                ))
                            }
                        }
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 搜索整数常量
     */
    fun searchInteger(value: Int): Result<List<IntegerSearchResult>> {
        return try {
            val results = mutableListOf<IntegerSearchResult>()
            val hexValue = "0x${value.toString(16)}"
            
            for ((dexName, dexFile) in dexFiles) {
                for (classDef in dexFile.classes) {
                    for (method in classDef.methods) {
                        val impl = method.implementation ?: continue
                        for (instruction in impl.instructions) {
                            val instrStr = instruction.toString()
                            if (instrStr.contains("const") && 
                                (instrStr.contains(" $value") || instrStr.contains(hexValue))) {
                                results.add(IntegerSearchResult(
                                    className = classDef.type,
                                    methodName = method.name,
                                    instruction = instrStr,
                                    dexName = dexName
                                ))
                            }
                        }
                    }
                }
            }
            
            Result.success(results)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取类的详细信息（字段、方法列表）
     */
    fun getClassInfo(className: String): Result<ClassDetailInfo> {
        return try {
            val classDef = findClass(className)
                ?: return Result.failure(Exception("Class not found: $className"))
            
            val methods = classDef.methods.map { m ->
                MethodInfo(
                    name = m.name,
                    params = m.parameterTypes.joinToString(""),
                    returnType = m.returnType,
                    accessFlags = m.accessFlags
                )
            }
            
            val fields = classDef.fields.map { f ->
                FieldInfo(
                    name = f.name,
                    type = f.type,
                    accessFlags = f.accessFlags
                )
            }
            
            Result.success(ClassDetailInfo(
                className = classDef.type,
                superClass = classDef.superclass,
                interfaces = classDef.interfaces.toList(),
                accessFlags = classDef.accessFlags,
                methods = methods,
                fields = fields
            ))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 批量替换代码
     */
    fun replaceInClass(className: String, oldText: String, newText: String): Result<ReplaceResult> {
        return try {
            val smaliResult = getClassSmali(className)
            if (smaliResult.isFailure) {
                return Result.failure(smaliResult.exceptionOrNull()!!)
            }
            
            val originalSmali = smaliResult.getOrNull()!!
            val newSmali = originalSmali.replace(oldText, newText)
            
            if (originalSmali == newSmali) {
                return Result.success(ReplaceResult(replaced = false, count = 0))
            }
            
            val count = originalSmali.split(oldText).size - 1
            
            val modifyResult = modifyClass(className, newSmali)
            if (modifyResult.isFailure) {
                return Result.failure(modifyResult.exceptionOrNull()!!)
            }
            
            Result.success(ReplaceResult(replaced = true, count = count))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 删除类
     */
    fun deleteClass(className: String): Result<Boolean> {
        return try {
            // 自动存档
            if (autoCheckpoint) {
                autoCheckpointCounter++
                createCheckpoint("auto_$autoCheckpointCounter")
            }
            
            // 标记类为已删除（用空实现替代）
            modifiedClasses.remove(className)
            
            // 在dexFiles中也标记删除
            for ((_, dexFile) in dexFiles) {
                val classDef = dexFile.classes.find { it.type == className }
                if (classDef != null) {
                    // 这里我们用一个特殊标记表示删除
                    // 实际保存时会跳过这个类
                    deletedClasses.add(className)
                    
                    // 记录历史
                    recordHistory(HistoryAction(
                        type = "delete",
                        className = className,
                        oldSmali = null,
                        newSmali = null
                    ))
                    
                    return Result.success(true)
                }
            }
            
            Result.failure(Exception("Class not found: $className"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private val deletedClasses = mutableSetOf<String>()
    
    // 存档点系统
    private val checkpoints = mutableMapOf<String, CheckpointData>()
    
    // 操作历史（用于撤销）
    private val history = mutableListOf<HistoryAction>()
    private var historyIndex = -1
    private val maxHistorySize = 50
    
    // 自动存档设置
    private var autoCheckpoint = false
    private var autoCheckpointCounter = 0
    
    /**
     * 创建存档点
     */
    fun createCheckpoint(name: String): Result<Boolean> {
        return try {
            val data = CheckpointData(
                modifiedClasses = modifiedClasses.toMap(),
                deletedClasses = deletedClasses.toSet(),
                timestamp = System.currentTimeMillis()
            )
            checkpoints[name] = data
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 恢复到存档点
     */
    fun restoreCheckpoint(name: String): Result<Boolean> {
        return try {
            val data = checkpoints[name]
                ?: return Result.failure(Exception("Checkpoint not found: $name"))
            
            modifiedClasses.clear()
            modifiedClasses.putAll(data.modifiedClasses)
            deletedClasses.clear()
            deletedClasses.addAll(data.deletedClasses)
            
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 列出所有存档点
     */
    fun listCheckpoints(): Result<List<CheckpointInfo>> {
        return try {
            val list = checkpoints.map { (name, data) ->
                CheckpointInfo(
                    name = name,
                    modifiedCount = data.modifiedClasses.size,
                    deletedCount = data.deletedClasses.size,
                    timestamp = data.timestamp
                )
            }
            Result.success(list)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 删除存档点
     */
    fun deleteCheckpoint(name: String): Result<Boolean> {
        return try {
            if (checkpoints.remove(name) != null) {
                Result.success(true)
            } else {
                Result.failure(Exception("Checkpoint not found: $name"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 获取当前修改状态
     */
    fun getStatus(): Result<StatusInfo> {
        return try {
            Result.success(StatusInfo(
                apkPath = apkPath,
                dexCount = dexFiles.size,
                totalClasses = dexFiles.values.sumOf { it.classes.size },
                modifiedCount = modifiedClasses.size,
                deletedCount = deletedClasses.size,
                checkpointCount = checkpoints.size,
                historyCount = history.size,
                historyIndex = historyIndex,
                autoCheckpoint = autoCheckpoint
            ))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 重置所有修改（恢复到原始状态）
     */
    fun reset(): Result<Boolean> {
        return try {
            modifiedClasses.clear()
            deletedClasses.clear()
            history.clear()
            historyIndex = -1
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 记录历史操作（用于撤销）
     */
    private fun recordHistory(action: HistoryAction) {
        // 如果在历史中间，删除后面的记录
        if (historyIndex < history.size - 1) {
            history.subList(historyIndex + 1, history.size).clear()
        }
        
        history.add(action)
        historyIndex = history.size - 1
        
        // 限制历史大小
        while (history.size > maxHistorySize) {
            history.removeAt(0)
            historyIndex--
        }
    }
    
    /**
     * 撤销操作
     */
    fun undo(): Result<UndoResult> {
        return try {
            if (historyIndex < 0) {
                return Result.success(UndoResult(success = false, message = "Nothing to undo"))
            }
            
            val action = history[historyIndex]
            
            // 恢复之前的状态
            when (action.type) {
                "modify" -> {
                    if (action.oldSmali != null) {
                        // 恢复旧的smali
                        val tempDir = File.createTempFile("smali_undo_", "").apply {
                            delete()
                            mkdirs()
                            deleteOnExit()
                        }
                        val smaliFile = File(tempDir, action.className.substring(1, action.className.length - 1) + ".smali")
                        smaliFile.parentFile?.mkdirs()
                        smaliFile.writeText(action.oldSmali)
                        
                        val options = SmaliOptions()
                        options.outputDexFile = File.createTempFile("undo_", ".dex").apply { deleteOnExit() }.absolutePath
                        
                        if (Smali.assemble(options, tempDir.absolutePath)) {
                            val dexFile = DexFileFactory.loadDexFile(File(options.outputDexFile), opcodes)
                            dexFile.classes.firstOrNull()?.let { classDef ->
                                modifiedClasses[action.className] = classDef
                            }
                        }
                        tempDir.deleteRecursively()
                    } else {
                        modifiedClasses.remove(action.className)
                    }
                }
                "delete" -> {
                    deletedClasses.remove(action.className)
                }
            }
            
            historyIndex--
            Result.success(UndoResult(success = true, message = "Undone: ${action.type} ${action.className}"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 重做操作
     */
    fun redo(): Result<UndoResult> {
        return try {
            if (historyIndex >= history.size - 1) {
                return Result.success(UndoResult(success = false, message = "Nothing to redo"))
            }
            
            historyIndex++
            val action = history[historyIndex]
            
            // 重新执行操作
            when (action.type) {
                "modify" -> {
                    if (action.newSmali != null) {
                        val tempDir = File.createTempFile("smali_redo_", "").apply {
                            delete()
                            mkdirs()
                            deleteOnExit()
                        }
                        val smaliFile = File(tempDir, action.className.substring(1, action.className.length - 1) + ".smali")
                        smaliFile.parentFile?.mkdirs()
                        smaliFile.writeText(action.newSmali)
                        
                        val options = SmaliOptions()
                        options.outputDexFile = File.createTempFile("redo_", ".dex").apply { deleteOnExit() }.absolutePath
                        
                        if (Smali.assemble(options, tempDir.absolutePath)) {
                            val dexFile = DexFileFactory.loadDexFile(File(options.outputDexFile), opcodes)
                            dexFile.classes.firstOrNull()?.let { classDef ->
                                modifiedClasses[action.className] = classDef
                            }
                        }
                        tempDir.deleteRecursively()
                    }
                }
                "delete" -> {
                    deletedClasses.add(action.className)
                }
            }
            
            Result.success(UndoResult(success = true, message = "Redone: ${action.type} ${action.className}"))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 设置自动存档模式
     */
    fun setAutoCheckpoint(enabled: Boolean): Result<Boolean> {
        autoCheckpoint = enabled
        return Result.success(true)
    }
    
    /**
     * 获取历史记录
     */
    fun getHistory(): Result<List<HistoryInfo>> {
        return try {
            val list = history.mapIndexed { index, action ->
                HistoryInfo(
                    index = index,
                    type = action.type,
                    className = action.className,
                    timestamp = action.timestamp,
                    isCurrent = index == historyIndex
                )
            }
            Result.success(list)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 保存存档点到文件
     */
    fun saveCheckpointToFile(name: String, filePath: String): Result<Boolean> {
        return try {
            val data = checkpoints[name]
                ?: return Result.failure(Exception("Checkpoint not found: $name"))
            
            val json = com.google.gson.GsonBuilder().setPrettyPrinting().create()
            val content = json.toJson(mapOf(
                "name" to name,
                "timestamp" to data.timestamp,
                "modifiedClasses" to data.modifiedClasses.keys.toList(),
                "deletedClasses" to data.deletedClasses.toList()
            ))
            
            File(filePath).writeText(content)
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * 关闭编辑器
     */
    fun close() {
        apkPath = null
        dexFiles.clear()
        modifiedClasses.clear()
        deletedClasses.clear()
        checkpoints.clear()
        history.clear()
        historyIndex = -1
    }
    
    // ===== 辅助方法 =====
    
    private fun findClass(className: String): ClassDef? {
        modifiedClasses[className]?.let { return it }
        
        for ((_, dexFile) in dexFiles) {
            val classDef = dexFile.classes.find { it.type == className }
            if (classDef != null) return classDef
        }
        return null
    }
    
    private fun classDefToSmali(classDef: ClassDef): String {
        val tempDir = File.createTempFile("baksmali_", "").apply {
            delete()
            mkdirs()
            deleteOnExit()
        }
        
        try {
            val options = BaksmaliOptions()
            
            // 创建临时DexFile只包含这一个类
            val singleClassDex = object : DexFile {
                override fun getClasses() = setOf(classDef)
                override fun getOpcodes() = this@DexEditor.opcodes
            }
            
            Baksmali.disassembleDexFile(singleClassDex, tempDir, 1, options)
            
            // 读取生成的smali文件
            val classPath = classDef.type.substring(1, classDef.type.length - 1) + ".smali"
            val smaliFile = File(tempDir, classPath)
            
            return if (smaliFile.exists()) {
                smaliFile.readText()
            } else {
                "# Failed to disassemble class: ${classDef.type}"
            }
        } finally {
            tempDir.deleteRecursively()
        }
    }
    
    private fun methodToSmali(method: Method): String {
        val sb = StringBuilder()
        sb.appendLine(".method ${getAccessFlagsString(method.accessFlags)} ${method.name}(${method.parameterTypes.joinToString("")})${method.returnType}")
        
        method.implementation?.let { impl ->
            sb.appendLine("    .registers ${impl.registerCount}")
            for (instruction in impl.instructions) {
                sb.appendLine("    $instruction")
            }
        }
        
        sb.appendLine(".end method")
        return sb.toString()
    }
    
    private fun getAccessFlagsString(flags: Int): String {
        val parts = mutableListOf<String>()
        if (flags and 0x0001 != 0) parts.add("public")
        if (flags and 0x0002 != 0) parts.add("private")
        if (flags and 0x0004 != 0) parts.add("protected")
        if (flags and 0x0008 != 0) parts.add("static")
        if (flags and 0x0010 != 0) parts.add("final")
        if (flags and 0x0020 != 0) parts.add("synchronized")
        if (flags and 0x0100 != 0) parts.add("native")
        if (flags and 0x0400 != 0) parts.add("abstract")
        return parts.joinToString(" ")
    }
}

data class ClassInfo(
    val className: String,
    val dexName: String,
    val accessFlags: Int,
    val superClass: String?,
    val methodCount: Int,
    val fieldCount: Int
)

data class StringSearchResult(
    val className: String,
    val methodName: String,
    val dexName: String,
    val context: String
)

data class MethodCallResult(
    val callerClass: String,
    val callerMethod: String,
    val callInstruction: String,
    val dexName: String
)

data class FieldRefResult(
    val className: String,
    val methodName: String,
    val instruction: String,
    val dexName: String
)

data class IntegerSearchResult(
    val className: String,
    val methodName: String,
    val instruction: String,
    val dexName: String
)

data class ClassDetailInfo(
    val className: String,
    val superClass: String?,
    val interfaces: List<String>,
    val accessFlags: Int,
    val methods: List<MethodInfo>,
    val fields: List<FieldInfo>
)

data class MethodInfo(
    val name: String,
    val params: String,
    val returnType: String,
    val accessFlags: Int
)

data class FieldInfo(
    val name: String,
    val type: String,
    val accessFlags: Int
)

data class ReplaceResult(
    val replaced: Boolean,
    val count: Int
)

data class CheckpointData(
    val modifiedClasses: Map<String, ClassDef>,
    val deletedClasses: Set<String>,
    val timestamp: Long
)

data class CheckpointInfo(
    val name: String,
    val modifiedCount: Int,
    val deletedCount: Int,
    val timestamp: Long
)

data class StatusInfo(
    val apkPath: String?,
    val dexCount: Int,
    val totalClasses: Int,
    val modifiedCount: Int,
    val deletedCount: Int,
    val checkpointCount: Int,
    val historyCount: Int = 0,
    val historyIndex: Int = -1,
    val autoCheckpoint: Boolean = false
)

data class HistoryAction(
    val type: String,  // "modify" or "delete"
    val className: String,
    val oldSmali: String?,
    val newSmali: String?,
    val timestamp: Long = System.currentTimeMillis()
)

data class HistoryInfo(
    val index: Int,
    val type: String,
    val className: String,
    val timestamp: Long,
    val isCurrent: Boolean
)

data class UndoResult(
    val success: Boolean,
    val message: String
)

data class ClassSummary(
    val className: String,
    val superClass: String?,
    val interfaces: List<String>,
    val methodCount: Int,
    val fieldCount: Int,
    val smaliLength: Int,
    val methods: List<MethodSummary>,
    val fields: List<FieldSummary>
)

data class MethodSummary(
    val name: String,
    val params: String,
    val returnType: String,
    val accessFlags: Int,
    val isVirtual: Boolean
)

data class FieldSummary(
    val name: String,
    val type: String,
    val accessFlags: Int
)

data class PagedSmali(
    val smali: String,
    val offset: Int,
    val length: Int,
    val totalLength: Int,
    val hasMore: Boolean
)

data class PackageDecompileResult(
    val totalMatched: Int,
    val decompiled: Int,
    val classes: Map<String, String>,
    val truncated: Boolean
)
