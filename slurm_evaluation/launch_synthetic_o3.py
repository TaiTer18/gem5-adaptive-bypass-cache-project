import os
import subprocess

def launch():
    l2_size = "1MB"
    assoc = 8
    target_binary = "synthetic_cache_killer.x"
    
    print("Compiling C++ Synthetic Workload natively...")
    subprocess.run(["g++", "-O3", "-static", "synthetic_cache_killer.cpp", "-o", target_binary])

    for policy in ["LRURP", "AdaptiveBypassRP"]:
        for init_prob in [0, 100]:
            if policy == "LRURP" and init_prob > 0: continue
            
            output_dir = f"results/X86_SYNTHETIC/{target_binary}/{l2_size}/{assoc}/{policy}/{init_prob}"
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                "../../build/X86/gem5.opt",
                f"--outdir={output_dir}",
                "../configs/evaluation/run_benchmark.py",
                f"--binary={os.path.abspath(target_binary)}",
                f"--l2_size={l2_size}",
                f"--l2_assoc={assoc}",
                f"--l2_rp={policy}",
                f"--init_prob={init_prob}",
                "--cpu_type=DerivO3CPU"
            ]
            print(f"Running synthetic {policy} (init={init_prob}) on O3CPU")
            subprocess.run(cmd)

if __name__ == "__main__":
    launch()
