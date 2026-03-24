import os
import argparse
import multiprocessing as mp
from pathlib import Path
from run import gem5Run

def worker(run):
    run.run()
    json = run.dumpsJson()
    print(json)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('experiment', choices=['adaptive_eval'],
                      help='Which experiment to run')
    parser.add_argument('N', action="store",
                      default=1, type=int,
                      help="Number of cores used for simulation multiprocessing")
    args = parser.parse_args()

    bm_list = []

    # Derive gem5 root from this script's location (slurm_evaluation/ -> parent = gem5 root)
    script_dir = Path(__file__).resolve().parent
    gem5_root = str(script_dir.parent)
    print(f"Using gem5 root: {gem5_root}")

    # Iterate through the gem5 test-progs directory to find pre-built binaries
    test_progs_dir = os.path.join(gem5_root, 'tests/test-progs')
    
    if os.path.exists(test_progs_dir):
        for root, dirs, files in os.walk(test_progs_dir):
            if 'bin/x86/linux' in root:
                for file in files:
                    bm_list.append((file, os.path.join(root, file)))
    
    if not bm_list:
        print("Warning: No x86 linux binaries found in tests/test-progs.")
        print("Please compile some test programs or provide a valid benchmark directory.")
        # Fallback to hello_world just to provide an example
        bm_list.append(('hello', os.path.join(gem5_root, 'tests/test-progs/hello/bin/x86/linux/hello')))

    jobs = []

    if args.experiment == 'adaptive_eval':
        # Experiment: Evaluate Baseline LRU vs Adaptive Bypass across different L2 Cache Capacities
        cpu_type = 'TimingSimpleCPU'
        mem_type = 'DDR3_1600_8x8'
        l2_sizes = ['256kB', '512kB', '1MB', '2MB']
        policies = ['LRURP', 'AdaptiveBypassRP']
        
        for bm_name, binary_path in bm_list:
            for l2_size in l2_sizes:
                for policy in policies:
                    name = f"{bm_name}_{l2_size}_{policy}"
                    outdir = f'results/X86/adaptive_eval/{bm_name}/{l2_size}/{policy}'
                    
                    # Point to the simulation runner inside configs/
                    run_script_path = os.path.join(gem5_root, 'configs/evaluation/run_benchmark.py')
                    
                    # Pack args to gem5Run. Everything after run_script_path gets passed into the run script.
                    run = gem5Run.createSERun(
                        name,
                        os.path.join(gem5_root, 'build/X86/gem5.opt'),
                        run_script_path,
                        outdir,
                        # Arguments passed sequentially to the python simulation script
                        '--l2_size', l2_size,
                        '--l2_rp', policy,
                        binary_path # Positional argument expected by run_benchmark.py
                    )
                    jobs.append(run)

    with mp.Pool(args.N) as pool:
        pool.map(worker, jobs)
