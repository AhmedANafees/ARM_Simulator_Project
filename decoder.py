# decoder.py
# Ahmed Nafees
# nafe3598@mylaurier.ca
# 169053598

class DecodedInstruction:
    """
    This class represents the 'contract' between the Decoder and the Executor.
    It holds a decoded instruction in a structured format.
    """
    def __init__(self, machine_code, is_thumb=False):
        self.machine_code = machine_code
        self.is_thumb = is_thumb
        self.op_type = 'UNKNOWN'
        self.op_code = 'UNK'
        self.cond = (machine_code >> 28) if not is_thumb else 0b1110 # Condition field for ARM
        self.rn = None
        self.rd = None
        self.rm = None
        self.imm = None

    def __str__(self):
        return (f"Code: {hex(self.machine_code)} {'(Thumb)' if self.is_thumb else '(ARM)'}\n"
                f"  Op: {self.op_code}, Type: {self.op_type}\n"
                f"  Regs: Rd={self.rd}, Rn={self.rn}, Rm={self.rm}\n"
                f"  Imm: {self.imm}")

def decode_arm(machine_code):
    """Decodes a 32-bit ARM instruction."""
    inst = DecodedInstruction(machine_code, is_thumb=False)

    # --- Data Processing (Immediate) ---
    if (machine_code >> 25) & 0b111 == 0b001:
        inst.op_type, inst.rn, inst.rd, inst.imm = 'DP_IMM', (machine_code >> 16) & 0xF, (machine_code >> 12) & 0xF, machine_code & 0xFFF
        opcode = (machine_code >> 21) & 0xF
        op_map = {0b0100: 'ADD', 0b0010: 'SUB', 0b1101: 'MOV', 0b0000: 'AND', 0b1100: 'ORR', 0b1011: 'CMN', 0b1001: 'TST', 0b1010: 'CMP'}
        if opcode in op_map: inst.op_code = op_map[opcode]
        return inst
    
    # --- Data Processing (Register) ---
    elif (machine_code >> 25) & 0b111 == 0b000:
        inst.op_type, inst.rn, inst.rd, inst.rm = 'DP_REG', (machine_code >> 16) & 0xF, (machine_code >> 12) & 0xF, machine_code & 0xF
        opcode = (machine_code >> 21) & 0xF
        if opcode == 0b0100: inst.op_code = 'ADD'
        # ... add other register-based DP instructions ...
        return inst

    # --- Load/Store (Immediate) ---
    elif (machine_code >> 25) & 0b110 == 0b010:
        inst.op_type, inst.rn, inst.rd, inst.imm = 'LOAD_STORE', (machine_code >> 16) & 0xF, (machine_code >> 12) & 0xF, machine_code & 0xFFF
        inst.op_code = 'LDR' if (machine_code >> 20) & 1 else 'STR'
        return inst

    # --- Branch ---
    elif (machine_code >> 25) & 0b111 == 0b101:
        inst.op_type, inst.imm = 'BRANCH', machine_code & 0x00FFFFFF
        if (inst.imm >> 23) & 1: inst.imm |= 0xFF000000 # Sign extend
        inst.op_code = 'BL' if (machine_code >> 24) & 1 else 'B'
        return inst
        
    return inst

def decode_thumb(machine_code):
    """Decodes a 16-bit Thumb instruction."""
    inst = DecodedInstruction(machine_code, is_thumb=True)

    # --- ADD/SUB register (format 3) ---
    if (machine_code >> 11) == 0b00011:
        inst.op_type = 'DP_REG'
        inst.rn, inst.rd = (machine_code >> 3) & 0x7, machine_code & 0x7
        inst.op_code = 'SUB' if (machine_code >> 9) & 1 else 'ADD'
        return inst

    # --- MOV/CMP/ADD/SUB immediate (format 4) ---
    elif (machine_code >> 13) == 0b001:
        inst.op_type, inst.rd, inst.imm = 'DP_IMM', (machine_code >> 8) & 0x7, machine_code & 0xFF
        opcode = (machine_code >> 11) & 0x3
        op_map = {0b00: 'MOV', 0b01: 'CMP', 0b10: 'ADD', 0b11: 'SUB'}
        if opcode in op_map: inst.op_code = op_map[opcode]
        return inst

    return inst

def read_and_decode(filename, cpu_is_thumb=False):
    """
    Reads a binary file and yields decoded instructions, handling ARM/Thumb state.
    This fulfills the requirement to 'Read ARM/Thumb machine code file'. [cite: 9]
    """
    try:
        with open(filename, 'rb') as f:
            while True:
                if cpu_is_thumb:
                    # In Thumb state, read 2 bytes (16-bit word)
                    word = f.read(2)
                    if not word: break
                    machine_code = int.from_bytes(word, 'little')
                    yield decode_thumb(machine_code)
                else:
                    # In ARM state, read 4 bytes (32-bit word)
                    word = f.read(4)
                    if not word: break
                    machine_code = int.from_bytes(word, 'little')
                    yield decode_arm(machine_code)
                # NOTE: A real implementation needs the BX instruction to modify the cpu_is_thumb flag
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
