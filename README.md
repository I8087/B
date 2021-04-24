# The B Programming Language
This is my hobby compiler for the B programming language. The goal was to create a B variant that is usuable on modern computers. More will follow once I write a rough draft manual.

## Releases
You can download the latest pre-built binaries [here](https://github.com/I8087/B/releases). **NOTE: Although the compiler has builds for win64 and Linux, the compiler can only generate code for win32.**

## Getting Started
To get started, you'll need to download the compiler for your specific system. Then you'll need to add the `bin` directory to your system's path. From here, you can access the compiler via the terminal by using `b`. **NOTE: You'll also need to have MSVC Linker `link` and the Netwide Assembler `nasm` on your system's path too.**

## Example
Here is a simple hello world example.

```c
main () {
    puts("Hello World!*n");
    return 0;
}
```

Now save that in `hello.b`. To compile this on a `win32` platform, open up your terminal and type `b -f win32 -o hello.exe hello.b`. Afterwards, if you run `hello.exe` from a terminal, you should see this:

```
Hello World!
```

Congratulations, you've compiled your first B program!

## Links
* [Orignal Technical Memo](https://www.bell-labs.com/usr/dmr/www/kbman.pdf)
