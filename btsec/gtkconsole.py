import __builtin__
import __main__
import codeop
import keyword
import re
import threading
import traceback
import sys
if sys.version[0] == '2':
    import pygtk
    pygtk.require("2.0")
import gtk

from axel import Event


class Completer:
    def __init__ (self, lokals):
        self.locals = lokals

        self.completions = keyword.kwlist + \
                            __builtin__.__dict__.keys() + \
                            __main__.__dict__.keys()
    def complete (self, text, state):
        if state == 0:
            if "." in text:
                self.matches = self.attr_matches (text)
            else:
                self.matches = self.global_matches (text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def update (self, locs):
        self.locals = locs

        for key in self.locals.keys ():
            if not key in self.completions:
                self.completions.append (key)

    def global_matches (self, text):
        matches = []
        n = len (text)
        for word in self.completions:
            if word[:n] == text:
                matches.append (word)
        return matches

    def attr_matches (self, text):
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return
        expr, attr = m.group(1, 3)

        obj = eval (expr, self.locals)
        words = dir(eval(expr, self.locals))
            
        matches = []
        n = len(attr)
        for word in words:
            if word[:n] == attr:
                matches.append ("%s.%s" % (expr, word))
        return matches

class GtkInterpreter (threading.Thread):
    """Run a gtk main() in a separate thread.
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback.
    """
    TIMEOUT = 100 # Millisecond interval between timeouts.
    
    def __init__ (self):
        threading.Thread.__init__ (self)
        self.ready = threading.Condition ()
        self.globs = globals ()
        self.locs = locals ()
        self._kill = 0
        self.cmd = ''       # Current code block
        self.new_cmds = []  # List of commands not yet added to the code
        
        self.out = OutputCatcher()
        sys.stdout = self.out
        
        self.completer = Completer (self.locs)

    def run (self):
        gtk.timeout_add (self.TIMEOUT, self.code_exec)
        try:
            if gtk.gtk_version[0] == 2:
                gtk.threads_init()
        except:
            pass        
        gtk.main ()

    def code_exec (self):
        """Execute waiting code.  Called every timeout period."""
        self.ready.acquire ()
        if self._kill: gtk.main_quit ()
        if len(self.new_cmds) > 0:  
            self.ready.notify ()  
            self.cmd = self.cmd + self.new_cmds[0]
            del self.new_cmds[0]
            try:
                code = codeop.compile_command (self.cmd[:-1]) 
                if code: 
                    self.cmd = ''
                    exec (code, self.globs, self.locs)
                    self.completer.update (self.locs)
            except Exception:
                traceback.print_exc ()
                self.cmd = ''  
                                    
        self.ready.release()
        return 1 
            
    def feed (self, code):
        """Feed a line of code to the thread.
        This function will block until the code checked by the GTK thread.
        Return true if executed the code.
        Returns false if deferring execution until complete block available.
        """
        if (not code) or (code[-1]<>'\n'): code = code +'\n' # raw_input strips newline
        self.completer.update (self.locs) 
        self.ready.acquire()
        self.new_cmds.append(code)
        self.ready.release ()
        
    def kill (self):
        """Kill the thread, returning when it has been shut down."""
        self.ready.acquire()
        self._kill=1
        self.ready.release()
        self.join()

class CodeLine(object):
    """
    Object containing code to run.
    """
    def __init__(self, code):
        # Code to run
        self.code = code
        
        # First line in the command
        self.first = self
        
        # Is this line complete? None means unknown
        self._incomplete = None
        
        # Has this line been run?
        self._finished = False
        
        # Error that has occurred while compiling. None if no errors.
        self._compile_error = None
        
        # Error that has occurred while running. None if no errors.
        self._exec_error = None
        
        # Next line of code
        self.next = None
    
    @property
    def incomplete(self):
        """
        Is this set of lines complete?
        """
        return self.first._incomplete
    
    @incomplete.setter
    def incomplete(self, value):
        self.first._incomplete = value
    
    @property
    def finished(self):
        """
        Has this set of lines run to completion?
        """
        
    def add_last(self, line):
        last = self
        while last.next:
            last = last.next
        last.next = line
        line.first = self.first
        
    def __iter__(self):
        return CodeLineIter(self.first)
    
    def __add__(self, other):
        self.add_last(other)
        return self
    
    def __iadd__(self, other):
        self.add_last(other)
        return self
    
    def get_full_command(self):
        cmd = ""
        for line in self:
            cmd += line.code
        
        return cmd

class CodeLineIter(object):
    """
    Special iterator to iterate over a set of code lines.
    """
    def __init__(self, line):
        self.line = line
    
    def next(self):
        return self.__next__()
    
    def __next__(self):
        if not self.line:
            raise StopIteration
        res = self.line
        self.line = self.line.next
        return res


class OutputCatcher(object):
    
    output_received = Event()        

    def write(self, data):
        self.output_received(data)
    
