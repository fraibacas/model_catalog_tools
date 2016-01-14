
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit


from Products.AdvancedQuery import Eq, Or, Generic, And, In, MatchRegexp
from Products.Zuul.catalog.interfaces import IModelCatalogTool
from Products.Zuul.interfaces.tree import ICatalogTool
from zenoss.modelindex.searcher import SearchParams
from zenoss.modelindex.exceptions import SearchException

import random
import time

from utils import get_device_classes, get_mib_organizers

DEVICE_CLASSES = get_device_classes(dmd)

class GlobalCatalogTester(object):

    def __init__(self):
        pass

    def test_device_classes_devices(self):
        """ Check devices under device classes are the same """
        failed_device_classes = []
        for dc in DEVICE_CLASSES:
            dc_object = dmd.unrestrictedTraverse(dc)

            # Devices under device class in global catalog
            global_catalog = ICatalogTool(dc_object)
            global_catalog_brains = global_catalog.search('Products.ZenModel.Device.Device')
            global_catalog_results = set([ brain.getPath() for brain in global_catalog_brains.results ])

            # Devices under device class in model catalog
            model_catalog = IModelCatalogTool(dc_object)
            model_catalog_brains = model_catalog.search('Products.ZenModel.Device.Device', limit=10000)
            model_catalog_results = set([ brain.getPath() for brain in model_catalog_brains.results ])

            result = "FAILED"
            if len(global_catalog_results - model_catalog_results) == 0 and  \
               len(model_catalog_results-global_catalog_results) ==0:
               result = "PASSED"
            else:
                failed_device_classes.append(dc)

        if not failed_device_classes:
            print "TEST PASSED: All devices found in the same device classes for both catalogs!!"
        else:
            print "TEST FAILED: The following device classes have different devices in the catalogs:"
            for failed in failed_device_classes:
                print "\t{0}".format(failed)

        return len(failed_device_classes) == 0


    def validate_mib_counts(self):
        """ """
        mib_organizers = get_mib_organizers(dmd)
        failed_counts = []
        global_catalog = ICatalogTool(dmd)
        model_catalog = IModelCatalogTool(dmd)
        for organizer in mib_organizers:
            global_catalog_count = global_catalog.count(("Products.ZenModel.MibModule.MibModule",), organizer)
            model_catalog_count = model_catalog.count(("Products.ZenModel.MibModule.MibModule",), organizer)
            if global_catalog_count != model_catalog_count:
                failed_counts.append(organizer)

        if not failed_counts:
            print "TEST PASSED: All mib organizers have the same count in both catalogs!!"
        else:
            print "TEST FAILED: The following mib organizers have different counts in the catalogs:"
            for failed in failed_counts:
                print "\t{0}".format(failed)
        return len(failed_counts) == 0

    def validate_templates(self):
        """ Check that both catalogs return same data for templates """
        global_catalog = ICatalogTool(dmd.Devices)
        model_catalog = IModelCatalogTool(dmd.Devices)

        # get template nodes from global catalog
        global_catalog_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',))
        global_catalog_templates = set([ brain.getPath() for brain in global_catalog_brains ])

        # get template nodes from model catalog
        model_catalog_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',))
        model_catalog_templates = set([ brain.getPath() for brain in model_catalog_brains ])

        # compare results
        if len(model_catalog_templates - global_catalog_templates) == 0 and \
            len(global_catalog_templates - model_catalog_templates) == 0:
            for template in global_catalog_templates:
                template_object = dmd.unrestrictedTraverse(template)
                query = Eq('id', template_object.id)
                
                gc_brains = global_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',), query=query)
                gc_templates = set([ brain.getPath() for brain in gc_brains ])

                mc_brains = model_catalog.search(types=('Products.ZenModel.RRDTemplate.RRDTemplate',), query=query)
                mc_templates = set([ brain.getPath() for brain in mc_brains ])

                failed_templates = []
                if not (len(mc_templates - gc_templates) == 0 and \
                   len(gc_templates - mc_templates) == 0):
                    failed_templates.append(template)

            if failed_templates:
                print "TEST FAILED: Inconsistent results from catalogs for templates:"
                for failure in failed_templates:
                    print "\t{0}".format(failure)
            else:
                print "TEST PASSED: Both catalogs returned same results!!"
                return True

        else:
            print "TEST FAILED: Inconsistent results from catalogs:"
            print "\t{0}".format("Templates found in global catalog and not in model catalog: {0}".format(global_catalog_templates - model_catalog_templates))
            print "\t{0}".format("Templates found in model catalog and not in global catalog: {0}".format(model_catalog_templates - global_catalog_templates))

        return False

    def validate_total_objects(self):
        """
        check that the number of objects and their paths are the same in both catalogs 
        this can take some time
        """
        success = False
        ts=time.time()
        print "Searching for all objects in global catalog..."
        global_catalog_results = ICatalogTool(dmd).search()
        print "Search took: {0}\n".format(time.time() - ts)

        print "Searching for all objects in model catalog..."
        ts=time.time()
        model_catalog_results = IModelCatalogTool(dmd).search()
        print "Search took: {0}\n".format(time.time() - ts)
        if model_catalog_results.total == global_catalog_results.total:
            global_catalog_uids = set( [ brain.getPath() for brain in global_catalog_results.results ] )
            model_catalog_uids = set( [ brain.getPath() for brain in model_catalog_results.results ] )
            if len(global_catalog_uids - model_catalog_uids) == 0:
                success = True
                print "TEST PASSED: Both catalogs returned same results!!"
            else:
                global_not_model = global_catalog_uids - model_catalog_uids
                model_not_global = model_catalog_uids - global_catalog_uids
                print "TEST FAILED: Catalogs returned different objects"
                if global_not_model:
                    print "The following objects were found in global catalog and not in model catalog: {0}".format(global_not_model)
                if model_not_global:
                    print "The following objects were found in model catalog and not in global catalog: {0}".format(model_not_global)
        else:
            print "TEST FAILED: Catalogs returned different number of objects"
        return success

    def run(self):
        return self.validate_total_objects() and self.test_device_classes_devices() and self.validate_mib_counts() and self.validate_templates()


def main():
    success = GlobalCatalogTester().run()
    print "\n============================="
    if success:
        print "  TEST PASSED"
    else:
        print "  TEST FAILED"
    print "============================="


if __name__ == '__main__':
    main()
