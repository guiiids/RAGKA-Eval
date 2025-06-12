#!/usr/bin/env python3
import json
import os

# Determine paths
base_dir = os.path.dirname(__file__)
input_path = os.path.join(base_dir, '..', 'egressips (1).json')
output_path = os.path.expanduser('~/Desktop/ip_ncali.txt')

# Load JSON and collect addresses
with open(input_path, 'r') as f:
    data = json.load(f)

addresses = []
for region_list in data.get('region', {}).values():
    for entry in region_list:
        addr = entry.get('address', '').strip()
        if addr:
            addresses.append(addr)

# Write to Desktop/ip_ncali.txt
with open(output_path, 'w') as f:
    f.write('\n'.join(addresses))

print(f"Wrote {len(addresses)} addresses to {output_path}")
