"""
Given a list of server IPs, print the server with the minimum est. processing time
Also stores a dict of server -> (bottleneck_bw, processing_power, process_power_unit)
Does this using pathneck BW measurements, and requesting each server for a processing power.
"""

import argparse
import ast
import os
import socket
import subprocess
import time
import traceback
from collections import defaultdict

from utils.experiment_helpers import pathneck, parse_pathneck_result, ping, iperf_server, iperf_client_bw, iperf_client
from andrew.server import PORT as SERVER_PORT
from andrew.client_scripts import make_request_power_script, make_send_data_script

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--client', type=str, required=True,
                    help='(name, ip) of client node')
parser.add_argument('-d', '--data-size', type=float, required=False, default=100,
                    help='size of client data in MB (default 100)')
parser.add_argument('-s', '--servers', type=str, required=True,
                    help='list of servers (name, ip) for data node to connect to')
parser.add_argument('-cc', '--contesting_clients', type=str, required=False, default='[]',
                    help='list of contesting clients (name, target_server_ip) for generating background traffic')
parser.add_argument('--iperf', action='store_true', help='use iperf to measure bandwidth instead of pathneck')
args = parser.parse_args()

(client, client_ip) = ast.literal_eval(args.client)
data_size_mb = args.data_size
servers = ast.literal_eval(args.servers)
server_info = defaultdict(dict)  # key is server ip
contesting_clients = ast.literal_eval(args.contesting_clients)
use_iperf = args.iperf

SOCK_TIMEOUT_S = 10
MbPS_TO_MBPS = 1/8

# start background traffic from contesting clients USING IPERF
# for server, _ in servers:
#     iperf_server(server)
#
# # contesting_clients = [
# #     ('c3', '10.0.4.5'),  # ip is for target SERVER
# #     ('c4', '10.0.3.5'),
# # ]
# for c, server_ip in contesting_clients:
#     iperf_client(c, server_ip)

# start server program to listen for power and process_data requests
for server, _ in servers:
    subprocess.Popen(['docker', 'exec', server, 'python3', 'server.py'])

# start background traffic USING PROTOCOL FROM server.py (echos data via TCP stream)
contesting_clients = [
    ('c3', '10.0.4.5'),  # ip is for target SERVER
]

for c, server_ip in contesting_clients:
    send_data_script = make_send_data_script(SOCK_TIMEOUT_S, server_ip, SERVER_PORT, 0.2)
    subprocess.Popen(['docker', 'exec', c, 'python3', '-c', send_data_script])

# find best server
best_server_ip, min_process_t = None, float('inf')
for server, ip in servers:
    # try to reach server and request processing power, via TCP
    power = None  # note: megaByte/s, not megabits
    try:
        request_power_script = make_request_power_script(SOCK_TIMEOUT_S, ip, SERVER_PORT)
        result = subprocess.run(['docker', 'exec', client, 'python3', '-c', request_power_script], stdout=subprocess.PIPE)
        power = float(result.stdout.decode('utf-8'))
    except:
        traceback.print_exc()

    print(f'---{server} POWER={power}---')
    if power is None:
        continue

    if use_iperf:
        bottleneck_bw = iperf_client_bw(client, ip)
        bottleneck_link = None

    else:  # use PATHNECK
        retcode, result = pathneck(client, ip)
        print(retcode, result)

        bottleneck_link, bottleneck_bw = None, None
        min_bw_link, min_bw = None, float('inf')
        prev_hop = client_ip
        for line in result.splitlines():
            line = line.split()
            if len(line) == 8:
                curr_hop, bw = line[2], float(line[6])
                if line[5] == '1':
                    bottleneck_link, bottleneck_bw = (prev_hop, curr_hop), bw
                    break
                elif bw < min_bw:
                    min_bw_link, min_bw = (prev_hop, curr_hop), bw
                prev_hop = curr_hop

        # default to minimum bw measurement if no bottleneck found  #TODO: verify this is an ok substitution
        if bottleneck_link is None and min_bw_link is not None:
            bottleneck_link, bottleneck_bw = min_bw_link, min_bw

    # estimate processing time
    process_t = data_size_mb * (1. / (power*1000) + 2. / (bottleneck_bw * MbPS_TO_MBPS)) #TODO: make helper fx
    if process_t < min_process_t:
        best_server_ip = ip
        min_process_t = process_t

    # store measurements
    # server_info[ip]['bottleneck_link'] = bottleneck_link
    server_info[ip]['bottleneck_bw'] = bottleneck_bw
    server_info[ip]['process_power'] = power
    server_info[ip]['power_unit'] = 'MB/s'

for c, _ in contesting_clients:
    os.system(f"docker exec {c} pkill iperf")
for server, _ in servers:
    os.system(f"docker exec {server} pkill iperf")
    os.system(f"docker exec {server} pkill python3")

time.sleep(3)

print('------------------------------------------------')
print(server_info)
print(best_server_ip, 'estimated processing time (s) =', min_process_t)
