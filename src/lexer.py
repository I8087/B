"""New B lexer."""

import string

class Lexer():

    def __init__(self, inp):

        self.line = 1
        self.char = 1

        self.linp = inp.split("\n")
        self.inp = inp

        self.outp = []

    def peek(self, c=1):
        return self.inp[:c]

    # Move right.
    def move(self, i=1):
        self.inp = self.inp[i:]
        self.char += i

    # Move down.
    def newline(self, i=1):
        self.line += i
        self.char = 1

    # Skips over a comment.
    def comment(self):
        self.move(2)
        found = False
        while self.inp:
            if self.peek(2) == "*/":
                self.move(2)
                found = True
                break
            elif self.peek() == "\n":
                self.move()
                self.newline()
            else:
                self.move()

        if found:
            return
        else:
            error(1)

    # Gets the name of a declaration.
    def name(self):
        n = ""
        l = self.line
        c = self.char
        test = string.digits+string.ascii_letters+"_@"

        while self.peek() in test:
            if self.peek() == "@":
                test = string.digits
            n = n+self.peek()
            self.move()

        self.add("NAME", n, l, c)

    # Gets the name of a declaration.
    def num(self):
        n = ""
        l = self.line
        c = self.char

        # Default type is an integer with a base 10.
        b = 10
        s = string.digits

        # Check the base for each number.
        if self.peek(2) == "0x":
            self.move(2)
            b = 16
            s = string.hexdigits

        while self.peek() in s:
            n = n+self.peek()
            self.move()

        self.add("NUMBER", str(int(n, b)), l, c)

    # Turns an escape character into the actual character.
    def esc_char(self, c):
        if c[0] != "*":
            self.error(0)

        if c[1] == "0":
            return "\0"
        elif c[1] == "e":
            return "\x04"
        elif c[1] == "(":
            return "{"
        elif c[1] == ")":
            return "}"
        elif c[1] == "t":
            return "\t"
        elif c[1] == "*":
            return "*"
        elif c[1] == "'":
            return "'"
        elif c[1] == "\"":
            return "\""
        elif c[1] == "n":
            return "\n"
        else:
            self.error(0)

    # Handles inline assembly code.
    def asm(self):
        self.move()
        found = False
        s = ""
        while self.inp:
            if self.peek() == ";":
                found = True
                break
            elif self.peek() == "}":
                found = True
                break
            elif self.peek() == "\n":
                self.move()
                self.newline()
            elif self.peek() == "*":
                s += self.esc_char(self.peek(2))
                self.move(2)
            else:
                s += self.peek()
                self.move()

        if found:
            self.add("ASM", s.strip())
        else:
            self.error(111)

    # Handles chars.
    # Character constants are right justified and zero filled.

    # ***EXAMPLE***
    # 'abcd' == 'abcd'
    # 'abc' == '*0abc'
    # 'ab' == '*0*0ab'
    # 'a' == '*0*0*0a'
    # '' == '*0*0*0*0' ==  0

    def mchar(self):

        self.move()

        c = 0
        b = 0

        while self.inp:

            if self.peek() == "'":
                self.move()
                self.add("NUMBER", c)
                return

            elif self.peek() == "\n":
                self.move()
                self.newline()

            elif self.peek() == "*":
                c += ord(self.esc_char(self.peek(2))) << b
                b += 8
                self.move(2)

            else:
                c += ord(self.peek()) << b
                b += 8
                self.move()

        # Print an error if we ran out of input.
        self.error(1)

    # Handles strings.
    # Strings are vectors of characters that end with an additional null
    # character, left justified, and filled with null characters.
    def mstring(self):

        self.move()

        # A list to hold characters of our string vector.
        s = []

        c = 0
        i = 0

        while self.inp:

            if self.peek() == "\"":
                self.move()

                # If this character constant is full, just use the next.
                if not i%4:
                    s.append(c)
                    c = 0

                s.append(c)

                self.add("STRING", tuple(s))

                return

            elif self.peek() == "\n":
                self.move()
                self.newline()

            elif self.peek() == "*":
                c += ord(self.esc_char(self.peek(2))) << (i%4)*8
                i += 1
                self.move(2)

            else:
                c += ord(self.peek()) << (i%4)*8
                i += 1
                self.move()

            # Add this character constant to the list.
            if not i%4:
                s.append(c)
                c = 0

        # Print an error if we ran out of input.
        self.error(1)

    def add(self, tn, data="", line=-1, char=-1):
        if line == -1:
            line = self.line

        if char == -1:
            char = self.char

        self.outp.append((tn, data, line, char))

    # Error control.
    def error(self, err_num=0):
        print(self.linp[self.line-1].replace("\t", " "))
        print((self.char-1)*" "+"^")
        print("Lexer Error #{} at {}:{}\n".format(err_num, self.line, self.char))
        exit(err_num)

    def lexer(self):

        while self.inp:

            # Handle comments.
            if self.peek(2) == "/*":
                self.comment()

            # Handle whitespaces.
            elif self.peek() in (" ", "\t"):
                self.move()

            # Handle new lines.
            elif self.peek() == "\n":
                self.move()
                self.newline()

            # Handle keywords.
            elif self.peek(6) in ("default",):
                self.add(self.peek(7).upper())
                self.move(7)

            elif self.peek(6) in ("repeat", "switch", "return"):
                self.add(self.peek(6).upper())
                self.move(6)

            elif self.peek(5) in ("extrn", "while", "break"):
                self.add(self.peek(5).upper())
                self.move(5)

            elif self.peek(4) in ("auto", "else", "goto", "next", "case"):
                self.add(self.peek(4).upper())
                self.move(4)

            elif self.peek(3) in ("for"):
                self.add(self.peek(3).upper())
                self.move(3)

            elif self.peek(2) in ("if", "do"):
                self.add(self.peek(2).upper())
                self.move(2)

            # Handle operators.
            elif self.peek(3) in ("<<=", ">>="):
                self.add("OP", self.peek(3))
                self.move(3)

            elif self.peek(2) in ("++", "--", "<<", ">>", "<=",
                                  ">=", "==", "^=", "|=", "&=",
                                  "+=", "-=", "%=", "*=", "/="):

                self.add("OP", self.peek(2))
                self.move(2)

            elif self.peek() in ("&", "!", "~", "*", "/", "%", "+", "-",
                                 "<", ">", "^", "|", "=", "?", ":"):
                self.add("OP", self.peek())
                self.move()

            # Handle delimiters.
            elif self.peek() == "(":
                self.add("SP", "(")
                self.move()

            elif self.peek() == ")":
                self.add("EP", ")")
                self.move()

            elif self.peek() == "[":
                self.add("SB", "[")
                self.move()

            elif self.peek() == "]":
                self.add("EB", "]")
                self.move()

            elif self.peek() == "{":
                self.add("SC", "{")
                self.move()

            elif self.peek() == "}":
                self.add("EC", "}")
                self.move()

            elif self.peek() == ",":
                self.add("COMMA", ",")
                self.move()

            elif self.peek() == ";":
                self.add("SEMICOLON", ";")
                self.move()

            elif self.peek() == "\\":
                self.add("BSLASH", "\\")
                self.move()

            # Handle inline assembly.
            elif self.peek() == "@":
                self.asm()

            # Handle ASCII character constants.
            elif self.peek() == "'":
                self.mchar()

            # Handle string constants.
            elif self.peek() == "\"":
                self.mstring()

            # Handle all number constants.
            elif self.peek() in string.digits:
                self.num()

            # Handle all indentifers.
            elif self.peek() in string.ascii_letters+"_":
                self.name()

            # If the input is invalid, throw an error.
            else:
                self.error(88)

        # Return the tokenized output tuple and
        # the source input's lines in a tuple.
        return self.outp, self.linp
