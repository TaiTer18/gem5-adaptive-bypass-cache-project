import os
import re
import matplotlib.pyplot as plt

def parse():
    base_dir = "results/X86_SYNTHETIC/synthetic_cache_killer.x/1MB/8"
    lru_file = os.path.join(base_dir, "LRURP/0/stats.txt")
    adapt_file = os.path.join(base_dir, "AdaptiveBypassRP/100/stats.txt")
    
    if not os.path.exists(lru_file) or not os.path.exists(adapt_file):
        print("Waiting for SLURM jobs to complete to extract stats...")
        return
    
    lru_ipc = 0
    adapt_ipc = 0
    
    with open(lru_file, 'r') as f:
        for line in f:
            if 'system.cpu.ipc' in line:
                lru_ipc = float(line.split()[1])
                break
                
    with open(adapt_file, 'r') as f:
        for line in f:
            if 'system.cpu.ipc' in line:
                adapt_ipc = float(line.split()[1])
                break
                
    pct_increase = ((adapt_ipc - lru_ipc) / lru_ipc) * 100
    
    plt.figure(figsize=(6, 8))
    bars = plt.bar(['LRU Baseline', 'Adaptive Bypass (V2)'], [lru_ipc, adapt_ipc], color=['lightgray', 'mediumseagreen'])
    plt.title('Out-of-Order IPC Verification (Synthetic V2)', fontsize=14)
    plt.ylabel('Instructions Per Cycle (IPC)')
    
    plt.text(bars[1].get_x() + bars[1].get_width()/2, adapt_ipc + 0.05, f"+{pct_increase:.1f}%\nSpeedup!", ha='center', color='green', fontweight='bold', fontsize=12)
    
    plt.ylim(0, max(lru_ipc, adapt_ipc) * 1.3)
    os.makedirs('plots_all', exist_ok=True)
    plt.savefig('plots_all/8_synthetic_ipc_verification.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"LRU IPC: {lru_ipc:.4f}")
    print(f"Adapt IPC: {adapt_ipc:.4f}")
    if adapt_ipc > lru_ipc:
        print(f"Geometric Speedup Verified: {pct_increase:.2f}% !!!")
    else:
        print("Pipeline bottleneck not fully mitigated.")

if __name__ == "__main__":
    parse()
