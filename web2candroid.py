#!/usr/bin/env python3
"""
=============================================================================
   WEB2NATIVE UNIVERSAL COMPILER - ANDROID EDITION (v1.0.0)
=============================================================================
   Version: 1.0.0
   Author:  Narendra Kumar
   License: MIT
=============================================================================
"""

import os
import sys
import shutil
import argparse
import subprocess
import platform
import datetime
import zipfile
from pathlib import Path

# ===========================================================================
# CONFIGURATION
# ===========================================================================
ROOT_DIR = Path.cwd().resolve()
OUTPUT_DIR = ROOT_DIR / "output"
LOG_PREFIX = "[Web2Native]"

class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    if level == "INFO":
        print(f"{Colors.GREEN}{LOG_PREFIX} [INFO] {timestamp} - {msg}{Colors.ENDC}")
    elif level == "WARN":
        print(f"{Colors.WARNING}{LOG_PREFIX} [WARN] {timestamp} - {msg}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.FAIL}{LOG_PREFIX} [ERROR] {timestamp} - {msg}{Colors.ENDC}")
    elif level == "STEP":
        print(f"\n{Colors.BOLD}>>> {msg} <<<{Colors.ENDC}")

def resolve_asset_path(path_str, asset_name):
    """
    Smartly resolves paths (handles ~, relative paths) and checks existence.
    Returns absolute Path object or None.
    """
    if not path_str:
        return None
    
    # Expand user (~) and resolve absolute path
    path = Path(os.path.expanduser(path_str)).resolve()
    
    if path.exists() and path.is_file():
        log(f"Found custom {asset_name}: {path}", "INFO")
        return path
    else:
        log(f"Could NOT find {asset_name} at: {path_str}", "WARN")
        log(f"-> Verified absolute path was: {path}", "WARN")
        log(f"-> Proceeding with default {asset_name}.", "WARN")
        return None

# ===========================================================================
# ASSET BUNDLING
# ===========================================================================
def bundle_website(url, target_path):
    log(f"Downloading website assets from {url}...", "STEP")
    target_path.mkdir(parents=True, exist_ok=True)
    temp_download = target_path / "temp_dl"
    if temp_download.exists(): shutil.rmtree(temp_download)
    temp_download.mkdir()
    
    cmd = [
        "wget", 
        "--mirror", 
        "--convert-links", 
        "--adjust-extension", 
        "--page-requisites", 
        "--no-parent", 
        "--level=1", 
        "--execute", "robots=off", 
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", 
        "--directory-prefix", str(temp_download), 
        url
    ]
    
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        found = False
        for root, dirs, files in os.walk(temp_download):
            if "index.html" in files:
                for item in os.listdir(root):
                    s = os.path.join(root, item)
                    d = os.path.join(target_path, item)
                    if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                    else: shutil.copy2(s, d)
                found = True
                break
        
        if not found:
            log("Warning: Specific index.html not found. Copying all files.", "WARN")
            shutil.copytree(temp_download, target_path, dirs_exist_ok=True)

        shutil.rmtree(temp_download)
        log(f"Assets cached locally at {target_path}")

    except Exception as e:
        log(f"Asset Error: {e}", "ERROR")
        sys.exit(1)

