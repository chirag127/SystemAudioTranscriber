[app]

# (str) Title of your application
title = System Audio Transcriber

# (str) Package name
package.name = systemaudiotranscriber

# (str) Package domain (needed for android/ios packaging)
package.domain = org.systemaudiotranscriber

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,gitignore,git

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pyjnius==1.4.2,plyer==2.1.0,vosk==0.3.45

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
services = TranscriptionService:main.py

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = INTERNET,RECORD_AUDIO,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,CAPTURE_AUDIO_OUTPUT,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (list) features (adds uses-feature -tags to manifest)
android.features = android.hardware.audio.output

# (int) Target Android API, should be as high as possible.
android.api = 30

# (int) Minimum API your APK / AAB will support.
android.minapi = 29

# (int) Android SDK version to use
android.sdk = 30

# (str) Android NDK version to use
android.ndk = 21c

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 29

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Android additional libraries
android.add_libs_armeabi = libs/android/*.so

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) python-for-android branch to use, defaults to stable
p4a.branch = master

# (str) XML file for custom activity declaration
android.manifest.activity_declaration = %(source.dir)s/AndroidManifest.xml

#
# Python for android (p4a) specific
#

# (str) python-for-android fork to use in case if p4a.branch is master, useful to dev on p4a
# p4a.fork = kivy

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

#
# iOS Specific
#

# (str) Path to a custom kivy-ios folder
# ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master

# (str) Name of the certificate to use for signing the debug version
# Get a list of available identities: buildozer ios list_identities
# ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) The development team to use for signing the debug version
# ios.codesign.development_team.debug = <hexstring>

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
