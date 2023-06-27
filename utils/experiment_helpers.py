"""
Helper functions useful when setting up an experiment
"""
import subprocess
from ipaddress import ip_network

def capture_traffic(node_name, interface, duration, filename):
	"""
	Capture traffic with tcpdump on a node for a given time
	duration and write to file.
	:param node_name: name of node to run tcpdump on
	:param interface: interface to capture traffic on
	:param duration: time to measure traffic in seconds
	:param filename: file to write output to
	:return: None
	"""
	try:
		subprocess.check_call(f"docker exec {node_name} timeout {duration} tcpdump -v -i {interface} > {filename} &", shell=True)
	except subprocess.CalledProcessError as e:
		print(f"Command {e.cmd} returned non-zero exit status: {e.returncode}")


def iperf_server(node_name):
	"""
	Starts an iperf server on a node
	:param node_name: name of node to start iperf server on
	:return: None
	"""
	try:
		subprocess.check_call(f'docker exec {node_name} iperf -s &', shell=True)
	except subprocess.CalledProcessError as e:
		print(f"Command {e.cmd} returned non-zero exit status: {e.returncode}")


def iperf_client(node_name, server_ip):
	"""
	Start iperf client on node
	:param node_name: name of client node
	:param server_ip: ip address of server node
	:return: None
	"""
	try:
		subprocess.check_call(f"docker exec {node_name} iperf -t 0 -c {server_ip} &", shell=True)
	except subprocess.CalledProcessError as e:
		print(f"Command {e.cmd} returned non-zero exit status: {e.returncode}")


def pathneck(client_name, server_ip):
	"""
	Run pathneck from client to server
	:param client_name: name of client node
	:param server_ip: ip address of server node
	:return: String containing output of Pathneck
	run with online flag set
	"""
	result = subprocess.run(['docker', 'exec', f'{client_name}', './pathneck-1.3/pathneck', '-o', f'{server_ip}'],
	                        stdout=subprocess.PIPE)
	return result.stdout.decode('utf-8')


def parse_pathneck_result(pathneck_result):
	"""
	Returns detected bottleneck and estimated bandwidth
	:param pathneck_result: result of pathneck run such as output
	of pathneck function
	:return: tuple (bottleneck, bottleneck_bandwidth)
	the detected bottleneck and the estimated bottleneck bandwidth if found,
	else returns None
	"""
	for line in pathneck_result.splitlines():
		line = line.split()
		if len(line) == 8:
			if line[5] == '1':
				bottleneck = line[0]
				bottleneck_bw = float(line[6])
				return bottleneck, bottleneck_bw
	return None, None

def traceroute(client_name, server_ip, query_timeout_ms=500, n_queries=3, max_hops=30):
	"""
	Run traceroute from client to server
	:param client_name: name of client node
	:param server_ip: ip address of server node
	:return: String containing output of traceroute run
	"""
	# TODO: take average rtt and consider num trials
	# use timeout?
	# -q {num_trials} -m {max_hops}
	result = subprocess.run(['docker', 'exec', f'{client_name}', 'timeout', str(n_queries*query_timeout_ms/1000), 'traceroute', '-q',
							str(n_queries), '-m', str(max_hops), f'{server_ip}'], stdout=subprocess.PIPE)
	print(result.returncode)
	return result.stdout.decode('utf-8')
	# return None

def parse_traceroute_result(traceroute_result):
	"""
	Returns detected bottleneck and estimated bandwidth
	:param traceroute_result: output of successful traceroute run
	of traceroute function
	:return: tuple (ips, rtts)
	"""
	ips, rtts = [], []
	for line in traceroute_result.splitlines()[1:]:
		line = line.split()
		ips.append(line[2].strip('()'))
		rtts.append(float(line[3]))
	return ips, rtts

def get_subnet_cidr_from_ifconfig(server):
	ifconfig_result = subprocess.run(['docker', 'exec', f'{server["name"]}', 'ifconfig'], stdout=subprocess.PIPE) \
		.stdout.decode('utf-8')
	subnet_mask = None
	for line in ifconfig_result.splitlines():
		# TODO: check returned IPv4?
		if 'netmask' in line:
			subnet_mask = line.split()[3]
			break

	if subnet_mask is None:
		print(f"Failed to find a subnet from {server['name']}'s ifconfig information")
		exit(1)

	subnet = ip_network(f"{server['ip']}/{subnet_mask}", strict=False)
	return f'{subnet.network_address}/{subnet.prefixlen}'

def get_reachable_ips(server, subnet_cidr):
	print(f'getting reachable ips for subnet {subnet_cidr}..')

	# ping sweep
	ping_result = subprocess.run(['docker', 'exec', f'{server["name"]}', 'nmap', '-sn', f'{subnet_cidr}'],
								 stdout=subprocess.PIPE).stdout.decode('utf-8')
	reachable_ips = []
	for line in ping_result.splitlines():
		if 'Nmap scan report' in line:
			ip = line.split()[-1].strip("()")
			if ip != server['ip']:
				reachable_ips.append(ip)
	print(reachable_ips)
	return reachable_ips