# ===========================================================================
# ANDROID BUILDER
# ===========================================================================
def build_android_native(work_dir, app_name, package_name, assets_path, icon_path, splash_path, archs, target_url):
    log("Starting Native Android Build (Dual Mode)...", "STEP")
    
    android_root = work_dir / "android_project"
    if android_root.exists(): shutil.rmtree(android_root)
    android_root.mkdir()
    
    package_path = package_name.replace('.', '/')
    app_dir = android_root / "app"
    src_main = app_dir / "src/main"
    java_dir = src_main / f"java/{package_path}"
    res_dir = src_main / "res"
    layout_dir = res_dir / "layout"
    assets_target = src_main / "assets"
    
    java_dir.mkdir(parents=True)
    res_dir.mkdir(parents=True)
    layout_dir.mkdir(parents=True)
    assets_target.mkdir(parents=True)
    
    shutil.copytree(assets_path, assets_target / "www", dirs_exist_ok=True)

    ndk_abi_filters = ""
    if archs:
        abi_list = [f"'{a.strip()}'" for a in archs.split(',')]
        ndk_abi_filters = f"ndk {{ abiFilters {', '.join(abi_list)} }}"

    # SETTINGS.GRADLE
    (android_root / "settings.gradle").write_text(f'''
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "{app_name}"
include ':app'
''', encoding='utf-8')

    # GRADLE.PROPERTIES
    (android_root / "gradle.properties").write_text('''
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
kotlin.code.style=official
''', encoding='utf-8')

    # ROOT BUILD.GRADLE
    (android_root / "build.gradle").write_text('''
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.0"
    }
}
task clean(type: Delete) {
    delete rootProject.buildDir
}
''', encoding='utf-8')

    # APP BUILD.GRADLE (With Minification Enabled)
    (app_dir / "build.gradle").write_text(f'''
plugins {{
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}}

android {{
    namespace '{package_name}'
    compileSdk 34

    defaultConfig {{
        applicationId "{package_name}"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
        {ndk_abi_filters}
    }}

    buildTypes {{
        release {{
            minifyEnabled true   // <--- ENABLED FOR SECURITY
            shrinkResources true // <--- REMOVES UNUSED FILES
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
    }}
    
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = '17'
    }}
}}

dependencies {{
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.webkit:webkit:1.9.0'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.biometric:biometric:1.1.0'
}}
''', encoding='utf-8')

    # PROGUARD RULES (Crucial for Minification to work without crashing)
    (app_dir / "proguard-rules.pro").write_text('''
# Keep generic Android classes
-keep class ** { *; }

# Keep WebView and JavaScript Interfaces
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-keepattributes JavascriptInterface
-keepattributes *Annotation*

# Prevent warnings from stopping the build
-dontwarn **
''', encoding='utf-8')

    # LAYOUT & SPLASH      
    splash_xml_block = ""
    kt_splash_var = ""
    kt_splash_init = ""
    kt_splash_logic = "progressBar.visibility = View.GONE"

    if splash_path:
        ext = splash_path.suffix.lower() or ".png"
        (res_dir / "drawable").mkdir(exist_ok=True)
        shutil.copy(splash_path, res_dir / "drawable" / f"splash_img{ext}")
        
        splash_xml_block = f'''
    <LinearLayout
        android:id="@+id/splash_layout"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical"
        android:gravity="center"
        android:background="#FFFFFF"
        android:clickable="true"
        android:focusable="true"
        android:elevation="10dp">
        <ImageView
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:scaleType="centerCrop"
            android:src="@drawable/splash_img"/>
    </LinearLayout>'''
        
        kt_splash_var = "private lateinit var splashLayout: LinearLayout"
        kt_splash_init = "splashLayout = findViewById(R.id.splash_layout)"
        kt_splash_logic = """
            progressBar.visibility = View.GONE
            if (::splashLayout.isInitialized && splashLayout.visibility == View.VISIBLE) {
                splashLayout.animate()
                    .alpha(0f)
                    .setDuration(400)
                    .setListener(object : AnimatorListenerAdapter() {
                        override fun onAnimationEnd(animation: Animator) {
                            splashLayout.visibility = View.GONE
                        }
                    })
            }
        """

    (layout_dir / "activity_main.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout 
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="#FFFFFF">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical">
        
        <ProgressBar
            android:id="@+id/progressBar"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="4dp"
            android:visibility="gone"
            android:indeterminate="true"
            android:progressTint="#4CAF50"/>

        <WebView
            android:id="@+id/webview"
            android:layout_width="match_parent"
            android:layout_height="match_parent" />
    </LinearLayout>

    {splash_xml_block}

</RelativeLayout>
''', encoding='utf-8')

    # MANIFEST FILE
    (src_main / "AndroidManifest.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" /> 
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
    <uses-permission android:name="android.permission.READ_MEDIA_VISUAL_USER_SELECTED" />
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.WRITE_CONTACTS" />
    <uses-permission android:name="android.permission.READ_SMS" />
    <uses-permission android:name="android.permission.RECEIVE_SMS" />
    <uses-permission android:name="android.permission.SEND_SMS" />
    <uses-permission android:name="android.permission.CALL_PHONE" />
    <uses-permission android:name="android.permission.READ_PHONE_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.NFC" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:allowBackup="true"
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher"
        android:theme="@style/Theme.AppCompat.NoActionBar"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="true">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden|uiMode">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''', encoding='utf-8')

    # KOTLIN LOGIC
    kt_imports = """
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.WindowManager
import androidx.biometric.BiometricPrompt
import androidx.core.app.NotificationCompat
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Vibrator
import android.os.VibratorManager
import android.os.VibrationEffect
import android.content.ClipboardManager
import android.content.ClipData
import android.os.BatteryManager
import android.os.PowerManager
import androidx.biometric.BiometricManager
import android.animation.Animator
import android.animation.AnimatorListenerAdapter
import android.hardware.camera2.CameraManager
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.webkit.PermissionRequest
"""

    (java_dir / "MainActivity.kt").write_text(f'''
package {package_name}

/* * --- CORE ANDROID IMPORTS ---
 * Essential for Activity lifecycle, UI management, and system services.
 */
import android.Manifest
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.net.*
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.webkit.*
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
{kt_imports}

/**
 * MAIN ACTIVITY: The core engine of the application.
 * This class handles: WebView Rendering, Connectivity States, 
 * Runtime Permissions, and File Uploading.
 */
class MainActivity : AppCompatActivity() {{

    // --- UI COMPONENT REFERENCES ---
    private lateinit var myWebView: WebView
    private lateinit var progressBar: ProgressBar
    private lateinit var networkCallback: ConnectivityManager.NetworkCallback
    {kt_splash_var}

    // --- BIOMETRIC SYSTEM REFERENCES ---
    private lateinit var biometricPrompt: BiometricPrompt
    private lateinit var promptInfo: BiometricPrompt.PromptInfo

    // --- NAVIGATION & STATE CONFIGURATION ---
    private val LIVE_URL = "{target_url}"
    private val LOCAL_URL = "file:///android_asset/www/index.html"
    private var lastLiveUrl = LIVE_URL 
    private var isOffline = false
    private var doubleBackToExitPressedOnce = false

    // --- FILE UPLOADER SYSTEM ---
    // Manages the bridge between the WebView and the Android File System
    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private val fileChooserLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {{ result ->
        if (result.resultCode == RESULT_OK) {{
            val data: Intent? = result.data
            val results = if (data?.dataString != null) arrayOf(Uri.parse(data.dataString)) else null
            filePathCallback?.onReceiveValue(results)
        }} else {{
            // CRITICAL: Must return null to the callback if cancelled, otherwise the WebView 
            // will stop responding to file upload clicks until the app restarts.
            filePathCallback?.onReceiveValue(null)
        }}
        filePathCallback = null
    }}

    // --- PERMISSION SYSTEM: MULTI-REQUEST ---
    // Processes the massive permission request block (Camera, SMS, Location, etc.)
    private val multiplePermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {{ results ->
        val fineLocationGranted = results[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
        // Android 10+ requires Background Location to be requested in a separate system dialog
        if (fineLocationGranted && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {{
            requestBackgroundLocation()
        }}
    }}

    // --- PERMISSION SYSTEM: BACKGROUND LOCATION ---
    private val backgroundLocationLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) {{ _ -> /* Permission handled by OS flow */ }}

    // =========================================================================
    // LIFECYCLE: ON CREATE
    // =========================================================================
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        
        // SESSION RESET: Always start at the target URL on fresh launch
        lastLiveUrl = LIVE_URL
        
        // Keep screen active while the app is visible
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContentView(R.layout.activity_main)
        
        // UI Bindings
        myWebView = findViewById(R.id.webview)
        progressBar = findViewById(R.id.progressBar)
        {kt_splash_init}

        // Setup Biometric System
        setupBiometricSystem()

        // Setup WebView Core Settings
        setupWebView()
        
        // FAST START: Immediate network check
        if (isNetworkAvailable()) {{
            myWebView.loadUrl(LIVE_URL)
        }} else {{
            loadOffline("No Internet Connection")
        }}

        // PERMISSION DELAY: Request permissions after 5s to ensure UI is ready
        Handler(Looper.getMainLooper()).postDelayed({{
            if (!isFinishing && !isDestroyed) requestFullPermissions()
        }}, 5000)

        // Back Press Logic (Inside onCreate)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {{
            override fun handleOnBackPressed() {{
                if (myWebView.canGoBack()) {{
                    myWebView.goBack()
                }} else {{
                    if (doubleBackToExitPressedOnce) {{
                        finish()
                        return
                    }}
                    doubleBackToExitPressedOnce = true
                    showToast("Press back again to exit")
                    Handler(Looper.getMainLooper()).postDelayed({{
                        doubleBackToExitPressedOnce = false
                    }}, 2000)
                }}
            }}
        }})

        // Initialize Real-time Network Listener
        setupNetworkMonitor()
    }}

    // =========================================================================
    // BIOMETRIC INITIALIZATION logic
    // =========================================================================
    private fun setupBiometricSystem() {{
        val executor = ContextCompat.getMainExecutor(this)
        biometricPrompt = BiometricPrompt(this, executor, object : BiometricPrompt.AuthenticationCallback() {{
            
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {{
                super.onAuthenticationSucceeded(result)
                // HANDLE SUCCESS NATIVELY
                runOnUiThread {{
                    showToast("Login Successful!")
                    // Optional: You can still tell JS to unlock the dashboard
                    myWebView.evaluateJavascript("javascript:console.log('Natively Authenticated')", null)
                }}
            }}

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {{
                super.onAuthenticationError(errorCode, errString)
                // HANDLE ERROR NATIVELY
                runOnUiThread {{
                    showToast("Authentication Error: $errString")
                }}
            }}

            override fun onAuthenticationFailed() {{
                super.onAuthenticationFailed()
                runOnUiThread {{
                    showToast("Authentication Failed. Try again.")
                }}
            }}
        }})

        promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Biometric Login")
            .setSubtitle("Confirm your identity to continue")
            .setNegativeButtonText("Use Password")
            .build()
    }}

    // =========================================================================
    // WEBVIEW SETUP & CONFIGURATION
    // =========================================================================
    private fun setupWebView() {{
        myWebView.settings.apply {{
            javaScriptEnabled = true            
            domStorageEnabled = true           
            databaseEnabled = true
            allowFileAccess = true             
            allowContentAccess = true
            setGeolocationEnabled(true) 
            cacheMode = WebSettings.LOAD_DEFAULT
            mediaPlaybackRequiresUserGesture = false 
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW 
        }}

        // JAVASCRIPT INTERFACE
        myWebView.addJavascriptInterface(WebAppInterface(this@MainActivity), "Native")

        // CHROME CLIENT: Handles file uploads, location, and HARDWARE PERMISSIONS
        myWebView.webChromeClient = object : WebChromeClient() {{
            
            // This allows the website to actually use the Camera, Mic, etc.
            override fun onPermissionRequest(request: PermissionRequest?) {{
                runOnUiThread {{
                    val resources = request?.resources ?: arrayOf()
                    // Log the requested resources to help debug if needed
                    for (resource in resources) {{
                        android.util.Log.d("WebAuth", "Website is requesting: $resource")
                    }}
                    // Directly grant all requested resources (Camera, Mic, etc.)
                    request?.grant(resources)
                }}
            }}

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {{
                this@MainActivity.filePathCallback?.onReceiveValue(null)
                this@MainActivity.filePathCallback = filePathCallback
                
                val intent = fileChooserParams?.createIntent()
                try {{
                    fileChooserLauncher.launch(intent)
                }} catch (e: Exception) {{
                    this@MainActivity.filePathCallback = null
                    return false
                }}
                return true
            }}

            override fun onGeolocationPermissionsShowPrompt(origin: String?, callback: GeolocationPermissions.Callback?) {{
                callback?.invoke(origin, true, false)
            }}
        }}

        // WEB CLIENT: Handles page transitions and error states
        myWebView.webViewClient = object : WebViewClient() {{
            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {{
                if (!isFinishing) progressBar.visibility = View.VISIBLE
                if (url != null && !url.startsWith("file:///android_asset/")) {{
                    lastLiveUrl = url
                }}
            }}
            
            override fun onPageFinished(view: WebView?, url: String?) {{
                if (!isFinishing) progressBar.visibility = View.GONE
                {kt_splash_logic}
            }}

            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {{
                val targetUrl = request?.url.toString()
                
                // 1. Always allow local assets (Offline Page)
                if (targetUrl.startsWith("file:///android_asset/")) return false

                // 2. Proactive Network Check (The Guard)
                if (!isNetworkAvailable()) {{
                    showToast("No Connection")
                    return true // STOP the navigation
                }}

                // 3. The Gatekeeper (Keep navigation inside the app)
                return false 
            }}

            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {{
                if (request?.isForMainFrame == true) {{
                    val failingUrl = request.url.toString()
                    // Don't redirect to index.html anymore, just alert the user.
                    if (failingUrl != LOCAL_URL && !isNetworkAvailable()) {{
                        runOnUiThread {{ 
                            showToast("Unable to load. Waiting for connection...")
                        }}
                    }}
                }}
            }}
        }}
    }}

    // =========================================================================
    // CONNECTIVITY MANAGEMENT & MONITORING
    // =========================================================================

    // Online Methods
    private fun loadOnline() {{ 
        isOffline = false
        myWebView.loadUrl(lastLiveUrl) 
        showToast("Back Online")
    }}

    // Offline Methods
    private fun loadOffline(msg: String) {{ 
        isOffline = true
        val currentUrl = myWebView.url
        if (currentUrl != null && !currentUrl.startsWith("file:///android_asset/")) {{
            lastLiveUrl = currentUrl
        }}
        myWebView.loadUrl(LOCAL_URL) 
        showToast(msg)
    }}

    // Show Toast
    private fun showToast(msg: String) {{
        runOnUiThread {{
            if (!isFinishing && !isDestroyed) {{
                Toast.makeText(this@MainActivity, msg, Toast.LENGTH_SHORT).show()
            }}
        }}
    }}

    // =========================================================================
    // CONNECTIVITY MONITOR: Real-time status
    // =========================================================================
    private fun setupNetworkMonitor() {{
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val req = NetworkRequest.Builder().addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET).build()
        
        networkCallback = object : ConnectivityManager.NetworkCallback() {{
            override fun onAvailable(n: Network) {{ 
                runOnUiThread {{ 
                    if (!isFinishing) {{
                        showToast("Back Online")
                        // AUTO-RELOAD: If the user was stuck on the offline page (initial boot),
                        // take them to the live site. Otherwise, let them stay where they are.
                        if (myWebView.url == LOCAL_URL) {{
                            myWebView.loadUrl(lastLiveUrl)
                        }}
                    }}
                }} 
            }}
            override fun onLost(n: Network) {{ 
                runOnUiThread {{ 
                    if (!isFinishing) {{
                        showToast("Connection Lost")
                    }}
                }} 
            }}
        }}
        cm.registerNetworkCallback(req, networkCallback)
    }}

    // =========================================================================
    // SYSTEM PERMISSIONS (MULTI-VERSION SUPPORT)
    // =========================================================================
    private fun requestFullPermissions() {{
        val p = mutableListOf(
            Manifest.permission.CAMERA, Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_CONTACTS, Manifest.permission.WRITE_CONTACTS,
            Manifest.permission.CALL_PHONE, Manifest.permission.READ_PHONE_STATE,
            Manifest.permission.READ_SMS, Manifest.permission.RECEIVE_SMS, Manifest.permission.SEND_SMS,
            Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION
        )
        
        // Handle specific permission changes for Android 13 (API 33) and 14 (API 34)
        if (Build.VERSION.SDK_INT >= 33) {{
            p.add(Manifest.permission.POST_NOTIFICATIONS)
            p.add(Manifest.permission.READ_MEDIA_IMAGES)
            p.add(Manifest.permission.READ_MEDIA_VIDEO)
            p.add(Manifest.permission.READ_MEDIA_AUDIO)
            if (Build.VERSION.SDK_INT >= 34) p.add(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)
        }} else {{
            p.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            p.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        }}
        multiplePermissionLauncher.launch(p.toTypedArray())
    }}

    private fun requestBackgroundLocation() {{
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {{
            val permissionCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION)
            if (permissionCheck != PackageManager.PERMISSION_GRANTED) {{
                backgroundLocationLauncher.launch(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
            }}
        }}
    }}

    // =========================================================================
    // UTILS & CLEANUP
    // =========================================================================
    override fun onDestroy() {{
        // Unregister callback to prevent memory leaks or crashes during rotation
        try {{
            val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            if (::networkCallback.isInitialized) cm?.unregisterNetworkCallback(networkCallback)
        }} catch (e: Exception) {{ }}

        myWebView.apply {{
            stopLoading()
            webViewClient = WebViewClient() 
            webChromeClient = WebChromeClient()
            destroy()
        }}
        super.onDestroy()
    }}

    private fun isNetworkAvailable(): Boolean {{
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val net = cm.activeNetwork ?: return false
        val cap = cm.getNetworkCapabilities(net) ?: return false
        return cap.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }}

    // =========================================================================
    // JAVASCRIPT INTERFACE (THE BRIDGE)
    // =========================================================================
    inner class WebAppInterface(private val mContext: Context) {{    

        @JavascriptInterface
        fun close() {{ finish() }}
        
        @JavascriptInterface
        fun getPackageName(): String {{ return mContext.packageName }}

        @JavascriptInterface
        fun reload() {{ runOnUiThread {{ myWebView.reload() }} }}

        @JavascriptInterface
        fun clearCache() {{ runOnUiThread {{ myWebView.clearCache(true) }} }}     

        @JavascriptInterface
        fun enableSecureScreen() {{
            runOnUiThread {{ window.addFlags(WindowManager.LayoutParams.FLAG_SECURE) }}
        }}

        @JavascriptInterface
        fun disableSecureScreen() {{
            runOnUiThread {{ window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }}
        }}

        @JavascriptInterface
        fun getDeviceInfo(): String {{
            return "${{Build.MANUFACTURER}} ${{Build.MODEL}} (Android ${{Build.VERSION.RELEASE}})"
        }}

        @JavascriptInterface
        fun loginBiometric() {{
            runOnUiThread {{
                biometricPrompt.authenticate(promptInfo)
            }}
        }}

        @JavascriptInterface
        fun getBatteryLevel(): Int {{
            val bm = mContext.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        }}

        @JavascriptInterface
        fun isCharging(): Boolean {{
            val intent = mContext.registerReceiver(null, android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED))
            val status = intent?.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1) ?: -1
    
            return status == android.os.BatteryManager.BATTERY_STATUS_CHARGING || 
            status == android.os.BatteryManager.BATTERY_STATUS_FULL
        }}

        @JavascriptInterface
        fun isPowerSaveMode(): Boolean {{
            val pm = getSystemService(Context.POWER_SERVICE) as PowerManager
            return pm.isPowerSaveMode
        }}

        @JavascriptInterface
        fun copyToClipboard(text: String) {{
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("label", text)
            clipboard.setPrimaryClip(clip)
        }}

        @JavascriptInterface
        fun openExternalBrowser(url: String) {{
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            startActivity(intent)
        }}

        @JavascriptInterface
        fun vibrate(duration: Long) {{
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {{
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as android.os.VibratorManager
                vibratorManager.defaultVibrator
            }} else {{
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }}

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
                vibrator.vibrate(VibrationEffect.createOneShot(duration, VibrationEffect.DEFAULT_AMPLITUDE))
            }} else {{
                @Suppress("DEPRECATION")
                vibrator.vibrate(duration)
            }}
        }}

        // --- NFC SUPPORT ---
        @JavascriptInterface
        fun startNFCScan() {{
            runOnUiThread {{
                // Trigger the native NFC Dispatch system
                // This usually requires the Activity to handle onNewIntent
                showToast("NFC Scanning Started...")
            }}
        }}

        @JavascriptInterface
        fun stopNFCScan() {{
            showToast("NFC Scanning Stopped")
        }}

        @JavascriptInterface
        fun onScreen(enable: Boolean) {{
            runOnUiThread {{
                if (enable) window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                else window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            }}
        }}

        @JavascriptInterface
        fun flashlight(on: Boolean) {{
            try {{
                val cameraManager = mContext.getSystemService(Context.CAMERA_SERVICE) as CameraManager
                val cameraId = cameraManager.cameraIdList[0]
                cameraManager.setTorchMode(cameraId, on)
            }} catch (e: Exception) {{
                showToast("Flashlight Error: ${{e.message}}")
            }}
        }}

        @JavascriptInterface
        fun bluetooth(enable: Boolean) {{
            val bluetoothManager = mContext.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
            val bluetoothAdapter = bluetoothManager.adapter
            if (enable) {{
                if (bluetoothAdapter?.isEnabled == false) {{
                    val enableBtIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
                    startActivity(enableBtIntent)
                }}
            }} else {{
                showToast("Please disable Bluetooth in Settings")
            }}
        }}

        @JavascriptInterface
        fun notification(title: String, message: String) {{
            showNotification(title, message)
        }}
        
        // Helper for Notifications
        private fun showNotification(title: String, message: String) {{
            val channelId = "default_channel"
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
                val channel = NotificationChannel(channelId, "App Notifications", NotificationManager.IMPORTANCE_DEFAULT)
                notificationManager.createNotificationChannel(channel)
            }}
            val builder = NotificationCompat.Builder(mContext, channelId)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(message)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            notificationManager.notify(System.currentTimeMillis().toInt(), builder.build())
        }}
    }}
}}
''', encoding='utf-8')

    # ICONS
    if icon_path:
        ext = icon_path.suffix.lower() or ".png"
        for dpi in ['mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi']:
            (res_dir / f"mipmap-{dpi}").mkdir(exist_ok=True)
            try: shutil.copy(icon_path, res_dir / f"mipmap-{dpi}" / f"ic_launcher{ext}")
            except: pass
    else:
        for dpi in ['mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi']:
            (res_dir / f"mipmap-{dpi}").mkdir(exist_ok=True)
            (res_dir / f"mipmap-{dpi}/ic_launcher.xml").write_text('<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24.0" android:viewportHeight="24.0"><path android:fillColor="#000000" android:pathData="M12,2L2,22h20L12,2z"/></vector>', encoding='utf-8')

    # EXECUTION
    gradle_cmd = "gradle" if platform.system() != "Windows" else "gradle.bat"
    if not shutil.which("gradle"): print("Gradle not found."); return

    # BUILD BOTH DEBUG AND RELEASE
    log("Building APK (Debug) & AAB (Release)...", "INFO")
    
    # Paths where Gradle outputs files
    debug_apk_src = app_dir / "build/outputs/apk/debug/app-debug.apk"
    meta_json_src = app_dir / "build/outputs/apk/debug/output-metadata.json"
    release_aab_src = app_dir / "build/outputs/bundle/release/app-release.aab"

    # Paths where we want them in the Output folder
    dest_apk = OUTPUT_DIR / f"{app_name}-debug.apk"
    dest_json = OUTPUT_DIR / "output-metadata.json"
    dest_aab = OUTPUT_DIR / f"{app_name}-release.aab"

    # 1. Debug APK Build
    subprocess.run([gradle_cmd, "assembleDebug"], cwd=android_root, check=True)
    if debug_apk_src.exists():
        shutil.copy(debug_apk_src, dest_apk)
        shutil.copy(meta_json_src, dest_json)
        log(f"Generated: {dest_apk.name}", "INFO")
    else: 
        log("Debug Build Failed.", "ERROR")

    # 2. Release AAB Build
    subprocess.run([gradle_cmd, "bundleRelease"], cwd=android_root, check=True)
    if release_aab_src.exists():
        shutil.copy(release_aab_src, dest_aab)
        log(f"Generated: {dest_aab.name}", "INFO")
    else: 
        log("Release Build Failed.", "ERROR")

    # =======================================================================
    # NEW FEATURE: AUTO-ZIP AND CLEANUP
    # =======================================================================
    log("Compressing artifacts into single ZIP...", "STEP")
    zip_filename = OUTPUT_DIR / f"{app_name}.zip"
    
    # List of files to put inside the zip
    files_to_zip = [dest_apk, dest_json, dest_aab]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            if file_path.exists():
                # Add file to zip (arcname prevents full path directory structure)
                zipf.write(file_path, arcname=file_path.name)
                log(f"Added to zip: {file_path.name}", "INFO")
        
    # Verify Zip was created successfully before deleting originals
    if zip_filename.exists():
        for file_path in files_to_zip:
            if file_path.exists():
                os.remove(file_path)
        log("Zip created successfully & temporary files removed", "INFO")
        log(f"FINAL OUTPUT: {zip_filename}", "INFO")
            
    else:
        log(f"Zipping failed: {e}", "ERROR")

