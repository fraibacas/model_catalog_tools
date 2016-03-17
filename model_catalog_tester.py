
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

from collections import defaultdict
from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp, MatchGlob
from Products.Zuul.catalog.interfaces import IModelCatalogTool, IPathReporter
from zenoss.modelindex.model_index import SearchParams

import time

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ModelCatalogHelper(object):

    def __init__(self):
        self.model_catalog = IModelCatalogTool(dmd)

    def get_device_classes(self, return_paths=True):
        query = Eq("objectImplements", "Products.ZenModel.DeviceClass.DeviceClass")
        search_response = self.model_catalog.search(query=query)
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_devices_path_for_device_class(self, dc_path, return_paths=True):
        query =  [ Eq("objectImplements", "Products.ZenModel.Device.Device") ]
        query.append(MatchGlob("path", "{0}/devices/*".format(dc_path)))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_device_components(self, device, return_paths=True):
        """ """
        if not isinstance(device, basestring):
            device = "/".join(device.getPrimaryPath())
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.DeviceComponent.DeviceComponent"))
        query.append(Eq("deviceId", device))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_device_ipInterfaces(self, device, return_paths=True):
        """ """
        if not isinstance(device, basestring):
            device = "/".join(device.getPrimaryPath())
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.IpInterface.IpInterface"))
        query.append(Eq("meta_type", "IpInterface"))
        query.append(Eq("deviceId", device))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_networks(self, return_paths=True):
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.IpNetwork.IpNetwork"))
        query.append( Or( MatchGlob("uid", "/zport/dmd/Networks/*"), MatchGlob("uid", "/zport/dmd/IPv6Networks/*") ) )
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_device_ipaddresses(self, device, return_paths=True):
        if not isinstance(device, basestring):
            device = "/".join(device.getPrimaryPath())
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.IpAddress.IpAddress"))
        query.append(Eq("meta_type", "IpAddress"))
        query.append(Eq("deviceId", device))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_device_processes(self, device, return_paths=True):
        if not isinstance(device, basestring):
            device = "/".join(device.getPrimaryPath())
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.OSProcess.OSProcess"))
        query.append(MatchGlob("path", "{0}*".format(device)))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results        

    def get_doc_by_uid(self, uid):
        if not isinstance(uid, basestring):
            uid = "/".join(uid.getPrimaryPath())
        query = 'uid:"{0}"'.format(uid)
        search_response = self.model_catalog.search(query=query)
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_network_ips(self, net, return_paths=True):
        if not isinstance(net, basestring):
            net = "/".join(net.getPrimaryPath())
        query = []
        query.append(Eq("objectImplements", "Products.ZenModel.IpAddress.IpAddress"))
        query.append(Eq("networkId", net))
        search_response = self.model_catalog.search(query=And(*query))
        results = search_response.results
        if return_paths:
            results = [ brain.getPath() for brain in results ]
        return results

    def get_object_paths(self, obj):
        paths = []
        if not isinstance(obj, basestring):
            obj = "/".join(obj.getPrimaryPath())
        search_response = self.model_catalog.search(query=Eq("uid", obj))
        if search_response.total == 1:
            brain = next(search_response.results)
            if brain.path is not None:
                paths = brain.path
        else:
            paths = [ "found more than 1 uid for {0}".format(obj) ]
        return paths


class ZodbHelper(object):

    def __init__(self, _dmd):
        self.dmd = _dmd

    def ppath(self, obj):
        return "/".join(obj.getPrimaryPath())

    def ppaths(self, objs):
        return [ self.ppath(obj) for obj in objs ]

    def get_all_devices(self):
        return dmd.Devices.getSubDevices_recursive()

    def get_all_device_classes_path(self):
        prefix = '/'.join(self.dmd.Devices.getPrimaryPath())
        return [ "{0}{1}".format(prefix, dc).rstrip('/') for dc in self.dmd.Devices.getPeerDeviceClassNames() ]

    def get_devices_path_for_device_class(self, dc_path):
        """ returns all devices right in dc_path """
        dc_object = dmd.unrestrictedTraverse(dc_path)
        return self.ppaths(dc_object.getDevices())

    def get_device_components(self, device):
        """ """
        return device.getDeviceComponentsNoIndexGen()

    def get_device_components_path(self, device):
        return self.ppaths(self.get_device_components(device))


MODEL_CATALOG_HELPER = ModelCatalogHelper()


ZODB_HELPER = ZodbHelper(dmd)


