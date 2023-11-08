import subprocess
import sys

def kill_process(process_name, port=None):
    # find process id
    command = f"ps aux | grep {process_name}"
    
    if port:
        command = f"lsof -t -i:{port}"

    try:
        ps_output = subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError:
        return f"No {process_name} process found on port {port}"

    lines = ps_output.splitlines()

    for line in lines:
        if "grep" not in line and line:
            pid = line.strip()  # Getting PID
            # kill process
            subprocess.run(f"kill {pid}", shell=True)
            return f"Killing {process_name} process with pid {pid} on port {port}"

    return f"No {process_name} process found on port {port}"

if __name__ == "__main__":
    if len(sys.argv) > 2:
        process_name = sys.argv[1]
        port = sys.argv[2]
        print(kill_process(process_name, port))
    else:
        print("Please provide the process name and the port as arguments.")
