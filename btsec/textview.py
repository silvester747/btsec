'''
Created on Jan 3, 2012

@author: rob
'''

import pygtk
pygtk.require('2.0')
import gtk

from btsec.gtkconsole import GtkInterpreter

class Terminal(object):
    
    def __init__(self):
        self.command_history = []
        
        self.interpreter = GtkInterpreter()
        self.interpreter.out.output_received += self.interpreter_out
        self.interpreter.start()
        self.interpreter.command_created += self.command_created
        self.interpreter.command_updated += self.command_updated

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Terminal")
        self.window.connect("destroy", lambda w: gtk.main_quit())
        
        table = gtk.Table(rows=2, columns=1, homogeneous=False)
        self.window.add(table)
        table.show()
        
        self.output = gtk.TextView()
        self.output.set_editable(False)
        self.output.set_wrap_mode(gtk.WRAP_WORD_CHAR)
        self.output.show()
        self.output_buffer = self.output.get_buffer()
        
        self.tag_code_complete = self.output_buffer.create_tag("code_complete",
                                                               foreground="#00AA00")
        self.tag_code_incomplete = self.output_buffer.create_tag("code_incomplete",
                                                                 foreground="#000000")
        self.tag_code_error = self.output_buffer.create_tag("code_error",
                                                            foreground="#AA0000")
        self.tag_error_trace = self.output_buffer.create_tag("error_trace",
                                                             foreground="#AA0000",
                                                             left_margin=10)
        self.tag_stdout = self.output_buffer.create_tag("stdout",
                                                        foreground="#000000",
                                                        editable=False,
                                                        left_margin=10,
                                                        wrap_mode=gtk.WRAP_WORD_CHAR)
        
        
        scroll = gtk.ScrolledWindow()
        scroll.add_with_viewport(self.output)
        scroll.show()
        table.attach(scroll, 0, 1, 0, 1)
        
        self.input = gtk.Entry()
        self.input.show()
        table.attach(self.input, 0, 1, 1, 2, yoptions=gtk.SHRINK)
        self.input.connect("activate", self.entry_activate, None)
        self.input.connect("key-press-event", self._input_key_press_event)
        
        self._history_index = 0
        
        self.window.set_default_size(500, 400)
        self.window.show()

        
    def entry_activate(self, entry, data=None):
        
        self.interpreter.feed(entry.get_text())
        
        #end = self.output_buffer.get_end_iter()
        #self.output_buffer.insert(end, entry.get_text() + "\n")
        entry.set_text("")
        self._history_index = 0
        
    def interpreter_out(self, data):
        end = self.output_buffer.get_end_iter()
        self.output_buffer.insert_with_tags(end, data, self.tag_stdout)
        
    def command_created(self, command):
        self.command_history.append(command)
        self._update_command_text(command)
        
    def command_updated(self, command):
        self._update_command_text(command)

    def _input_key_press_event(self, widget, event):
        #print(event.keyval)
        if event.keyval == 65362: # code for up arrow
            self._show_input_history(+1)
            return True
        if event.keyval == 65364: # code for down arrow
            self._show_input_history(-1)
            return True
        return False
            
    def _show_input_history(self, delta):
        self._history_index += delta
        if self._history_index < 0:
            self._history_index = 0
        elif self._history_index > len(self.command_history):
            self._history_index = len(self.command_history)
        
        if self._history_index == 0:
            self.input.set_text("")
        else:
            self.input.set_text(self.command_history[0 - self._history_index].command)
    
    def _update_command_text(self, command):
        """
        Make sure the text is shown for the command.
        """
        
        # If marks present, remove all text
        # Use original start mark to insert text again
        # If no marks present, start at the end of the buffer
        # After insertion store end mark
        
        start = None
        if hasattr(command, 'start_mark'):
            start = self.output_buffer.get_iter_at_mark(command.start_mark)
            end = self.output_buffer.get_iter_at_mark(command.end_mark)
            self.output_buffer.delete(start, end)
            self.output_buffer.delete_mark(command.end_mark)
            # start and end should be reinitialised now by delete
        else:
            start = self.output_buffer.get_end_iter()
            command.start_mark = self.output_buffer.create_mark(None, start, left_gravity=True)
            
        tag = self.tag_code_incomplete
        if command.finished:
            tag = self.tag_code_complete
        if command.compile_error or command.exec_error:
            tag = self.tag_code_error
        self.output_buffer.insert_with_tags(start, command.command, tag)
        
        if command.compile_error:
            self.output_buffer.insert_with_tags(start, 
                                                "%s: %s\n" % (command.compile_error.__class__.__name__,
                                                               command.compile_error.message) , 
                                                self.tag_error_trace)
        if command.exec_error:
            self.output_buffer.insert_with_tags(start, 
                                                "%s: %s\n" % (command.exec_error.__class__.__name__,
                                                               command.exec_error.message), 
                                                self.tag_error_trace)
        
        command.end_mark = self.output_buffer.create_mark(None, start, left_gravity=True)
        
        
if __name__ == "__main__":
    t = Terminal()
