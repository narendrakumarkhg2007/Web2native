#!/usr/bin/env python3
"""
=============================================================================
    WEB2NATIVE UNIVERSAL COMPILER - IOS EDITION (v1.0.0)
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
import datetime
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()

class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    color = Colors.GREEN if level == "INFO" else Colors.WARNING if level == "WARN" else Colors.FAIL
    print(f"{color}[Web2Native-iOS] [{level}] {timestamp} - {msg}{Colors.ENDC}")

def setup_assets(app_src_dir, icon_path=None, splash_path=None):
    """Handles the creation of icons and splash screens in xcassets."""
    assets_dir = app_src_dir / "Assets.xcassets"
    assets_dir.mkdir(exist_ok=True)
    
    # 1. App Icon
    icon_set = assets_dir / "AppIcon.appiconset"
    icon_set.mkdir(exist_ok=True)
    if icon_path and Path(icon_path).exists():
        log(f"Integrating App Icon: {icon_path}")
        shutil.copy(icon_path, icon_set / "icon_1024.png")
        # Simplified Contents.json for AppIcon
        icon_json = {
            "images": [{"size": "1024x1024", "idiom": "ios-marketing", "filename": "icon_1024.png", "scale": "1x"}],
            "info": {"version": 1, "author": "xcode"}
        }
        (icon_set / "Contents.json").write_text(json.dumps(icon_json))
    
    # 2. Splash Screen (Launch Image)
    splash_set = assets_dir / "LaunchImage.imageset"
    splash_set.mkdir(exist_ok=True)
    if splash_path and Path(splash_path).exists():
        log(f"Integrating Splash Screen: {splash_path}")
        shutil.copy(splash_path, splash_set / "splash.png")
        splash_json = {
            "images": [{"idiom": "universal", "filename": "splash.png", "scale": "1x"}],
            "info": {"version": 1, "author": "xcode"}
        }
        (splash_set / "Contents.json").write_text(json.dumps(splash_json))

def build_ios_native(work_dir, app_name, bundle_id, target_url, icon=None, splash=None):
    log("Perfecting iOS Native Project (Unified Bridge)...", "INFO")
    
    proj_dir = work_dir / "ios_project"
    app_src_dir = proj_dir / app_name
    
    if proj_dir.exists(): shutil.rmtree(proj_dir)
    app_src_dir.mkdir(parents=True)
    
    (app_src_dir / "Base.lproj").mkdir(exist_ok=True)
    setup_assets(app_src_dir, icon, splash)

    # 1. THE UNIFIED BRIDGE SCRIPT
    bridge_js = """
    var Native = {{
        post: function(name, data) {{
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers[name]) {{
                window.webkit.messageHandlers[name].postMessage(data);
            }}
        }},
        vibrate: function(ms) {{ this.post('vibrate', ms); }},
        loginBiometric: function() {{ this.post('loginBiometric', null); }},
        finishApp: function() {{ this.post('finishApp', null); }},
        copyToClipboard: function(text) {{ this.post('copyToClipboard', text); }},
        getBatteryStatus: function() {{ this.post('getBatteryStatus', null); }},
        flashlight: function(on) {{ this.post('flashlight', on); }}
    }};
    window.Native = Native;
    """

    # 2. VIEWCONTROLLER.SWIFT
    swift_content = r'''
import UIKit
import WebKit
import CoreNFC
import CoreBluetooth
import LocalAuthentication
import AudioToolbox
import AVFoundation

class ViewController: UIViewController, WKScriptMessageHandler, WKNavigationDelegate {{
    var webView: WKWebView!
    
    override func viewDidLoad() {{
        super.viewDidLoad()
        self.view.backgroundColor = .white // Fallback for splash transition
        setupWebView()
    }}

    private func setupWebView() {{
        let contentController = WKUserContentController()
        let methods = ["vibrate", "loginBiometric", "close", "copyToClipboard", "getBatteryLevel", "flashlight"]
        methods.forEach { contentController.add(self, name: $0) }}

        let userScript = WKUserScript(source: """
        ''' + bridge_js + r'''
        """, injectionTime: .atDocumentStart, forMainFrameOnly: true)
        contentController.addUserScript(userScript)

        let config = WKWebViewConfiguration()
        config.userContentController = contentController
        config.allowsInlineMediaPlayback = true
        
        webView = WKWebView(frame: self.view.bounds, configuration: config)
        webView.navigationDelegate = self
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        
        self.view.addSubview(webView)

        if let url = URL(string: "''' + target_url + r'''") {{
            webView.load(URLRequest(url: url))
        }}
    }}

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {{
        switch message.name {{
        case "vibrate": AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)

        case "close": exit(0)

        case "copyToClipboard":
            if let text = message.body as? String {{ UIPasteboard.general.string = text }}

        case "loginBiometric":
            let context = LAContext()
            var error: NSError?

            // To check if hardware is available
            if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {{
                context.evaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, localizedReason: "Authentication required to open the app") {{ success, authenticationError in
            
                DispatchQueue.main.async {{
                    if success {{
                        // SUCCESS: Do nothing (let the user stay in the app/webview)
                        print("Biometric Success")
                    }} else {{
                        // FAILURE: Show a native toast/alert and then exit
                        self.showErrorAndExit(message: "Authentication Failed")
                        }}
                    }}
                }}
            }} else {{
                // Biometrics not configured or available
                self.showErrorAndExit(message: "Biometrics not available")
            }}

        case "getBatteryLevel":
            UIDevice.current.isBatteryMonitoringEnabled = true
            let level = Int(UIDevice.current.batteryLevel * 100)
            // Even if you don't want a JS dependency, you usually need to 
            // show this somewhere. Here we just print it or you could toast it.
            print("Battery level requested: \(level)")

        case "flashlight":
            if let status = message.body as? Bool {{
                guard let device = AVCaptureDevice.default(for: .video), device.hasTorch else {{ return }}
                try? device.lockForConfiguration()
                device.torchMode = status ? .on : .off
                device.unlockForConfiguration()
            }}

        default: break

        }}
    }}
}}
'''
    (app_src_dir / "ViewController.swift").write_text(swift_content, encoding='utf-8')

    # 3. APPDELEGATE & SCENEDELEGATE
    (app_src_dir / "AppDelegate.swift").write_text("import UIKit\n@main class AppDelegate: UIResponder, UIApplicationDelegate { var window: UIWindow? }")
    (app_src_dir / "SceneDelegate.swift").write_text(f'''
import UIKit
class SceneDelegate: UIResponder, UIWindowSceneDelegate {{
    var window: UIWindow?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {{
        guard let windowScene = (scene as? UIWindowScene) else {{ return }}
        window = UIWindow(windowScene: windowScene)
        window?.rootViewController = ViewController()
        window?.makeKeyAndVisible()
    }}
}}''')

    # 4. INFO.PLIST (With Launch Screen Support)
    launch_screen_dict = ""
    if splash:
        launch_screen_dict = "<key>UILaunchImageFile</key><string>LaunchImage</string>"

    (app_src_dir / "Info.plist").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key><string>{bundle_id}</string>
    <key>CFBundleName</key><string>{app_name}</string>
    <key>UILaunchScreen</key><dict><key>UIImageName</key><string>splash</string></dict>
    {launch_screen_dict}
    <key>UIApplicationSceneManifest</key>
    <dict><key>UIApplicationSupportsMultipleScenes</key><false/><key>UISceneConfigurations</key><dict><key>UIWindowSceneSessionRoleApplication</key><array><dict><key>UISceneConfigurationName</key><string>Default Configuration</string><key>UISceneDelegateClassName</key><string>$(PRODUCT_MODULE_NAME).SceneDelegate</string></dict></array></dict></dict>
    <key>NSFaceIDUsageDescription</key><string>Authentication Required</string>
    <key>NSCameraUsageDescription</key><string>Flashlight Access</string>
</dict>
</plist>''')

    log(f"iOS Project Ready at: {work_dir}", "INFO")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="App Name")
    parser.add_argument("--package", required=True, help="Bundle ID (e.g. com.test.app)")
    parser.add_argument("--url", required=True, help="Web URL to wrap")
    parser.add_argument("--icon", required=False, help="Path to 1024x1024 PNG icon")
    parser.add_argument("--splash", required=False, help="Path to PNG splash image")
    
    args = parser.parse_args()
    safe_name = "".join(x for x in args.name if x.isalnum())
    work_dir = ROOT_DIR / f"build_ios_{safe_name}"
    work_dir.mkdir(exist_ok=True)
    
    try:
        build_ios_native(work_dir, args.name, args.package, args.url, args.icon, args.splash)
    except Exception as e:
        log(f"An error occurred: {e}", "FAIL")

if __name__ == "__main__":
    main()
