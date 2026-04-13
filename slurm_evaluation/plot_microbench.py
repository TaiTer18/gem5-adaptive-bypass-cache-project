import os
import matplotlib.pyplot as plt
import numpy as np

def parse():
    base_dir = "results/X86_MICROBENCH"
    benchmarks = ['MM', 'ML2', 'MIM', 'STL2', 'CCa']
    
    lru_ipcs, adapt_0_ipcs, adapt_100_ipcs = [], [], []
    lru_reps, adapt_0_reps, adapt_100_reps = [], [], []
    lru_misses, adapt_0_misses, adapt_100_misses = [], [], []
    lru_wbs, adapt_0_wbs, adapt_100_wbs = [], [], []
    
    for bm in benchmarks:
        lru_file = os.path.join(base_dir, bm, "32kB/8/LRURP/0/stats.txt")
        adapt_0_file = os.path.join(base_dir, bm, "32kB/8/AdaptiveBypassRP/0/stats.txt")
        adapt_100_file = os.path.join(base_dir, bm, "32kB/8/AdaptiveBypassRP/100/stats.txt")
        
        ipcs = {'lru': 0.0, 'a0': 0.0, 'a100': 0.0}
        reps = {'lru': 0.0, 'a0': 0.0, 'a100': 0.0}
        misses = {'lru': 0.0, 'a0': 0.0, 'a100': 0.0}
        wbs = {'lru': 0.0, 'a0': 0.0, 'a100': 0.0}
        
        for key, filepath in [('lru', lru_file), ('a0', adapt_0_file), ('a100', adapt_100_file)]:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    for line in f:
                        if 'system.cpu.ipc' in line and not 'ipc_total' in line:
                            ipcs[key] = float(line.split()[1])
                        elif 'system.l2cache.replacements' in line:
                            reps[key] = float(line.split()[1])
                        elif 'system.l2cache.overall_misses::total' in line:
                            misses[key] = float(line.split()[1])
                        elif 'system.l2bus.trans_dist::WritebackDirty' in line:
                            wbs[key] = float(line.split()[1])
                            
        lru_ipcs.append(ipcs['lru']); adapt_0_ipcs.append(ipcs['a0']); adapt_100_ipcs.append(ipcs['a100'])
        lru_reps.append(reps['lru']); adapt_0_reps.append(reps['a0']); adapt_100_reps.append(reps['a100'])
        lru_misses.append(misses['lru']); adapt_0_misses.append(misses['a0']); adapt_100_misses.append(misses['a100'])
        lru_wbs.append(wbs['lru']); adapt_0_wbs.append(wbs['a0']); adapt_100_wbs.append(wbs['a100'])
        
    x = np.arange(len(benchmarks))
    width = 0.25
    
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    
    # IPC Plot
    axs[0, 0].bar(x - width, lru_ipcs, width, label='LRU Baseline', color='lightcoral')
    axs[0, 0].bar(x, adapt_0_ipcs, width, label='Adaptive (Init 0%)', color='mediumseagreen')
    axs[0, 0].bar(x + width, adapt_100_ipcs, width, label='Adaptive (Init 100%)', color='teal')
    axs[0, 0].set_ylabel('Instructions Per Cycle (IPC)', fontsize=12, fontweight='bold')
    axs[0, 0].set_title('Execution Speed (IPC)', fontsize=14, fontweight='bold')
    axs[0, 0].set_xticks(x); axs[0, 0].set_xticklabels(benchmarks, fontweight='bold'); axs[0, 0].legend()
    axs[0, 0].grid(axis='y', linestyle='--', alpha=0.7)

    # Replacements Plot
    axs[0, 1].bar(x - width, lru_reps, width, label='LRU Baseline', color='lightcoral')
    axs[0, 1].bar(x, adapt_0_reps, width, label='Adaptive (Init 0%)', color='mediumseagreen')
    axs[0, 1].bar(x + width, adapt_100_reps, width, label='Adaptive (Init 100%)', color='teal')
    axs[0, 1].set_ylabel('Total Evictions', fontsize=12, fontweight='bold')
    axs[0, 1].set_title('Cache Thrashing (L2 Replacements)', fontsize=14, fontweight='bold')
    axs[0, 1].set_xticks(x); axs[0, 1].set_xticklabels(benchmarks, fontweight='bold'); axs[0, 1].legend()
    axs[0, 1].grid(axis='y', linestyle='--', alpha=0.7)

    # Misses Plot
    axs[1, 0].bar(x - width, lru_misses, width, label='LRU Baseline', color='lightcoral')
    axs[1, 0].bar(x, adapt_0_misses, width, label='Adaptive (Init 0%)', color='mediumseagreen')
    axs[1, 0].bar(x + width, adapt_100_misses, width, label='Adaptive (Init 100%)', color='teal')
    axs[1, 0].set_ylabel('Total L2 Misses', fontsize=12, fontweight='bold')
    axs[1, 0].set_title('L2 Cache Misses', fontsize=14, fontweight='bold')
    axs[1, 0].set_xticks(x); axs[1, 0].set_xticklabels(benchmarks, fontweight='bold'); axs[1, 0].legend()
    axs[1, 0].grid(axis='y', linestyle='--', alpha=0.7)

    # Writeback Traffic
    axs[1, 1].bar(x - width, lru_wbs, width, label='LRU Baseline', color='lightcoral')
    axs[1, 1].bar(x, adapt_0_wbs, width, label='Adaptive (Init 0%)', color='mediumseagreen')
    axs[1, 1].bar(x + width, adapt_100_wbs, width, label='Adaptive (Init 100%)', color='teal')
    axs[1, 1].set_ylabel('Total Dirty Writebacks', fontsize=12, fontweight='bold')
    axs[1, 1].set_title('DRAM Traffic Savings (L2 to DRAM Writebacks)', fontsize=14, fontweight='bold')
    axs[1, 1].set_xticks(x); axs[1, 1].set_xticklabels(benchmarks, fontweight='bold'); axs[1, 1].legend()
    axs[1, 1].grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    os.makedirs('plots_all', exist_ok=True)
    plt.savefig('plots_all/9_microbench_ipc_verification.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Graph successfully saved to: plots_all/9_microbench_ipc_verification.png")

if __name__ == "__main__":
    parse()
