
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp
from Products.Zuul.catalog.interfaces import IModelCatalogTool

from utils import get_all_devices

class Layer2Tester(object):
    """
    Does a search similar to the one done in getChildLinks:
    https://github.com/zenoss/zenoss-prodbin/blob/develop/Products/ZenModel/LinkManager.py#L342
    and compares results between model_catalog and layer_3 catalog
    """

    def validate_devices_interfaces_and_mac_addresses(self):
        """
        get macs of avery device in the system with both catalogs
        """
        layer2_catalog = dmd.ZenLinkManager.layer2_catalog
        model_catalog = IModelCatalogTool(dmd)
        failed_devices = []
        for device in get_all_devices(dmd):
            device_uid = "/".join(device.getPrimaryPath())
            layer2_query = Eq('deviceId', device_uid)
            layer2_brains = layer2_catalog.evalAdvancedQuery(layer2_query)
            layer2_macs = set([ brain.macaddress for brain in layer2_brains if brain.macaddress ])
            layer2_ifaces = set([ brain.interfaceId for brain in layer2_brains if brain.interfaceId ])

            model_catalog_query = And(Eq('deviceId', "{0}".format(device_uid)), Eq('meta_type', "IpInterface"))
            search_results = model_catalog.search(query=model_catalog_query)
            model_catalog_brains = [ brain for brain in search_results.results ]
            model_catalog_macs = set([ brain.macaddress for brain in model_catalog_brains if brain.macaddress ])
            model_catalog_ifaces = set([ brain.interfaceId for brain in model_catalog_brains if brain.interfaceId ])
            if not ( len(layer2_macs - model_catalog_macs) == len(model_catalog_macs- layer2_macs) == 0 and \
                len(layer2_ifaces - model_catalog_ifaces) == len(model_catalog_ifaces- layer2_ifaces) == 0 ):
                failed_devices.append(device)

        if failed_devices:
            print "TEST FAILED: Catalogs return different mac addresses or interfaces for the following devices:"
            for dev in failed_devices:
                print "\t\t{0}".format(dev.getPrimaryId())
        else:
            print "TEST PASSED: Both catalogs returned the same mac addresses and interfaces for every device."
        return len(failed_devices) == 0

    def run(self):
        return self.validate_devices_interfaces_and_mac_addresses()

def main():
    success = Layer2Tester().run()
    print "\n============================="
    if success:
        print "  TEST PASSED"
    else:
        print "  TEST FAILED"
    print "============================="



if __name__ == '__main__':
    main()