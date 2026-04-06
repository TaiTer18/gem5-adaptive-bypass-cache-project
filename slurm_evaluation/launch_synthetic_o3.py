import os
import argparse
import multiprocessing as mp
from pathlib import Path
import subprocess
from run import gem5Run

def worker(run):
    run.run()
    json = run.dumpsJson()
    print(json)

def launch():
    parser = argparse.ArgumentParser()
    parser.add_argument('N', action="store", default=1, type=int, nargs='?', help="Number of cores used")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    gem5_root = str(script_dir.parent)

    l2_size = '1MB'
    assoc = 8
    target_binary = "synthetic_cache_killer.x"
    
    print("Compiling C++ Synthetic Workload natively...")
    subprocess.run(["g++", "-O3", "-static", "synthetic_cache_killer.cpp", "-o", target_binary])

    target_bin_path = os.path.abspath(target_binary)

    jobs = []
    
    for policy in ["LRURP", "AdaptiveBypassRP"]:
        for init_prob in [0, 100]:
            if policy == "LRURP" and init_prob > 0: continue
            
            name = f"synthetic_{l2_size}_{assoc}w_{policy}_{init_prob}p_O3"
            outdir = f'results/X86_SYNTHETIC/{target_binary}/{l2_size}/{assoc}/{policy}/{init_prob}'
            
            run_script_path = os.path.join(gem5_root, 'configs/evaluation/run_benchmark.py')
            
            run = gem5Run.createSERun(
                name,
                os.path.join(gem5_root, 'build/X86/gem5.opt'),
                run_script_path,
                outdir,
                '--l2_size', l2_size,
                '--l2_assoc', str(assoc),
                '--l2_initial_bypass_probability', str(init_prob),
                '--l2_rp', policy,
                '--cpu_type', 'DerivO3CPU',
                target_bin_path
            )
            jobs.append(run)

    with mp.Pool(args.N) as pool:
        pool.map(worker, jobs)

if __name__ == "__main__":
    launch()