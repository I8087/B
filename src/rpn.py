"""B Compiler RPN."""

import sys

class RPN():

    def __init__(self, inp, linp, funcs):

        self.inp = inp
        self.linp = linp
        self.funcs = funcs

        self.outp = []

        # The operator stack.
        self.stack = []

        # Is this a unary operator?
        self.unary = True

        self.unary_ops = ("+", "-", "!", "*", "&", "++", "--")

        # A dictionary of operators, their precedence level, and if they're left associative.
        self.ops = {
                    "++":  (13, True),  # Unary
                    "--":  (13, True),  # Unary
                    "(":   (13, True),
                    ")":   (13, True),
                    "[":   (13, True),
                    "]":   (13, True),
                    "u++": (12, False), # Unary     FIX: Acts like ++.
                    "u--": (12, False), # Unary     FIX: Acts like --.
                    "u+":  (12, False), # Unary     FIX: Not implimented.
                    "u-":  (12, False), # Unary
                    "u!":  (12, False), # Unary
                    "u*":  (12, False), # Unary     FIX: Not implimented.
                    "u&":  (12, False), # Unary
                    "*":   (11, True),  # Binary
                    "/":   (11, True),  # Binary
                    "%":   (11, True),  # Binary
                    "+":   (10, True),  # Binary
                    "-":   (10, True),  # Binary
                    "<<":  (9, True),   # Binary
                    ">>":  (9, True),   # Binary
                    "<":   (8, True),
                    "<=":  (8, True),
                    ">":   (8, True),
                    ">=":  (8, True),
                    "==":  (7, True),
                    "!=":  (7, True),
                    "&":   (6, True),   # Binary
                    "^":   (5, True),   # Binary
                    "|":   (4, True),   # Binary
                    "?":   (3, False),
                    ":":   (3, False),
                    "=":   (2, False),
                    "+=":  (2, False),
                    "-=":  (2, False),
                    "*=":  (2, False),
                    "/=":  (2, False),
                    "%=":  (2, False),
                    "<<=": (2, False),
                    ">>=": (2, False),
                    "&=":  (2, False),
                    "^=":  (2, False),
                    "|=":  (2, False),
                    ",":   (1, True)
                   }

    def error(self, err_num=0):
        l = self.peek()[0][2]
        c = self.peek()[0][3]
        print(self.linp[l-1].replace("\t", " "))
        print((c-1)*" "+"^")
        print("RPN Error #{} at {}:{}\n".format(err_num, l, c))
        sys.exit(err_num)

    # Appends the output.
    def add(self, o):
        self.outp.append(o)

    # Peek at the input list.
    def peek(self, c=1):
        return self.inp[:c]

    # Discards used tags in the input list.
    def discard(self, i=1):
        self.inp = self.inp[i:]

    def do_op(self):

        while self.stack:
            if (self.stack[-1][1] not in ("(", "[")) and (self.ops[self.stack[-1][1]][0] > self.ops[self.peek()[0][1]][0]) or (self.stack[-1][1] not in ("(", "[")) and (self.ops[self.stack[-1][1]][0] == self.ops[self.peek()[0][1]][0] and self.ops[self.peek()[0][1]][1]):
                self.add(self.stack.pop())
            else:
                break

        # Don't foget to add the operator to the stack.
        self.stack.append(self.peek()[0])
        self.discard()

    # Might let errors slip by. Go back over this function later.
    def do_ep(self):

        # Discard ending parenthesis.
        self.discard()

        # Pop the operator stack until a starting parenthesis is found.
        while self.stack and self.stack[-1][1] != "(":
            self.add(self.stack.pop())


        # Check for mismatching parentheses.
        if self.stack and self.stack[-1][1] == "(":
            self.stack.pop()
        else:
            self.error(23)

        # If there's a function, pop it onto the output stack.
        if self.stack and self.stack[-1][0] == "FUNC":
            self.add(("COMMA", ",", -1, -1))
            self.add(self.stack.pop())

    # Might let errors slip by. Go back over this function later.
    def do_eb(self):
        # Save the ending baracket and discard it.
        save = self.peek()[0]
        self.discard()

        # Pop the operator stack until a starting parenthesis is found.
        while self.stack and self.stack[-1][1] != "[":
            self.add(self.stack.pop())


        # Check for mismatching parentheses.
        if self.stack and self.stack[-1][1] == "[":
            self.stack.pop()
        else:
            print(self.stack)
            self.error(28)

        self.add(save)

    # Main loop.
    def rpn(self):
        
        while self.inp:

            # Check for unary.
            if self.unary and self.peek()[0][1] in self.unary_ops:
                self.inp[0] = (self.peek()[0][0],
                               "u{}".format(self.peek()[0][1]),
                               self.peek()[0][2],
                               self.peek()[0][3])
            
            # Handles empty functions.
            if (len(self.inp) > 2) and (self.peek()[0][0] == "NAME" and self.peek(2)[1][0] == "SP" and self.peek(3)[2][0] == "EP"):
                self.add(("FUNC", self.peek()[0][1], self.peek()[0][2], self.peek()[0][3]))
                self.discard(3)
                self.unary = False
            elif (len(self.inp) > 1) and (self.peek()[0][0] == "NAME" and self.peek(2)[1][0] == "SP"):
                self.stack.append(("FUNC", self.peek()[0][1], self.peek()[0][2], self.peek()[0][3]))
                self.discard()
                self.unary = False
            elif self.peek()[0][0] == "NAME" or self.peek()[0][0] == "NUMBER":
                self.add(self.peek()[0])
                self.discard()
                self.unary = False
            elif self.peek()[0][0] == "STRING":
                self.add(self.peek()[0])
                self.discard()
                self.unary = False
            elif self.peek()[0][1] == "(":
                self.stack.append(self.peek()[0])
                self.discard()
                self.unary = True
            elif self.peek()[0][1] == ")":
                self.do_ep()
                self.unary = False
            elif self.peek()[0][1] == "[":
                self.stack.append(self.peek()[0])
                self.add(self.peek()[0])
                self.discard()
                self.unary = True
            elif self.peek()[0][1] == "]":
                self.do_eb()
                self.unary = False
            elif self.peek()[0][1] == ",":
                self.stack.append(self.peek()[0])
                self.discard()
                self.unary = True
            elif self.peek()[0][1] in self.ops:
                self.do_op()
                self.unary = True
            else:
                self.error(300)

        # Clean up the stack if there's no more input.
        while self.stack:
            self.add(self.stack.pop())

        # FOR DEBUG!
        #print(self.outp)

        return self.outp
