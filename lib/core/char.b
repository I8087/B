char (s, n) {

    /* Declare the local variables. */
    auto c;

    /* Extract the character from the string vector. */
    c = s[n/4];
    c = c >> n%4*8;
    c = c & 0xFF;

    /* Return the character. */
    return c;

}