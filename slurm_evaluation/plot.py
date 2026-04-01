import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def parse_stats_file(filepath):
    """
    Parses a single gem5 stats.txt file and extracts key performance metrics.
    Returns a dictionary of the extracted values.
    """
    stats = {
        'ipc': 0.0,
        'l2_miss_rate': 0.0,
        'effective_bypasses': 0,
        'ineffective_bypasses': 0
    }
    
    if not os.path.exists(filepath):
        return stats

    committed_insts = None
    num_cycles = None

    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('system.cpu.ipc '):
                stats['ipc'] = float(line.split()[1])
            elif line.startswith('system.cpu.committedInsts '):
                committed_insts = float(line.split()[1])
            elif line.startswith('system.cpu.numCycles '):
                num_cycles = float(line.split()[1])
            elif (
                line.startswith('system.l2cache.overall_miss_rate::total')
                or line.startswith('system.l2cache.overallMissRate::total')
            ):
                stats['l2_miss_rate'] = float(line.split()[1])
            elif 'system.l2cache.replacement_policy.effectiveBypasses' in line:
                stats['effective_bypasses'] = int(line.split()[1])
            elif 'system.l2cache.replacement_policy.ineffectiveBypasses' in line:
                stats['ineffective_bypasses'] = int(line.split()[1])

    # Some gem5 configs don't emit system.cpu.ipc explicitly. Derive it.
    if stats['ipc'] == 0.0 and committed_insts and num_cycles and num_cycles > 0:
        stats['ipc'] = committed_insts / num_cycles
                
    return stats

def extract_all_data(base_dir):
    """
    Traverses the nested gem5 results directory structure:
    <base_dir>/<size>/<assoc>/<policy>/<prob>/stats.txt
    
    Returns a pandas DataFrame containing all extracted data.
    """
    data = []
    
    if not os.path.exists(base_dir):
        print(f"Error: Directory {base_dir} does not exist.")
        return pd.DataFrame()

    # Directory layout: size / assoc / policy / prob
    for size in os.listdir(base_dir):
        size_path = os.path.join(base_dir, size)
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
                    
                    # Convert prob to integer, handle LRU which is saved under '50' but doesn't use prob
                    prob_val = int(prob) if prob.isdigit() else 50
                    
                    # Size ordering helper (e.g. 128kB -> 128, 1MB -> 1024)
                    size_kb = int(size.replace('kB', '')) if 'kB' in size else int(size.replace('MB', '')) * 1024
                    
                    data.append({
                        'Size': size,
                        'Size_KB': size_kb, # Hidden column used purely for sorting the X-axis
                        'Assoc': assoc,
                        'Policy': policy,
                        'InitProb': prob_val,
                        'IPC': stats['ipc'],
                        'L2_Miss_Rate': stats['l2_miss_rate'],
                        'Effective_Bypasses': stats['effective_bypasses'],
                        'Ineffective_Bypasses': stats['ineffective_bypasses']
                    })
                    
    df = pd.DataFrame(data)
    # Sort by actual cache size so the graphs render small -> large sizes correctly
    if not df.empty:
        df = df.sort_values('Size_KB')
    return df

def plot_ipc_vs_size(df, output_dir):
    """
    Generates a bar chart comparing the IPC of Baseline LRU vs Adaptive Bypass
    across different cache sizes. For Adaptive, it samples the 0% prob run as the ideal safe-start.
    """
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    # Filter for standard LRU and Adaptive (Prob 0) since Prob 0 prevents learning-phase pollution
    lru_df = df[df['Policy'] == 'LRURP'].copy()
    adapt_df = df[(df['Policy'] == 'AdaptiveBypassRP') & (df['InitProb'] == 0)].copy()
    
    plot_df = pd.concat([lru_df, adapt_df])
    if plot_df.empty: return
        
    ax = sns.barplot(x='Size', y='IPC', hue='Policy', data=plot_df, palette="viridis")
    
    # Auto-zoom the Y-axis so microscopic performance differences are visible
    min_val = plot_df['IPC'].min()
    max_val = plot_df['IPC'].max()
    y_padding = (max_val - min_val) * 0.15
    if y_padding == 0: y_padding = 0.05
    plt.ylim(min_val - y_padding, max_val + y_padding)
    
    plt.title('IPC Comparison: LRU vs Adaptive Bypassing across Cache Sizes')
    plt.ylabel('Instructions Per Cycle (Higher is Better)')
    plt.xlabel('L2 Cache Size')
    
    plt.savefig(os.path.join(output_dir, 'ipc_vs_size.png'), dpi=300, bbox_inches='tight')
    print(f"Saved plot: {os.path.join(output_dir, 'ipc_vs_size.png')}")
    plt.close()

