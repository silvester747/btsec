'''
Interface for Bluetooth devices using dbus

@author: SeelfesteR
'''

import dbus
from axel import Event
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()

manager_obj = bus.get_object('org.bluez', '/')
manager = dbus.Interface(manager_obj, 'org.bluez.Manager')


class DbusProperty(object):
    '''
    Special property descriptor to handle dbus properties. Retrieves and sets
    the property by property name. Allows an option to set the property to 
    read-only.
    
    It is required that classes using this property descriptor have an interface
    attribute containing the dbus interface.
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


class DbusObjectWrapper(object):
    '''
    Generic wrapper for Dbus objects.
    '''
    
    def __init__(self, bus_name, object_path, dbus_interface):
        '''
        Initialize the interface to the wrapped dbus object.
        '''
        obj = bus.get_object(bus_name, object_path)
        self.interface = dbus.Interface(obj, dbus_interface)

    def __getattr__(self, name):
        '''
        For unknown attributes try to relay to dbus methods.
        '''
        return getattr(self.interface, name)
    


class Device(DbusObjectWrapper):
    '''
    Wrapper for a bluetooth device connected to the bluetooth adapter.
    '''
    
    def __init__(self, object_path):
        '''
        Initialize for the bt device at the given object path.
        '''
        super(Device, self).__init__('org.bluez', 
                                     object_path, 
                                     'org.bluez.Device')
    
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

    
    
class Adapter(DbusObjectWrapper):
    '''
    Wrapper for a bluetooth adapter.
    '''
    
    def __init__(self, object_path):
        '''
        Initialize for the hci device at the given object path.
        '''
        super(Adapter, self).__init__('org.bluez', 
                                      object_path, 
                                      'org.bluez.Adapter')
        self.interface.connect_to_signal('DeviceFound', self.__device_found)
        self.interface.connect_to_signal('DeviceDisappeared', self.__device_disappeared)
        self.interface.connect_to_signal('DeviceCreated', self.__device_created)
        self.interface.connect_to_signal('DeviceRemoved', self.__device_removed)
        
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

    device_found = Event()
    device_disappeared = Event()
    device_created = Event()
    device_removed = Event()
    
    def get_devices(self):
        '''
        Get all devices associated with this adapter.
        '''
        return get_objects_from_property(Device, self.interface, 'Devices')
    
    def __device_found(self, address, values):
        print("device_found: %s (%s)" % (address, values))
        self.device_found(address, values)
        
    def __device_disappeared(self, address):
        pass
    
    def __device_created(self, device):
        pass
    
    def __device_removed(self, device):
        pass

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