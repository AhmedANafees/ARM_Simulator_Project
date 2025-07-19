import unittest
from cache import Cache

class MockMemory:
    """A mock main memory for testing purposes. Acts as the lowest level."""
    def __init__(self, size_bytes=65536):
        self.memory = bytearray(size_bytes)

    def read(self, address, size):
        return self.memory[address : address + size]

    def write(self, address, data):
        self.memory[address : address + len(data)] = data

class TestCacheConfigurations(unittest.TestCase):

    def setUp(self):
        """Set up a fresh memory for each test."""
        self.memory = MockMemory()

    def calculate_cost(self, cache: Cache):
        """Calculate and return the cost based on cache statistics."""
        cost = 0.5 * cache.misses + cache.write_backs
        return cost

    def run_configuration(self, name, size_kb, block_size, mapping_type):
        """Run a single cache configuration and return the cost."""
        cache = Cache(name, size_kb, block_size, mapping_type, self.memory)

        # Simulate memory accesses (example: sequential reads)
        for address in range(0, 256, block_size):  # Access sequential blocks
            cache.read(address)

        # Calculate cost
        cost = self.calculate_cost(cache)
        print(f"Configuration: {name}, Size: {size_kb}KB, Block Size: {block_size}B, Mapping: {mapping_type}")
        print(f"  Misses: {cache.misses}, Write-Backs: {cache.write_backs}, Cost: {cost:.2f}")
        return cost

    def test_configurations(self):
        """Test multiple cache configurations and log results."""
        configurations = [
            {"name": "Config1", "size_kb": 1, "block_size": 4, "mapping_type": "direct"},
            {"name": "Config2", "size_kb": 1, "block_size": 8, "mapping_type": "direct"},
            {"name": "Config3", "size_kb": 1, "block_size": 16, "mapping_type": "direct"},
            {"name": "Config4", "size_kb": 1, "block_size": 4, "mapping_type": "fully-assoc"},
            {"name": "Config5", "size_kb": 1, "block_size": 8, "mapping_type": "fully-assoc"},
            {"name": "Config6", "size_kb": 1, "block_size": 16, "mapping_type": "fully-assoc"},
        ]

        results = []
        for config in configurations:
            cost = self.run_configuration(
                config["name"], config["size_kb"], config["block_size"], config["mapping_type"]
            )
            results.append((config["name"], config["size_kb"], config["block_size"], config["mapping_type"], cost))

        # Print results in a table format
        print("\n--- Results ---")
        print(f"{'Name':<10} {'Size (KB)':<10} {'Block Size (B)':<15} {'Mapping':<15} {'Cost':<10}")
        for result in results:
            print(f"{result[0]:<10} {result[1]:<10} {result[2]:<15} {result[3]:<15} {result[4]:<10.2f}")

if __name__ == '__main__':
    unittest.main(verbosity=2)