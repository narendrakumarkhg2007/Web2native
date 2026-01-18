# Web2Native Universal Compiler 🚀

**The safest and fastest way to transform any Web Application into high-performance Native Android & iOS apps.**

Web2Native is a lightweight "Native Wrapper Engine" that bridges the gap between web development and mobile deployment. Unlike heavy frameworks (Cordova/Capacitor), it uses the platform's native high-performance engines (**WKWebView** for iOS and **WebView2/AndroidX** for Android) to wrap your site. It injects a **Universal JavaScript Bridge** so your web code can trigger native biometrics, haptics, and system-level APIs with zero configuration.

---

## 🌟 Key Features

* **Biometric Authentication:** FaceID/TouchID (iOS) and Fingerprint/Face (Android) integration.
* **Secure Screen:** Native prevention of screenshots and screen recording for sensitive data.
* **Push Notifications:** Trigger local system notifications from JS using Native.pushNotification("Title", "Message").
* **Clipboard Access:** Copy text to the physical device clipboard using Native.copyToClipboard("text").
* **Device Info:** Retrieve the physical hardware model and Android version via Native.getDeviceInfo().
* **Keep Screen On:** Prevent the device from dimming or sleeping during long-running web tasks using Native.toggleKeepScreenOn(true).
* **Bluetooth:** To access device native bluetooth access & control.
* **Flashlight:** To access native device flashlight.
* **External browser Access:** To open a url or a hyperlink on external browser for full access & control.
* **NFC:** To access built-in NFC on supported devices.

### ⚡ The Unified Bridge (Write Once, Run Everywhere)
A shared API allows your website to talk to the phone hardware directly:
* **Haptics:** `Native.vibrate(duration)`
* **System Alerts:** `Native.pushNotification(title, message)`
* **Hardware Sensors:** Access Battery level and Power-save status.
* **Clipboard:** `Native.copyToClipboard(text)`

### 📦 Pro Build Pipeline
* **Offline Mirroring:** Automatically clones your website assets for offline-first capabilities.
* **Adaptive Layouts:** Built-in support for iPhone notches (Safe Areas) and Android Material 3 design.
* **Multi-Arch Support:** Optimized for `arm64-v8a`, `armeabi-v7a`, `x86_64` and `x86`.

---

## 🛠️ Prerequisites

| Platform | Requirements |
| :--- | :--- |
| **Android** | Python 3.14+, JDK 17+, [Gradle](https://gradle.org/install/) |
| **iOS** | macOS with Xcode 14+, Python 3.14+ |
| **General** | `wget` (for website asset mirroring) |

---

## 🚀 Getting Started

### 1. Build for Android
This script handles asset mirroring, project generation, and compilation of a Debug APK and Release AAB all bundled in a zip file.

```bash
python3 web2candroid.py \
  --name "MyApp" \
  --package "com.company.myapp" \
  --url "[https://your-web-app.com](https://your-web-app.com)" \
  --icon "./path/to/icon.png" \
  --splash "./path/to/splash.png"

```

### 2. Build for iOS  
This script handle assest mirroring, project generation, and compilation of iOS .ipa file bundle in a zip file.

```bash
python3 web2cios.py \
  --name "MyApp" \
  --package "com.company.myapp" \
  --url "[https://your-web-app.com](https://your-web-app.com)"
```

🔗 Using the Native Bridge (JS API)
Once your app is running inside the Web2Native wrapper, you can call these functions directly from your web application's JavaScript.

// Trigger Biometric Login
window.onload() => {
    Native.loginBiometric(); // **For Biometric login access to the app.**
}

// Reload app
Native.reload();

// To get package name of the application
Native.getPackageName();

// To get Device Information
Native.getDeviceInfo();

// To clear cache Memory
Native.clearCache();

// To enable secure screen
Native.enableSecureScreen() // **For enable the secure screen to disable screenshots or screen recorders for privacy based apps.**

// To disable secure screen
Native.disableSecureScreen() // **For disable the secure screen to enable screenshots or screen recorders for privacy based apps.**

// To get battery percentage
Native.getBatteryLevel();

// To know the device is Charging or not
Native.isCharging();

// To know the power saving mode is on or not
Native.isPowerSaveMode();

// To copy data into Clipboard
Native.copyToClipboard();

// To open external browser
Native.openExternalBrowser(URL);

// To send Haptics effect
Native.vibrate(duration);

// To keep screen on
Native.onScreen();

// To start NFC Scan
Native.startNFCScan();

// To stop NFC Scan
Native.stopNFCScan();

// To access device's flashlight
Native.flashlight();

// Bluetooth Access
Native.bluetooth();

// Push Notification
Native.notification(title, msg);

/**
 * Web2Native Bridge API
 * Exposes all hardware methods defined in the Kotlin MainActivity.
 */
const HardwareAPI = {
    
    // --- AUTHENTICATION ---
    loginBiometric: () => Native.loginBiometric(),

    // --- SYSTEM & SECURITY ---
    finishApp: () => Native.finishApp(),
    getPackageName: () => Native.getPackageName(),
    reloadPage: () => Native.reloadPage(),
    clearCache: () => Native.clearCache(),
    enableSecureScreen: () => Native.enableSecureScreen(), // Prevents Screenshots/Recordings
    disableSecureScreen: () => Native.disableSecureScreen(),
    getDeviceInfo: () => Native.getDeviceInfo(),
    toggleKeepScreenOn: (bool) => Native.toggleKeepScreenOn(bool),

    // --- BATTERY & POWER ---
    getBatteryStatus: () => Native.getBatteryStatus(), // Returns 0-100
    isPowerSaveMode: () => Native.isPowerSaveMode(),   // Returns boolean

    // --- HARDWARE PERIPHERALS ---
    vibrate: (durationMs) => Native.vibrate(durationMs || 500),
    toggleFlashlight: (status) => Native.toggleFlashlight(status),
    toggleBluetooth: (status) => Native.toggleBluetooth(status),
    
    // --- NFC CONTROLS ---
    startNFCScan: () => Native.startNFCScan(),
    stopNFCScan: () => Native.stopNFCScan(),

    // --- UTILITIES ---
    copyToClipboard: (text) => Native.copyToClipboard(text),
    openExternalBrowser: (url) => Native.openExternalBrowser(url),
    pushNotification: (title, message) => Native.pushNotification(title, message)

};
📂 Output Structure
The compiler automates the cleanup process, leaving you only with the final artifacts:

Android: A .zip containing the Debug APK, Release AAB (for Play Store), and metadata.

iOS: A structured Xcode project directory ready for one-click deployment.

📝 License & Author
Author: Narendra Kumar

License: MIT

Build the future of the web, natively.

This project is made for an easy way to convert any web apps into Android &amp; iOS native mobile app look &amp; feel. 
