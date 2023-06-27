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

with open('ip_list.txt', 'r') as ip_list_file:
    target_ips = ip_list_file.read().splitlines()

# map the network
topology = {
    'clients': defaultdict(dict),  # ip -> info dict
    'links': defaultdict(list)     # adjacency list
}
for ip in target_ips:
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
