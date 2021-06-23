sys_write(file, buf, len) {

    /* Write to the stdout.*/
    @ mov eax, 4;
    @ mov ebx, 1;
    @ mov ecx, [ebp+12];
    @ mov edx, [ebp+16];
    @ int 0x80;
}
