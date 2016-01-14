
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd


class DeviceSearchTester(object):
    """
    Tests that searches that were previously done with device search catalog
    can be done with model_catalog and the results are consistent
    """
    def __init__(self):
        pass


    def validate_location_search(self):
        """
        https://github.com/zenoss/zenoss-prodbin/blob/develop/Products/ZenModel/LinkManager.py#L317
        getChildLinks uses the device catalog to get all the devices belonging to a location organizer
        """

        

