# test_cache.py
# Unit tests for the Cache Logic Engineer's module with detailed output.

import unittest
from cache import Cache

class MockMemory:
    """A mock main memory for testing purposes. Acts as the lowest level."""
    def __init__(self, size_bytes=65536):
        self.memory = bytearray(size_bytes)

    def read(self, address, size):
        return self.memory[address : address + size]

    def write(self, address, data):
        # Simulate a write to memory with a print statement
        print(f"  [MEM WRITE] Writing {len(data)} bytes to address 0x{address:X}")
        self.memory[address : address + len(data)] = data

class TestCache(unittest.TestCase):

    def setUp(self):
        """Set up a fresh cache and memory for each test."""
        self.memory = MockMemory()
        
        # A 1KB direct-mapped cache with 16-byte blocks
        self.direct_cache = Cache("L1-Test", 1, 16, 'direct', self.memory)
        
        # A small 4-line fully-associative cache (total size 64 bytes).
        # Calculate size in KB without using standard division to avoid floats.
        assoc_cache_size_bytes = 4 * 16
        assoc_cache_size_kb = assoc_cache_size_bytes / 1024
        self.assoc_cache = Cache("FA-Test", assoc_cache_size_kb, 16, 'fully-assoc', self.memory)
        print("\n" + "="*50)

    def print_cache_state(self, cache: Cache):
        """Helper function to print the current state of the cache lines."""
        print(f"--- Cache State: {cache.name} ---")
        for i, line in enumerate(cache.lines):
            if line.valid:
                print(f"  Line {i:02d}: Valid=True , Dirty={line.dirty}, Tag=0x{line.tag:X}, LRU={line.lru_counter}")
            else:
                print(f"  Line {i:02d}: Valid=False")
        print("-------------------------" + "-"*len(cache.name))

    def test_read_miss_and_hit_direct(self):
        """Test a simple read miss followed by a read hit."""
        print("Running Test: Read Miss and Hit (Direct-Mapped)")
        address = 0x1000
        self.memory.memory[address:address+4] = b'\xDE\xAD\xBE\xEF'

        print(f"\n1. Reading from address 0x{address:X} (should be a MISS)")
        data = self.direct_cache.read(address)
        self.assertEqual(self.direct_cache.misses, 1, "Should be 1 miss")
        self.assertEqual(self.direct_cache.hits, 0, "Should be 0 hits")
        # FIX: Cast the returned bytearray to bytes for a consistent comparison
        self.assertEqual(bytes(data), b'\xDE\xAD\xBE\xEF')
        print(f"-> Miss confirmed. Fetched data: {data.hex().upper()}")
        self.print_cache_state(self.direct_cache)

        print(f"\n2. Reading again from address 0x{address:X} (should be a HIT)")
        data2 = self.direct_cache.read(address)
        self.assertEqual(self.direct_cache.misses, 1, "Miss count should not change")
        self.assertEqual(self.direct_cache.hits, 1, "Should be 1 hit")
        # FIX: Cast the returned bytearray to bytes for a consistent comparison
        self.assertEqual(bytes(data2), b'\xDE\xAD\xBE\xEF')
        print(f"-> Hit confirmed. Read data: {data2.hex().upper()}")
        self.print_cache_state(self.direct_cache)

    def test_write_back_direct(self):
        """Test that a dirty block is written back on eviction."""
        print("Running Test: Write-Back on Eviction (Direct-Mapped)")
        addr1 = 0x1000
        addr2 = addr1 + (self.direct_cache.num_lines * self.direct_cache.block_size)
        print(f"Using two addresses that map to the same index: 0x{addr1:X} and 0x{addr2:X}")

        print(f"\n1. Writing to address 0x{addr1:X} (should be a WRITE MISS)")
        self.direct_cache.write(addr1, b'\x12\x34\x56\x78')
        self.assertEqual(self.direct_cache.misses, 1)
        self.assertTrue(self.direct_cache.lines[0].dirty)
        print("-> Write miss confirmed. Line is now dirty.")
        self.print_cache_state(self.direct_cache)

        print(f"\n2. Reading from address 0x{addr2:X} (should EVICT line for 0x{addr1:X} and cause a WRITE-BACK)")
        self.direct_cache.read(addr2)
        self.assertEqual(self.direct_cache.misses, 2)
        self.assertEqual(self.direct_cache.write_backs, 1, "Should be 1 write-back")
        print("-> Eviction and write-back confirmed.")
        self.print_cache_state(self.direct_cache)

        # FIX: Cast the returned bytearray to bytes for a consistent comparison
        self.assertEqual(bytes(self.memory.read(addr1, 4)), b'\x12\x34\x56\x78')
        print("-> Verified data was correctly written back to mock memory.")

    def test_lru_replacement_fully_assoc(self):
        """Test that the least recently used line is replaced."""
        print("Running Test: LRU Replacement (Fully-Associative)")
        addrs = [0x0, 0x10, 0x20, 0x30] # 4 distinct addresses for our 4-line cache
        
        print("\n1. Filling the cache with 4 distinct blocks...")
        for i, addr in enumerate(addrs):
            print(f"  Reading from 0x{addr:X}")
            self.assoc_cache.read(addr)
        
        self.print_cache_state(self.assoc_cache)
        print("-> Cache is now full. Line 0 (for addr 0x0) is the LRU.")

        addr_new = 0x40
        print(f"\n2. Reading from new address 0x{addr_new:X} to trigger eviction...")
        self.assoc_cache.read(addr_new)
        self.assertEqual(self.assoc_cache.misses, 5)
        print("-> Eviction miss confirmed.")
        self.print_cache_state(self.assoc_cache)

        # Verify that the tag for the new address is now in the cache
        new_tag, _, _ = self.assoc_cache._get_address_parts(addr_new)
        self.assertTrue(any(line.tag == new_tag for line in self.assoc_cache.lines), "New tag should be in cache")
        print(f"-> Verified new tag 0x{new_tag:X} is present.")

        # Verify that the tag for the old LRU address (0x0) has been evicted
        old_tag, _, _ = self.assoc_cache._get_address_parts(addrs[0])
        self.assertFalse(any(line.tag == old_tag for line in self.assoc_cache.lines), "Old LRU tag should be evicted")
        print(f"-> Verified old LRU tag 0x{old_tag:X} has been evicted.")


if __name__ == '__main__':
    # Run tests with verbosity to see the print statements
    unittest.main(verbosity=2)
