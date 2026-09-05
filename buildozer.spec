[app]
title = Gateball Lovers
package.name = gateball_lovers
package.domain = org.gateballlovers
source.dir = .
source.include_exts = py,png,jpg,jpeg,ico,kv,atlas,json
source.exclude_dirs = .git,.venv,venv,build,bin,.buildozer,.gradle,.idea
version = 1.0
requirements = python3,kivy,python-dotenv,supabase
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions = android.permission.INTERNET
android.archs = arm64-v8a,armeabi-v7a
