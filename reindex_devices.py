
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit

import sys

from Products.Zuul.catalog.interfaces import IModelCatalog
from Products.AdvancedQuery import Eq
from zope.component import getUtility

def get_device_classes():
    prefix = '/'.join(dmd.Devices.getPrimaryPath())
    return [ "{0}{1}".format(prefix, dc) for dc in dmd.Devices.getPeerDeviceClassNames() ]

def reindex_all_devices():
    model_catalog = getUtility(IModelCatalog)
    prefix = '/'.join(dmd.Devices.getPrimaryPath())
    all_device_classes = [ "{0}{1}".format(prefix, dc) for dc in dmd.Devices.getPeerDeviceClassNames() ]
    for dc in all_device_classes:
        dc_object = dmd.unrestrictedTraverse(dc)
        for device in dc_object.devices():
            model_catalog.catalog_object(device)

def reindex_uids(uids):
    model_catalog = getUtility(IModelCatalog)
    for uid in uids:
        try:
            obj = dmd.unrestrictedTraverse(uid)
            model_catalog.catalog_object(obj)
        except:
            # if not found, we remove it from the index
            query = 'uid:"{0}"'.format(uid)
            model_catalog.indexer.solr_connection_manager.connection.delete(query=query, commit=True)
            print "Could not retrieve object {0}".format(uid)

if __name__=="__main__":
    if len(sys.argv) > 1:
        uids = sys.argv[1:]
        print "Reindexing uids {0}".format(uids)
        reindex_uids(uids)
    else:
        print "Reindexing all devices...."
        reindex_all_devices()
