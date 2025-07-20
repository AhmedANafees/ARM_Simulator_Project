# cpu_simulator.py
"""
Executor (CPU) for ARMv7/Thumb Simulator
Implements CPU state, execution logic, and memory hierarchy integration.
"""
from decoder import DecodedInstruction, decode_arm, decode_thumb, read_and_decode
from cache import Cache


class MainMemory:
    """Simple byte-addressable main memory."""
    def __init__(self, size_bytes):
        self.memory = bytearray(size_bytes)

    def read(self, address, size):
        return self.memory[address:address + size]

    def write(self, address, data: bytes):
        self.memory[address:address + len(data)] = data


class MemoryHierarchy:
    """
    2-level cache + main memory.
    L1I and L1D are separate; both point to a unified L2.
    """
    def __init__(self, l1i_cfg, l1d_cfg, l2_cfg, main_memory_size):
        # build main memory and caches
        self.main_mem = MainMemory(main_memory_size)

        self.l2 = Cache(
            name="L2",
            size_kb=l2_cfg["size_kb"],
            block_size_bytes=l2_cfg["block_size"],
            mapping_type=l2_cfg["mapping"],
            lower_level=self.main_mem
        )
        self.l1i = Cache(
            name="L1I",
            size_kb=l1i_cfg["size_kb"],
            block_size_bytes=l1i_cfg["block_size"],
            mapping_type=l1i_cfg["mapping"],
            lower_level=self.l2
        )
        self.l1d = Cache(
            name="L1D",
            size_kb=l1d_cfg["size_kb"],
            block_size_bytes=l1d_cfg["block_size"],
            mapping_type=l1d_cfg["mapping"],
            lower_level=self.l2
        )

    def read_instruction(self, address):
        data = self.l1i.read(address)
        return int.from_bytes(data, "little")

    def read_data(self, address):
        data = self.l1d.read(address)
        return int.from_bytes(data, "little")

    def write_data(self, address, value):
        data = (value & 0xFFFFFFFF).to_bytes(4, "little")
        self.l1d.write(address, data)

    @property
    def stats(self):
        return {
            "l1i_misses":  self.l1i.misses,
            "l1d_misses":  self.l1d.misses,
            "l2_misses":   self.l2.misses,
            "write_backs": self.l1i.write_backs + self.l1d.write_backs + self.l2.write_backs
        }


