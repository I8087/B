# Import all of the required libraries.
import os, sys, glob, platform
from lexer import Lexer
from parse import Parser

# Compiler version
__version__ = "0.1.0"

# Buffer for storing the B program's source code.
buf = ""

# Map out the directory of the compiler.
b_dir = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))

# Get the CPU's architecture.
_bit = int(platform.architecture()[0][:2])

# Get the number of bytes in one word.
_bytes = _bit // 8

# Get the CPU's machine name.
_cpu = platform.machine()

# Get the operating system's name.
if platform.system() == "Windows":
    _sys = "win"
elif platform.system() == "Linux":
    _sys = "lin"
elif platform.system() == "Darwin":
    _sys = "mac"
else:
    exit(-1)

# A dictionary of options used by the compiler.
options = {
    "f":     _sys+str(_bit),# The file format. Based on os and cpu.
    "o":     "out.exe",     # The output file name.
    "ob":    "out",         # The output file's base name.
    "oe":    "exe",         # The output file's extension name.
    "S":     False,         # Should the assembly output files be saved?
    "v":     False,         # Display compiler version info?
    "files": [],            # The input file name(s).
    "sys":   _sys,          # Operating system
    "cpu":   _cpu,          # CPU machine name
    "bit":   _bit,          # CPU bits
    "bytes": _bytes         # Number of bytes in one word.
    }

# Get a copy of the command line arguments.
a = sys.argv[1:]

# Go through and read the command line arguments.
while a:

    if a[0] == "-o":

        # Set the output file's name.
        options["o"] = a[1]

        # Seperate the output file's name and extension.
        if a[1].rfind(".") != -1:
            options["ob"] = a[1][:a[1].rfind(".")]
            options["oe"] = a[1][a[1].rfind(".")+1:]
        else:
            options["ob"] = a[1]

        a = a[2:]
        

    elif a[0] == "-f":
        if a[1] not in ("win32", "win64", "lin32", "lin64"):
            print("Unknown format!")
            exit(-1)
        options["f"] = a[1]
        a = a[2:]

    elif a[0] == "-S":
        options["S"] = True
        a = a[1:]

    elif a[0] == "-v":
        options["v"] = True
        a = a[1:]

    else:
        options["files"].append(a[0])
        a = a[1:]

# Get a glob of all the files in the B standard library.
# NOTE: We'll need to do this after we go throught the command line.
lib_glob = os.path.join(b_dir, "lib", "libb", "*.b")
lib_h_glob = os.path.join(b_dir, "lib", "libb", "*.h")
sys_glob = os.path.join(b_dir, "lib", options["f"], "*.b")
sys_h_glob = os.path.join(b_dir, "lib", options["f"], "*.h")
if options["v"]:
    print("B Compiler Version {}\n".format(__version__))

# We need to compile something or there's no reason to continue.
if not options["files"]:
    print("No input file specified!")
    exit(-100)

# Add each system library header file to the buffer.
for i in [f for f in glob.glob(sys_h_glob)]:
    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open library header file '{}'!".format(i))
        exit(-1)

# Add each library header file to the buffer.
for i in [f for f in glob.glob(lib_h_glob)]:
    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open library header file '{}'!".format(i))
        exit(-1)

# Add each file to the buffer.
for i in options["files"]:

    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open input file '{}'!".format(i))
        exit(-1)

# Add each system library file to the buffer.
for i in [f for f in glob.glob(sys_glob)]:
    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open library file '{}'!".format(i))
        exit(-1)

# Add each library file to the buffer.
for i in [f for f in glob.glob(lib_glob)]:
    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open library file '{}'!".format(i))
        exit(-1)

# Compile the source code into assemble.
b, c = Lexer(buf, options).lexer()
d = Parser(b, c, options).parser()

# Write the assembly code into the out file. 
with open("{0[ob]}.asm".format(options), "w") as f:
    for i in d:
        f.write(i)
        f.write("\n")

# Assemble the assembly output and link the object file into an executable
# based on the output format.

# win32
if options["f"] == "win32":
    os.system("nasm -fwin32 -o{0[ob]}.obj {0[ob]}.asm".format(options))
    os.system("link /entry:_start /subsystem:console /machine:x86 /defaultlib:kernel32.lib {0[ob]}.obj".format(options))

# win64
elif options["f"] == "win64":
    os.system("nasm -fwin64 -o{0[ob]}.obj {0[ob]}.asm".format(options))
    os.system("link /entry:_start /subsystem:console /machine:x64 /defaultlib:kernel32.lib {0[ob]}.obj".format(options))

# lin32
elif options["f"] == "lin32":
    os.system("nasm -felf32 -o{0[ob]}.o {0[ob]}.asm".format(options))
    os.system("ld -o{0[ob]} -melf_i386 {0[ob]}.o".format(options))

else:
    print("Failed to build specified output format!")
    exit(-100)

# Clean up the mess that was made!
if not options["S"]:
    os.remove("{0[ob]}.asm".format(options))
os.remove("{0[ob]}.obj".format(options))
