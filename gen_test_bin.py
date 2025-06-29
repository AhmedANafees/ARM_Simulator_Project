# gen_test_bin.py
instructions = [
    0xE3A0007B,  # MOV   R0, #123
    0xE2801005,  # ADD   R1, R0, #5
    0xE2412002,  # SUB   R2, R1, #2
    0xE0023000,  # AND   R3, R2, R0
    0xE1834001,  # ORR   R4, R3, R1
    0xE5854000,  # STR   R4, [R5]
    0xE5956000,  # LDR   R6, [R5]
    0xEB000000,  # BL    to next instruction
    0xEAFFFFFF,  # B     to PC+4 (offset = -1)
]
with open("testprog.bin", "wb") as f:
    for instr in instructions:
        f.write(instr.to_bytes(4, "little"))
