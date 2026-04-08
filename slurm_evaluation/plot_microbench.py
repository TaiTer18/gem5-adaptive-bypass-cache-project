import os
import matplotlib.pyplot as plt
import numpy as np

def parse():
    base_dir = "results/X86_MICROBENCH"
    benchmarks = ['MM', 'ML2', 'MIM', 'STL2', 'CCa']
    
    lru_ipcs = []
    adapt_0_ipcs = []
    adapt_100_ipcs = []
    
    for bm in benchmarks:
        lru_file = os.path.join(base_dir, bm, "1MB/8/LRURP/0/stats.txt")
        adapt_0_file = os.path.join(base_dir, bm, "1MB/8/AdaptiveBypassRP/0/stats.txt")
        adapt_100_file = os.path.join(base_dir, bm, "1MB/8/AdaptiveBypassRP/100/stats.txt")
        
        ipcs = {'lru': 0, 'a0': 0, 'a100': 0}
        
        for key, filepath in [('lru', lru_file), ('a0', adapt_0_file), ('a100', adapt_100_file)]:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    for line in f:
                        if 'system.cpu.ipc' in line and not 'ipc_total' in line:
                            ipcs[key] = float(line.split()[1])
                            break
                            
        lru_ipcs.append(ipcs['lru'])
        adapt_0_ipcs.append(ipcs['a0'])
        adapt_100_ipcs.append(ipcs['a100'])
        
    x = np.arange(len(benchmarks))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    rects1 = ax.bar(x - width, lru_ipcs, width, label='LRU Baseline', color='lightcoral')
    rects2 = ax.bar(x, adapt_0_ipcs, width, label='Adaptive (Init 0%)', color='mediumseagreen')
    rects3 = ax.bar(x + width, adapt_100_ipcs, width, label='Adaptive (Init 100%)', color='teal')
    
    ax.set_ylabel('Instructions Per Cycle (IPC)', fontsize=12, fontweight='bold')
    ax.set_title('Out-of-Order IPC Validation (Wisconsin Microbenchmarks)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(benchmarks, fontweight='bold')
    ax.legend()
    
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    os.makedirs('plots_all', exist_ok=True)
    plt.savefig('plots_all/9_microbench_ipc_verification.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Graph successfully saved to: plots_all/9_microbench_ipc_verification.png")

if __name__ == "__main__":
    parse()
