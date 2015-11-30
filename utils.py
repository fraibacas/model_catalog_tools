
import random

def get_device_classes(dmd):
    prefix = '/'.join(dmd.Devices.getPrimaryPath())
    return [ "{0}{1}".format(prefix, dc) for dc in dmd.Devices.getPeerDeviceClassNames() ]

def get_mib_organizers(dmd):
    prefix = '/'.join(dmd.Mibs.getPrimaryPath())
    return [ "{0}{1}".format(prefix, org) for org in dmd.Mibs.getOrganizerNames() ]

def get_networks(dmd):
    nets = []
    for net in dmd.Networks.children():
        nets.append("/".join(net.getPrimaryPath()))
    return nets

def generate_random_ip():
    blockOne = random.randrange(0, 255, 1)
    blockTwo = random.randrange(0, 255, 1)
    blockThree = random.randrange(0, 255, 1)
    blockFour = random.randrange(0, 255, 1)
    #print 'Random IP: ' + str(blockOne) + '.' + str(blockTwo) + '.' + str(blockThree) + '.' + str(blockFour)
    return str(blockOne) + '.' + str(blockTwo) + '.' + str(blockThree) + '.' + str(blockFour)


def get_all_devices(dmd):
    return dmd.Devices.getSubDevices()