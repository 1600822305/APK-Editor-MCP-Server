package com.apkeditor.dex

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import java.io.BufferedReader
import java.io.InputStreamReader

/**
 * DEX编辑器命令行入口
 * 通过stdin/stdout进行JSON通信
 */

val gson: Gson = GsonBuilder().setPrettyPrinting().create()
val editor = DexEditor()

fun main(args: Array<String>) {
    // 如果有命令行参数，执行单次命令
    if (args.isNotEmpty()) {
        val command = args[0]
        val params = if (args.size > 1) args.drop(1).toTypedArray() else emptyArray()
        val result = executeCommand(command, params)
        println(gson.toJson(result))
        return
    }
    
    // 否则进入交互模式
    val reader = BufferedReader(InputStreamReader(System.`in`))
    
    System.err.println("DEX Editor started. Waiting for commands...")
    
    while (true) {
        try {
            val line = reader.readLine() ?: break
            if (line.isBlank()) continue
            
            val request = gson.fromJson(line, Request::class.java)
            val result = executeCommand(request.command, request.args.toTypedArray())
            
            println(gson.toJson(result))
            System.out.flush()
        } catch (e: Exception) {
            val error = Response(
                success = false,
                error = e.message ?: "Unknown error"
            )
            println(gson.toJson(error))
            System.out.flush()
        }
    }
}

