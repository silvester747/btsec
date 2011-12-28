'''
Interface for Bluetooth devices using dbus

@author: rob
'''

import dbus

bus = dbus.SystemBus()

manager_obj = bus.get_object('org.bluez', '/')
manager = dbus.Interface(manager_obj, 'org.bluez.Manager')

class DbusProperty(object):
    '''
    Special property descriptor to handle dbus properties. Retrieves and sets
    the property by property name. Allows an option to set the property to 
    read-only.
    '''

    def __init__(self, name, read_only=False):
        self.name = name
        self.read_only = read_only
        
    def __get__(self, instance, owner):
        props = instance.interface.GetProperties()
        if not self.name in props:
            raise AttributeError("Property currently not available.")
        return props[self.name]
    
    def __set__(self, instance, value):
        if self.read_only:
            raise AttributeError("Property is read-only!")
        instance.interface.SetProperty(self.name, value)
    
    
class Adapter(object):
    '''
    Wrapper for a bluetooth adapter.
    '''
    
    def __init__(self, hci_object_path):
        '''
        Initialize for the hci device at the given object path.
        '''
        obj = bus.get_object('org.bluez', hci_object_path)
        self.interface = dbus.Interface(obj, 'org.bluez.Adapter')
        
    address = DbusProperty('Address', read_only=True)
    name = DbusProperty('Name', read_only=False)
    device_class = DbusProperty('Class', read_only=True)
    powered = DbusProperty('Powered', read_only=False)
    discoverable = DbusProperty('Discoverable', read_only=False)
    pairable = DbusProperty('Pairable', read_only=False)
    pairable_timeout = DbusProperty('PairableTimeout', read_only=False)
    discoverable_timeout = DbusProperty('DiscoverableTimeout', read_only=False)
    discovering = DbusProperty('Discovering', read_only=True)
    devices = DbusProperty('Devices', read_only=True)
    uuids = DbusProperty('UUIDs', read_only=True)
    

def get_adapters():
    '''
    Retrieve all connected bluetooth adapters
    '''
    props = manager.GetProperties()
    adapter_paths = props['Adapters']
    adapters = []
    for path in adapter_paths:
        adapters.append(Adapter(path))
    return adapters
    

if __name__ == "__main__":
    print("Test")