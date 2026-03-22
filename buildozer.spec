[app]
title = SafeStride
package.name = safestride
package.domain = org.safestride
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,env
version = 1.0
requirements = python3,kivy,requests,geopy,pyttsx3,pillow,python-dotenv
android.permissions = CAMERA,INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
orientation = portrait

[buildozer]
log_level = 2
