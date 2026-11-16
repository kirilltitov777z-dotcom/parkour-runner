[app]
title = Parkour Runner
package.name = parkourrunner
package.domain = org.parkourrunner

source.dir = .
source.include_exts = py,png,jpg,jpeg,txt
source.exclude_exts = spec,md,yml,yaml
source.exclude_dirs = dist,build,.git

version = 1.0
requirements = hostpython3==3.11.9,python3==3.11.9,pygame==2.6.1

orientation = landscape
fullscreen = 1

android.api = 35
android.minapi = 21
android.ndk_api = 24
android.archs = arm64-v8a
android.sdk_path = /usr/local/lib/android/sdk
android.build_tools_version = 35.0.0
android.permissions =
android.gradle_dependencies =

p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
