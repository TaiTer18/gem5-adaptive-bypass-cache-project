import m5
from m5.objects import *
import os
import argparse
import sys

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

    def __init__(self, size=None, rp='LRURP'):
        super(L2Cache, self).__init__()
        if size: self.size = size
        
        if rp == 'AdaptiveBypassRP':
            self.replacement_policy = AdaptiveBypassRP(initial_bypass_probability=50)
        else:
            self.replacement_policy = LRURP()

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.master
    def connectMemSideBus(self, bus):
        self.mem_side = bus.slave

SimpleOpts.add_option('--l2_size', default='256kB', help="L2 cache size")
SimpleOpts.add_option('--l2_rp', default='LRURP', choices=['LRURP', 'AdaptiveBypassRP'], help="Replacement Policy")
(opts, args) = SimpleOpts.parse_args()

if len(args) != 1:
    print("Error: Expected exactly one positional argument for the binary to execute.")
    sys.exit(1)

binary = args[0]

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '1GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('512MB')]

system.cpu = TimingSimpleCPU()
system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()

system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()

system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2cache = L2Cache(size=opts.l2_size, rp=opts.l2_rp)
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
process.cmd = [binary]

system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system = False, system = system)
m5.instantiate()

print(f"Beginning simulation with L2={opts.l2_size}, RP={opts.l2_rp}")
exit_event = m5.simulate()
print('Exiting @ tick %i because %s' % (m5.curTick(), exit_event.getCause()))
