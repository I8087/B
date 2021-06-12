putchar(chr) {

    /* Declare our local variables. */
    auto c, n, i;

    /* Assign our local variables initial values. */
    c = i = n = 0;

    /* Check for null characters. */
    while (i < 4) {
        if ((chr >> (3-i)*8) & 0xFF) {
            c <<= 8;
            n++;
        }

        c +=  (chr >> (3-i)*8) & 0xFF;

        i++;
    }

    /*c <<= (4-n)*8;*/

    /* Write to the stdout.*/
    write(0, &c, n);
}