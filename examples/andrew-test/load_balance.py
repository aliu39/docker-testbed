"""
Uses pathneck measurements to assign clients to servers
(Use topologies/load_balance.py)
"""
import os
import sys
from collections import defaultdict

sys.path.append('../..')
from utils.experiment_helpers import pathneck, parse_pathneck_result

clients = [
    {'name': 'c1', 'ip': '10.0.1.3'},
    {'name': 'c2', 'ip': '10.0.2.2'},
]

servers = [
    {'name': 's1', 'ip': '10.0.4.4'},
]

# clients = [
#     {'name': 'c1', 'ip': '10.0.1.1'},
#     {'name': 'c2', 'ip': '10.0.1.2'},
#     {'name': 'c3', 'ip': '10.0.1.3'},
# ]
#
# servers = [
#     {'name': 's1', 'ip': '10.0.4.1'},
#     {'name': 's2', 'ip': '10.0.4.2'},
#     {'name': 's3', 'ip': '10.0.4.3'},
# ]

assignments = defaultdict(list)  # server -> client
# assigns clients sequentially (not necessarily fair)
for client in clients:
    best_server, best_bw = None, float('-inf')
    for server in servers:
        pathneck_result = pathneck(client['name'], server['ip'])
        print(pathneck_result)
        bottleneck, bottleneck_bw = parse_pathneck_result(pathneck_result)
        if bottleneck_bw is None:
            continue  # assume no bottleneck means server is unreachable

        if server['name'] in assignments:
            bw_est = bottleneck_bw / len(assignments[server['name']])  # assume worst case: bottleneck is shared
        else:
            bw_est = bottleneck_bw

        if bw_est > best_bw:
            best_server, best_bw = server, bw_est

    if best_server is not None:
        assignments[best_server['name']].append((client['name'], best_bw))

print(assignments)
