# Import all of the required libraries.
import os, sys, glob
from lexer import Lexer
from parse import Parser

# Compiler version
__version__ = "0.1.0"

# Buffer for storing the B program's source code.
buf = ""

# Map out the directory of the compiler.
b_dir = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))

# Get a glob of all the files in the B standard library.
# NOTE: We'll need to do this after we go throught the command line.
lib_glob =  os.path.join(b_dir, "lib", "libb", "*.b")

# A dictionary of options used by the compiler.
options = {
    "f":     "win32",    # The file format. Based on os and cpu.
    "o":     "out.exe",  # The output file name.
    "ob":    "out",      # The output file's base name.
    "oe":    "exe",      # The output file's extension name.
    "S":     False,      # Should the assembly output files be saved?
    "v":     False,      # Display compiler version info?
    "files": []          # The input file name(s).
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

if options["v"]:
    print("B Compiler Version {}\n".format(__version__))

# We need to compile something or there's no reason to continue.
if not options["files"]:
    print("No input file specified!")
    exit(-100)

# Add each file to the buffer.
for i in options["files"]:

    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open input file '{}'!".format(i))
        exit(-1)

# Add each library file to the buffer.
for i in [f for f in glob.glob(lib_glob)]:
    try:
        with open(i, "r") as f:
            buf += f.read()

    except:
        print("Could not open find library file '{}'!".format(i))
        exit(-1)

# Compile the source code into assemble.
b, c = Lexer(buf).lexer()
d = Parser(b, c).parser()

# Write the assembly code into the out file. 
with open("{0[ob]}.asm".format(options), "w") as f:
    for i in d:
        f.write(i)
        f.write("\n")

# Assemble the assembly output.
os.system("nasm -f{0[f]} -o{0[ob]}.obj {0[ob]}.asm".format(options))

# Link the object file into an executable.
os.system("link /entry:main /subsystem:console /machine:x86 /defaultlib:kernel32.lib {0[ob]}.obj".format(options))

# Clean up the mess that was made!
if not options["S"]:
    os.remove("{0[ob]}.asm".format(options))
os.remove("{0[ob]}.obj".format(options))
