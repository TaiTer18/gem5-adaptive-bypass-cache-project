# Adaptive Bypass Cache Replacement in gem5

This project implements and evaluates an adaptive cache bypassing policy for the last-level cache (LLC) in the gem5 architectural simulator.

Instead of always inserting data into the cache, the policy dynamically learns when it is beneficial to bypass insertion, reducing cache pollution and improving overall efficiency.

---

## Authors

- Sara Magdalinski  
- Nicholas Tait  

Simon Fraser University  
CMPT 450/750 — Spring 2026

---

## Overview

Traditional cache replacement policies such as LRU can perform poorly in the LLC, where many cache lines are never reused. This leads to cache pollution and reduced effective cache capacity.

This project explores an adaptive bypassing approach that:
- Identifies low-value cache insertions
- Dynamically adjusts bypass probability based on observed outcomes
- Improves performance depending on workload characteristics

We evaluate the policy using:
- NAS Parallel Benchmarks (NPB)
- Multiple cache configurations
- Microbenchmarks and validation experiments

---

## Evaluation Metrics

We analyze performance using the following metrics:
- IPC (Instructions Per Cycle)
- Miss Rate / MPKI
- Bypass effectiveness
- Memory traffic trends

---

## Getting Started

Full setup, build, and execution instructions are provided in:

[HOW_TO_RUN.md](./HOW_TO_RUN.md)

This includes:
- gem5 setup and build
- Benchmark compilation
- Running experiments (including SLURM)
- Generating results and graphs

---

## Dependencies

This project is built on top of the gem5 architectural simulator:

- gem5: https://www.gem5.org/

Please refer to the official gem5 documentation for installation details and system requirements.
