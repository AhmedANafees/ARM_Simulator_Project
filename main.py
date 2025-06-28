# main.py

from decoder import read_and_decode
from cpu_simulator import CPU

def main():
    # 1) Initialize a CPU with e.g. 4 KB of memory
    cpu = CPU(memory_size=4096)

    # 2) Set PC to 0 (we load binary at address 0x00)
    cpu.pc = 0

    # 3) Read, decode, and execute every ARM word in 'testprog.bin'
    for inst in read_and_decode('testprog.bin', cpu_is_thumb=False):
        # print the decoded instruction
        print(inst)
        # execute it on the CPU state
        cpu.execute(inst)
        print('-----')

if __name__ == "__main__":
    main()