# ===========================================================================
# MAIN
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Web2Native Ultimate Compiler")
    parser.add_argument("--name", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--url", required=True)
    
    # Optional Args
    parser.add_argument("--icon")
    parser.add_argument("--splash")
    parser.add_argument("--archs")
    
    args = parser.parse_args()
    
    # RESOLVE ASSETS
    icon_p = resolve_asset_path(args.icon, "Icon")
    splash_p = resolve_asset_path(args.splash, "Splash Screen")
    
    work_dir = ROOT_DIR / f"build_{args.name}"
    assets_dir = work_dir / "assets"
    
    # STEP 1: PRE-BUILD CLEANUP
    # We do a simple check here to clear old failed builds before starting
    if work_dir.exists(): shutil.rmtree(work_dir, ignore_errors=True)

    work_dir.mkdir()
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # STEP 2: COMPILATION
    bundle_website(args.url, assets_dir)    
    build_android_native(work_dir, args.name, args.package, assets_dir, icon_p, splash_p, args.archs, args.url)
    
    # STEP 3: FINAL MANDATORY CLEANUP (The "Best" Logic)
    if work_dir.exists():
        try:
            shutil.rmtree(work_dir, ignore_errors=False) 
            log("BUILD PROCESS COMPLETED & STORAGE CLEANED", "STEP")
            print(f"Zipped output bundle is located in: {OUTPUT_DIR}")
        except Exception as error:
            print(f"CRITICAL: Final cleanup failed for {work_dir}")
            print(f"ERROR: {error}")
            raise # Stops the backend so you know storage is at risk

if __name__ == "__main__":
    main()
