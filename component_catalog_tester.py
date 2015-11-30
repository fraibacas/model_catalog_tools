import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

from collections import defaultdict
from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp
from Products.Zuul.catalog.interfaces import IModelCatalogTool

from utils import get_all_devices

class ComponentCatalogTester(object):

    def validate_device_components(self):
        """ search for devices components with both old a new catalogs """
        model_catalog = IModelCatalogTool(dmd)
        failed_devices = []
        object_implements_query = Eq('objectImplements', "Products.ZenModel.DeviceComponent.DeviceComponent")
        for device in get_all_devices(dmd):
            device_catalog = device.componentSearch
            device_catalog_components = defaultdict(list)
            for brain in device_catalog():
                device_catalog_components[brain.meta_type].append(brain.getPath())

            model_query = And(object_implements_query, Eq("deviceId", device.getPrimaryUrlPath()))
            model_query_results = model_catalog.search(query=model_query)
            model_catalog_components = defaultdict(list)
            for brain in model_query_results.results:
                model_catalog_components[brain.meta_type].append(brain.getPath())

            same_keys = len(device_catalog_components.keys()) == len(model_catalog_components.keys()) and  \
                        len(set(device_catalog_components.keys()) - set(model_catalog_components.keys())) == 0

            if not same_keys:
                failed_devices.append(device)
            else:
                for meta_type in model_catalog_components.keys():
                    device_catalog_values = device_catalog_components[meta_type]
                    model_catalog_values = model_catalog_components[meta_type]
                    same_values = len(device_catalog_values) == len(model_catalog_values) and \
                        len(set(device_catalog_values) - set(model_catalog_values)) == 0
                    if not same_values:
                        failed_devices.append(device)
                        break

        if failed_devices:
            print "TEST FAILED: Catalogs return different components for the following devices:"
            for dev in failed_devices:
                print "\t\t{0}".format(dev.getPrimaryId())
        else:
            print "TEST PASSED: Both catalogs returned the same components for every device."
        return len(failed_devices) == 0



    def run(self):
        return self.validate_device_components()


def main():
    success = ComponentCatalogTester().run()
    print "\n============================="
    if success:
        print "  TEST PASSED"
    else:
        print "  TEST FAILED"
    print "============================="



if __name__ == '__main__':
    main()