strlen (str) {

    /* Declare the local variables. */
    auto i;

    /* If the string is a null pointer, then the string has zero characters. */
    if (str == 0)
        return 0;

    /* Initialize the temporary string length.*/
    i = 0;

    /* Endless loop till a null character is found. */
    repeat {

        /* Return the string length if this is a null character.*/
        if (char(str, i) == 0)
            return i;

        /* If not, continue searching. */
        i++;
    }
}