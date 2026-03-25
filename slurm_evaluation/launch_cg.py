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
    parser.add_argument('N', action="store",
                      default=1, type=int,
                      help="Number of cores used for simulation multiprocessing")
    args = parser.parse_args()

    # Derive gem5 root
    script_dir = Path(__file__).resolve().parent
    gem5_root = str(script_dir.parent)
    print(f"Using gem5 root: {gem5_root}")

    bm_list = []

    # Point directly to the specific cg.S.x benchmark
    cg_bin_path = os.path.join(gem5_root, 'NPB3.3.1/NPB3.3-SER/bin/cg.S.x')
    
    if os.path.isfile(cg_bin_path) and os.access(cg_bin_path, os.X_OK):
        bm_list.append(('cg.S', cg_bin_path))
    else:
        print(f"Error: Could not find executable {cg_bin_path}")
        exit(1)

    jobs = []

    # Evaluate Baseline LRU vs Adaptive Bypass
    l2_sizes = ['128kB', '256kB', '512kB', '1MB']
    l2_assocs = [8]
    initial_probs = [0, 20, 50, 80, 100]
    policies = ['LRURP', 'AdaptiveBypassRP']
    
    for bm_name, binary_path in bm_list:
        for l2_size in l2_sizes:
            for assoc in l2_assocs:
                for policy in policies:
                    # LRU doesn't have an initial probability, so test it once per assoc
                    probs_to_test = [50] if policy == 'LRURP' else initial_probs
                    
                    for prob in probs_to_test:
                        name = f"{bm_name}_{l2_size}_{assoc}w_{policy}_{prob}p"
                        outdir = f'results/X86/cg_eval/{bm_name}/{l2_size}/{assoc}w/{policy}/{prob}'
                        
                        run_script_path = os.path.join(gem5_root, 'configs/evaluation/run_benchmark.py')
                        
                        run = gem5Run.createSERun(
                            name,
                            os.path.join(gem5_root, 'build/X86/gem5.opt'),
                            run_script_path,
                            outdir,
                            '--l2_size', l2_size,
                            '--l2_assoc', str(assoc),
                            '--l2_initial_bypass_probability', str(prob),
                            '--l2_rp', policy,
                            binary_path
                        )
                        jobs.append(run)

    with mp.Pool(args.N) as pool:
        pool.map(worker, jobs)