class BaseValidator(object):

    def validate_result_sets(self, set1, set2):
        """
        given two sets check both sets contain the same elements
        return tuple (boolean indicating sets are equal, elements in set 1 and not in set 2, elements in set 2 and not in set 1)
        """
        in_set1_and_not_in_set2 = set1 - set2
        in_set2_and_not_in_set1 = set2 - set1
        success = len(in_set1_and_not_in_set2) == len(in_set2_and_not_in_set1) == 0
        return (success, in_set1_and_not_in_set2, in_set2_and_not_in_set1)

    def print_results(self, success, not_in_catalog, not_in_zodb, inconsistent=None):
        """ """
        if success:
            print "\t{0}STEP PASSED{1}: Model Catalog is consistent!".format(BColors.OKGREEN, BColors.ENDC)
        else:
            print "\t{0}STEP FAILED{1}: Model Catalog is not consistent.".format(BColors.FAIL, BColors.ENDC)
            if not_in_catalog:
                print "\t\t Items not found in catalog:"
                if isinstance(not_in_catalog, list):
                    for item in not_in_catalog:
                        print "\t\t\t{0}".format(item)
                elif isinstance(not_in_catalog, dict):
                    for item, values in not_in_catalog.iteritems():
                        if values:
                            print "\t\t\t{0}: {1}".format(item, values)
            if not_in_zodb:
                print "\t\t Items not found in zodb:"
                if isinstance(not_in_catalog, list) or isinstance(not_in_catalog, set):
                    for item in not_in_zodb:
                        print "\t\t\t{0}".format(item)
                elif isinstance(not_in_catalog, dict):
                    for item, values in not_in_zodb.iteritems():
                        if values:
                            print "\t\t\t{0}: {1}".format(item, values)
            if inconsistent:
                print "\t\t Items found in catalog with inconsistent information:"
                if isinstance(not_in_catalog, list):
                    for item in inconsistent:
                        print "\t\t\t{0}".format(item)
                elif isinstance(not_in_catalog, dict):
                    for item, values in inconsistent.iteritems():
                        if values:
                            print "\t\t\t{0}: {1}".format(item, values)

    def validate_paths(self, objects):
        """ Given an object checks that the object paths are properly indexed """
        success = True
        paths_not_in_zodb = {}
        paths_not_in_catalog = {}
        for obj in objects:
            zodb_paths = set( [ "/".join(path) for path in IPathReporter(obj).getPaths() ] )
            indexed_paths = set(MODEL_CATALOG_HELPER.get_object_paths(obj))
            ok, not_in_catalog, not_in_zodb =  self.validate_result_sets(zodb_paths, indexed_paths)
            if not ok:
                success = False
                obj_path = ZODB_HELPER.ppath(obj)
                paths_not_in_catalog[obj_path] = not_in_catalog
                paths_not_in_zodb[obj_path] = not_in_zodb

        self.print_results(success, paths_not_in_catalog, paths_not_in_zodb)

    def run(self):
        raise NotImplementedError


class DeviceClassValidator(BaseValidator):
    """
    Check that all device classes are indexed in model catalog and that 
    each device class has the same devices in both zodb and model_catalog
    """

    def __init__(self):
        self.device_classes = ZODB_HELPER.get_all_device_classes_path()

    def validate_device_classes(self):
        """ """
        print "\nValidating Device Classes..."
        device_classes = set(self.device_classes)
        indexed_device_classes = set(MODEL_CATALOG_HELPER.get_device_classes())
        success, not_in_catalog, not_in_zodb =  self.validate_result_sets(device_classes, indexed_device_classes)
        self.print_results(success, not_in_catalog, not_in_zodb)

        return success

    def validate_devices(self):
        """ All devices must be found in the catalog under the same device class """
        success = True
        print "\nValidating Device Classes' Devices..."
        devices_not_in_zodb = []
        devices_not_in_catalog = []
        for device_class in self.device_classes:
            zodb_devices = set(ZODB_HELPER.get_devices_path_for_device_class(device_class))
            catalog_devices = set(MODEL_CATALOG_HELPER.get_devices_path_for_device_class(device_class))
            ok, not_in_catalog, not_in_zodb =  self.validate_result_sets(zodb_devices, catalog_devices)
            if not ok:
                success = False
                if not_in_catalog:
                    devices_not_in_catalog.extend(not_in_catalog)
                if not_in_zodb:
                    devices_not_in_zodb.extend(not_in_zodb)
        self.print_results(success, devices_not_in_catalog, devices_not_in_zodb)

        return success

    def run(self):
        self.validate_device_classes()
        self.validate_devices()


