"""
An experiment to find a path to a target node
"""
import os
import sys
# import subprocess

# sys.path.append('..')
# from utils.experiment_helpers import iperf_server, iperf_client, pathneck, parse_pathneck_result, capture_traffic

# RUN FROM PROJECT ROOT

# global variables
# TODO: read these from cmd line args or topology config file

src_node = 's1'
# from topology_config.py:
target_ip = "10.0.1.2"  # c1
# "10.0.5.2",  # c2
# "10.0.1.4",  # r1
# "10.0.2.2",  # r2
# "10.0.2.4",  # r3
# "10.0.3.2",  # r4
# "10.0.3.4",  # r5
# "10.0.4.2",  # r6
# "10.0.4.4",  # s1
# "10.0.6.9",  # fake node
max_hops = 30
num_trials = 3
timeout_s = 5
out_filename = 'examples/andrew-test/traceroute_out.txt'

# TODO: can decide to print experiment output and/or errors

status = os.system(f"docker exec {src_node} timeout {timeout_s} traceroute -q {num_trials} -m {max_hops} {target_ip} > {out_filename}")
exit_status = os.WEXITSTATUS(status)  # https://stackoverflow.com/questions/6466711/what-is-the-return-value-of-os-system-in-python

fail_msg = None
if exit_status == 124:
	fail_msg = f"Traceroute from {src_node} to {target_ip} TIMED OUT after {timeout_s} seconds.\n"
elif exit_status != 0:
	fail_msg = f"Traceroute from {src_node} to {target_ip} returned with exit status {exit_status}\n"

if fail_msg is not None:
	with open(out_filename, 'w') as out_file:
		out_file.write(fail_msg)
	sys.exit(1)

# store output in code
path = []
with open(out_filename, 'r') as out_file:
	for line in out_file.readlines()[1:]:
		tokens = line.split()
		path.append({'name': tokens[1], 'ip': tokens[2]})

print(path)
