sys_write(file, buf, len) {

    /* Declare our local variables. */
    auto stdout, obytes;

    /* Get the stdout's file handle. */
    stdout = GetStdHandle(-11);

    /* Write to the stdout.*/
    WriteFile(stdout, buf, len, &obytes, 0);
}