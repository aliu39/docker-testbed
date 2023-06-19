"""
An experiment pinging node IPs from one source node to check connection status
"""
import os
# import subprocess

# sys.path.append('..')
# from utils.experiment_helpers import iperf_server, iperf_client, pathneck, parse_pathneck_result, capture_traffic

# RUN FROM PROJECT ROOT

# global variables
# TODO: read these from cmd line args or topology config file

src_node = 's1'
# from topology_config.py:
target_ips = [
	"10.0.1.2",  # c1
	"10.0.5.2",  # c2
	"10.0.1.4",  # r1
	"10.0.2.2",  # r2
	"10.0.2.4",  # r3
	"10.0.3.2",  # r4
	"10.0.3.4",  # r5
	"10.0.6.9",  # fake node
	"10.0.4.2",  # r6
	# "10.0.4.4",  # s1
]
num_trials = 4
timeout_s = 5
out_filename = 'examples/andrew-test/ping_out.txt'

# clear file contents
with open(out_filename, 'w') as _:
	pass

# ping target_ips in sequence
# TODO: ping in parallel? Makes it hard to process output
# subprocess.run, call, or check_call to run in parallel.
# also can add '&' to run in parallel?
for ip in target_ips:
	status = os.system(f"docker exec {src_node} timeout {timeout_s} ping -c {num_trials} {ip} >> {out_filename}")
	exit_status = os.WEXITSTATUS(status)  # https://stackoverflow.com/questions/6466711/what-is-the-return-value-of-os-system-in-python

	if exit_status == 124:
		with open(out_filename, 'a') as out_file:
			out_file.write(f"\nPING {ip} TIMED OUT after {timeout_s} seconds.\n\n")

	elif exit_status != 0:
		with open(out_filename, 'a') as out_file:
			out_file.write(f"PING {ip} returned with exit status {exit_status}\n")

# store output in code
# code expects out_file to contain ordered output for all ips in target_ips
results = []
with open(out_filename, 'r') as out_file:
	lines = out_file.readlines()
	i = 0
	while i < len(lines):
		line = lines[i]
		if "TIMED OUT" in line:
			results.append({"ip": target_ips[len(results)], "success": False})
		elif "statistics" in line:
			results.append({"ip": target_ips[len(results)], "success": True})

			packet_loss_str = lines[i+1].split(", ")[2]  # "x% packet loss"
			results[-1]["packet_loss"] = float(packet_loss_str[:packet_loss_str.find('%')]) / 100.0

			line2_tokens = lines[i+2].split()
			for name, val in zip(line2_tokens[1].split('/'), line2_tokens[3].split('/')):
				results[-1][f"rtt_{name}_ms"] = float(val)
			i += 2
		i += 1

print(results)


