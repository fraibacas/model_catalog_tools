
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit


from Products.ZenModel.ZDeviceLoader import JobDeviceLoader
from Products.Zuul.catalog.interfaces import IModelCatalogTool

import json

def create_device(ip, device_class="/Server/Linux"):
    device = JobDeviceLoader(dmd).load_device(ip, device_class, 'none', 'localhost', manageIp=ip)
    iface_id = "interface_{0}".format(ip)
    device.os.addIpInterface(iface_id, True)
    interface = device.os.interfaces._getOb(iface_id)
    interface.macaddress = iface_id + "_macaddress"
    interface.description = "hola {0}".format(ip)
    interface.addIpAddress(ip)
    return device


def ip_assigned(ip):
    cat = IModelCatalogTool(dmd.Networks)
    query = {}
    query["meta_type"] = "IpAddress"
    query["uid"] = "*{0}".format(ip)
    query["deviceId"] = "*"
    res = cat.search(query=query)
    device = None
    if res.total > 0:
        deviceId = str(next(res.results).deviceId)
        device = dmd.unrestrictedTraverse(deviceId)
    return device


def get_location(location):
    cat = IModelCatalogTool(dmd.Locations)
    query = {}
    query["meta_type"] = "Location"
    query["uid"] = "/zport/dmd/Locations/*{0}".format(location)
    res = cat.search(query=query)
    location = None
    if res.total > 0:
        locationUid = str(next(res.results).uid)
        location = dmd.unrestrictedTraverse(locationUid)
    return location


def create_location(location):
    loc = dmd.Locations.createOrganizer("{0}".format(location))
    return loc


def set_up_test_for_getChildLinks(links):
    # get two devices that belong to the same network
    devices = []
    for ip, loc in links:
        # Get / create device with ip
        device  = ip_assigned(ip)
        if not device:
            device = create_device(ip)

        # Create and assign device to location
        location = get_location(loc)
        if not location:
            location = create_location(loc)
        
        device.setLocation(location.id)
        devices.append( (device, ip, location) )
        commit()
    return devices


def test_getChildLinks(devices):
    """
    devices : list of tuple (device, ip, location)
    """
    link_to_find = set( [ devices[0][2].getPrimaryId(), devices[1][2].getPrimaryId() ] )
    links = dmd.ZenLinkManager.getChildLinks(dmd.Locations)
    links = json.loads(links)
    child_links = []
    found = False
    for link in links:
        locations = link[0]
        if len( link_to_find - set(locations) ) == 0:
            found = True
            break
    return found


def main():
    links = [ ("10.10.10.1", "location1"), ("10.10.10.35", "location2") ]
    print "Setting up test"
    devices = set_up_test_for_getChildLinks(links)
    print "Calling getChildLinks"
    success = test_getChildLinks(devices)
    if success:
        print "TEST PASSED"
    else:
        print "TEST FAILED"


if __name__ == "__main__":
    main()
