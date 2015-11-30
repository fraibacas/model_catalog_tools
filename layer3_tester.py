
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit

from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp
from Products.Zuul.catalog.interfaces import IModelCatalogTool

from zenoss.modelindex.searcher import SearchParams
from zenoss.modelindex.exceptions import SearchException

from utils import get_networks, get_all_devices

class Layer3Tester(object):
    """
    Does a search similar to the one done in getChildLinks:
    https://github.com/zenoss/zenoss-prodbin/blob/develop/Products/ZenModel/LinkManager.py#L342
    and compares results between model_catalog and layer_3 catalog
    """

    def validate_devices_in_networks(self):
        """
        Get deviceId's of every network using both catalogs and compare results
        Network -> Devices
        """
        networks = get_networks(dmd)
        layer3_catalog = dmd.ZenLinkManager.layer3_catalog
        model_catalog = IModelCatalogTool(dmd)
        failed_networks = {}
        for network in networks:
            # Devices under device class in global catalog
            query = Eq('networkId', network)
            layer3_brains = layer3_catalog.evalAdvancedQuery(query)
            layer3_device_ids = set([ brain.deviceId for brain in layer3_brains if brain.deviceId ])

            model_catalog_brains = model_catalog.search(query=query)
            model_catalog_device_ids = set([ brain.deviceId.split("/")[-1] for brain in model_catalog_brains.results if brain.deviceId ])

            if not len(layer3_device_ids - model_catalog_device_ids) == len(model_catalog_device_ids - layer3_device_ids) == 0:
                #import pdb; pdb.set_trace()
                failed_networks[network] = (layer3_device_ids, model_catalog_device_ids)
        if failed_networks:
            print "TEST FAILED: Catalogs return different devices for the following networks:"
            print "\t\t{0}".format(failed_networks.keys())
        else:
            print "TEST PASSED: Both catalogs returned the same devices for all networks."

        return len(failed_networks) == 0

    def validate_ips_and_networks_for_device(self):
        """
        for every device, get the ips and networks
        Device -> Ip Addresses
        Device -> Network
        """
        layer3_catalog = dmd.ZenLinkManager.layer3_catalog
        model_catalog = IModelCatalogTool(dmd)
        failed_devices = []
        for device in get_all_devices(dmd):
            l3_query = Eq('deviceId', device.id)
            layer3_brains = layer3_catalog.evalAdvancedQuery(l3_query)
            layer3_ips = set([ brain.ipAddressId for brain in layer3_brains if brain.ipAddressId ])
            layer3_nets = set([ brain.networkId for brain in layer3_brains if brain.networkId ])

            model_catalog_query = And(Eq('deviceId', "*{0}".format(device.id)), Eq('meta_type', "IpAddress"))
            search_results = model_catalog.search(query=model_catalog_query)
            model_catalog_brains = [ brain for brain in search_results.results ]
            model_catalog_ips = set([ brain.ipAddressId for brain in model_catalog_brains if brain.ipAddressId ])
            model_catalog_nets = set([ brain.networkId for brain in model_catalog_brains if brain.networkId ])

            if not (len(layer3_ips - model_catalog_ips) == len(model_catalog_ips- layer3_ips) == 0 and \
               len(layer3_nets - model_catalog_nets) == len(model_catalog_nets- layer3_nets) == 0) :
                failed_devices.append(device)

        if failed_devices:
            print "TEST FAILED: Catalogs return different ip addresses for the following devices:"
            for dev in failed_devices:
                print "\t\t{0}".format(dev.getPrimaryId())
        else:
            print "TEST PASSED: Both catalogs returned the same ips for every device."
        return len(failed_devices) == 0


    def run(self):
        return self.validate_devices_in_networks() and self.validate_ips_and_networks_for_device()

def main():
    success = Layer3Tester().run()
    print "\n============================="
    if success:
        print "  TEST PASSED"
    else:
        print "  TEST FAILED"
    print "============================="



if __name__ == '__main__':
    main()