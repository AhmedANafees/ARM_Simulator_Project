# system_simulator.py

from decoder import decode_instruction
from cpu_simulator import CPU

class SystemSimulator:
    def __init__(self, binary_file_path):
        self.cpu = CPU()
        self.memory = {}
        self.PC = 0x00
        self.load_binary(binary_file_path)

    def load_binary(self, path):
        with open(path, "rb") as f:
            byte_data = f.read()
            for i in range(0, len(byte_data), 4):
                word = int.from_bytes(byte_data[i:i+4], byteorder='little')
                self.memory[self.PC + i] = word

    def fetch(self):
        return self.memory.get(self.PC, None)

    def run(self):
        print("\n--- Starting Simulation ---\n")
        while True:
            instruction_word = self.fetch()
            if instruction_word is None:
                print(f"No instruction at address 0x{self.PC:08X}, halting.")
                break

            decoded = decode_instruction(instruction_word)
            print(f"0x{self.PC:08X}: Executing {decoded.opcode}")

            self.cpu.execute(decoded)
            self.PC += 4  
            if decoded.opcode in ["BX"] and decoded.rd == 15:
                print("Encountered BX LR/PC, halting.")
                break

        print("\n--- Simulation Complete ---\n")
        self.cpu.print_state() 

if __name__ == "__main__":
    sim = SystemSimulator("testprog.bin")
    sim.run()
