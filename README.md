# Introduction
Mosmodel is is primarily useful for architectural virtual memory studies. It allows researchers to construct mathematical models that predict the runtime of applications executing on top of some newly proposed virtual memory design. This methodology requires a partial simulation of only the said newly proposed memory subsystem, as opposed to a full "cycle accurate" simulation of the entire processor.
The Mosmodel repo is fully automated and contains all required tools to produce the Mosmodel for any workload on any x86-64 Linux system.

# Setup and Configuration
Before you start building and running Mosmodel, you need to set and configure the following:
- Update the following variables in `benchmark.mk`:
    - `BENCHMARK_COMMAND`: an executable or script that runs the benchmark.
    - `MMAP_POOL_LIMIT` (defaults to 100MB):

# Build and Run
After 

# What is Mosmodel
# Mosmodel Directory Structure

# Prerequisites
- Please note that makefile tries to download necessary packages using apt for Ubuntu. If you are using a different distribution, then please modify the makefile to use the proper package management software. 
- Sudo permissions: multiple steps requires sudo priviliges, e.g., installing apt packages (perf, numactl, ...) and reserving hugepages. We recommend to configure sudo permissions without password to fully automate the workflow. Sudo without password may stop the workflow at these steps prompting for your password.
- Python3

# Technical Details
- Mosmodel assumes that the benchmark allocates < 100MB through `mmap()`. In case your benchmark allocates more than 100MB, please increase the `MMAP_POOL_LIMIT` in benchmark.mk
- Mosmodel uses Intel PEBS to find interesting Mosalloc layouts. PEBS only works on Intel Broadwell processors or newer.

# TODO
Currently, Mosmodel scans only Mosalloc layouts on the `brk()` pool because it assumes that the benchmark allocates memory through `malloc()`. In case the benchmark uses different allocators (than glibc `malloc()`), then this assumption may not hold. We need to customize the python scripts and makefile infrastructure that create the Mosalloc layouts. The first step toward this goal is running the `mmap_vs_brk` experiments to measure the performance impact of hugepages in the `mmap()` and `brk()` pools, respectively. 
