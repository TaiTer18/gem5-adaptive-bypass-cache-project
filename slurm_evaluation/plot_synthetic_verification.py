import os
import re
import matplotlib.pyplot as plt
import seaborn as sns

def extract_ipc(stats_file):
    if not os.path.isfile(stats_file):
        return None
    with open(stats_file, 'r') as f:
        for line in f:
            if line.startswith('system.cpu.ipc'):
                match = re.search(r'system\.cpu\.ipc\s+([0-9.]+)', line)
                if match:
                    return float(match.group(1))
    return None

def main():
    print("Extracting Synthetic Verification stats...")
    base_dir = "results/X86_O3/synthetic/synthetic_killer/1MB/8w"
    
    lru_stats = os.path.join(base_dir, "LRURP/50/stats.txt")
    adapt_stats = os.path.join(base_dir, "AdaptiveBypassRP/0/stats.txt")
    
    lru_ipc = extract_ipc(lru_stats)
    adapt_ipc = extract_ipc(adapt_stats)
    
    if lru_ipc is None or adapt_ipc is None:
        print("Error: Could not find stats.txt for both configurations. Are the SLURM jobs completely finished?")
        return
        
    speedup = adapt_ipc / lru_ipc
    improvement_pct = (speedup - 1.0) * 100.0
    
    print(f"LRU IPC:      {lru_ipc:.6f}")
    print(f"Adaptive IPC: {adapt_ipc:.6f}")
    print(f"Speedup:      {speedup:.4f}x (+{improvement_pct:.2f}%)")
    
    # Plotting
    plt.figure(figsize=(8, 6))
    sns.set_theme(style="whitegrid")
    
    policies = ['Baseline LRU', 'Adaptive Bypassing']
    ipcs = [lru_ipc, adapt_ipc]
    
    ax = sns.barplot(x=policies, y=ipcs, hue=policies, palette=['#e74c3c', '#2ecc71'], legend=False)
    
    # Add absolute values on top of bars
    for i, v in enumerate(ipcs):
        ax.text(i, v + (max(ipcs)*0.01), f"{v:.4f}", color='black', ha="center", fontweight='bold')
    
    plt.ylim(0, max(ipcs) * 1.15)
    plt.title(f'Synthetic Memory-Bound IPC (Out-of-Order, 1MB L2)\\nSpeedup: {speedup:.4f}x (+{improvement_pct:.2f}%)')
    plt.ylabel('Instructions Per Cycle (IPC)')
    
    out_dir = "plots_all"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, '8_synthetic_ipc_verification.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\\nSuccessfully generated Synthetic verification graph: {out_path}")

if __name__ == "__main__":
    main()
