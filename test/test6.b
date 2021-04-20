main () {
    auto i;
    i = -1;

    repeat {
        i++;
        if (i >= 20) break;
        if (i > 10) next;
        printn(i, 10);
        putchar('*n');
    }
    printn(i, 10);
    putchar('*n');
    return i;

}