class CPU:
    """
    ARM Executor, now optionally backed by a MemoryHierarchy.
    If mem_hier is None, falls back to direct bytearray memory.
    """
    def __init__(self, memory_size=1024, mem_hier: MemoryHierarchy = None):
        self.regs = [0] * 16
        self.flags = {'N': 0, 'Z': 0, 'C': 0, 'V': 0}
        self.cpu_is_thumb = False
        self.mem_hier = mem_hier
        if mem_hier is None:
            self.memory = bytearray(memory_size)

    @property
    def pc(self):
        return self.regs[15]

    @pc.setter
    def pc(self, value):
        self.regs[15] = value & 0xFFFFFFFF

    def execute(self, inst: DecodedInstruction):
        handler_name = f"exec_{inst.op_code.lower()}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            print(f"[WARN] No handler for opcode '{inst.op_code}'")
            return

        before_regs = self.regs.copy()
        before_mem = None
        mem_addr = None
        if inst.op_type == 'LOAD_STORE':
            mem_addr = self.regs[inst.rn] + inst.imm
            if self.mem_hier is None:
                before_mem = self.memory[mem_addr:mem_addr+4]

        handler(inst)

        # PC update if not changed by handler
        if self.regs[15] == before_regs[15]:
            step = 2 if self.cpu_is_thumb else 4
            self.pc = self.pc + step

        self._report_changes(before_regs, before_mem, mem_addr)

    def _report_changes(self, before_regs, before_mem, mem_addr):
        for idx, (old, new) in enumerate(zip(before_regs, self.regs)):
            if old != new:
                print(f"R{idx} changed: {old} -> {new}")

        if before_mem is not None and mem_addr is not None:
            after_mem = self.memory[mem_addr:mem_addr+4]
            if after_mem != before_mem:
                val_before = int.from_bytes(before_mem, 'little')
                val_after = int.from_bytes(after_mem, 'little')
                print(f"Mem[0x{mem_addr:X}] changed: {val_before} -> {val_after}")

    def _set_nz_flags(self, result):
        self.flags['N'] = (result >> 31) & 1
        self.flags['Z'] = int(result == 0)

    # Execution handlers for each opcode
    def exec_add(self, inst):
        """
        ADD: Rd = Rn + operand2 (+ carry)
        Supports both immediate and register.
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] + op2
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_sub(self, inst):
        """
        SUB: Rd = Rn - operand2
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] - op2
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_mov(self, inst):
        """
        MOV: Rd = operand2
        """
        value = inst.imm if inst.imm is not None else self.regs[inst.rm]
        self.regs[inst.rd] = value & 0xFFFFFFFF
        self._set_nz_flags(value)

    def exec_and(self, inst):
        """
        AND: Rd = Rn & operand2
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] & op2
        self.regs[inst.rd] = result
        self._set_nz_flags(result)

    def exec_eor(self, inst):
        """
        EOR: Rd = Rn ^ operand2
        """
        result = self.regs[inst.rn] ^ self.regs[inst.rm]
        self.regs[inst.rd] = result
        self._set_nz_flags(result)

    def exec_orr(self, inst):
        """
        ORR: Rd = Rn | operand2
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] | op2
        self.regs[inst.rd] = result
        self._set_nz_flags(result)

    def exec_rsb(self, inst):
        """
        RSB: Rd = operand2 - Rn
        """
        result = (inst.imm if inst.imm is not None else self.regs[inst.rm]) - self.regs[inst.rn]
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_adc(self, inst):
        """
        ADC: Rd = Rn + operand2 + carry
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        carry = self.flags['C']
        result = self.regs[inst.rn] + op2 + carry
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_sbc(self, inst):
        """
        SBC: Rd = Rn - operand2 + carry - 1
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        carry = self.flags['C']
        result = self.regs[inst.rn] - op2 + carry - 1
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_rsc(self, inst):
        """
        RSC: Rd = operand2 - Rn + carry - 1
        """
        result = (inst.imm if inst.imm is not None else self.regs[inst.rm]) - self.regs[inst.rn] + self.flags['C'] - 1
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_tst(self, inst):
        """
        TST: Test bits, sets flags but does not write Rd.
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] & op2
        self._set_nz_flags(result)

    def exec_teq(self, inst):
        """
        TEQ: Test equivalence bits, sets flags.
        """
        result = self.regs[inst.rn] ^ self.regs[inst.rm]
        self._set_nz_flags(result)

    def exec_cmp(self, inst):
        """
        CMP: Compare Rn - operand2, sets flags.
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] - op2
        self._set_nz_flags(result)

    def exec_cmn(self, inst):
        """
        CMN: Compare negative (Rn + operand2), sets flags.
        """
        result = self.regs[inst.rn] + (inst.imm if inst.imm is not None else self.regs[inst.rm])
        self._set_nz_flags(result)

    def exec_bic(self, inst):
        """
        BIC: Rd = Rn & ~operand2
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = self.regs[inst.rn] & (~op2)
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

    def exec_mvn(self, inst):
        """
        MVN: Rd = ~operand2
        """
        op2 = inst.imm if inst.imm is not None else self.regs[inst.rm]
        result = ~op2
        self.regs[inst.rd] = result & 0xFFFFFFFF
        self._set_nz_flags(result)

   def exec_ldr(self, inst):
        addr = self.regs[inst.rn] + inst.imm
        if self.mem_hier:
            self.regs[inst.rd] = self.mem_hier.read_data(addr)
        else:
            word = int.from_bytes(self.memory[addr:addr+4], 'little')
            self.regs[inst.rd] = word

    def exec_str(self, inst):
        addr = self.regs[inst.rn] + inst.imm
        val = self.regs[inst.rd] & 0xFFFFFFFF
        if self.mem_hier:
            self.mem_hier.write_data(addr, val)
        else:
            self.memory[addr:addr+4] = val.to_bytes(4, 'little')

    def exec_b(self, inst):
        """
        B: Branch to PC + (imm << 2).
        """
        imm24 = inst.imm & 0x00FFFFFF
        if imm24 & (1 << 23):
            imm24 -= (1 << 24)
        offset = imm24 << 2
        next_pc = self.pc + 8
        self.pc = next_pc + offset

    def exec_bl(self, inst):
        """
        BL: Branch with link. LR = PC + 4; PC += imm<<2
        """
        # sign-extend 24-bit imm to Python int
        imm24 = inst.imm & 0x00FFFFFF
        if imm24 & (1 << 23):
            imm24 -= (1 << 24)
        offset = imm24 << 2
        next_pc = self.pc + 8          
        self.regs[14] = self.pc + 4    
        self.pc = next_pc + offset

# Unit tests

import unittest

class TestCPUExecutor(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU(memory_size=256)

    def test_add_imm(self):
        # ADD R2 = R1 + #5
        inst = DecodedInstruction(0)  
        inst.op_code, inst.op_type, inst.rn, inst.rd, inst.imm = 'ADD', 'DP_IMM', 1, 2, 5
        self.cpu.regs[1] = 10
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[2], 15)

    def test_sub_reg(self):
        # SUB R3 = R4 - R5
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.rn, inst.rd, inst.rm = 'SUB', 'DP_REG', 4, 3, 5
        self.cpu.regs[4], self.cpu.regs[5] = 20, 7
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[3], 13)

    def test_mov_imm(self):
        # MOV R0 = #123
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.rd, inst.imm = 'MOV', 'DP_IMM', 0, 123
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[0], 123)

    def test_and_reg(self):
        # AND R6 = R6 & R7
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.rn, inst.rd, inst.rm = 'AND', 'DP_REG', 6, 6, 7
        self.cpu.regs[6], self.cpu.regs[7] = 0b1100, 0b1010
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[6], 0b1000)

    def test_orr_imm(self):
        # ORR R1 = R1 | #0xF0
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.rn, inst.rd, inst.imm = 'ORR', 'DP_IMM', 1, 1, 0xF0
        self.cpu.regs[1] = 0x0F
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[1], 0xFF)

    def test_ldr_str(self):
        # STR R2 -> [R3], then LDR R4 from [R3]
        addr = 100
        self.cpu.regs[3], self.cpu.regs[2] = addr, 0xDEADBEEF
        inst_str = DecodedInstruction(0)
        inst_str.op_code, inst_str.op_type, inst_str.rn, inst_str.rd, inst_str.imm = 'STR', 'LOAD_STORE', 3, 2, 0
        self.cpu.execute(inst_str)
        inst_ldr = DecodedInstruction(0)
        inst_ldr.op_code, inst_ldr.op_type, inst_ldr.rn, inst_ldr.rd, inst_ldr.imm = 'LDR', 'LOAD_STORE', 3, 4, 0
        self.cpu.execute(inst_ldr)
        self.assertEqual(self.cpu.regs[4], 0xDEADBEEF)

    def test_branch(self):
        # B #2 (offset=2<<2=8)
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.imm = 'B', 'BRANCH', 2
        self.cpu.regs[15] = 0
        self.cpu.execute(inst)
       
        self.assertEqual(self.cpu.regs[15], 16)

    def test_branch_link(self):
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.imm = 'BL', 'BRANCH', 0
        self.cpu.regs[15] = 0
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.regs[15], 8)
        self.assertEqual(self.cpu.regs[14], 4)

    def test_bl_negative_offset(self):
        inst = DecodedInstruction(0)
        inst.op_code, inst.op_type, inst.imm = 'BL', 'BRANCH', 0xFFFFFF
        self.cpu.pc = 0
        self.cpu.execute(inst)
        self.assertEqual(self.cpu.pc, 4)
        self.assertEqual(self.cpu.regs[14], 4)


if __name__ == '__main__':
    unittest.main()
