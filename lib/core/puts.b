puts(str) {

    /* Declare our local variables. */
    auto i;

    /* Get the length of the string. */
    i = strlen(str);

    /* Write to the stdout.*/
    write(0, str, i);
}