fun executeCommand(command: String, args: Array<String>): Response {
    return try {
        when (command.lowercase()) {
            "open" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing APK path")
                } else {
                    val result = editor.openApk(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "list", "list_classes" -> {
                val dexName = args.getOrNull(0)
                val result = editor.listClasses(dexName)
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "get", "get_class" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.getClassSmali(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("smali" to result.getOrNull()))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "get_method" -> {
                if (args.size < 2) {
                    Response(false, error = "Missing class name or method name")
                } else {
                    val result = editor.getMethodSmali(args[0], args[1])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("smali" to result.getOrNull()))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            // 新功能: 类摘要（方法列表、长度等）
            "summary", "class_summary" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.getClassSummary(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            // 新功能: 分页获取smali
            "get_paged", "get_class_paged" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val offset = args.getOrNull(1)?.toIntOrNull() ?: 0
                    val limit = args.getOrNull(2)?.toIntOrNull() ?: 0
                    val result = editor.getClassSmaliPaged(args[0], offset, limit)
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            // 新功能: smali转Java
            "to_java", "decompile" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.smaliToJava(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("java" to result.getOrNull()))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            // 设置jadx路径
            "set_jadx", "jadx_path" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing jadx path")
                } else {
                    editor.setJadxPath(args[0])
                    Response(true, data = mapOf("jadxPath" to args[0]))
                }
            }
            
            // 反混淆并转Java
            "deobf", "deobfuscate" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.deobfuscateToJava(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("java" to result.getOrNull()))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            // 批量反编译包
            "decompile_package", "batch_decompile" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing package pattern (e.g., com.example.*)")
                } else {
                    val maxClasses = args.getOrNull(1)?.toIntOrNull() ?: 10
                    val result = editor.decompilePackage(args[0], maxClasses)
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "modify", "modify_class" -> {
                if (args.size < 2) {
                    Response(false, error = "Missing class name or smali code")
                } else {
                    val result = editor.modifyClass(args[0], args[1])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("modified" to true))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "save" -> {
                val outputPath = args.getOrNull(0)
                val result = editor.save(outputPath)
                if (result.isSuccess) {
                    Response(true, data = mapOf("output" to result.getOrNull()))
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "search_class" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing search pattern")
                } else {
                    val result = editor.searchClass(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "search_string" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing search text")
                } else {
                    val result = editor.searchString(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "search_calls", "search_method_calls" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing method pattern")
                } else {
                    val result = editor.searchMethodCalls(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "find_subclasses" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.findSubclasses(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "search_field", "search_field_refs" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing field pattern")
                } else {
                    val result = editor.searchFieldRefs(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "search_int", "search_integer" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing integer value")
                } else {
                    val result = editor.searchInteger(args[0].toInt())
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "class_info", "get_class_info" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.getClassInfo(args[0])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "replace", "replace_in_class" -> {
                if (args.size < 3) {
                    Response(false, error = "Missing class name, old text, or new text")
                } else {
                    val result = editor.replaceInClass(args[0], args[1], args[2])
                    if (result.isSuccess) {
                        Response(true, data = result.getOrNull())
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "delete_class" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing class name")
                } else {
                    val result = editor.deleteClass(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("deleted" to true))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "close" -> {
                editor.close()
                Response(true, data = mapOf("closed" to true))
            }
            
            // 存档点命令
            "checkpoint", "save_checkpoint" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing checkpoint name")
                } else {
                    val result = editor.createCheckpoint(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("saved" to args[0]))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "restore", "restore_checkpoint" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing checkpoint name")
                } else {
                    val result = editor.restoreCheckpoint(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("restored" to args[0]))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "checkpoints", "list_checkpoints" -> {
                val result = editor.listCheckpoints()
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "delete_checkpoint" -> {
                if (args.isEmpty()) {
                    Response(false, error = "Missing checkpoint name")
                } else {
                    val result = editor.deleteCheckpoint(args[0])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("deleted" to args[0]))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "status" -> {
                val result = editor.getStatus()
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "reset" -> {
                val result = editor.reset()
                if (result.isSuccess) {
                    Response(true, data = mapOf("reset" to true))
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "undo" -> {
                val result = editor.undo()
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "redo" -> {
                val result = editor.redo()
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "history" -> {
                val result = editor.getHistory()
                if (result.isSuccess) {
                    Response(true, data = result.getOrNull())
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "auto_checkpoint" -> {
                val enabled = args.getOrNull(0)?.lowercase() == "true"
                val result = editor.setAutoCheckpoint(enabled)
                if (result.isSuccess) {
                    Response(true, data = mapOf("autoCheckpoint" to enabled))
                } else {
                    Response(false, error = result.exceptionOrNull()?.message)
                }
            }
            
            "save_checkpoint_file" -> {
                if (args.size < 2) {
                    Response(false, error = "Missing checkpoint name or file path")
                } else {
                    val result = editor.saveCheckpointToFile(args[0], args[1])
                    if (result.isSuccess) {
                        Response(true, data = mapOf("saved" to args[1]))
                    } else {
                        Response(false, error = result.exceptionOrNull()?.message)
                    }
                }
            }
            
            "help" -> {
                Response(true, data = mapOf(
                    "commands" to listOf(
                        "open <apk_path> - Open APK file",
                        "list [dex_name] - List all classes",
                        "get <class_name> - Get class smali code",
                        "get_paged <class> [offset] [limit] - Get smali with pagination",
                        "summary <class_name> - Get class summary (methods, fields, size)",
                        "get_method <class_name> <method_name> - Get method smali",
                        "to_java <class_name> - Convert smali to Java (requires jadx)",
                        "class_info <class_name> - Get class details (methods, fields)",
                        "modify <class_name> <smali_code> - Modify class",
                        "replace <class_name> <old> <new> - Replace text in class",
                        "delete_class <class_name> - Delete a class",
                        "save [output_path] - Save modifications",
                        "search_class <pattern> - Search classes by name",
                        "search_string <text> - Search strings in code",
                        "search_calls <method_pattern> - Find method call sites",
                        "search_field <field_pattern> - Search field references",
                        "search_int <value> - Search integer constants",
                        "find_subclasses <class_name> - Find subclasses/implementations",
                        "checkpoint <name> - Create checkpoint (save point)",
                        "restore <name> - Restore to checkpoint",
                        "checkpoints - List all checkpoints",
                        "delete_checkpoint <name> - Delete checkpoint",
                        "save_checkpoint_file <name> <path> - Save checkpoint to file",
                        "undo - Undo last modification",
                        "redo - Redo undone modification",
                        "history - Show modification history",
                        "auto_checkpoint <true/false> - Enable/disable auto checkpoint",
                        "status - Show current status",
                        "reset - Reset all modifications",
                        "close - Close editor",
                        "help - Show this help"
                    )
                ))
            }
            
            else -> Response(false, error = "Unknown command: $command")
        }
    } catch (e: Exception) {
        Response(false, error = e.message ?: "Unknown error")
    }
}

data class Request(
    val command: String,
    val args: List<String> = emptyList()
)

data class Response(
    val success: Boolean,
    val data: Any? = null,
    val error: String? = null
)
