"""
Nodes Format:
{node_name: (ip_addr, base_link name), ...}
"""
nodes = {"c1": ("10.0.1.4", "c1-r1"),
         "c2": ("10.0.6.4", "c2-r2"),
         "r1": ("10.0.1.2", "c1-r1"),
         "r2": ("10.0.2.3", "r1-r2"),
         "r3": ("10.0.3.3", "r2-r3"),
         "r4": ("10.0.5.4", "r4-s1"),
         "s1": ("10.0.5.5", "r4-s1")}

"""
Links Format:
[(endpoint_name1, ip1, (endpoint_name2, ip2)), (bandwidth[Mbit/s], burst[kb], latency[ms])), ...]
"""
links = [(("c1", "10.0.1.4"), ("r1", "10.0.1.2"), (200, 12500, 1)),
         (("r4", "10.0.5.4"), ("s1", "10.0.5.5"), (200, 12500, 1)),
         (("r1", "10.0.2.2"), ("r2", "10.0.2.3"), (200, 12500, 1)),
         (("r2", "10.0.3.2"), ("r3", "10.0.3.3"), (200, 12500, 1)),
         (("c2", "10.0.6.4"), ("r2", "10.0.6.3"), (200, 12500, 1)),
         (("r3", "10.0.4.2"), ("r4", "10.0.4.3"), (140, 12500, 1))]
