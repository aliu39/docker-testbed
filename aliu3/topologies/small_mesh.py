"""
Nodes Format:
{node_name: (ip_addr, base_link name), ...}
"""
nodes = {"c1": ("10.0.1.2", "c1-r1"),
         "c2": ("10.0.2.2", "c2-r2"),
         "r1": ("10.0.3.4", "r1-s1"),
         "r2": ("10.0.4.4", "r2-s2"),
         "s1": ("10.0.3.5", "r1-s1"),
         "s2": ("10.0.4.5", "r2-s2")}

"""
Links Format:
[(endpoint_name1, ip1, (endpoint_name2, ip2)), (bandwidth[Mbit/s], burst[kb], latency[ms])), ...]
"""
links = [(("r1", "10.0.3.4"), ("s1", "10.0.3.5"), (200, 12500, 200)),
         (("r2", "10.0.4.4"), ("s2", "10.0.4.5"), (400, 12500, 200)),
         (("c1", "10.0.1.2"), ("r1", "10.0.1.4"), (200, 12500, 100)),
         (("c2", "10.0.2.2"), ("r2", "10.0.2.4"), (200, 12500, 100)),

         (("c1", "10.0.5.2"), ("r2", "10.0.5.4"), (200, 12500, 100)),
         (("c2", "10.0.6.2"), ("r1", "10.0.6.4"), (200, 12500, 100)),
         (("r1", "10.0.7.4"), ("s2", "10.0.7.5"), (400, 12500, 200)),
         (("r2", "10.0.8.4"), ("s1", "10.0.8.5"), (200, 12500, 200)),
         (("r1", "10.0.9.4"), ("r2", "10.0.9.8"), (100, 12500, 200)),
         (("s1", "10.0.10.5"), ("s2", "10.0.10.6"), (200, 12500, 100)),
         ]