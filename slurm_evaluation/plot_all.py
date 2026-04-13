import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def parse_stats_file(filepath):
    stats = {
        'ipc': 0.0,
        'l2_miss_rate': 0.0,
        'l2_mpki': 0.0,
        'effective_bypasses': 0,
        'ineffective_bypasses': 0,
        'sim_seconds': 0.0,
        'writebacks': 0.0
    }
    
    if not os.path.exists(filepath): return stats

    committed_insts = 0.0
    num_cycles = 0.0
    l2_misses = 0.0

    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('system.cpu.ipc '):
                stats['ipc'] = float(line.split()[1])
            elif line.startswith('system.cpu.committedInsts '):
                committed_insts = float(line.split()[1])
            elif line.startswith('system.cpu.numCycles '):
                num_cycles = float(line.split()[1])
            elif line.startswith('system.l2cache.overall_miss_rate::total') or line.startswith('system.l2cache.overallMissRate::total'):
                stats['l2_miss_rate'] = float(line.split()[1])
            elif line.startswith('system.l2cache.overall_misses::total') or line.startswith('system.l2cache.overallMisses::total'):
                l2_misses = float(line.split()[1])
            elif 'system.l2cache.replacement_policy.effectiveBypasses' in line:
                stats['effective_bypasses'] = int(line.split()[1])
            elif 'system.l2cache.replacement_policy.ineffectiveBypasses' in line:
                stats['ineffective_bypasses'] = int(line.split()[1])
            elif line.startswith('sim_seconds '):
                stats['sim_seconds'] = float(line.split()[1])
            elif 'system.l2bus.trans_dist::WritebackDirty' in line:
                stats['writebacks'] = float(line.split()[1])

    if stats['ipc'] == 0.0 and num_cycles > 0:
        stats['ipc'] = committed_insts / num_cycles
        
    if committed_insts > 0:
        stats['l2_mpki'] = l2_misses / (committed_insts / 1000.0)
                
    return stats

def extract_all_data(results_target_dir):
    data = []
    
    if not os.path.exists(results_target_dir):
        print(f"Directory {results_target_dir} does not exist.")
        return pd.DataFrame()

    for eval_dir in os.listdir(results_target_dir):
        if not eval_dir.endswith('_eval'): continue
        bm_name = eval_dir.replace('_eval', '').upper()
        eval_path = os.path.join(results_target_dir, eval_dir)
        
        for bin_dir in os.listdir(eval_path):
            bin_path = os.path.join(eval_path, bin_dir)
            if not os.path.isdir(bin_path): continue
            
            for size in os.listdir(bin_path):
                size_path = os.path.join(bin_path, size)
                if not os.path.isdir(size_path): continue
                    
                for assoc in os.listdir(size_path):
                    assoc_path = os.path.join(size_path, assoc)
                    if not os.path.isdir(assoc_path): continue
                        
                    for policy in os.listdir(assoc_path):
                        policy_path = os.path.join(assoc_path, policy)
                        if not os.path.isdir(policy_path): continue
                            
                        for prob in os.listdir(policy_path):
                            prob_path = os.path.join(policy_path, prob)
                            if not os.path.isdir(prob_path): continue
                                
                            stats_file = os.path.join(prob_path, 'stats.txt')
                            stats = parse_stats_file(stats_file)
                            
                            if stats['ipc'] == 0.0: continue
                            
                            prob_val = int(prob) if prob.isdigit() else 50
                            size_kb = int(size.replace('kB', '')) if 'kB' in size else int(size.replace('MB', '')) * 1024
                            
                            data.append({
                                'Benchmark': bm_name,
                                'Size': size,
                                'Size_KB': size_kb,
                                'Assoc': assoc,
                                'Policy': policy,
                                'InitProb': prob_val,
                                'IPC': stats['ipc'],
                                'L2_Miss_Rate': stats['l2_miss_rate'],
                                'L2_MPKI': stats['l2_mpki'],
                                'Effective_Bypasses': stats['effective_bypasses'],
                                'Ineffective_Bypasses': stats['ineffective_bypasses'],
                                'Sim_Seconds': stats['sim_seconds'],
                                'Writebacks': stats['writebacks']
                            })
                            
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(['Benchmark', 'Size_KB'])
    return df

