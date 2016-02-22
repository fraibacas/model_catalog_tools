
import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
dmd = ZenScriptBase(connect=True).dmd

import time

def ppath(obj):
    path = ""
    if obj:
        path = "/".join(obj.getPrimaryPath())
    return path

class NetworkCacheTester(object):

    def __init__(self):
        networks = dmd.Networks.getSubNetworks()
        self.networks=[]
        self.ips = []
        start = time.time()
        for net in networks:
            self.networks.append( (net.id, net.netmask, ppath(net)) )
            for ip in net.ipaddresses():
                str_ip = ip.id.split("/")[0]
                self.ips.append( (str_ip, net.netmask, ppath(ip)) )
        print "Loading nets and ips took {0} seconds".format(time.time()-start)
        print "   {0} nets found".format(len(self.networks))
        print "   {0} ips found".format(len(self.ips))

    def validate_nets(self, cache):
        inconsistent_nets = set()
        for netip, mask, path in self.networks:
            net = dmd.unrestrictedTraverse(path)
            cache_net = cache.get_net(netip, mask, dmd)
            if cache_net != net:
                inconsistent_nets.add( (netip, mask, path) )
            cache_net = cache.get_net(netip, None, dmd)
            if not ppath(cache_net).startswith(path):
                inconsistent_nets.add( (netip, mask, path) )
        return inconsistent_nets

    def validate_ips(self, cache):
        inconsistent_ips = set()
        for ip, mask, path in self.ips:
            ip_obj = dmd.unrestrictedTraverse(path)
            cache_ip = cache.get_ip(ip, mask, dmd)
            if cache_ip != ip_obj:
                inconsistent_ips.add( (ip, mask, path) )
            cache_ip = cache.get_ip(ip, None, dmd)
            if cache_ip != ip_obj:
                inconsistent_ips.add( (ip, mask, path) )
        return inconsistent_ips

    def run(self):
        cache = dmd.Networks.get_network_cache()
        inconsistent_nets = self.validate_nets(cache)
        inconsistent_ips = self.validate_ips(cache)
        if inconsistent_nets:
            print inconsistent_nets
        if inconsistent_ips:
            print inconsistent_ips
        print "\n\n Found {0} inconsistent nets and {1} inconsistent ips.\n".format(len(inconsistent_nets), len(inconsistent_ips))

def main():
    
    start = time.time()
    NetworkCacheTester().run()
    print "\nTest took {0} seconds.\n".format(time.time() - start)


if __name__ == '__main__':
    main()