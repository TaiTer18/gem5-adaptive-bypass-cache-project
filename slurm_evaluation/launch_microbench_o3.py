import os
import argparse
import multiprocessing as mp
from pathlib import Path
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

    l2_size = '32kB'
    assoc = 8

    # The exact isolated 5 workloads required to map the spectrum of cache behavior
    benchmarks = ['MM', 'ML2', 'MIM', 'STL2', 'CCa']

    jobs = []
    
    for bm in benchmarks:
        target_binary = os.path.join(script_dir, "microbench", bm, "bench.X86")
        
        for policy in ["LRURP", "AdaptiveBypassRP"]:
            for init_prob in [0, 100]:
                if policy == "LRURP" and init_prob > 0: continue
                
                name = f"microbench_{bm}_{l2_size}_{assoc}w_{policy}_{init_prob}p_O3"
                outdir = f'results/X86_MICROBENCH/{bm}/{l2_size}/{assoc}/{policy}/{init_prob}'
                
                run_script_path = os.path.join(gem5_root, 'configs/evaluation/run_benchmark.py')
                
                # Verify that the binary has been compiled by the user
                if not os.path.isfile(target_binary):
                    print(f"WARNING: Native binary {target_binary} not found! Please compile natively first.")
                    continue

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
                    target_binary
                )
                jobs.append(run)

    with mp.Pool(args.N) as pool:
        pool.map(worker, jobs)

if __name__ == "__main__":
    launch()
