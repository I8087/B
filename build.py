#!/usr/bin/python3
# -*- coding: utf-8 -*-

import glob, os, sys, shutil, platform
import PyInstaller.__main__

__version__ = "0.1.0"

# Make sure the platform is supported.
if sys.platform == "win32":
    plat = "win{}".format(platform.architecture()[0][:2])
elif sys.platform == "linux":
    plat = "linux{}".format(platform.architecture()[0][:2])
else:
    print("This platform is not supported!")
    exit(-1)

# Build the compiler.
PyInstaller.__main__.run(
    ["--clean",
     "--onefile",
     "--distpath",
     "dist/bin",
     "-nb",
     os.path.join(os.getcwd(), "src", "__main__.py")
     ])

# Add subdirectories!
for i in ("lib", "test"):
    os.mkdir(os.path.join(os.getcwd(), "dist", i))

# Clean up spec file.
if os.path.exists("b.spec"):
    try:
        os.remove("b.spec")
    except:
        exit(-1)


# Clean up the __pycache__ and build directory.
for i in (os.path.join(os.getcwd(), "src", "__pycache__"),
          os.path.join(os.getcwd(), "build")):
    if os.path.exists(i):
        try:
            shutil.rmtree(i)
        except:
            exit(-1)

# Make a build directory.
os.mkdir(os.path.join(os.getcwd(), "build"))

# Make library directories!!!
for i in glob.glob(os.path.join("lib", "*")):
    os.mkdir(os.path.join(os.getcwd(), "dist", i))

# Copy the standard library.
for i in glob.glob(os.path.join("lib", "**", "*.b")):
    shutil.copy2(i,
                 os.path.join(os.getcwd(), "dist", i))

# Copy the test files.
for i in glob.glob(os.path.join("test", "*")):
    print(i)
    shutil.copy2(os.path.join(os.getcwd(), i),
                 os.path.join(os.getcwd(), "dist", i))

# Move the rest of the required files into the dist directory.
# They will be bundled together into one archive.
for i in ("CHANGELOG.md", "LICENSE", "README.md"):
    shutil.copy2(os.path.join(os.getcwd(), i),
                 os.path.join(os.getcwd(), "dist", i))

# Archive the programs.
if sys.platform == "win32":
    arch_format = "zip"
else:
    arch_format = "gztar"

shutil.make_archive(os.path.join(os.getcwd(), "build", "B-{}-v{}".format(plat, __version__)), arch_format, "dist")

# Remove the dist directory.
if os.path.exists("dist"):
    try:
        shutil.rmtree("dist")
    except:
        exit(-1)


print("Successfully built the compiler!...")
