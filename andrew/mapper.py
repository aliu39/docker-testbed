"""
Maps the network from a central server node
- constructs topology graph using nmap (ping sweep) and traceroute
- stores min rtt to all nodes and bottleneck BW to client ("data") nodes
- TODO: periodic rebuilds?
"""
import argparse
import sys
import time
from collections import defaultdict

from utils.experiment_helpers import traceroute, parse_traceroute_result, capture_traffic

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--topology', type=str, required=False, default='fat_tree',
                    help='topology associated with "vantage point" servers, which traceroutes are run between')
args = parser.parse_args()

TRAFFIC_CAPTURE_DURATION_S = 5

query_servers = []
with open(f'andrew/ip_lists/{args.topology}', 'r') as query_file:
    for line in query_file.read().splitlines():
        line = line.split('#', 1)[0]
        if line and not line.isspace():
            [name, ip] = line.split(':', 1)
            name = name.strip(' "')
            ip = ip.strip('\n () "')
            if name and ip:
                query_servers.append({'name': name, 'ip': ip})
            else:
                print(f"empty server name and/or ip in line: {line}")
                exit(1)
print(query_servers)

# map the network
topology = {
    'links': defaultdict(dict)     # adjacency list with each link mapping to a list of rtts
}

# capture_traffic('s1', 'any', TRAFFIC_CAPTURE_DURATION_S, f'examples/andrew/out/mapper_s1_traffic_capture')
# time.sleep(TRAFFIC_CAPTURE_DURATION_S)

for idx1, src in enumerate(query_servers):
    for idx2 in range(idx1+1, len(query_servers)):
        returncode, output = traceroute(src['name'], query_servers[idx2]['ip'])
        print(returncode, output)
        if returncode == 0:
            prev_hop = src['ip']
            ips, rtts = parse_traceroute_result(output)
            for ip, rtt in zip(ips, rtts):
                # store links (assume bi-directional)
                measurements = topology['links'][prev_hop].get(ip, [])
                topology['links'][prev_hop][ip] = measurements + [rtt]

                measurements = topology['links'][ip].get(prev_hop, [])
                topology['links'][ip][prev_hop] = measurements + [rtt]

                prev_hop = ip

# print(topology)
print(sum(map(lambda x: len(x), topology['links'].values())), "LINKS MAPPED")
for ip1 in topology['links']:
    print(f'{ip1}:', end=' ')
    for ip2 in topology['links'][ip1]:
        print(ip2, end=' ')
    print()

# TODO: RESOLVE IP ALIASING
'''
Mercator is easiest to implement and doesn't require candidate pairs
Rocket Fuel may be more accurate

Mercator:
Use IP packet's source address, in traceroute responses
('normal' UDP-based traceroutes are used, rather than some specialized packet)

Rocket Fuel:
1. Identify potential alias pairs
1a. from traceroute results from a single node
    - similar TTLs
    - similar RTTs?
1b. from traceroute results from multiple nodes (distributed)
    - aliases much more likely
    - how to do this?
1c. DNS? 
1d. ?

2. Test candidate pairs
    - use IP packet identifier method 
    - send probes sequentially, make use of fact IP ID is a global counter in most routers
'''


