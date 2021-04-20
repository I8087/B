putchar(char) {

    /* Declare win32 API functions. */
    extrn GetStdHandle@4, WriteFile@20;

    /* Declare our local variables. */
    auto obytes, stdout, c, n, i;

    /* Assign our local variables initial values. */
    c = i = n = 0;

    /* Check for null characters. */
    while (i < 4) {
        if ((char >> (3-i)*8) & 0xFF) {
            c <<= 8;
            n++;
        }

        c +=  (char >> (3-i)*8) & 0xFF;

        i++;
    } 

    /*c <<= (4-n)*8;*/

    /* Get the stdout's file handle. */
    stdout = GetStdHandle@4(-11);

    /* Write to the stdout.*/
    WriteFile@20(stdout, &c, n, &obytes, 0);
}