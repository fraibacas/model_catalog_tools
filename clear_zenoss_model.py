import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

import time
import zope.component
from Products.Zuul.catalog.model_catalog import get_solr_config
from Products.Zuul.catalog.model_catalog import TX_SEPARATOR
from zenoss.modelindex.searcher import SearchParams

def delete_all_documents():

    query = {"uid" : "*"}
    search_params=SearchParams(query)
    searcher = zope.component.createObject('ModelSearcher', get_solr_config())
    searcher.unindex_search(search_params)

if __name__ == "__main__":
    start = time.time()
    delete_all_documents()
    print "Deleting all documents took {0} seconds".format(time.time() - start)
