# gen_test_bin.py
instructions = [
    0b11100010100000010010000000000101,  # ADD   R2, R1, #5
    0b11100010100000100011000000000010,  # ADD   R3, R2, #2
    0b11100001000000110010000000000000,  # STR   R2, [R3]
    0b11101011111111111111111111111111,  # B     <infinite loop> (offset = -1)
]
with open("testprog.bin", "wb") as f:
    for instr in instructions:
        f.write(instr.to_bytes(4, "little"))
