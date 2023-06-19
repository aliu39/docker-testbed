"""
Maps the network from a central server node
- constructs topology graph using nmap (ping sweep) and pathneck
- stores min rtt to all nodes and bottleneck BW to client ("data") nodes
- TODO: periodic rebuilds?
"""

import os
import sys
import subprocess
from collections import defaultdict

sys.path.append('../..')
from utils.experiment_helpers import pathneck, parse_pathneck_result, get_reachable_ips, get_subnet_cidr_from_ifconfig

server = {'name': 's1', 'ip': '10.0.4.4'}

subnet_cidr = get_subnet_cidr_from_ifconfig(server)  # 10.0.4.0/24, ['10.0.4.1', '10.0.4.2']
# subnet_cidr = '10.0.0.0/16'  # 65k pings! Don't use

# do a ping sweep over the subnet
reachable_ips = get_reachable_ips(server, subnet_cidr)
reachable_ips = ['10.0.1.2', '10.0.5.2']

# map the network
topology = {
    'clients': defaultdict(dict),  # ip -> info dict
    'links': defaultdict(list)     # adjacency list
}
for ip in reachable_ips:
    pathneck_result = pathneck(server['name'], ip)
    print(pathneck_result)

    bottleneck_ip, bottleneck_bw = None, None
    prev_hop = server['ip']
    for line in pathneck_result.splitlines():
        line = line.split()
        if len(line) == 8:
            # bottleneck info
            if line[5] == '1':
                bottleneck_ip = line[2]
                bottleneck_bw = float(line[6])

            # store links (assume bi-directional)
            curr_hop = line[2]
            topology['links'][prev_hop].append(curr_hop)
            topology['links'][curr_hop].append(prev_hop)
            prev_hop = curr_hop

    topology['clients'][ip]['bottleneck_ip'] = bottleneck_ip
    topology['clients'][ip]['bottleneck_bw'] = bottleneck_bw

print(topology)
