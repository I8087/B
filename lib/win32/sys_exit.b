sys_exit(errn) {
    extrn ExitProcess@4;
    ExitProcess@4(errn);
}