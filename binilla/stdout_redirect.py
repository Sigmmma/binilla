'''
This module serves as a way to redirect stdout to multiple targets.

This is useful for the console Window in Binilla as it is supposed mirror
stdout.

Best imported before anything else.
'''

# I'm hacky!

import sys

stdout_targets = dict()

buffer_output = False
stored_stdout = ""

real_stdout_write = sys.stdout.write

def stdout_write_wrapper(s, *a, **kw):
    '''Internal. Wraps stdout's print so we can print to multiple outputs'''
    global stdout_targets
    global stored_stdout

    # Write the output to the actual stdout.
    # Do this first because this is mighty important and we don't want to lose
    # anything.
    real_stdout_write(s, *a, **kw)

    # If we need to buffer output we should add it to out buffer string.
    # This code can actually be called before the initialization of the value.
    # So we check against None to be safe.
    if buffer_output:
        if stored_stdout is None:
            stored_stdout = s
        else:
            stored_stdout += s
    # Now we write to all the file streams that we want to copy to.
    for k in stdout_targets:
        stdout_targets[k].write(s)


sys.stdout.write = stdout_write_wrapper

def start_storing_output():
    '''Start storing output for later flushing.'''
    global buffer_output
    buffer_output = True

def flush_buffered_output():
    '''
    Flush the stored output into our targets excluding stdout, as it should
    already be in stdout.
    '''
    global buffer_output
    global stored_stdout
    global stdout_targets

    # Stop buffering
    buffer_output = False
    # Print the buffered output to all targets.
    for k in stdout_targets:
        stdout_targets[k].write(stored_stdout)
        stdout_targets[k].flush()

    # Empty buffer because this info is old now.
    stored_stdout = ""

def add_stdout_target(name, stream):
    '''
    Adds a target to copy new stdout prints to.
    '''
    global stdout_targets
    stdout_targets[name] = stream

def del_stdout_target(name):
    '''
    Makes it so we stop copying stdout to the given target name.
    '''
    global stdout_targets
    if name in stdout_targets:
        del stdout_targets[name]
