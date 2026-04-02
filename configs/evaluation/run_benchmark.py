import m5
from m5.objects import *
import os
import argparse
import sys
import shlex

# Add the common scripts to our path
m5.util.addToPath('../')
from common import SimpleOpts

class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def connectBus(self, bus):
        self.mem_side = bus.slave
    def connectCPU(self, cpu):
        raise NotImplementedError

class L1ICache(L1Cache):
    size = '16kB'
    def __init__(self, size=None):
        super(L1ICache, self).__init__()
        if size: self.size = size
    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port

class L1DCache(L1Cache):
    size = '64kB'
    def __init__(self, size=None):
        super(L1DCache, self).__init__()
        if size: self.size = size
    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port

class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

    def __init__(self, size=None, assoc=8, rp='LRURP', initial_bypass_probability=50):
        super(L2Cache, self).__init__()
        if size: self.size = size
        self.assoc = assoc
        
        if rp == 'AdaptiveBypassRP':
            self.replacement_policy = AdaptiveBypassRP(
                initial_bypass_probability=initial_bypass_probability
            )
        else:
            self.replacement_policy = LRURP()

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.master
    def connectMemSideBus(self, bus):
        self.mem_side = bus.slave

SimpleOpts.add_option('--l2_size', default='256kB', help="L2 cache size")
SimpleOpts.add_option('--l2_assoc', default=8, type="int", help="L2 cache set associativity")
SimpleOpts.add_option('--l2_rp', default='LRURP', choices=['LRURP', 'AdaptiveBypassRP'], help="Replacement Policy")
SimpleOpts.add_option('--l2_initial_bypass_probability', default=50, type='int', help="Initial bypass probability (0-100) for AdaptiveBypassRP")
SimpleOpts.add_option('--cpu_type', default='TimingSimpleCPU', choices=['TimingSimpleCPU', 'DerivO3CPU'], help="CPU model to use")
SimpleOpts.add_option('--binary_args', default='', help="Quoted argument string passed to the benchmark binary")
SimpleOpts.add_option('--env', action='append', default=[], help="Environment variables for the benchmark process (format: KEY=VALUE)")
SimpleOpts.add_option('--omp_threads', default=1, type='int', help="Value for OMP_NUM_THREADS in benchmark process environment")
(opts, args) = SimpleOpts.parse_args()

if len(args) != 1:
    print("Error: Expected exactly one positional argument for the binary to execute.")
    sys.exit(1)

binary = args[0]

if opts.l2_initial_bypass_probability < 0 or opts.l2_initial_bypass_probability > 100:
    print("Error: --l2_initial_bypass_probability must be between 0 and 100.")
    sys.exit(1)

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

if opts.cpu_type == 'DerivO3CPU':
    system.cpu = DerivO3CPU()
else:
    system.cpu = TimingSimpleCPU()
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()

system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2cache = L2Cache(
    size=opts.l2_size,
    assoc=opts.l2_assoc,
    rp=opts.l2_rp,
    initial_bypass_probability=opts.l2_initial_bypass_probability,
)
system.l2cache.connectCPUSideBus(system.l2bus)

system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)

system.cpu.createInterruptController()
if m5.defines.buildEnv['TARGET_ISA'] == "x86":
    system.cpu.interrupts[0].pio = system.membus.master
    system.cpu.interrupts[0].int_master = system.membus.slave
    system.cpu.interrupts[0].int_slave = system.membus.master

system.system_port = system.membus.slave

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.master

process = Process()
process.cmd = [binary] + shlex.split(opts.binary_args)

env_dict = {}
for kv in opts.env:
    if '=' not in kv:
        print(f"Error: invalid --env value '{kv}'. Expected KEY=VALUE.")
        sys.exit(1)
    key, value = kv.split('=', 1)
    env_dict[key] = value
env_dict['OMP_NUM_THREADS'] = str(opts.omp_threads)
process.env = [f"{k}={v}" for k, v in env_dict.items()]

system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system = False, system = system)
m5.instantiate()

print(f"Beginning simulation with L2={opts.l2_size} ({opts.l2_assoc}-way), RP={opts.l2_rp} (InitProb={opts.l2_initial_bypass_probability})")

in_roi = False
while True:
    exit_event = m5.simulate()
    cause = exit_event.getCause()
    cause_l = cause.lower()

    print('Exit @ tick %i because %s' % (m5.curTick(), cause))

    if 'workbegin' in cause_l:
        print('Resetting stats at ROI start')
        m5.stats.reset()
        in_roi = True
        continue

    if 'workend' in cause_l:
        print('Dumping stats at ROI end')
        m5.stats.dump()
        in_roi = False
        continue

    if in_roi:
        print('Dumping stats on non-ROI exit while ROI active')
        m5.stats.dump()
    break
