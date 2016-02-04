import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

import zope.component
from Products.ZenUtils.GlobalConfig import getGlobalConfiguration
from Products.Zuul.catalog.model_catalog import TX_SEPARATOR
from zenoss.modelindex.searcher import SearchParams

def remove_temp_transaction_docs():
    config = getGlobalConfiguration()
    solr_servers = config.get('solr-servers', 'localhost:8984')
    indexer = zope.component.createObject('ModelIndexer', solr_servers)
    searcher = zope.component.createObject('ModelSearcher', solr_servers)

    query = {"uid" : "*{0}*".format(TX_SEPARATOR)}
    results = searcher.search(SearchParams(query))
    uids = [ r.uid for r in results.results ]
    indexer._unindex_uids(uids)


if __name__ == "__main__":
    remove_temp_transaction_docs()