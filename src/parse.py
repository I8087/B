"""New B parser."""

import sys, collections

from rpn import RPN
from error import Error

class Parser():

    def __init__(self, inp, linp, options):

        self.inp = inp
        self.linp = linp

        # Save the compiler options and flags.
        self.options = options

        # The output code buffer.
        self.outp = ["bits 32", ""]

        # Holds a dictionary of segments and their assembly code.
        self.segments = {".text": [],
                         ".data": [],
                         ".bss": []}

        # A list of all names defined, including variables and functions.
        self.names = []

        # A dictionary of functions and their properties.
        # name = function name
        # call = function calling convention
        # prototype = True if this is a prototype function, otherwise false.
        # param = The number of parameters this function takes.
        # params = A list of all parameter names in this function.
        self.funcs = {}

        # A list of statements, including their start and stop points.
        self.compounds = []

        # A list of generated labels for conditions.
        self.l = -1

        # A dictionary of parameters for the current function.
        self.param = {}
        self.param_l = 0

        # A dictionary of local variables defined in the current function and there location on the stack.
        self.var = {}
        self.var_l = 0

        # A list of global variables and functions.
        self.extrn = []

        # Size of a word on the machine in 8-bit bytes.
        if self.options["f"] in ("win32", "lin32"):
            self.word = 4
        elif self.options["f"] in ("win64", "lin64"):
            self.word = 8
        else:
            self.error(75)

        self.format = self.options["f"]

        # Are we walking through a function right now?
        self.in_func = False

        # True if we just recieved a simple statement instead of a complex statement.
        self.in_simple = False

        # True if the next statement is a simple statement.
        self.next_simple = False

    def a(self):
        if self.options["f"] in ("win32", "lin32"):
            return "eax"
        elif self.options["f"] in ("win64", "lin64"):
            return "rax"
        else:
            self.error(45)

    def b(self):
        if self.options["f"] in ("win32", "lin32"):
            return "ebx"
        elif self.options["f"] in ("win64", "lin64"):
            return "rbx"
        else:
            self.error(45)

    def c(self):
        if self.options["f"] in ("win32", "lin32"):
            return "ecx"
        elif self.options["f"] in ("win64", "lin64"):
            return "rcx"
        else:
            self.error(45)

    def d(self):
        if self.options["f"] in ("win32", "lin32"):
            return "edx"
        elif self.options["f"] in ("win64", "lin64"):
            return "rdx"
        else:
            self.error(45)

    def bp(self):
        if self.options["f"] in ("win32", "lin32"):
            return "ebp"
        elif self.options["f"] in ("win64", "lin64"):
            return "rbp"
        else:
            self.error(45)

    def sp(self):
        if self.options["f"] in ("win32", "lin32"):
            return "esp"
        elif self.options["f"] in ("win64", "lin64"):
            return "rsp"
        else:
            self.error(45)

    def sys_data(self):
        if self.options["f"] in ("win32", "lin32"):
            return "dd"
        elif self.options["f"] in ("win64", "lin64"):
            return "dq"
        else:
            self.error(45)

    def sys_prefix(self):
        if self.options["f"] in ("win32", "lin32"):
            return "dword"
        elif self.options["f"] in ("win64", "lin64"):
            return "qword"
        else:
            self.error(45)

    # Takes a register and returns its lowest byte.
    # For when instructions require r8.
    def low_byte(self, reg):

        if reg == self.a():
            return "al"
        elif reg == self.b():
            return "bl"
        elif reg == self.c():
            return "cl"
        elif reg == self.d():
            return "dl"
        else:
            self.error(8)

    # Handles parser error.
    def error(self, err=0):
        l = self.peek()[0][2]
        c = self.peek()[0][3]
        print(self.linp[l-1].replace("\t", " "))
        print((c-1)*" "+"^")
        print("Parser Error #{} at {}:{}\n{}\n".format(int(err), l, c, err))
        sys.exit(int(err))

    # Appends the assembly output.
    def add(self, o="", segment=".text"):
        self.segments[segment].append(o)

    # Adds an empty line to the output if one doesn't exist already.
    def add_pretty(self, segment=".text"):
        if self.segments[segment] and self.segments[segment][-1]:
            self.add(segment=segment)

    # Peek at the input list.
    def peek(self, c=1):
        return self.inp[:c]

    # Peek at the first in the input list and strips it of the list.
    def speek(self):
        return self.inp[0]

    # Discards used tags in the input list.
    def discard(self, i=1):
        self.inp = self.inp[i:]

    # Looks for a tag until a semicolon is found.
    def findinline(self, tag):
        found = False
        for i in self.inp:
            if i[0] == tag:
                found = True
                break
            elif i[0] == "SEMICOLON":
                break

        return found

    # Creates an internal label used within function branching.
    def label(self):
        self.l += 1
        return ".L{}".format(self.l)

    # Creates a sorted dictionary of compound statements.
    def push_compound(self, before="", after="", _if=False, loop=False, func=False):
        self.compounds.append({
            "before":       before,
            "after":        after,
            "start":        self.label(),
            "end":          self.label(),
            "if":           _if,
            "loop":         loop,
            "func":         func})

        return self.compounds[-1]

    def pop_compound(self):

        # Pop label, save the label's name, and it's output assembly to place after the label.
        com = self.compounds.pop()

        # Add any needed assembly before the end label.
        for i in [i for i in com["before"].split("\n") if i]:
            self.add(i)

        # Add the end label.
        self.add("{}:".format(com["end"]))
        self.add_pretty()

        # Add any needed assembly after the end label.
        for i in [i for i in com["after"].split("\n") if i]:
            self.add(i)

        # If this is the end of a function, clean it up.
        if com["func"]:
            self.end_func()

    # Gets the label on the top of the stack.
    def get_top(self):
        return self.compounds[-1]

    # Finds the first loop label on top of the stack.
    def get_loop(self):

        for i in self.compounds[::-1]:
            if i["loop"]:
                return i

        # If we can't find a loop label, then something went wrong.
        return False

    def get_func(self):
        for i in self.compounds[::-1]:
            if i["func"]:
                return i

        # If we can't find a loop label, then something went wrong.
        return False

    def parser(self):
        while self.inp:

            #print("-> {}".format(self.peek()[0]))

            # Check to see if this is a simple statement.
            if self.next_simple:
                self.next_simple = False
                self.in_simple = True

            if (self.peek()[0][0] == "NAME") and (self.peek(2)[1][0] == "SP") and not self.in_func and self.peek()[0][1] not in self.names:
                self.do_func()
            elif (self.peek()[0][0] == "NAME") and self.in_func:
                self.do_math()
            elif (self.peek()[0][0] == "NAME") and not self.in_func:
                self.do_extern()

            # Calling convention keywords indicate the start of a new function.
            elif self.peek()[0][0] in ("STDCALL", "CDECL"):
                self.do_func()

            elif self.peek()[0][0] == "AUTO":
                self.do_auto()
            elif self.peek()[0][0] == "EXTRN":
                self.do_extrn()
            elif self.peek()[0][0] == "ASM":
                self.do_asm()

            # Handles control statements.
            elif self.peek()[0][0] == "GOTO":
                self.error(500)

            elif self.peek()[0][0] == "RETURN":
                self.do_return()

            elif self.peek()[0][0] == "BREAK":
                self.do_break()

            elif self.peek()[0][0] == "NEXT":
                self.do_next()

            # Handle conditional statement keywords.
            elif self.peek()[0][0] == "IF":
                self.do_if()

            elif self.peek()[0][0] == "ELSE":
                self.do_else()

            # Handle loop statement keywords.
            elif self.peek()[0][0] == "REPEAT":
                self.do_repeat()
            elif self.peek()[0][0] == "WHILE":
                self.do_while()

            elif self.peek()[0][0] == "EC":
                self.do_end()
            else:
                self.error(100)

            self.add_pretty()

            # If this is a simple statement, then end now.
            if self.in_simple:
                self.in_simple = False
                self.pop_compound()
                self.add_pretty()

        # {} mismatch!
        if self.compounds:
            self.error(900)

        # Add prototyped functions.
        for i in [i for i in self.funcs.keys() if self.funcs[i]["prototype"]]:
            self.outp.append("extern {}".format(self.funcs[i]["tname"]))
        self.outp.append("")

        # Make all functions global.
        for i in [i for i in self.funcs.keys() if not self.funcs[i]["prototype"]]:
            self.outp.append("global {}".format(self.funcs[i]["tname"]))
        self.outp.append("")

        # Add all of the segments together.
        for i in self.segments:
            self.outp.append("segment {}".format(i))
            self.outp.append("")

            for n in self.segments[i]:
                self.outp.append(n)

        return self.outp

    def do_asm(self):

        # Add the assembly.
        self.add(self.peek()[0][1])
        self.discard()

        # Make sure this is the end.
        if self.peek()[0][0] == "EC":
            pass
        elif self.peek()[0][0] == "SEMICOLON":
            self.discard()
        else:
            self.error(332)

    def do_extern(self):
        n = self.peek()[0][1]
        self.discard()

        if self.peek()[0][0] == "NUMBER":
            self.add("_{}: {} {}".format(n, self.sys_data(), self.peek()[0][1]), ".data")
            self.discard()
        elif self.peek()[0][0] == "SB":
            self.discard()
            if self.peek()[0][0] != "NUMBER":
                self.error()
            self.add("_{}: times {} {} 0".format(n, self.peek()[0][1], self.sys_data()), ".data")
            self.discard()
            if self.peek()[0][0] != "EB":
                self.error()
            self.discard()
        else:
            self.error()

        if self.peek()[0][0] != "SEMICOLON":
            self.error()

        self.discard()

    # Ends a function and cleans up the variables used for managing them.
    def end_func(self):

        # A list of all names defined, including variables and functions.
        self.names = []

        # Reset the labels, label counter, and label to do dictionary.
        self.l = -1
        self.labels = []
        self.labels_do = {}

        # Reset the parameters and parameter counter.
        self.param = {}
        self.param_l = 0

        # Reset the local variables and the local variables counter.
        self.var = {}
        self.var_l = 0

        # Reset the list of global variables and functions.
        self.extrn = []

        # Reset if we're in a function.
        self.in_func = False

        # Reset if we're in a simple statement.
        self.in_simple = False
        self.next_simple = False

    # }
    def do_end(self):
        self.discard()

        if self.compounds:
            self.pop_compound()
        else:
            self.error(3)

    def do_extrn(self):
        self.discard()

        while True:
            if self.peek()[0][0] == "NAME":
                if self.peek()[0][1] in self.names:
                    self.error()
                self.names.append(self.peek()[0][1])
                self.extrn.append(self.peek()[0][1])
                #self.add("extern _{}".format(self.peek()[0][1]))
                self.discard()
            else:
                self.error()

            if self.peek()[0][0] == "COMMA":
                self.discard()
            elif self.peek()[0][0] == "SEMICOLON":
                self.discard()
                break
            else:
                self.error()

    def do_auto(self):
        self.discard()

        while True:

            # Expecting a variable's name.
            if self.peek()[0][0] == "NAME":

                # Save the variable's name.
                var = self.peek()[0][1]
                self.discard()

                # Make sure this variable isn't already declared.
                if var in self.names:
                    self.error(Error.REDFINED_VAR)

                # Check to see if we need to allocate a vector on the stack.
                if self.peek()[0][0] == "SB":
                    self.discard()

                    # Expecting a number.
                    if self.peek()[0][0] != "NUMBER":
                        self.error()

                    # Save the vector size.
                    v = int(self.peek()[0][1])
                    self.discard()

                    # Set the variable's size on the stack.
                    self.var_l -= v*self.word

                    # If a vector was allocated, point to it. Otherwise set the vector as null.
                    if v:
                        self.add("lea {}, [{}{}]".format(self.a(), self.bp(), self.var_l))
                    else:
                        self.add("xor {}, {}".format(self.a(), self.a()))

                    # Set the size of the pointer on the stack.
                    self.var_l -= self.word

                    # Point the pointer at the vector.
                    self.add("mov [{}{}], {}".format(self.bp(), self.var_l, self.a()))

                    # Allocate space on the stack for the vector and pointer.
                    self.add("sub {}, {}".format(self.sp(), (v+1)*self.word))

                    # Expecting a ending bracket.
                    if self.peek()[0][0] != "EB":
                        self.error()

                    self.discard()

                else:

                    # Set the variable's size on the stack.
                    self.var_l -= self.word

                    # Allocate space on the stack for the variable.
                    self.add("sub {}, {}".format(self.sp(), self.word))

                # Add the variable to the list of names.
                self.names.append(var)

                # Set the variable's location on the stack.
                self.var[var] = self.var_l

                self.add("; {} @ [{}{}]".format(var, self.bp(), self.var_l))

            else:
                self.error()

            if self.peek()[0][0] == "COMMA":
                self.discard()
            elif self.peek()[0][0] == "SEMICOLON":
                self.discard()
                break
            else:
                self.error()

    def do_func(self):

        # A temporary dictionary to hold the functions properties.
        _func = {"name": "",
                 "call": "CDECL",
                 "prototype": False,
                 "param": 0,
                 "params": []}

        # If there's no statement, then this is a function prototype.
        _func["prototype"] = not self.findinline("SC")


        # A function cannot be declared inside another function!
        if self.in_func:
            self.error(123)

        # See if this function has a calling convention keyword.
        if self.peek()[0][0] in ("STDCALL", "CDECL"):
            _func["call"] = self.peek()[0][0]
            self.discard()

        # Check to see if this name exists already!
        if self.peek()[0][1] in self.names:
            self.error(Error.REDFINED_FUNC)

        # Save the function's name.
        _func["name"] = self.peek()[0][1]
        self.discard()

        if _func["name"] in self.funcs.keys():
            if not (not _func["prototype"] and self.funcs[_func["name"]]["prototype"]):
                self.error(554)
            

        # Save space for BP and IP.
        self.param_l = self.word*2
        self.var_l = 0

        # Make sure there's a (
        if self.peek()[0][0] == "SP":
            self.discard()
        else:
            self.error(125)

        while True:
            if self.peek()[0][0] == "NAME":
                if self.peek()[0][1] in self.names:
                    self.error(126)
                
                if not _func["prototype"]:
                    self.names.append(self.peek()[0][1])
                    self.param[self.peek()[0][1]] = self.param_l
                    self.param_l += self.word

                _func["params"].append(self.peek()[0][1])
                self.discard()

            elif self.peek()[0][0] == "EP":
                pass
            else:
                self.error(127)

            if self.peek()[0][0] == "COMMA":
                self.discard()
            elif self.peek()[0][0] == "EP":
                self.discard()
                break
            else:
                self.error(128)

        # Set param
        _func["param"] = len(_func["params"])

        if not _func["prototype"] and self.peek()[0][0] == "SC":
            self.discard()
        elif _func["prototype"] and self.peek()[0][0] == "SEMICOLON":
            self.discard()
        else:
            self.error(129)

        # Create function's true name used in assembly.
        if _func["call"] == "CDECL":
            _func["tname"] = "_{}".format(_func["name"])
        elif _func["call"] == "STDCALL":
            _func["tname"] = "_{}@{}".format(_func["name"], _func["param"]*self.word)
        else:
            self.error(130)

        if not _func["prototype"]:
            # Add the function to the list of compound statements.
            com = self.push_compound(before="xor {0}, {0}".format(self.a()),
                                     after="mov {0}, {1}\npop {1}\nret".format(self.sp(), self.bp()),
                                     func=True)

            ## NOTE: Fix this function!!!

            # Adjust the start and end points of the function.
            com["end"] = com["start"]
            self.l -= 1
            com["start"] = _func["tname"]

            # Add the function to the output.
            self.names.append(_func["name"])
            self.in_func = True
            #self.add_pretty()
            self.add("{}:".format(com["start"]))
            self.add("push {}".format(self.bp()))
            self.add("mov {}, {}".format(self.bp(), self.sp()))
            self.add_pretty()

        # Make sure we save how many parameters this function has.
        self.funcs[_func["name"]] = _func

    def do_return(self):
        # Get rid of the if token.
        self.discard()

        # Create a list of tokens for math.
        math_list = []

        # Get all the math tokens.
        while self.peek()[0][0] not in ("SEMICOLON", "EC"):
            math_list.append(self.peek()[0])
            self.discard()

        # If this is a semicolon then get rid of it.
        if self.peek()[0][0] == "SEMICOLON":
            self.discard()

        # Do the math!
        a = self.math(math_list)

        # Add some some space in the output assembly.
        #self.add()

        if a == None:
            self.add("xor {}, {}".format(self.a(), self.a()))
        elif a[0] == "NAME":
            self.add("mov {}, {}".format(self.a(), self.get_var(a[1])))
        elif a[0] == "NUMBER":
            self.add("mov {}, {}".format(self.a(), a[1]))
        elif a[0] == "REGISTER":
            if a[1] != self.a():
                self.add("mov {}, {}".format(self.a(), a[1]))
        else:
            self.error(54)

        # Get the function's end label.
        com = self.get_func()

        # Make sure we're in a function.
        if com:
            self.add("jmp {}".format(com["end"]))
        else:
            self.error(Error.RETURN_OUTSIDE_FUNC)


    def do_break(self):
        # Get rid of the if token.
        self.discard()

        # If this is a semicolon then get rid of it.
        if self.peek()[0][0] == "SEMICOLON":
            self.discard()
        else:
            self.error(Error.EXPECT_SC)

        # Get the end of the inner most loop statement.
        com = self.get_loop()

        # Can't break if you're not inside a loop statement!
        if not com:
            self.error(Error.BREAK_OUTSIDE_LOOP)

        self.add("jmp {}".format(com["end"]))


    def do_next(self):
        # Get rid of the if token.
        self.discard()

        # If this is a semicolon then get rid of it.
        if self.peek()[0][0] == "SEMICOLON":
            self.discard()
        else:
            self.error(Error.EXPECT_SC)

        # Get the end of the inner most loop statement.
        com = self.get_loop()

        # Can't break if you're not inside a loop statement!
        if not com:
            self.error(Error.NEXT_OUTSIDE_LOOP)

        self.add("jmp {}".format(com["start"]))

    def do_repeat(self):

        # Get rid of the repeat token.
        self.discard()

        # Add the repeat loop to the list of compound statements.
        com = self.push_compound(before="jmp .L{}".format(self.l+1), loop=True)

        # Add a starting comment.
        self.add("; REPEAT loop")

        # Add the repeat loop's label.
        self.add("{}:".format(com["start"]))

        # Check to see if this is a simple statement.
        if self.peek()[0][0] == "SC":
            self.discard()
        else:
            self.next_simple = True

    def do_while(self):
        # Get rid of the if token.
        self.discard()

        # Make sure there's a (
        if self.peek()[0][0] != "SP":
            self.error(Error.EXPECT_SP)

        # Discard (
        self.discard()

        # Set a () counter.
        c = 1

        # Create a list of tokens for math.
        math_list = []

        while c:
            if self.peek()[0][0] == "SP":
                c += 1
            elif self.peek()[0][0] == "EP":
                c -= 1
            elif self.peek()[0][0] == "SEMICOLON":
                self.error()

            # Don't appending a closing )
            if c:
                math_list.append(self.peek()[0])
            self.discard()

        # Add the while loop to the list of compound statements.
        com = self.push_compound(before="jmp .L{}".format(self.l+1), loop=True)

        # Add a starting comment.
        self.add("; WHILE loop")

        # Add while loop label.
        self.add("{}:".format(com["start"]))

        r = self.math(math_list)

        # Check to see if this is a simple statement.
        if self.peek()[0][0] == "SC":
            self.discard()
        else:
            self.next_simple = True

        if r[0] == "NUMBER":
            self.add("mov {}, {}".format(self.a(), r[1]))
            r = ("REGISTER", self.a(), -1, -1)

        # Skip loop if the expression is false.
        self.add("test {0}, {0}".format(r[1]))
        self.add("je {}".format(com["end"]))
        #self.add()

    def do_if(self):
        # Get rid of the if token.
        self.discard()

        # Make sure there's a (
        if self.peek()[0][0] != "SP":
            self.error(Error.EXPECT_SP)

        # Discard (
        self.discard()

        # Set a () counter.
        c = 1

        # Create a list of tokens for math.
        math_list = []

        while c:
            if self.peek()[0][0] == "SP":
                c += 1
            elif self.peek()[0][0] == "EP":
                c -= 1
            elif self.peek()[0][0] == "SEMICOLON":
                self.error()

            # Don't appending a closing )
            if c:
                math_list.append(self.peek()[0])
            self.discard()

        # Add the if condition to the list of compound statements.
        com = self.push_compound(_if=True)

        # Add a starting comment.
        self.add("; IF conditional")

        # Add if condition start label.
        self.add("{}:".format(com["start"]))

        r = self.math(math_list)

        # Check to see if this is a simple statement.
        if self.peek()[0][0] == "SC":
            self.discard()
        else:
            self.next_simple = True

        if r[0] == "NUMBER":
            self.add("mov {}, {}".format(self.a(), r[1]))
            r = ("REGISTER", self.a(), -1, -1)

        if r[1][0] == "[" and r[1][-1] == "]":
            self.add("mov {}, {} {}".format(self.a(), self.sys_prefix(), r[1]))
            r = ("REGISTER", self.a(), -1, -1)

        # Skip this statement if the test is false.
        self.add("test {0}, {0}".format(r[1]))
        self.add("je {}".format(com["end"]))
        #self.add()


    def do_else(self):
        # Get rid of the else token.
        self.discard()

        # Add the else condition to the list of compound statements.
        com = self.push_compound()

        # Add a starting comment.
        self.add("; ELSE conditional")

        # Add else condition start label.
        self.add("{}:".format(com["start"]))

        # Check to see if this is a simple statement.
        if self.peek()[0][0] == "SC":
            self.discard()
        else:
            self.next_simple = True

    def do_math(self):
        # Create a list of tokens for math.
        math_list = []

        while True:
            if self.peek()[0][0] == "SEMICOLON":
                self.discard()
                break
            elif self.peek()[0][0] == "EC":
                break

            math_list.append(self.peek()[0])
            self.discard()

        self.math(math_list)

    def math(self, math_list):

        # The comment string for the equation. For debug purposes.
        s = "; INFIX:"

        # Dict to str.
        for i in math_list:
            s = "{} {}".format(s, i[1])
        s = s.lstrip()

        # Add the equation comment to the output.
        self.add(s)

        # Turn the prefix code into postfix.
        math_list = RPN(math_list, self.linp, self.funcs).rpn()

        # The comment string for the equation. For debug purposes.
        s = "; POSTFIX:"

        # Dict to str.
        for i in math_list:
            s = "{} {}".format(s, i[1])
        s = s.lstrip()

        # Add the equation comment to the output.
        self.add(s)

        # A stack for holding variables and numbers.
        stack = []

        # Number of arguments passed.
        args = 0

        ## DEBUG!!
        #print(s)

        while math_list:

            ## DEBUG!!
            #print("{} -> {}".format(math_list[0][1], [i[1] for i in stack]))

            if math_list[0][0] == "FUNC":

                # Make sure this function exists!
                if math_list[0][1] not in self.funcs.keys():
                    self.error(701)

                self.add("call {}".format(self.funcs[math_list[0][1]]["tname"]))

                # Only clean up the stack if needed.
                if args and self.funcs[math_list[0][1]]["call"] == "CDECL":
                    self.add("add {}, {}".format(self.sp(), args*self.word))

                args = 0
                math_list = math_list[1:]

                stack.append(("REGISTER", self.a(), -1, -1))

            # Push all constants onto the stack.
            elif math_list[0][0] in ("NAME", "NUMBER", "STRING"):
                stack.append(math_list[0])
                math_list = math_list[1:]

            # Manages unary operators.
            elif math_list[0][1] in ("++", "--", "u++", "u--", "u+", "u-", "u!", "u*", "u&"):

                # a = op(a)
                op = math_list[0][1]
                a = stack.pop()

                # a = VAR | NUM | REG
                if self.is_var(a[1]):

                    # Get the location of a.
                    if op == "u&":
                        a = self.get_var(a[1])
                    else:
                        a = "{} {}".format(self.sys_prefix(), self.get_var(a[1]))

                elif a[0] == "NUMBER":

                    # Move a into that register.
                    self.add("mov {}, {}".format(self.a(), a[1]))

                    # Update a as that register.
                    a = self.a()

                elif a[0] == "REGISTER":

                    if op != "u&" and a[1][0] == "[":
                        a = "{} {}".format(self.sys_prefix(), a[1])
                    else:
                        a = a[1]

                else:

                    # a isn't the right type so throw an error.
                    self.error(25)

                # Do the operator now that we have a setup.
                if op == "++":
                    # a = a++
                    self.add("inc {}".format(a))

                elif op == "--":
                    # a = a--
                    self.add("dec {}".format(a))

                elif op == "u++":
                    # a = ++a
                    self.add("inc {}".format(a))

                elif op == "u--":
                    # a = --a
                    self.add("dec {}".format(a))

                elif op == "u-":
                    # a = -a
                    self.add("neg {}".format(a))

