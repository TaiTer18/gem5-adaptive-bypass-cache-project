import os
import argparse
import multiprocessing as mp
from pathlib import Path
from run import gem5Run

def worker(run):
    run.run()
    json = run.dumpsJson()
    print(json)


def get_l2_sizes_for_partition(part):
    if part == '1':
        return ['128kB', '256kB']
    if part == '2':
        return ['512kB', '1MB']
    return ['128kB', '256kB', '512kB', '1MB']


def build_ft_jobs(gem5_root, part):
    bm_list = []

    # Point directly to the specific ft.S.x benchmark.
    ft_bin_path = os.path.join(gem5_root, 'NPB3.3.1/NPB3.3-SER/bin/ft.S.x')

    if os.path.isfile(ft_bin_path) and os.access(ft_bin_path, os.X_OK):
        bm_list.append(('ft.S', ft_bin_path))
    else:
        print(f"Error: Could not find executable {ft_bin_path}")
        exit(1)

    jobs = []

    # Evaluate Baseline LRU vs Adaptive Bypass.
    l2_sizes = get_l2_sizes_for_partition(part)
    l2_assocs = [8]
    initial_probs = [0, 20, 50, 80, 100]
    policies = ['LRURP', 'AdaptiveBypassRP']

    for bm_name, binary_path in bm_list:
        for l2_size in l2_sizes:
            for assoc in l2_assocs:
                for policy in policies:
                    # LRU doesn't have an initial probability, so test it once per assoc.
                    probs_to_test = [50] if policy == 'LRURP' else initial_probs

                    for prob in probs_to_test:
                        name = f"{bm_name}_{l2_size}_{assoc}w_{policy}_{prob}p"
                        outdir = f"results/X86/ft_eval/{bm_name}/{l2_size}/{assoc}w/{policy}/{prob}"

                        run_script_path = os.path.join(
                            gem5_root, 'configs/evaluation/run_benchmark.py'
                        )

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

    return jobs


def main(num_workers, part='all'):
    # Derive gem5 root.
    script_dir = Path(__file__).resolve().parent
    gem5_root = str(script_dir.parent)
    print(f"Using gem5 root: {gem5_root}")

    jobs = build_ft_jobs(gem5_root, part)
    print(f"Prepared {len(jobs)} FT jobs for partition '{part}'")

    with mp.Pool(num_workers) as pool:
        pool.map(worker, jobs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('N', action="store",
                      default=1, type=int,
                      help="Number of cores used for simulation multiprocessing")
    parser.add_argument('--part', choices=['all', '1', '2'], default='all',
                      help="Run all FT jobs or only one split partition")
    args = parser.parse_args()
    main(args.N, args.part)
