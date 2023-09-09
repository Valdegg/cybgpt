import subprocess
import sys

def kill_process(process_name):
    # find process id
    ps_output = subprocess.check_output(f"ps aux | grep {process_name}", shell=True, text=True)
    lines = ps_output.splitlines()

    for line in lines:
        if "grep" not in line:
            fields = line.split()
            pid = fields[1]
            # kill process
            subprocess.run(f"kill {pid}", shell=True)
            return f"Killing {process_name} process with pid {pid}"

    return f"No {process_name} process found"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for process_name in sys.argv[1:]:
            print(kill_process(process_name))
    else:
        print("Please provide at least one process name as an argument.")