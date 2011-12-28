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


class Device(object):
    '''
    Wrapper for a bluetooth device connected to the bluetooth adapter.
    '''
    
    def __init__(self, hci_object_path):
        '''
        Initialize for the bt device at the given object path.
        '''
        obj = bus.get_object('org.bluez', hci_object_path)
        self.interface = dbus.Interface(obj, 'org.bluez.Device')
    
    address = DbusProperty('Address', read_only=True)
    name = DbusProperty('Name', read_only=True)
    vendor = DbusProperty('Vendor', read_only=True)
    product = DbusProperty('Product', read_only=True)
    version = DbusProperty('Version', read_only=True)
    icon = DbusProperty('Icon', read_only=True)
    device_class = DbusProperty('Class', read_only=True)
    uuids = DbusProperty('UUIDs', read_only=True)
    services = DbusProperty('Services', read_only=True)
    paired = DbusProperty('Paired', read_only=True)
    connected = DbusProperty('Connected', read_only=True)
    trusted = DbusProperty('Trusted', read_only=False)
    blocked = DbusProperty('Blocked', read_only=False)
    alias = DbusProperty('Alias', read_only=False)
    nodes = DbusProperty('Nodes', read_only=True)
    legacy_pairing = DbusProperty('LegacyPairing', read_only=True)

    
    
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
    uuids = DbusProperty('UUIDs', read_only=True)
    
    def get_devices(self):
        '''
        Get all devices associated with this adapter.
        '''
        return get_objects_from_property(Device, self.interface, 'Devices')
    

def get_adapters():
    '''
    Retrieve all connected bluetooth adapters
    '''
    return get_objects_from_property(Adapter, manager, 'Adapters')

def get_objects_from_property(klass, interface, prop_name):
    '''
    Construct instances of wrapper objects from dbus.
    The klass constructor is expected to only require a dbus object path.
    '''
    props = interface.GetProperties()
    paths = props[prop_name]
    res = []
    for path in paths:
        res.append(klass(path))
    return res

if __name__ == "__main__":
    print("Test")