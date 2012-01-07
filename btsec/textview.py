'''
Created on Jan 3, 2012

@author: rob
'''

import pygtk
pygtk.require('2.0')
import gtk

class Terminal(object):
    
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Terminal")
        self.window.connect("destroy", lambda w: gtk.main_quit())
        
        table = gtk.Table(rows=2, columns=1, homogeneous=False)
        self.window.add(table)
        table.show()
        
        self.output = gtk.TextView()
        self.output.show()
        self.output_buffer = self.output.get_buffer()
        
        scroll = gtk.ScrolledWindow()
        scroll.add_with_viewport(self.output)
        scroll.show()
        table.attach(scroll, 0, 1, 0, 1)
        
        self.input = gtk.Entry()
        self.input.show()
        table.attach(self.input, 0, 1, 1, 2, yoptions=gtk.SHRINK)
        self.input.connect("activate", self.entry_activate, None)
        
        self.window.set_default_size(500, 200)
        self.window.show()
        
    def entry_activate(self, entry, data=None):
        end = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end, entry.get_text() + "\n")
        entry.set_text("")
        
def main():
    gtk.main()
    
if __name__ == "__main__":
    Terminal()
    main()