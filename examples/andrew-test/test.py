import sys
sys.path.append('../..')
from utils.experiment_helpers import traceroute

returncode, output = traceroute('s1', '10.0.14.6')
print(returncode, output)
