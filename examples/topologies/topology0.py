"""
Nodes Format:
{node_name: (ip_addr, base_link name), ...}
"""
nodes = {"c1": ("10.0.1.2", "c1-r1"),
         "c2": ("10.0.5.2", "c2-r5"),
         "r1": ("10.0.1.4", "c1-r1"),
         "r2": ("10.0.2.2", "r2-r3"),
         "r3": ("10.0.2.4", "r2-r3"),
         "r4": ("10.0.3.2", "r4-r5"),
         "r5": ("10.0.3.4", "r4-r5"),
         "r6": ("10.0.4.2", "r6-s1"),
         "s1": ("10.0.4.4", "r6-s1")}
"""
Links Format:
[(endpoint_name1, ip1, (endpoint_name2, ip2)), (bandwidth[Mbit/s], burst[kb], latency[ms])), ...]
"""
links = [(("c1", "10.0.1.2"), ("r1", "10.0.1.4"), (100, 12500, 1)),
         (("r2", "10.0.2.2"), ("r3", "10.0.2.4"), (100, 12500, 1)),
         (("r4", "10.0.3.2"), ("r5", "10.0.3.4"), (100, 12500, 1)),
         (("r6", "10.0.4.2"), ("s1", "10.0.4.4"), (100, 12500, 1)),
         (("c2", "10.0.5.2"), ("r5", "10.0.5.4"), (100, 12500, 1)),
         (("r1", "10.0.6.2"), ("r2", "10.0.6.4"), (100, 12500, 1)),
         (("r3", "10.0.7.2"), ("r4", "10.0.7.4"), (100, 12500, 1)),
         (("r5", "10.0.8.2"), ("r6", "10.0.8.4"), (100, 12500, 1))]