# decoder.py
# Ahmed Nafees
# nafe3598@mylaurier.ca
# 169053598

class DecodedInstruction:
    """
    This class represents the 'contract' between the Decoder and the Executor.
    It holds a decoded instruction in a structured format.
    All fields are initialized to None and filled during decoding.
    """
    def __init__(self, machine_code):
        self.machine_code = machine_code  # The raw 32-bit machine code word
        self.op_type = None      # E.g., 'DP_IMM', 'LOAD_STORE', 'BRANCH'
        self.op_code = None      # E.g., 'ADD', 'SUB', 'LDR', 'B'
        self.rn = None           # First source register
        self.rd = None           # Destination register
        self.imm = None          # Immediate value
        self.is_thumb = False    # Flag for Thumb instructions

    def __str__(self):
        # Helper function to print the decoded instruction details
        return (f"Machine Code: {hex(self.machine_code)}\n"
                f"  Op Type: {self.op_type}\n"
                f"  Op Code: {self.op_code}\n"
                f"  Rd: {self.rd}, Rn: {self.rn}, Imm: {self.imm}")


def decode_instruction(machine_code):
    """
    Decodes a single 32-bit ARMv7 machine code word. 
    This function acts as the core of the disassembler/simulator. 
    
    Args:
        machine_code (int): A 32-bit integer representing one ARM instruction.

    Returns:
        DecodedInstruction: A structured object representing the instruction.
    """
    inst = DecodedInstruction(machine_code)

    # --- Example 1: Decode an ADD instruction (Data Processing with immediate) ---
    # Condition: 1110 (bits 31-28), OpType: 001 (bits 27-25), Opcode: 0100 (ADD, bits 24-21)
    if (machine_code >> 21) & 0b11111111111 == 0b11100010100:
        inst.op_type = 'DP_IMM'
        inst.op_code = 'ADD'
        inst.rn = (machine_code >> 16) & 0xF  # Extract Rn (bits 19-16)
        inst.rd = (machine_code >> 12) & 0xF  # Extract Rd (bits 15-12)
        inst.imm = machine_code & 0xFF        # Extract Imm (bits 7-0)
        return inst

    # --- Example 2: Decode an LDR instruction (Load/Store with immediate offset) ---
    # Condition: 1110 (bits 31-28), OpType: 010 (bits 27-25), Load bit: 1 (bit 20)
    if (machine_code >> 25) & 0b111 == 0b010 and (machine_code >> 20) & 0b1 == 1:
        inst.op_type = 'LOAD_STORE'
        inst.op_code = 'LDR'
        inst.rn = (machine_code >> 16) & 0xF  # Base register
        inst.rd = (machine_code >> 12) & 0xF  # Destination register
        inst.imm = machine_code & 0xFFF       # 12-bit immediate offset
        return inst
        
    # Add logic for the other 13+ instructions here...

    return inst # Return partially decoded or unknown instruction if no match


def read_binary_file(filename):
    """
    Reads a binary file containing ARM machine code and yields decoded instructions. 
    The first instruction is assumed to be at location 0x00 in the main memory. [cite: 11]

    Args:
        filename (str): The path to the binary file.

    Yields:
        DecodedInstruction: The next decoded instruction from the file.
    """
    try:
        with open(filename, 'rb') as f:
            while True:
                # Read 4 bytes (32-bit word) for the next ARM instruction [cite: 10]
                word = f.read(4)
                if not word:
                    break # End of file
                
                # Convert the 4 bytes to a 32-bit integer
                machine_code = int.from_bytes(word, 'little')
                
                # Decode the machine code word into an instruction 
                yield decode_instruction(machine_code)

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
