puts(str) {

    /* Declare our local variables. */
    auto stdout, obytes, i;

    /* Get the length of the string. */
    i = strlen(str);

    /* Get the stdout's file handle. */
    stdout = GetStdHandle(-11);

    /* Write to the stdout.*/
    WriteFile(stdout, str, i, &obytes, 0);
}