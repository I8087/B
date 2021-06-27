from enum import Enum

class Error(Enum):

    # Redfined errors.
    REDFINED_VAR = 301
    REDFINED_FUNC = 302

    # Outside errors.
    RETURN_OUTSIDE_FUNC = 303
    BREAK_OUTSIDE_LOOP = 304
    NEXT_OUTSIDE_LOOP = 305

    # Expected errors.
    EXPECT_SC = 306
    EXPECT_COMMA = 307
    EXPECT_SP = 308
    EXPECT_EP = 309

    def __init__(self, *args):
        self.err_msg = {301: "Redefined existing variable!",
                        302: "Redefined existing function!",
                        303: "Cannot return outside of a function!",
                        304: "Cannot break outside of a loop!",
                        305: "Cannot next outside of a loop!",
                        306: "Expected a semicolon!",
                        307: "Expected a comma!"}

    def __int__(self):
        return self.value

    def __str__(self):
        if self.value in self.err_msg:
            return self.err_msg[self.value]
        else:
            return "An unknown error has occured!"
