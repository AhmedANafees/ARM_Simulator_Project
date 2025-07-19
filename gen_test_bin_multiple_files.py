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

''' set 2
instructions = [
    0xE3A0000A,  # MOV   R0, #10
    0xE280100A,  # ADD   R1, R0, #10
    0xE2412005,  # SUB   R2, R1, #5
    0xE0023002,  # AND   R3, R2, R2
    0xE1834003,  # ORR   R4, R3, R3
    0xE5854000,  # STR   R4, [R5]
    0xE5956000,  # LDR   R6, [R5]
    0xEB000002,  # BL    to next instruction
    0xEAFFFFFF,  # B     to PC+4 (offset = -1)
]
'''

''' set 3
instructions = [
    0xE3A00001,  # MOV   R0, #1
    0xE2801002,  # ADD   R1, R0, #2
    0xE2412003,  # SUB   R2, R1, #3
    0xE0023001,  # AND   R3, R2, R1
    0xE1834002,  # ORR   R4, R3, R2
    0xE5854000,  # STR   R4, [R5]
    0xE5956000,  # LDR   R6, [R5]
    0xEB000001,  # BL    to next instruction
    0xEAFFFFFF,  # B     to PC+4 (offset = -1)
]
'''

''' set 4
instructions = [
    0xE3A00005,  # MOV   R0, #5
    0xE2801005,  # ADD   R1, R0, #5
    0xE2412005,  # SUB   R2, R1, #5
    0xE0023005,  # AND   R3, R2, R0
    0xE1834005,  # ORR   R4, R3, R1
    0xE5854000,  # STR   R4, [R5]
    0xE5956000,  # LDR   R6, [R5]
    0xEB000005,  # BL    to next instruction
    0xEAFFFFFF,  # B     to PC+4 (offset = -1)
]'''

''' set 5
instructions = [
    0xE3A0000F,  # MOV   R0, #15
    0xE280100F,  # ADD   R1, R0, #15
    0xE241200F,  # SUB   R2, R1, #15
    0xE002300F,  # AND   R3, R2, R0
    0xE183400F,  # ORR   R4, R3, R1
    0xE5854000,  # STR   R4, [R5]
    0xE5956000,  # LDR   R6, [R5]
    0xEB000004,  # BL    to next instruction
    0xEAFFFFFF,  # B     to PC+4 (offset = -1)
]

'''

with open("testprog.bin", "wb") as f:
    for instr in instructions:
        f.write(instr.to_bytes(4, "little"))


