# main.py
import argparse
from decoder import decode_arm, decode_thumb, read_and_decode
from cpu_simulator import CPU, MemoryHierarchy


def load_binary(path, mem_hier):
    with open(path, 'rb') as f:
        data = f.read()
    for addr in range(0, len(data), 4):
        mem_hier.main_mem.memory[addr:addr+4] = data[addr:addr+4]
    return len(data)              # return program size


def main():
    parser = argparse.ArgumentParser(
        description="ARM simulator with 2-level cache hierarchy"
    )
    # L1I options
    parser.add_argument("--l1i-mapping", required=True,
                        choices=["direct", "fully-assoc"])
    parser.add_argument("--l1i-block",   type=int, required=True,
                        choices=[4, 8, 16, 32])
    # L1D options
    parser.add_argument("--l1d-mapping", required=True,
                        choices=["direct", "fully-assoc"])
    parser.add_argument("--l1d-block",   type=int, required=True,
                        choices=[4, 8, 16, 32])
    # L2 block-size (direct mapping)
    parser.add_argument("--l2-block",    type=int, required=True,
                        choices=[16, 32, 64])
    parser.add_argument("binary", help="path to ARM machine-code file")

    args = parser.parse_args()

    # build hierarchy (1KB L1 caches, 16KB L2, 64KB main memory)
    mh = MemoryHierarchy(
        l1i_cfg={"size_kb": 1,  "block_size": args.l1i_block, "mapping": args.l1i_mapping},
        l1d_cfg={"size_kb": 1,  "block_size": args.l1d_block, "mapping": args.l1d_mapping},
        l2_cfg ={"size_kb": 16, "block_size": args.l2_block,  "mapping": "direct"},
        main_memory_size=64 * 1024
    )

    program_size = load_binary(args.binary, mh)

    cpu = CPU(mem_hier=mh)
    cpu.pc = 0

    while cpu.pc < program_size:
        instr_word = mh.read_instruction(cpu.pc)

        inst = decode_thumb(instr_word) if cpu.cpu_is_thumb else decode_arm(instr_word)
        cpu.execute(inst)

    stats = mh.stats
    cost = 0.5 * (stats["l1i_misses"] + stats["l1d_misses"]) + stats["l2_misses"] + stats["write_backs"]

    print("\n--- Cache Performance ---")
    print(f"L1I Misses:   {stats['l1i_misses']}")
    print(f"L1D Misses:   {stats['l1d_misses']}")
    print(f"L2  Misses:   {stats['l2_misses']}")
    print(f"Write-Backs:  {stats['write_backs']}")
    print(f"Cost:         {cost:.2f}")

if __name__ == "__main__":
    main()
