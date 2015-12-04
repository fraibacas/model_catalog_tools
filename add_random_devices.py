

import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd
from transaction import commit

import random
import sys
import time

from Products.ZenModel.ZDeviceLoader import JobDeviceLoader
from utils import get_device_classes, generate_random_ip


def assign_random_ips_to_device(device, n_ips=5):
    for i in range(n_ips):
        ip = generate_random_ip()
        #print "added ip {0} to {1}".format(ip, device)
        ts = int(time.time())
        iface_id = "testinterface_{0}_{1}".format(str(ts), i)
        device.os.addIpInterface(iface_id, True)
        interface = device.os.interfaces._getOb(iface_id)
        interface.macaddress = iface_id + "_macaddress"
        interface.description = "hola {0}".format(ts)
        interface.addIpAddress(ip)

def add_devices(n_devices):
    """ create n_devices devices with random ip and device class """
    device_classes = get_device_classes(dmd)
    for i in range(n_devices):
        ip = generate_random_ip()
        device_class = random.choice(device_classes)
        device_class = device_class[18:] # remove "/zport/dmd/Devices"
        print "Creating device {0} / {1}".format(ip, device_class)
        device = JobDeviceLoader(dmd).load_device(ip, device_class, 'none', 'localhost', manageIp=ip)
        assign_random_ips_to_device(device)
        commit()


def main():
    start = time.time()
    n_devices = 10
    if len(sys.argv) > 1:
        n_devices = int(sys.argv[1])
    add_devices(n_devices)
    print "Adding {0} devices took {1}".format(n_devices, time.time()-start)

if __name__ == "__main__":
    main()
