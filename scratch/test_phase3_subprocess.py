import subprocess
import time
import sys
import os

print("Starting FL Server...")
server_process = subprocess.Popen(
    [sys.executable, "-m", "src.fl_server.main", "--rounds", "2"],
    stdout=sys.stdout,
    stderr=sys.stderr,
)

# Wait for server to start
time.sleep(3)

print("Starting FL Clients...")
client_processes = []
for i in range(3):
    cp = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "src.fl_client.main",
            "--client-id",
            f"client_{i}",
            "--data-path",
            f"data/fl_splits/client_0{i}.csv",
            "--scaler-path",
            "data/processed/quantile_scaler.pkl",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    client_processes.append(cp)

# Wait for server to finish
server_process.wait()

# Terminate clients if still running
for cp in client_processes:
    if cp.poll() is None:
        cp.terminate()

if server_process.returncode == 0:
    print("Phase 3 FL test completed successfully!")
    sys.exit(0)
else:
    print("Phase 3 FL test failed!")
    sys.exit(1)