def get_normalized_speedup_df(df):
    adapt_df = df[df['Policy'] == 'AdaptiveBypassRP'].copy()
    lru_df = df[df['Policy'] == 'LRURP'].copy()
    
    lru_map = lru_df.set_index(['Benchmark', 'Size', 'Assoc'])['IPC'].to_dict()
    
    def get_speedup(row):
        key = (row['Benchmark'], row['Size'], row['Assoc'])
        lru_ipc = lru_map.get(key, None)
        if lru_ipc and lru_ipc > 0:
            return row['IPC'] / lru_ipc
        return 1.0
        
    adapt_df['Speedup'] = adapt_df.apply(get_speedup, axis=1)
    return adapt_df

def plot_normalized_ipc(df, output_dir):
    speedup_df = get_normalized_speedup_df(df)
    plot_df = speedup_df[speedup_df['InitProb'] == 0]
    if plot_df.empty: return
    
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    sns.barplot(x='Benchmark', y='Speedup', hue='Size', data=plot_df, palette="crest")
    plt.axhline(1.0, ls='--', color='red', label='Baseline LRU (1.0x)')
    
    # Force bounds to perfectly flatten the micro-jitter and prove absolute computational pipeline stability
    plt.ylim(0.995, 1.005)

    plt.title('Performance Speedup: Adaptive Bypassing vs Baseline LRU')
    plt.ylabel('Normalized Speedup (Adaptive IPC / LRU IPC)')
    plt.legend()
    plt.savefig(os.path.join(output_dir, '1_normalized_ipc.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_miss_rate_vs_prob(df, output_dir):
    adapt_df = df[df['Policy'] == 'AdaptiveBypassRP'].copy()
    if adapt_df.empty: return

    # Ensure Size parameter is sorted cleanly
    unique_sizes = sorted(adapt_df['Size_KB'].unique())
    
    # Define a clean ordering mapping for the rows
    def get_size_label(s_kb): return f"{s_kb}kB" if s_kb < 1024 else f"{s_kb//1024}MB"
    adapt_df['Size_Label'] = adapt_df['Size_KB'].apply(get_size_label)
    
    # We also need the LRU baseline to draw horizontal lines
    lru_df = df[df['Policy'] == 'LRURP'].groupby(['Size_KB', 'Benchmark'])['L2_Miss_Rate'].mean().reset_index()

    sns.set_theme(style="whitegrid")
    # Share x-axis (InitProb is same 0-100), but DO NOT share y-axis so variance zooms perfectly!
    g = sns.FacetGrid(adapt_df, row="Size_Label", col="Benchmark", sharey=False, sharex=True, height=2.5, aspect=1.2)
    
    # Plot the AdaptiveBypassRP lines
    g.map(sns.lineplot, "InitProb", "L2_Miss_Rate", marker="o", color="coral")

    # Add the LRU Baseline line to each specific subplot
    for (row_val, col_val), ax in g.axes_dict.items():
        # Hide offset formatting to avoid scientific notation display bugs
        ax.ticklabel_format(useOffset=False, style='plain', axis='y')
        
        # Determine the target mapping size
        size_kb = int(row_val.replace('kB','')) if 'kB' in row_val else int(row_val.replace('MB',''))*1024
        
        lru_val_series = lru_df[(lru_df['Size_KB'] == size_kb) & (lru_df['Benchmark'] == col_val)]['L2_Miss_Rate']
        if not lru_val_series.empty:
            lru_val = lru_val_series.iloc[0]
            # Only label the very first graph so the legend doesn't visually duplicate 24 times
            draw_label = 'LRU Baseline' if ax == g.axes[0, 0] else None
            ax.axhline(lru_val, ls='--', color='gray', label=draw_label)
            
            # Pad the y-axis exactly as before for visibility
            ymin, ymax = ax.get_ylim()
            pad = abs(lru_val - ymin) * 0.5
            if pad == 0: pad = 0.001
            ax.set_ylim(min(ymin, lru_val - pad), max(ymax, lru_val + pad))
            
            if ax == g.axes[0, 0]:
                ax.legend(loc='best')
            
    # Set text labels
    g.set_titles(row_template="L2: {row_name}", col_template="{col_name}")
    g.set_axis_labels("Initial Bypass Probability (%)", "L2 Miss Rate")
    g.figure.subplots_adjust(top=0.92)
    g.figure.suptitle('L2 Miss Rate Sensitivity to Tracker Init State (All Capacities)', fontsize=18)
    
    plt.savefig(os.path.join(output_dir, '2_miss_rate_vs_prob_unified.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Cleanup any old split files and the previous grouped file
    for f in os.listdir(output_dir):
        if f.startswith('2_miss_rate_vs_prob') and f != '2_miss_rate_vs_prob_unified.png':
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception:
                pass

def plot_bypass_accuracy(df, output_dir):
    adapt_df = df[(df['Policy'] == 'AdaptiveBypassRP') & (df['InitProb'] == 0)].copy()
    if adapt_df.empty: return
    
    unique_sizes = sorted(adapt_df['Size_KB'].unique())
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, size_kb in enumerate(unique_sizes):
        if idx >= 4: break
        
        ax = axes[idx]
        sub_df = adapt_df[adapt_df['Size_KB'] == size_kb].copy()
        
        bms = sub_df['Benchmark'].values
        eff = sub_df['Effective_Bypasses'].values
        ineff = sub_df['Ineffective_Bypasses'].values
        size_str = sub_df['Size'].iloc[0] if not sub_df.empty else ""
        
        ax.bar(bms, eff, label='Effective Bypasses', color='mediumseagreen')
        ax.bar(bms, ineff, bottom=eff, label='Ineffective Bypasses', color='crimson')
        
        ax.set_title(f'L2 Size: {size_str}')
        if idx % 2 == 0:
            ax.set_ylabel('Total Bypasses Taken')
        if idx > 1:
            ax.set_xlabel('Benchmark')
        if idx == 0:
            ax.legend()
            
    # Cleanup empty subplots if fewer than 4 cache sizes exist
    for idx in range(len(unique_sizes), 4):
        fig.delaxes(axes[idx])
        
    plt.suptitle('Bypass Tracker Efficacy Breakdown by Workload & Capacity', fontsize=16, y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3_bypass_accuracy.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_mpki(df, output_dir):
    adapt_df = df[(df['Policy'] == 'AdaptiveBypassRP') & (df['InitProb'] == 0)].copy()
    if adapt_df.empty: return
    
    unique_sizes = sorted(adapt_df['Size_KB'].unique())
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, size_kb in enumerate(unique_sizes):
        if idx >= 4: break
        
        ax = axes[idx]
        target_df = df[df['Size_KB'] == size_kb].copy()
        
        lru_s = target_df[target_df['Policy'] == 'LRURP'].set_index('Benchmark')['L2_MPKI']
        adapt_s = target_df[(target_df['Policy'] == 'AdaptiveBypassRP') & (target_df['InitProb'] == 0)].set_index('Benchmark')['L2_MPKI']
        
        if lru_s.empty or adapt_s.empty: continue
        
        reduction_s = ((lru_s - adapt_s) / lru_s) * 100
        reduction_s = reduction_s.dropna()
        plot_df = pd.DataFrame({'Benchmark': reduction_s.index, 'Savings_Pct': reduction_s.values})
        size_str = target_df['Size'].iloc[0] if not target_df.empty else ""
        
        if plot_df.empty: continue
        
        colors = ['mediumseagreen' if val >= 0 else 'crimson' for val in plot_df['Savings_Pct']]
        sns.barplot(x='Benchmark', y='Savings_Pct', hue='Benchmark', legend=False, data=plot_df, palette=colors, ax=ax)
        ax.axhline(0, color='black', linewidth=1.5)
        
        ax.set_title(f'L2 Size: {size_str}')
        if idx % 2 == 0:
            ax.set_ylabel('MPKI Payload % Savings')
        else:
            ax.set_ylabel('')
        if idx > 1:
            ax.set_xlabel('Benchmark')
        else:
            ax.set_xlabel('')
            
        for p in ax.patches:
            val = p.get_height()
            if val == 0: continue
            # Avoid warnings by using the correct center point
            center_x = p.get_x() + p.get_width() / 2.
            ax.annotate(f'{val:+.2f}%', (center_x, val), 
                        ha='center', va='bottom' if val >= 0 else 'top',
                        fontsize=9, color='black', xytext=(0, 5 if val >= 0 else -12),
                        textcoords='offset points')
                        
        ymin, ymax = ax.get_ylim()
        padding = max(abs(ymin), abs(ymax)) * 0.2
        if padding == 0: padding = 0.5
        ax.set_ylim(min(ymin, -0.2) - padding, max(ymax, 0.2) + padding)
        
    for idx in range(len(unique_sizes), 4):
        fig.delaxes(axes[idx])
        
    plt.suptitle('L2 Memory Traffic Savings vs Baseline LRU Across All Capacities', fontsize=16, y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_mpki_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_speedup_vs_size_all(df, output_dir):
    speedup_df = get_normalized_speedup_df(df)
    plot_df = speedup_df[speedup_df['InitProb'] == 0].copy()
    if plot_df.empty: return
    
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    sns.lineplot(x='Size_KB', y='Speedup', hue='Benchmark', style='Benchmark', markers=True, dashes=False, data=plot_df, linewidth=2.5)
    plt.axhline(1.0, ls='--', color='gray', label='Baseline LRU (1.0x)')
    
    sizes = sorted(plot_df['Size_KB'].unique())
    size_labels = [f"{s}kB" if s < 1024 else f"{s//1024}MB" for s in sizes]
    plt.xticks(sizes, size_labels)
    
    plt.ylim(0.995, 1.005)
    
    plt.title('Capacity Evaluation: Speedup Sweep Across Cache Sizes')
    plt.ylabel('IPC Speedup vs LRU (Higher is Better)')
    plt.xlabel('L2 Cache Size')
    
    plt.legend()
    plt.savefig(os.path.join(output_dir, '5_speedup_vs_size.png'), dpi=300, bbox_inches='tight')
    plt.close()

def plot_performance_heatmap(df, output_dir):
    speedup_df = get_normalized_speedup_df(df)
    unique_sizes = sorted(speedup_df['Size_KB'].unique())
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for idx, size_kb in enumerate(unique_sizes):
        if idx >= 4: break
        
        ax = axes[idx]
        target_df = speedup_df[speedup_df['Size_KB'] == size_kb].copy()
        if target_df.empty: continue
        size_str = target_df['Size'].iloc[0]
        
        pivot = target_df.pivot_table(index='InitProb', columns='Benchmark', values='Speedup')
        
        sns.heatmap(pivot, annot=True, fmt=".4f", cmap="vlag", center=1.0, ax=ax, cbar_kws={'label': 'Speedup vs LRU'})
        
        ax.set_title(f'Capacity: {size_str} L2')
        if idx % 2 == 0:
            ax.set_ylabel('Initial Bypass Probability (%)')
        else:
            ax.set_ylabel('')
            
        if idx > 1:
            ax.set_xlabel('Benchmark')
        else:
            ax.set_xlabel('')
            
    for idx in range(len(unique_sizes), 4):
        fig.delaxes(axes[idx])
        
    plt.suptitle('Algorithmic Tracker Stability Heatmap (Unified Metrics)', fontsize=18, y=0.98)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '6_stability_heatmap_unified.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Cleanup any old split files safely
    for f in os.listdir(output_dir):
        if f.startswith('6_stability_heatmap') and f != '6_stability_heatmap_unified.png':
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 6 critical architectural visualization plots for ALL benchmarks.")
    parser.add_argument('--results_dir', type=str, default='results/X86', help="Path to the master results folder")
    parser.add_argument('--target_size', type=str, default='256kB', help="Target cache size for static-size plots")
    parser.add_argument('--out_dir', type=str, default='plots_all', help="Directory to save the generated plots")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
        print(f"Created plotting output directory: {args.out_dir}/")
        
    print(f"Recursively extracting gem5 stats from {args.results_dir} ...")
    df = extract_all_data(args.results_dir)
    
    if df.empty:
        print("No valid stats.txt files found. Evaluator stopped.")
        exit(1)
        
    csv_path = os.path.join(args.out_dir, "extracted_metrics_summary.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved master dataset to CSV: {csv_path}")
    
    print("Generating [1/6]: Normalized IPC")
    plot_normalized_ipc(df, args.out_dir)
    
    print("Generating [2/6]: Miss Rate vs Probability Grid")
    plot_miss_rate_vs_prob(df, args.out_dir)
    
    print("Generating [3/6]: Bypass Accuracy Breakdown")
    plot_bypass_accuracy(df, args.out_dir)
    
    print("Generating [4/6]: Absolute MPKI")
    plot_mpki(df, args.out_dir)
    
    print("Generating [5/6]: Speedup Sweep vs Capacity Size")
    plot_speedup_vs_size_all(df, args.out_dir)
    
    print("Generating [6/6]: Parameter Stability Heatmaps")
    plot_performance_heatmap(df, args.out_dir)
    
    print("All multi-benchmark graphs successfully generated!")
