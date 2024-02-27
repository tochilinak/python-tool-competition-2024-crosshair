import z3
import time
import traceback
import sys


def get_wrapped_check(original_check):

    def wrapped_check(self, *args, **kwargs):
        print("check started...")
        start = time.time()
        result = original_check(self, *args, **kwargs)
        print("check finished in", time.time() - start)
        traceback.print_stack(file=sys.stdout)
        print("--------------")
        return result

    return wrapped_check


wrapped_check = get_wrapped_check(z3.Solver.check)
z3.Solver.check = wrapped_check


from crosshair.statespace import StateSpace

old_init = StateSpace.__init__

def new_init(self, *args, **kwargs):
    old_init(self, *args, **kwargs)
    self.solver.set("timeout", 100)


import crosshair.statespace

crosshair.statespace.StateSpace.__init__ = new_init
