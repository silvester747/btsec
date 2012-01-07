import __builtin__
import __main__
import codeop
import keyword
import re
import readline
import threading
import traceback
import signal
import sys
import string
if sys.version[0] == '2':
    import pygtk
    pygtk.require("2.0")
import gtk

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
        self.new_cmd = None # Waiting line of code, or None if none waiting

        self.completer = Completer (self.locs)
        readline.set_completer (self.completer.complete)
        readline.parse_and_bind ('tab: complete')

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
        if self.new_cmd != None:  
            self.ready.notify ()  
            self.cmd = self.cmd + self.new_cmd
            self.new_cmd = None
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
        self.new_cmd = code
        self.ready.wait ()  # Wait until processed in timeout interval
        self.ready.release ()
        
        return not self.cmd

    def kill (self):
        """Kill the thread, returning when it has been shut down."""
        self.ready.acquire()
        self._kill=1
        self.ready.release()
        self.join()
        
# Read user input in a loop, and send each line to the interpreter thread.

def signal_handler (*args):
    print "SIGNAL:", args
    sys.exit()

def run():
    signal.signal (signal.SIGINT, signal_handler)
    signal.signal (signal.SIGSEGV, signal_handler)
    
    prompt = '>>> '
    interpreter = GtkInterpreter ()
    interpreter.start ()
    interpreter.feed ("import gtk")
    interpreter.feed ("sys.path.append('.')")
    if len (sys.argv) > 1:
        for line in open (sys.argv[1]).readlines ():
            interpreter.feed (line)
    print 'Interactive GTK Shell'
    py_version = string.join(map(str, sys.version_info[:3]), '.')
    pygtk_version = string.join(map(str, gtk.pygtk_version), '.')
    gtk_version = string.join(map(str, gtk.gtk_version), '.')
    print 'Python %s, Pygtk %s, GTK+ %s' % (py_version, pygtk_version,
           gtk_version)

    try:
        while 1:
            command = raw_input (prompt) + '\n' # raw_input strips newlines
            prompt = interpreter.feed (command) and '>>> ' or '... '
    except (EOFError, KeyboardInterrupt): pass

    interpreter.kill()
    print

if __name__=="__main__":
    run()
