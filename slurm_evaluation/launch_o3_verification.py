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
    parser.add_argument('N', action="store", default=1, type=int, help="Number of cores used")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    gem5_root = str(script_dir.parent)

    cg_bin_path = os.path.join(gem5_root, 'NPB3.3.1/NPB3.3-SER/bin/cg.S.x')
    
    if not (os.path.isfile(cg_bin_path) and os.access(cg_bin_path, os.X_OK)):
        print(f"Error: Could not find executable {cg_bin_path}")
        exit(1)

    jobs = []

    # Targeted run: CG at 1MB L2 with O3CPU
    bm_name = 'cg.S'
    l2_size = '1MB'
    assoc = 8
    
    # We evaluate normal LRU vs AdaptiveBypass 0%
    configurations = [
        ('LRURP', 50),
        ('AdaptiveBypassRP', 0)
    ]
    
    for policy, prob in configurations:
        name = f"{bm_name}_{l2_size}_{assoc}w_{policy}_{prob}p_O3"
        outdir = f'results/X86_O3/verification/{bm_name}/{l2_size}/{assoc}w/{policy}/{prob}'
        
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
            '--cpu_type', 'DerivO3CPU',
            cg_bin_path
        )
        jobs.append(run)

    with mp.Pool(args.N) as pool:
        pool.map(worker, jobs)
