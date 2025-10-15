import os
import subprocess
import shutil
import csv
import re
import pandas as pd
import matplotlib.pyplot as plt

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Paths
bin_dir = "bin_reps_baseline"
results_file = "reps_baseline_results.csv"

# Fixed parameters for BASELINE test
N = 2048  # Fixed matrix size
SCHEDULE = "baseline"  # Fixed schedule type
CHUNK_SIZE = "n/a"  # Not applicable for baseline
THREADS = 1  # Single thread for baseline

# Variable parameter: REPS
REPS_VALUES = [1, 5, 10, 50, 100, 200]

# --- Setup ---
# Ensure the bin directory exists and clear it for a fresh run
if os.path.exists(bin_dir):
    shutil.rmtree(bin_dir)
os.makedirs(bin_dir)

# --- CSV Initialization ---
header = ["reps", "N", "schedule", "chunk_size", "threads", "loop1_time_s", "loop2_time_s", "loop1_avg_time_ms", "loop2_avg_time_ms"]
with open(results_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(header)

# --- Main Execution Logic ---
print("Starting REPS measurement process...")
print(f"Fixed Configuration: N={N}, Schedule={SCHEDULE}, Chunk={CHUNK_SIZE}, Threads={THREADS}")
print(f"Testing REPS values: {REPS_VALUES}\n")

for reps in REPS_VALUES:
    print(f"Processing REPS = {reps}")
    
    # 1. Compile the C++ source for the specific N and REPS
    exe_file = os.path.join(bin_dir, f"main_reps{reps}")
    compile_command = (
        f"g++ -O3 -fopenmp -march=native "
        f"-o {exe_file} main.cc -DN={N} -Dreps={reps}"
    )
    
    compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)
    if compile_result.returncode != 0:
        print(f"  [Error] Compilation failed for REPS={reps}:\n{compile_result.stderr}")
        continue
    
    print(f"  Compilation successful.")

    # 2. Run the compiled executable
    print(f"  Running test...")
    
    # Set environment variables for OpenMP (Baseline Configuration)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(THREADS)
    # For baseline, we do not set OMP_SCHEDULE.
    # Optional: prevent dynamic teams from changing thread count
    env["OMP_DYNAMIC"] = "FALSE"

    # Run the command
    result = subprocess.run(exe_file, shell=True, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"    [Error] Execution failed:\n{result.stderr}")
        continue

    # 3. Parse the output to find timings
    output = result.stdout
    try:
        # Use regex to find the floating-point numbers
        time1_match = re.search(r"Total time for \d+ reps of loop 1 = ([\d.]+)", output)
        time2_match = re.search(r"Total time for \d+ reps of loop 2 = ([\d.]+)", output)

        if not time1_match or not time2_match:
            raise ValueError("Could not find time values in output.")

        loop1_time = float(time1_match.group(1))
        loop2_time = float(time2_match.group(1))
        
        # Calculate average time per iteration (in milliseconds)
        loop1_avg_time_ms = (loop1_time / reps) * 1000
        loop2_avg_time_ms = (loop2_time / reps) * 1000
        
        # 4. Write the results to the CSV file
        row = [reps, N, SCHEDULE, CHUNK_SIZE, THREADS, loop1_time, loop2_time, loop1_avg_time_ms, loop2_avg_time_ms]
        with open(results_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
        
        print(f"  Total time - Loop1: {loop1_time:.4f}s, Loop2: {loop2_time:.4f}s")
        print(f"  Avg time - Loop1: {loop1_avg_time_ms:.4f}ms, Loop2: {loop2_avg_time_ms:.4f}ms")

    except (ValueError, IndexError) as e:
        print(f"    [Error] Failed to parse output for REPS={reps}: {e}")
        print(f"      Output was:\n---\n{output}\n---")

print(f"\nAll measurements completed. Results saved to '{results_file}'")

# --- Plotting ---
print("\nGenerating plots...")

# Load data
df = pd.read_csv(results_file)

# Create figure with 2 subplots
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Plot 1: Total execution time vs. REPS
axes[0].plot(df['reps'], df['loop1_time_s'], marker='o', linestyle='-', linewidth=2, label='Loop 1', color='#2E86AB')
axes[0].plot(df['reps'], df['loop2_time_s'], marker='s', linestyle='-', linewidth=2, label='Loop 2', color='#A23B72')
axes[0].set_xlabel('Number of Repetitions (reps)', fontsize=12)
axes[0].set_ylabel('Total Execution Time (s)', fontsize=12)
axes[0].set_title(f'Baseline Total Execution Time vs. REPS\n(N={N}, Threads={THREADS})', fontsize=13)
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)
axes[0].set_xscale('log')
axes[0].set_yscale('log')

# Plot 2: Average time per iteration vs. REPS
axes[1].plot(df['reps'], df['loop1_avg_time_ms'], marker='o', linestyle='-', linewidth=2, label='Loop 1', color='#2E86AB')
axes[1].plot(df['reps'], df['loop2_avg_time_ms'], marker='s', linestyle='-', linewidth=2, label='Loop 2', color='#A23B72')
axes[1].set_xlabel('Number of Repetitions (reps)', fontsize=12)
axes[1].set_ylabel('Average Time per Iteration (ms)', fontsize=12)
axes[1].set_title(f'Baseline Average Iteration Time vs. REPS\n(N={N}, Threads={THREADS})', fontsize=13)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)
axes[1].set_xscale('log')
axes[1].set_yscale('log')

plt.tight_layout()

# Save the figure
output_filename = 'reps_analysis_baseline.png'
plt.savefig(output_filename, dpi=150, bbox_inches='tight')
print(f"Plot saved to '{output_filename}'")
plt.close()

# Create a second figure showing the linear relationship for total time
fig2, ax = plt.subplots(1, 1, figsize=(10, 6))

ax.plot(df['reps'], df['loop1_time_s'], marker='o', linestyle='-', linewidth=2, label='Loop 1', color='#2E86AB')
ax.plot(df['reps'], df['loop2_time_s'], marker='s', linestyle='-', linewidth=2, label='Loop 2', color='#A23B72')
ax.set_xlabel('Number of Repetitions (reps)', fontsize=12)
ax.set_ylabel('Total Execution Time (s)', fontsize=12)
ax.set_title(f'Baseline Linear Scale: Total Execution Time vs. REPS\n(N={N}, Threads={THREADS})', fontsize=13)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()

# Save the second figure
output_filename2 = 'reps_analysis_baseline_linear.png'
plt.savefig(output_filename2, dpi=150, bbox_inches='tight')
print(f"Plot saved to '{output_filename2}'")
plt.close()

print("\nAnalysis complete!")
print(f"\nSummary:")
print(f"  Configuration: N={N}, Schedule={SCHEDULE}, Chunk Size={CHUNK_SIZE}, Threads={THREADS}")
print(f"  REPS range: {min(REPS_VALUES)} to {max(REPS_VALUES)}")
print(f"  Results saved to: {results_file}")
print(f"  Plots saved to: {output_filename}, {output_filename2}")
