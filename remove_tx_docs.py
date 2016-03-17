import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

import zope.component
from Products.ZenUtils.GlobalConfig import getGlobalConfiguration
from Products.Zuul.catalog.model_catalog import TX_SEPARATOR
from zenoss.modelindex.model_index import SearchParams

def remove_temp_transaction_docs():
    config = getGlobalConfiguration()
    solr_servers = config.get('solr-servers', 'localhost:8983')
    uid = "*{0}*".format(TX_SEPARATOR)
    query = {"uid" : uid}
    search_params=SearchParams(query)
    searcher = zope.component.createObject('ModelIndex', solr_servers)
    searcher.unindex_search(search_params)

if __name__ == "__main__":
    remove_temp_transaction_docs()
