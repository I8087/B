puts(str) {

    /* Declare win32 API functions. */
    extrn GetStdHandle@4, WriteFile@20;

    /* Declare our local variables. */
    auto stdout, obytes, i;

    /* Get the length of the string. */
    i = strlen(str);

    /* Get the stdout's file handle. */
    stdout = GetStdHandle@4(-11);

    /* Write to the stdout.*/
    WriteFile@20(stdout, str, i, &obytes, 0);
}