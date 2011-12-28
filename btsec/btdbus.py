'''
Interface for Bluetooth devices using dbus

@author: rob
'''

import dbus

bus = dbus.SystemBus()

manager_obj = bus.get_object('org.bluez', '/')
manager = dbus.Interface(manager_obj, 'org.bluez.Manager')

class Adapter(object):
    def __init__(self, hci_object_path):
        obj = bus.get_object('org.bluez', hci_object_path)
        self.interface = dbus.Interface(obj, 'org.bluez.Adapter')

def get_adapters():
    props = manager.GetProperties()
    adapter_paths = props['Adapters']
    adapters = []
    for path in adapter_paths:
        adapters.append(Adapter(path))
    return adapters
    

if __name__ == "__main__":
    print("Test")