class DeviceValidator(BaseValidator):
    """ """

    def __init__(self):
        self.devices = {}
        self.ipinterfaces = defaultdict(list)
        self.ipaddresses = defaultdict(list)
        self.components = defaultdict(list)
        for device in ZODB_HELPER.get_all_devices():
            path = ZODB_HELPER.ppath(device)
            self.devices[path] = device
            self.ipinterfaces[path] = device.os.interfaces()
            for iface in self.ipinterfaces[path]:
                self.ipaddresses[path].extend(iface.ipaddresses())
            self.components[path].extend( list(device.getDeviceComponentsNoIndexGen()) )

    def validate_device_components(self, device):
        """ """
        device_path = ZODB_HELPER.ppath(device)
        components = set( [ ZODB_HELPER.ppath(component) for component in self.components[device_path] ] )
        indexed_components = set(MODEL_CATALOG_HELPER.get_device_components(ZODB_HELPER.ppath(device)))
        success, not_in_catalog, not_in_zodb =  self.validate_result_sets(components, indexed_components)

        return (success, not_in_catalog, not_in_zodb)

    def validate_devices_components(self):
        """ Check that all device components are indexed in model catalog """

        print "\nValidating Devices' components ..."
        success = True
        components_not_in_catalog = {}
        components_not_in_zodb = {}

        for device in self.devices.values():
            ok, not_in_catalog, not_in_zodb = self.validate_device_components(device)
            if not ok:
                success = False
                device_path = ZODB_HELPER.ppath(device)
                if not_in_catalog:
                    components_not_in_catalog[device_path] = not_in_catalog
                if not_in_zodb:
                    components_not_in_zodb[device_path] = not_in_zodb

        self.print_results(success, components_not_in_catalog, components_not_in_zodb)

    def validate_device_components_paths(self):

        print "\nValidating Devices' Components' paths ..."
        all_components = []
        for comps in self.components.values():
            all_components.extend(comps)
        return self.validate_paths(all_components)

    def validate_device_ipInterfaces(self, device):

        device_path = ZODB_HELPER.ppath(device)
        ip_interfaces = self.ipinterfaces[device_path]
        brains = MODEL_CATALOG_HELPER.get_device_ipInterfaces(device, return_paths=False)

        indexed_ifaces_brains = {}
        for brain in brains:
            indexed_ifaces_brains[brain.getPath()] = brain

        # Lets first check we have the same interfaces
        ifaces_paths = set([ ZODB_HELPER.ppath(iface) for iface in ip_interfaces ])
        indexed_ifaces_paths = set( indexed_ifaces_brains.keys() )

        success, not_in_catalog, not_in_zodb = self.validate_result_sets(ifaces_paths, indexed_ifaces_paths)

        inconsistent_interfaces = set()

        # Now that for each ipInterface, lets check macaddres, and lan_id
        for iface in ip_interfaces:
            ok = True
            path = ZODB_HELPER.ppath(iface)
            if path not in indexed_ifaces_brains:
                continue
            brain = indexed_ifaces_brains[path]
            # check mac
            if not iface.macaddress: # it may return ""
                iface.macaddress = None
            if iface.macaddress!=brain.macaddress:
                ok = False
            # check lan_id
            iface_lanId = iface.lanId()
            if not iface_lanId or iface_lanId=="None":
                iface_lanId = None
            if iface_lanId!=brain.lanId:
                ok = False
            if not ok:
                inconsistent_interfaces.add(path)

        success = len(not_in_catalog) == len(not_in_zodb) == len(inconsistent_interfaces) == 0
        return (success, not_in_catalog, not_in_zodb, inconsistent_interfaces)

    def validate_ipInterfaces(self):
        """ Check all IpInterfaces have been properly indexed """
        print "\nValidating Devices' IpInterfaces ..."
        success = True
        interfaces_not_in_catalog = {}
        interfaces_not_in_zodb = {}
        inconsistent_interfaces = {}
        for device in self.devices.values():
            ok, not_in_catalog, not_in_zodb, inconsistent = self.validate_device_ipInterfaces(device)
            if not ok:
                success = False
                path = ZODB_HELPER.ppath(device)
                interfaces_not_in_catalog[path] = not_in_catalog
                interfaces_not_in_zodb[path] = not_in_zodb
                inconsistent_interfaces[path] = inconsistent

        self.print_results(success, interfaces_not_in_catalog, interfaces_not_in_zodb, inconsistent_interfaces)

    def validate_ipAddresses(self):
        """ """
        print "\nValidating Devices' IpAddresses ..."
        success = True
        ips_not_in_catalog = {}
        ips_not_in_zodb = {}
        for device, ips in self.ipaddresses.iteritems():
            ips_paths = set([ ZODB_HELPER.ppath(iface) for iface in ips ])
            indexed_ips_paths = set(MODEL_CATALOG_HELPER.get_device_ipaddresses(device))
            ok, not_in_catalog, not_in_zodb = self.validate_result_sets(ips_paths, indexed_ips_paths)
            if not ok:
                success = False
                ips_not_in_catalog[device] = not_in_catalog
                ips_not_in_zodb[device] = not_in_zodb

        self.print_results(success, ips_not_in_catalog, ips_not_in_zodb)


    def validate_ip_services(self):
        """ """
        print "\nValidating Devices' Ip Services ...    NOT IMPLEMENTED"

    def validate_os_processes(self):
        """ """
        print "\nValidating Devices' OsProcesses ..."
        success = True
        processes_not_in_catalog = {}
        processes_not_in_zodb = {}
        for device_path, device in self.devices.iteritems():
            processes_paths = set([ ZODB_HELPER.ppath(process) for process in device.os.processes() ])
            indexed_processes_paths = set(MODEL_CATALOG_HELPER.get_device_processes(device))
            ok, not_in_catalog, not_in_zodb = self.validate_result_sets(processes_paths, indexed_processes_paths)
            if not ok:
                success = False
                if not_in_catalog:
                    processes_not_in_catalog[device_path] = not_in_catalog
                if not_in_zodb:
                    processes_not_in_zodb[device_path] = not_in_zodb

        self.print_results(success, processes_not_in_catalog, processes_not_in_zodb)


    def validate_device_paths(self):
        print "\nValidating Devices' paths..."
        return self.validate_paths(self.devices.values())

    def run(self):
        self.validate_devices_components()
        self.validate_device_components_paths()
        self.validate_ipInterfaces()
        self.validate_ipAddresses()
        self.validate_device_paths()
        self.validate_os_processes()
        self.validate_ip_services()


