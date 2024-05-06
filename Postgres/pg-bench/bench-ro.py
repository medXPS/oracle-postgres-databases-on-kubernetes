import subprocess
import csv
import os
import re

# Command template
command_template = "PGPASSWORD='ZzUklqhC|{{}}xQ[u:f?F8=l^z0}}' pgbench -U mohamed -h localhost -p 5432 -c {} -t 1 -S adriadb"

# Number of connections
start_connections = 100

# Increment value
increment = 10

# Number of iterations
num_iterations = 5

# Output CSV file
csv_file = "pgbench_metrics-ro.csv"

# Function to execute pgbench command and write metrics to CSV
def execute_pgbench(connections):
    command = command_template.format(connections)
    
    # Execute command
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Get output
    output, _ = process.communicate()
    
    # Decode output
    output = output.decode()
    
    # Search for metrics using regular expressions
    tps_match = re.search(r"including\s+(\d+)\s+transactions", output)
    latency_match = re.search(r"latency\s+(\d+\.\d+)\s+ms", output)
    
    if tps_match and latency_match:
        tps = tps_match.group(1)
        latency = latency_match.group(1)
        return [connections, tps, latency]
    else:
        return None

# Create CSV file and write header row if it doesn't exist
if not os.path.isfile(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Connections", "TPS", "Latency"])

# Execute pgbench command with incremented number of connections
with open(csv_file, mode='a', newline='') as file:
    writer = csv.writer(file)
    
    for i in range(num_iterations):
        connections = start_connections + (i * increment)
        metrics = execute_pgbench(connections)
        if metrics:
            writer.writerow(metrics)
        else:
            print(f"Metrics not found for {connections} connections")
