plugins {
    kotlin("jvm") version "1.9.22"
    application
    id("com.github.johnrengelman.shadow") version "8.1.1"
}

group = "com.apkeditor"
version = "1.0.0"

repositories {
    mavenCentral()
    google()
}

dependencies {
    // smali/dexlib2 - DEX操作核心库
    implementation("com.android.tools.smali:smali-dexlib2:3.0.3")
    implementation("com.android.tools.smali:smali:3.0.3")
    implementation("com.android.tools.smali:smali-baksmali:3.0.3")
    
    // jadx-core - 反编译到Java
    implementation("io.github.skylot:jadx-core:1.5.0")
    implementation("io.github.skylot:jadx-dex-input:1.5.0")
    
    // JSON处理
    implementation("com.google.code.gson:gson:2.10.1")
    
    // Kotlin
    implementation(kotlin("stdlib"))
}

application {
    mainClass.set("com.apkeditor.dex.MainKt")
}

tasks.shadowJar {
    archiveBaseName.set("dex-editor")
    archiveClassifier.set("")
    archiveVersion.set("")
    manifest {
        attributes["Main-Class"] = "com.apkeditor.dex.MainKt"
    }
}

kotlin {
    jvmToolchain(17)
}