class NetworkValidator(BaseValidator):

    def __init__(self):
        networks = dmd.Networks.getSubNetworks()
        networks.extend(dmd.IPv6Networks.getSubNetworks())

        self.networks = { ZODB_HELPER.ppath(net):net for net in networks }
        self.ips = { ZODB_HELPER.ppath(net):net.ipaddresses() for net in networks }

    def validate_networks(self):
        """ All networks should be indexed in solr """
        print "\nValidating Networks..."
        nets_paths = set(self.networks.keys())
        indexed_nets_paths = set(MODEL_CATALOG_HELPER.get_networks())
        success, not_in_catalog, not_in_zodb =  self.validate_result_sets(nets_paths, indexed_nets_paths)
        self.print_results(success, not_in_catalog, not_in_zodb)
        return success

    def validate_ipAddresses(self):
        """ This is expensive """
        print "\nValidating Networks' IpAddresses..."
        ips_not_in_catalog = []
        ips_not_in_zodb = []
        inconsistent_ips = []

        for net in self.networks.keys():
            ips = { ZODB_HELPER.ppath(ip): ip for ip in self.ips[net] }
            indexed_ips = { brain.getPath(): brain for brain in MODEL_CATALOG_HELPER.get_network_ips(net, return_paths=False) }
            ok, not_in_catalog, not_in_zodb =  self.validate_result_sets(set(ips.keys()), set(indexed_ips.keys()))

            if not ok:
                ips_not_in_catalog.extend(not_in_catalog)
                ips_not_in_zodb.extend(not_in_zodb)

            for ip_path, ip in ips.iteritems():
                indexed_ip = indexed_ips.get(ip_path)
                if not indexed_ip:
                    continue
                
                device_path = ZODB_HELPER.ppath(ip.device()) if ip.device() else None
                interface_path = ZODB_HELPER.ppath(ip.interface()) if ip.interface() else None
                if device_path!=indexed_ip.deviceId or interface_path!=indexed_ip.interfaceId:
                    inconsistent_ips.append(ip_path)

        success = len(ips_not_in_catalog) == len(ips_not_in_zodb) == len(inconsistent_ips) == 0
        self.print_results(success, ips_not_in_catalog, ips_not_in_zodb, inconsistent_ips)

        return success

    def validate_ipaddresses_paths(self):
        print "\nValidating IpAddresses' paths..."
        all_ips = []
        for ip in self.ips.values():
            all_ips.extend(ip)
        return self.validate_paths(all_ips)

    def run(self):
        self.validate_networks()
        self.validate_ipAddresses()
        self.validate_ipaddresses_paths()


class ModelCatalogValidator(object):

    def __init__(self):
        self.validators = []
        self.validators.append(DeviceClassValidator())
        self.validators.append(DeviceValidator())
        self.validators.append(NetworkValidator())

    def run(self):
        for validator in self.validators:
            validator.run()


def main():
    
    start = time.time()
    ModelCatalogValidator().run()
    print "\nTest took {0} seconds.\n".format(time.time() - start)


if __name__ == '__main__':
    main()