def plot_miss_rate_vs_prob(df, target_size, output_dir):
    """
    Generates a line plot showing how the L2 Miss Rate changes as the initial
    bypass probability shifts for a specifically chosen cache size.
    """
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    # Filter for the target size under Adaptive policy
    adapt_df = df[(df['Policy'] == 'AdaptiveBypassRP') & (df['Size'] == target_size)].copy()
    if adapt_df.empty: return
        
    # Sort strictly by Initial Probability for a smooth line chart
    adapt_df = adapt_df.sort_values('InitProb')
    
    sns.lineplot(x='InitProb', y='L2_Miss_Rate', data=adapt_df, marker='o', linewidth=2.5, color='coral')
    
    # Get the LRU baseline for this specific cache size to plot a static horizontal reference line
    lru_baseline = df[(df['Policy'] == 'LRURP') & (df['Size'] == target_size)]['L2_Miss_Rate'].mean()
    if not pd.isna(lru_baseline):
        plt.axhline(lru_baseline, ls='--', color='gray', label='Baseline LRU')
        plt.legend()
        
        # Force the Y-axis to expand so the baseline LRU line is actually visible on the chart!
        current_ymin, current_ymax = plt.ylim()
        padding = abs(lru_baseline - current_ymin) * 0.5
        if padding == 0: padding = 0.001
        plt.ylim(min(current_ymin, lru_baseline - padding), max(current_ymax, lru_baseline + padding))
        
    plt.title(f'L2 Miss Rate vs Initial Bypass Probability ({target_size} L2 Cache)')
    plt.ylabel('L2 Miss Rate (Lower is Better)')
    plt.xlabel('Initial Bypass Probability (%)')
    
    filename = f'missrate_vs_prob_{target_size}.png'
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    print(f"Saved plot: {os.path.join(output_dir, filename)}")
    plt.close()

def plot_bypass_efficacy(df, target_size, output_dir):
    """
    Plots a stacked bar chart explicitly revealing the volume of Effective vs Ineffective
    protective bypass decisions made by the Cache tracker at a specific cache size.
    """
    adapt_df = df[(df['Policy'] == 'AdaptiveBypassRP') & (df['Size'] == target_size)].copy()
    if adapt_df.empty: return
        
    adapt_df = adapt_df.sort_values('InitProb')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    probs = adapt_df['InitProb'].astype(str)
    eff = adapt_df['Effective_Bypasses'].values
    ineff = adapt_df['Ineffective_Bypasses'].values
    
    # Stack the graphs visually
    ax.bar(probs, eff, label='Effective Bypasses', color='mediumseagreen')
    ax.bar(probs, ineff, bottom=eff, label='Ineffective Bypasses', color='crimson')
    
    ax.set_ylabel('Number of Bypasses Taken')
    ax.set_xlabel('Initial Bypass Probability Start State (%)')
    ax.set_title(f'Bypass Tracker Accuracy Breakdown ({target_size} L2 Cache)')
    ax.legend()
    
    filename = f'bypass_accuracy_{target_size}.png'
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    print(f"Saved plot: {os.path.join(output_dir, filename)}")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract gem5 stats and generate analysis plots.")
    parser.add_argument('--results_dir', type=str, required=True, help="Path to the binary evaluation folder (e.g. results/X86/is_eval/is.S)")
    parser.add_argument('--plot', type=str, choices=['all', 'ipc_size', 'miss_prob', 'accuracy'], default='all', help="Which plot to generate")
    parser.add_argument('--target_size', type=str, default='256kB', help="Target cache size for probability/accuracy plots (default: 256kB)")
    parser.add_argument('--out_dir', type=str, default='plots', help="Directory to save the generated plots")
    
    args = parser.parse_args()
    
    # Setup output
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
        print(f"Created plotting output directory: {args.out_dir}/")
        
    print(f"Extracting nested gem5 stats from {args.results_dir} ...")
    df = extract_all_data(args.results_dir)
    
    if df.empty:
        print("No valid stats.txt files found. Check your --results_dir argument!")
        exit(1)
        
    # Standardize data backup
    csv_path = os.path.join(args.out_dir, "extracted_metrics_summary.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved global metrics to CSV: {csv_path}")
    
    # Dispatch rendering
    if args.plot in ['all', 'ipc_size']:
        plot_ipc_vs_size(df, args.out_dir)
        
    if args.plot in ['all', 'miss_prob']:
        plot_miss_rate_vs_prob(df, args.target_size, args.out_dir)
        
    if args.plot in ['all', 'accuracy']:
        plot_bypass_efficacy(df, args.target_size, args.out_dir)
        
    print("Graph generation finished.")