##                elif op == "u+":
##                    # a = +a
##                   self.add("{}".format(a))

                elif op == "u!":
                    # a = !a
                    self.add("not {}".format(a))

##                elif op == "u*":
##                    # a = *a
##                    self.add("{}".format(a))

                elif op == "u&":
                    # a = &a
                    self.add("lea {}, {}".format(self.a(), a))
                    a = self.a()

                else:

                    # This shouldn't be possible, but just in case.
                    self.error(600)

                # Push a onto the stack.
                if a.startswith(self.sys_prefix()):
                    a = a[len(self.sys_prefix()):].strip()
                stack.append(("REGISTER", a, -1, -1))

                # Remove the op off of the math list.
                math_list = math_list[1:]


            # Manages binary operators.
            elif math_list[0][1] in ("*", "/", "%", "+", "-", "<<", ">>", "&", "^", "|"):

                # a = a op b
                op = math_list[0][1]
                b = stack.pop()
                a = stack.pop()

                # a = VAR | NUM | REG
                if self.is_var(a[1]):

                    # Find an empty register.
                    reg = self.d() if b[1] == self.a() else self.a()

                    # Move a into that register.
                    self.add("mov {}, {}".format(reg, self.get_var(a[1])))

                    # Update a as that register.
                    a = reg

                elif a[0] == "NUMBER":

                    # Find an empty register.
                    reg = self.d() if b[1] == self.a() else self.a()

                    # Move a into that register.
                    self.add("mov {}, {}".format(reg, a[1]))

                    # Update a as that register.
                    a = reg

                elif a[0] == "REGISTER":

                    # Move a into register A if not done so already.
                    if a != self.a():
                        self.add("mov {}, {}".format(self.a(), a[1]))

                    # Save a.
                    a = self.a()

                else:

                    # a isn't the right type so throw an error.
                    self.error(35)

                # b = VAR | NUM | REG
                if self.is_var(b[1]):

                    # Move b into register C.
                    self.add("mov {}, {}".format(self.c(), self.get_var(b[1])))

                    # Save b.
                    if op in ("<<", ">>"):
                        b = "cl" # Can only shift using register CL, to my knowledge.
                    else:
                        b = self.c()

                elif b[0] == "NUMBER":

                    # If b is a number, move it into register C.
                    self.add("mov {}, {}".format(self.c(), b[1]))

                    # Save b.
                    if op in ("<<", ">>"):
                        b = "cl"
                    else:
                        b = self.c()

                elif b[0] == "REGISTER":

                    # Move a into register A if not done so already.
                    if b != self.c():
                        self.add("mov {}, {}".format(self.c(), b[1]))

                    # Save b.
                    if op in ("<<", ">>"):
                        b = "cl" # Can only shift using register CL, to my knowledge.
                    else:
                        b = self.c()

                else:

                    # b isn't the right type so throw an error.
                    self.error(45)

                # Do the operator now that we have a and b setup.
                if op == "*":
                    # a = a * b
                    self.add("mul {}".format(b))

                elif op == "/":
                    # a = a / b
                    self.add("xor {0}, {0}".format(self.d()))
                    self.add("div {}".format(b))
                    a = self.a()

                elif op == "%":
                    # a = a % b
                    self.add("xor {0}, {0}".format(self.d()))
                    self.add("div {}".format(b))
                    a = self.d()

                elif op == "+":
                    # a = a + b
                    self.add("add {}, {}".format(a, b))

                elif op == "-":
                    # a = a - b
                    self.add("sub {}, {}".format(a, b))

                elif op == "<<":
                    # a = a << b
                    self.add("shl {}, {}".format(a, b))

                elif op == ">>":
                    # a = a >> b
                    self.add("shr {}, {}".format(a, b))

                elif op == "&":
                    # a = a & b
                    self.add("and {}, {}".format(a, b))

                elif op == "^":
                    # a = a ^ b
                    self.add("xor {}, {}".format(a, b))

                elif op == "|":
                    # a = a | b
                    self.add("or {}, {}".format(a, b))

                else:

                    # This shouldn't be possible, but just in case.
                    self.error(400)

                # Push a onto the stack.
                stack.append(("REGISTER", a, -1, -1))

                # Remove the op off of the math list.
                math_list = math_list[1:]

            # Relational and Equality Operators.
            elif math_list[0][1] in ("<", ">","<=", ">=", "==", "!="):

                # Get the operator and the variables.
                op = math_list[0][1]
                b = stack.pop()
                a = stack.pop()

                # Do A.
                if self.is_var(a[1]):
                    self.add("mov {}, {}".format(self.d(), self.get_var(a[1])))
                    a = self.d()
                elif a[0] == "REGISTER":
                    a = a[1]
                    if a == self.a():
                        self.add("mov {}, {}".format(self.d(), a))
                        a = self.d()

                else:
                    self.error(212)

                # Do B.
                if self.is_var(b[1]):
                    b = self.get_var(b[1])
                elif b[0] in ("REGISTER", "NUMBER"):
                    b = b[1]
                    if b == self.a():
                        self.add("mov {}, {}".format(self.d(), b))
                        b = self.d()

                else:
                    self.error(212)

                # Universal start.
                self.add("xor {}, {}".format(self.a(), self.a()))
                self.add("cmp {}, {}".format(a, b))

                # Get a label for the logical jump.
                lbl = self.label()

                # Inverse branch based on the operator.
                if op == "<":
                    self.add("jae {}".format(lbl))
                elif op == ">":
                    self.add("jbe {}".format(lbl))
                elif op == "<=":
                    self.add("ja {}".format(lbl))
                elif op == ">=":
                    self.add("jb {}".format(lbl))
                elif op == "==":
                    self.add("jne {}".format(lbl))
                elif op == "!=":
                    self.add("je {}".format(lbl))
                else:
                    self.error(215)

                # Universal end.
                self.add("inc {}".format(self.a()))
                self.add("{}:".format(lbl))
                #self.add_pretty()

                # Add our results to the stack.
                stack.append(("REGISTER", self.a(), -1, -1))

                # Remove the operator from the math list.
                math_list = math_list[1:]

            # Start of an vector index.
            elif math_list[0][1] == "[":

                a = stack.pop()

                if self.is_var(a[1]):
                    a = self.get_var(a[1])
                elif a[0] == "REGISTER":
                    a = a[1]
                else:
                    self.error(2)

                stack.append(("REGISTER", a, -1, -1))

                math_list = math_list[1:]

            # End of an vector index.
            elif math_list[0][1] == "]":

                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    a = "{} {}".format(self.sys_prefix(), self.get_var(a[1]))

                elif a[0] == "REGISTER":
                    a = a[1]

                else:
                    self.error(2)

                if self.is_var(b[1]):
                    self.add("mov {}, {}".format(self.a(), self.get_var(b[1])))
                    b = self.a()
                elif b[0] == "REGISTER":
                    b = b[1]

                    if b[0] == "[":
                        self.add("mov {}, {} {}".format(self.a(), self.sys_prefix(), b))
                        b = self.a()

                else:
                    self.error(2)

                self.add("shl {}, 2".format(b))
                self.add("add {}, {}".format(b, a))

                if b.startswith(self.sys_prefix()):
                    b = b[len(self.sys_prefix()):].strip()

                stack.append(("REGISTER", "[{}]".format(b), -1, -1))

                math_list = math_list[1:]

            elif math_list[0][1] == "<<=":
                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    a = self.get_var(a[1])
                    stack.append(("REGISTER", a, -1, -1))
                    a = "{} {}".format(self.sys_prefix(), a)

                elif a[0] == "REGISTER":
                    a = a[1]

                else:                    self.error(23)

                if self.is_var(b[1]):
                    b = self.get_var(b[1])

                elif b[0] == "NUMBER":
                    b = b[1]

                elif b[0] == "REGISTER":
                    b = b[1]

                    if a.startswith(self.sys_prefix()) and b == self.c():
                        b = "cl"
                    elif a.startswith(self.sys_prefix()) :
                        self.add("mov {}, {}".format(self.c(), b))
                        b = "cl"
                else:
                    self.error(24)

                if a.startswith(self.sys_prefix()) and not isinstance(b, int) and b[0] == "[":
                    self.add("mov {}, dword {}".format(self.a(), b))
                    b = self.a()

                self.add("shl {}, {}".format(a, b))
                math_list = math_list[1:]

            elif math_list[0][1] == ">>=":
                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    a = self.get_var(a[1])
                    stack.append(("REGISTER", a, -1, -1))
                    a = "{} {}".format(self.sys_prefix(), a)

                elif a[0] == "REGISTER":
                    a = a[1]

                else:
                    self.error(23)

                if self.is_var(b[1]):
                    b = self.get_var(b[1])

                elif b[0] == "NUMBER":
                    b = b[1]

                elif b[0] == "REGISTER":
                    b = b[1]

                    if a.startswith(self.sys_prefix()) and b == self.c():
                        b = "cl"
                    elif a.startswith(self.sys_prefix()) :
                        self.add("mov {}, {}".format(self.c(), b))
                        b = "cl"
                else:
                    self.error(24)

                if a.startswith(self.sys_prefix()) and not isinstance(b, int) and b[0] == "[":
                    self.add("mov {}, dword {}".format(self.a(), b))
                    b = self.a()

                self.add("shr {}, {}".format(a, b))
                math_list = math_list[1:]

            elif math_list[0][1] == "+=":
                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    a = self.get_var(a[1])
                    stack.append(("REGISTER", a, -1, -1))
                    a = "{} {}".format(self.sys_prefix(), a)

                elif a[0] == "REGISTER":
                    a = a[1]

                else:
                    self.error(23)

                if self.is_var(b[1]):
                    b = self.get_var(b[1])

                elif b[0] in ("REGISTER", "NUMBER"):
                    b = b[1]

                else:
                    self.error(24)

                if a.startswith(self.sys_prefix()) and not isinstance(b, int) and b[0] == "[":
                    self.add("mov {}, dword {}".format(self.a(), b))
                    b = self.a()

                self.add("add {}, {}".format(a, b))
                math_list = math_list[1:]

            elif math_list[0][1] == "=":

                b = stack.pop()
                a = stack.pop()

                if a[0] == "NAME" and self.is_var(a[1]):
                    stack.append(("REGISTER", self.get_var(a[1]), -1, -1))
                    a = "{} {}".format(self.sys_prefix(), self.get_var(a[1]))

                elif a[0] == "REGISTER":
                    stack.append(("REGISTER", a[1], -1, -1))
                    a = a[1]

                    # Is this a pointer?
                    if a[0] == "[":
                        a = "{} {}".format(self.sys_prefix(), a)
                else:
                    self.error(62)

                if b[0] == "NAME" and self.is_var(b[1]):
                    b = self.get_var(b[1])
                elif b[0] == "STRING":
                    b = self.get_str(b[1])
                elif b[0] in ("REGISTER", "NUMBER"):
                    b = b[1]
                else:
                    self.error(63)

                if a.startswith(self.sys_prefix()) and not isinstance(b, int) and b[0] == "[":
                    self.add("mov {}, dword {}".format(self.c(), b))
                    b = self.c()

                self.add("mov {}, {}".format(a, b))
                math_list = math_list[1:]

            elif math_list[0][1] == "+=":
                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    a = self.get_var(a[1])
                    stack.append(("REGISTER", a, -1, -1))
                    a = "{} {}".format(self.sys_prefix(), a)

                elif a[0] == "REGISTER":
                    a = a[1]

                else:
                    self.error(23)

                if self.is_var(b[1]):
                    b = self.get_var(b[1])

                elif b[0] in ("REGISTER", "NUMBER"):
                    b = b[1]

                else:
                    self.error(24)

                if a.startswith(self.sys_prefix()) and not isinstance(b, int) and b[0] == "[":
                    self.add("mov {}, dword {}".format(self.a(), b))
                    b = self.a()

                self.add("add {}, {}".format(a, b))
                math_list = math_list[1:]

            elif math_list[0][1] == "/=":

                b = stack.pop()
                a = stack.pop()

                if self.is_var(a[1]):
                    self.add("mov {}, {}".format(self.a(), self.get_var(a[1])))

                elif a[0] == "NUMBER":
                    self.add("mov {}, {}".format(self.a(), a[1]))

                elif a[0] == "REGISTER":
                    if a[1] != self.a():
                        self.add("mov {}, {}".format(self.a(), a[1]))
                else:
                    self.error(2)

                if self.is_var(b[1]):
                    self.add("mov {}, {}".format(self.c(), self.get_var(b[1])))
                elif b[0] == "NUMBER":
                    self.add("mov {}, {}".format(self.c(), b[1]))
                elif b[0] == "REGISTER":
                    if b[1] != self.c():
                        self.add("mov {}, {}".format(self.c(), b[1]))
                else:
                    self.error(2)

                self.add("xor {}, {}".format(self.d(), self.d()))
                self.add("div {}".format(self.c()))
                math_list = math_list[1:]

            elif math_list[0][1] == ":" and math_list[1][1] == "?":

                c = stack.pop()
                b = stack.pop()
                a = stack.pop()

                if a[0] == "NAME" and self.is_var(a[1]):
                    a = self.get_var(a[1])
                elif a[0] in ("REGISTER", "NUMBER"):
                    a = a[1]
                else:
                    self.error(2)

                if b[0] == "NAME" and self.is_var(b[1]):
                    b = self.get_var(b[1])

                elif b[0] in ("REGISTER", "NUMBER"):
                    b = b[1]
                else:
                    self.error(2)

                if c[0] == "NAME" and self.is_var(c[1]):
                    c = self.get_var(c[1])
                elif c[0] in ("REGISTER", "NUMBER"):
                    c = c[1]
                else:
                    self.error(2)

                # a ? b :C

                mid = self.label()
                end = self.label()

                # a
                self.add("cmp {}, 0".format(a))
                self.add("jz {}".format(mid))

                # b
                self.add("mov {}, {}".format(self.a(), b))
                self.add("jmp {}".format(end))

                # c
                self.add("{}:".format(mid))
                self.add("mov {}, {}".format(self.a(), c))
                self.add("{}:".format(end))


                stack.append(("REGISTER", self.a(), -1, -1))
                math_list = math_list[2:]

            elif math_list[0][1] == ",":

                a = stack.pop()
                if self.is_var(a[1]):
                    a = "{} {}".format(self.sys_prefix(), self.get_var(a[1]))
                elif a[0] == "NUMBER":
                    a = "{} {}".format(self.sys_prefix(), a[1])
                elif a[0] == "REGISTER":
                    a = a[1]
                else:
                    self.error()

                # ,
                self.add("push {}".format(a))
                args += 1
                math_list = math_list[1:]

            else:
                print(stack)
                # Point to the right error information.
                self.inp = math_list
                self.error(4)

        # Add some space in the output code.
        #self.add()

        # Return the topmost item on the stack for statements.
        if stack:
            r = stack[-1]
        else:
            r = None

        return r

    # Builds a string vector and returns its memory location.
    def get_str(self, s):

        # Add a comment for debugging purposes.
        self.add("; string size {} @ [{}{}]".format(len(s)*self.word, self.bp(), self.var_l-(len(s)*self.word)))

        # Allocate space on the stack for the string vector.
        self.var_l -= len(s)*self.word
        self.add("sub {}, {}".format(self.sp(), len(s)*self.word))

        # Load the string onto the stack.
        for i in range(len(s)):
            self.add("mov {} [{}{}], {}".format(self.sys_prefix(), self.bp(), self.var_l+(i*4), s[i]))

        # Load the string pointer into register A.
        self.add("lea {}, [{}{}]".format(self.a(), self.bp(), self.var_l))

        # Return the location of the string.
        return self.a()

    # Returns the base pointer location of a variable.
    def get_var(self, var):

        if not self.is_var(var):
            a += 1

        # Find the location of the variable.
        if var in self.param.keys():
            return "[{}+{}]".format(self.bp(), self.param[var])
        elif var in self.var.keys():
            return "[{}{}]".format(self.bp(), self.var[var])
        elif var in self.extrn:
            return "{} [_{}]".format(self.sys_prefix(), var)
        else:
            self.error(10)

    # Checks to see if this is a variable.
    def is_var(self, var):
        if var in self.param.keys() or var in self.var.keys() or var in self.extrn:
            return True
        return False
