[app]
title = Parkour Runner
package.name = parkourrunner
package.domain = org.parkourrunner

source.dir = .
source.include_exts = py,png,jpg,jpeg,txt
source.exclude_exts = spec,md,yml,yaml
source.exclude_dirs = dist,build,.git

version = 1.0
requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.api = 35
android.minapi = 21
android.ndk_api = 24
android.arch = arm64-v8a
android.permissions =
android.gradle_dependencies =

p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
