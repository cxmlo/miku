import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.cxmlo.miku.android"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.cxmlo.miku.android"
        minSdk = 26
        targetSdk = 35
        versionCode = 5
        versionName = "0.2.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            val keystorePath = System.getenv("KEYSTORE_PATH")
            val keystorePassword = System.getenv("KEYSTORE_PASSWORD")
            val keyAlias = System.getenv("KEY_ALIAS")
            val keyPassword = System.getenv("KEY_PASSWORD")

            val releaseFile = if (!keystorePath.isNullOrBlank()) file(keystorePath) else null

            if (releaseFile != null && releaseFile.exists()) {
                storeFile = releaseFile
                storePassword = keystorePassword ?: ""
                this.keyAlias = keyAlias ?: ""
                this.keyPassword = keyPassword ?: ""
            } else {
                val bundledDebugKeystore = file("debug.keystore")
                val rootDebugKeystore = rootProject.file("debug.keystore")
                val debugConfig = signingConfigs.getByName("debug")
                val userDebug = debugConfig.storeFile

                val fallbackFile = when {
                    bundledDebugKeystore.exists() -> bundledDebugKeystore
                    rootDebugKeystore.exists() -> rootDebugKeystore
                    userDebug != null && userDebug.exists() -> userDebug
                    else -> null
                }

                if (fallbackFile != null) {
                    storeFile = fallbackFile
                    storePassword = "android"
                    this.keyAlias = "androiddebugkey"
                    this.keyPassword = "android"
                }
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            val releaseSigning = signingConfigs.getByName("release")
            if (releaseSigning.storeFile != null && releaseSigning.storeFile!!.exists()) {
                signingConfig = releaseSigning
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.10.01"))
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.9.4")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.4")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")

    testImplementation("junit:junit:4.13.2")
}
