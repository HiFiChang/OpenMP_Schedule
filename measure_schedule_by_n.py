import os
import subprocess
import shutil
import csv
import re

# --- Configuration ---
# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Paths
bin_dir = "bin"
results_dir = "results"
results_file = os.path.join(results_dir, "schedule_by_n_results.csv")

# Experiment parameters
N_VALUES = [256, 512, 729, 1024, 1440, 2048, 2880, 4096, 6144, 8192]
SCHEDULES = ["static", "dynamic", "guided"]
CHUNK_SIZES = [1, 16, 64]
THREADS = os.cpu_count() or 8 # Use all available cores, or 8 as a fallback
REPS = 1000 # Must match the 'reps' used in the C++ code if not passed via -D

# --- Setup ---
# Ensure the bin and results directories exist, and clear them for a fresh run
for directory in [bin_dir, results_dir]:
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

# --- CSV Initialization ---
header = [
    "N", 
    "schedule", 
    "chunk_size", 
    "threads", 
    "reps", 
    "loop1_time_s", 
    "loop2_time_s"
]
with open(results_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)

# --- Main Execution Logic ---
print("Starting measurement process...")
print(f"Configuration: Ns={N_VALUES}, Schedules={SCHEDULES}, Chunks={CHUNK_SIZES}, Threads={THREADS}, Reps={REPS}")

for n in N_VALUES:
    print(f"\nProcessing N = {n}")
    
    # 1. Compile the C++ source for the specific N and REPS
    exe_file = os.path.join(bin_dir, f"main_n{n}")
    compile_command = (
        f"g++ -O3 -fopenmp -march=native "
        f"-o {exe_file} main.cc -DN={n} -Dreps={REPS}"
    )
    
    compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)
    if compile_result.returncode != 0:
        print(f"  [Error] Compilation failed for N={n}:\n{compile_result.stderr}")
        continue # Skip to the next N value
    
    print(f"  Compilation successful for N={n}.")

    # 2. Run the compiled executable for each schedule and chunk size
    for schedule in SCHEDULES:
        for chunk in CHUNK_SIZES:
            print(f"  Running test: schedule={schedule}, chunk={chunk}...")
            
            # Set environment variables for OpenMP
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = str(THREADS)
            env["OMP_SCHEDULE"] = f"{schedule},{chunk}"

            # Run the command
            run_command = exe_file
            result = subprocess.run(run_command, shell=True, capture_output=True, text=True, env=env)
            
            if result.returncode != 0:
                print(f"    [Error] Execution failed:\n{result.stderr}")
                continue

            # 3. Parse the output to find timings
            output = result.stdout
            try:
                # Use regex to find the floating-point numbers in the specific lines
                time1_match = re.search(r"Total time for \d+ reps of loop 1 = ([\d.]+)", output)
                time2_match = re.search(r"Total time for \d+ reps of loop 2 = ([\d.]+)", output)

                if not time1_match or not time2_match:
                    raise ValueError("Could not find time values in output.")

                loop1_time = float(time1_match.group(1))
                loop2_time = float(time2_match.group(1))
                
                # 4. Write the results to the CSV file
                row = [n, schedule, chunk, THREADS, REPS, loop1_time, loop2_time]
                with open(results_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(row)

            except (ValueError, IndexError) as e:
                print(f"    [Error] Failed to parse output for N={n}, schedule={schedule}, chunk={chunk}: {e}")
                print(f"      Output was:\n---\n{output}\n---")

        # Also run one test per schedule using the default chunk size
        print(f"  Running test: schedule={schedule}, chunk=default...")

        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(THREADS)
        env["OMP_SCHEDULE"] = f"{schedule}"

        run_command = exe_file
        result = subprocess.run(run_command, shell=True, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            print(f"    [Error] Execution failed:\n{result.stderr}")
            continue

        output = result.stdout
        try:
            time1_match = re.search(r"Total time for \d+ reps of loop 1 = ([\d.]+)", output)
            time2_match = re.search(r"Total time for \d+ reps of loop 2 = ([\d.]+)", output)

            if not time1_match or not time2_match:
                raise ValueError("Could not find time values in output.")

            loop1_time = float(time1_match.group(1))
            loop2_time = float(time2_match.group(1))

            row = [n, schedule, "default", THREADS, REPS, loop1_time, loop2_time]
            with open(results_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(row)

        except (ValueError, IndexError) as e:
            print(f"    [Error] Failed to parse output for N={n}, schedule={schedule}, chunk=default: {e}")
            print(f"      Output was:\n---\n{output}\n---")

    # Baseline run: single-thread, default scheduling (no explicit chunk)
    print("  Running baseline: threads=1, default schedule...")

    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    # Ensure no explicit schedule is set so runtime uses its default
    env.pop("OMP_SCHEDULE", None)
    # Optional: prevent dynamic teams from changing thread count
    env["OMP_DYNAMIC"] = "FALSE"

    result = subprocess.run(exe_file, shell=True, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print(f"    [Error] Baseline execution failed:\n{result.stderr}")
        continue

    output = result.stdout
    try:
        time1_match = re.search(r"Total time for \d+ reps of loop 1 = ([\d.]+)", output)
        time2_match = re.search(r"Total time for \d+ reps of loop 2 = ([\d.]+)", output)

        if not time1_match or not time2_match:
            raise ValueError("Could not find time values in output.")

        loop1_time = float(time1_match.group(1))
        loop2_time = float(time2_match.group(1))

        row = [n, "baseline", "n/a", 1, REPS, loop1_time, loop2_time]
        with open(results_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)

    except (ValueError, IndexError) as e:
        print(f"    [Error] Failed to parse output for baseline N={n}: {e}")
        print(f"      Output was:\n---\n{output}\n---")

print(f"\nAll measurements completed. Results are saved in '{results_file}'")
