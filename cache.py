# cache.py
# Implemented by the Cache Logic Engineer for Milestone 2

import math

class CacheLine:
    """
    Represents a single line (or block) within a cache. This is a simple data structure.
    """
    def __init__(self, block_size):
        self.valid = False
        self.dirty = False
        self.tag = -1
        self.data = bytearray(block_size)
        self.lru_counter = 0

class Cache:
    """
    Contains all the core logic for cache operations.
    It supports Direct-Mapped and Fully-Associative caches with a write-back policy.
    """
    def __init__(self, name, size_kb, block_size_bytes, mapping_type, lower_level):
        self.name = name
        self.size = size_kb * 1024
        self.block_size = block_size_bytes
        self.mapping_type = mapping_type
        self.lower_level = lower_level

        self.num_lines = int(self.size / self.block_size)
        self.lines = [CacheLine(self.block_size) for _ in range(self.num_lines)]

        self.offset_bits = int(math.log2(self.block_size))
        if self.mapping_type == 'direct':
            # Ensure num_lines is not zero to avoid math domain error
            if self.num_lines > 0:
                self.index_bits = int(math.log2(self.num_lines))
            else:
                self.index_bits = 0
            self.tag_bits = 32 - self.index_bits - self.offset_bits
        else:  # fully-assoc
            self.index_bits = 0
            self.tag_bits = 32 - self.offset_bits

        self.hits = 0
        self.misses = 0
        self.write_backs = 0
        
    def _get_address_parts(self, address):
        """Helper function to decompose a 32-bit address into tag, index, and offset."""
        offset = address & ((1 << self.offset_bits) - 1)
        if self.mapping_type == 'direct':
            index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
            tag = address >> (self.offset_bits + self.index_bits)
        else:  # fully-assoc
            index = 0
            tag = address >> self.offset_bits
        return tag, index, offset

    def read(self, address):
        tag, index, offset = self._get_address_parts(address)
        line_index, line = self._find_line(tag, index)
        if line and line.valid and line.tag == tag:
            self.hits += 1
            if self.mapping_type == 'fully-assoc': self._update_lru(line_index)
        else:
            self.misses += 1
            line_index = self._handle_miss(address, tag, index)
        return self.lines[line_index].data[offset : offset + 4]

    def write(self, address, data_word):
        tag, index, offset = self._get_address_parts(address)
        line_index, line = self._find_line(tag, index)
        if line and line.valid and line.tag == tag:
            self.hits += 1
            if self.mapping_type == 'fully-assoc': self._update_lru(line_index)
            line = self.lines[line_index]
        else:
            self.misses += 1
            line_index = self._handle_miss(address, tag, index)
            line = self.lines[line_index]
        for i in range(len(data_word)):
            line.data[offset + i] = data_word[i]
        line.dirty = True

    def _handle_miss(self, address, tag, index):
        if self.mapping_type == 'fully-assoc':
            victim_line_index = self._find_lru_line()
        else:
            victim_line_index = index
        victim_line = self.lines[victim_line_index]
        if victim_line.valid and victim_line.dirty:
            self.write_backs += 1
            old_address = (victim_line.tag << (self.offset_bits + self.index_bits)) | (victim_line_index << self.offset_bits)
            self.lower_level.write(old_address, victim_line.data)
        block_start_address = address & ~(self.block_size - 1)
        victim_line.data = self.lower_level.read(block_start_address, self.block_size)
        victim_line.tag = tag
        victim_line.valid = True
        victim_line.dirty = False
        if self.mapping_type == 'fully-assoc': self._update_lru(victim_line_index)
        return victim_line_index

    def _find_line(self, tag, index):
        if self.mapping_type == 'direct':
            return index, self.lines[index]
        else:
            for i, line in enumerate(self.lines):
                if line.valid and line.tag == tag: return i, line
            return -1, None

    def _find_lru_line(self):
        for i, line in enumerate(self.lines):
            if not line.valid: return i
        oldest_line_index, max_lru_counter = 0, -1
        for i, line in enumerate(self.lines):
            if line.lru_counter > max_lru_counter:
                max_lru_counter = line.lru_counter
                oldest_line_index = i
        return oldest_line_index

    def _update_lru(self, accessed_index):
        for i, line in enumerate(self.lines):
            if line.valid:
                if i == accessed_index: line.lru_counter = 0
                else: line.lru_counter += 1
