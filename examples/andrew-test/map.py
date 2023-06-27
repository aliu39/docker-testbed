"""
Maps the network from a central server node
- constructs topology graph using nmap (ping sweep) and traceroute
- stores min rtt to all nodes and bottleneck BW to client ("data") nodes
- TODO: periodic rebuilds?
"""

import os
import sys
import subprocess
from collections import defaultdict

sys.path.append('../..')
from utils.experiment_helpers import traceroute, parse_traceroute_result, capture_traffic

known_servers = []
with open('examples/andrew-test/ip_list.txt', 'r') as ip_list_file:
    for line in ip_list_file.read().splitlines():
        line = line.split('#', 1)[0]
        if line and not line.isspace():
            [name, ip] = line.split(',', 1)
            name = name.strip(' ( ')
            ip = ip.strip('\n ) ')
            if name and ip:
                known_servers.append({'name': name, 'ip': ip})
            else:
                print(f"empty server name and/or ip in line: {line}")
                exit(1)

# capture_traffic(server['name'], 'any', '10', 'examples/andrew-test/traffic-capture.txt')

# map the network
topology = {
    'links': defaultdict(dict)     # adjacency list with each link mapping to a list of rtts
}
# TODO: RESOLVE IP ALIASING
for idx1, src in enumerate(known_servers):
    for idx2 in range(idx1+1, len(known_servers)):
        traceroute_result = traceroute(src['name'], known_servers[idx2]['ip'])
        print(traceroute_result)
        if traceroute_result is not None:
            prev_hop = src['ip']
            ips, rtts = parse_traceroute_result(traceroute_result)
            for ip, rtt in zip(ips, rtts):
                # store links (assume bi-directional)
                measurements = topology['links'][prev_hop].get(ip, [])
                topology['links'][prev_hop][ip] = measurements + [rtt]

                measurements = topology['links'][ip].get(prev_hop, [])
                topology['links'][ip][prev_hop] = measurements + [rtt]

                prev_hop = ip

print(topology)
print(sum(map(lambda e: len(e[1]), topology['links'].items())), "LINKS MAPPED")
