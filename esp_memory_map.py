# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

# data here from: http://esp8266-re.foogod.com/wiki/Memory_Map

class EspMemoryRegion(object):
    def __init__(self, base_address, size, permissions, min_access_width, description):
        self.base_address = base_address
        self.size = size
        self.permissions = permissions
        self.min_access_width = min_access_width
        self.description = description

    def __str__(self):
        rep = "EspMemoryRegion("
        rep += "base_address: 0x%08x, " % (self.base_address)
        rep += "size: 0x%x, " % (self.size)
        rep += "permissions: %s, " % (self.permissions)
        rep += "min_access_width: %d, " % (self.min_access_width)
        rep += "description: %s)" % (self.description)

        return rep


memory_regions = [
    EspMemoryRegion(0x00000000, 0x20000000,   '',  8, "Protected Region"),
    EspMemoryRegion(0x20000000, 0x1FF00000,  'r',  8, "unmapped? (reads 0x00800000)"),
    EspMemoryRegion(0x3FF00000, 0x10000,    'rw',  8, "Dport0"),
    EspMemoryRegion(0x3FF10000, 0x10000,     'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FF20000, 0x10000,    'rw',  8, "WDev Control Registers"),
    EspMemoryRegion(0x3FF30000, 0x90000,     'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FFC0000, 0x20000,     'r',  8, "Unknown Region 1"),
    EspMemoryRegion(0x3FFE0000, 0x8000,      'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FFE8000, 0x18000,    'rw',  8, "Data RAM"),
    EspMemoryRegion(0x40000000, 0x10000,     'r', 32, "Boot ROM"),
    EspMemoryRegion(0x40010000, 0x10000,     'r', 32, "Boot ROM (repeated)"),
    EspMemoryRegion(0x40020000, 0xD0000,     'r', 32, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x40100000, 0x8000,     'rw', 32, "Instruction RAM"),
    EspMemoryRegion(0x40108000, 0x8000,     'rw', 32, "Mappable Instruction RAM"),
    EspMemoryRegion(0x40110000, 0x30000,     'r', 32, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x40140000, 0xC0000,     'r', 32, "unmapped? (reads 0x5931d8ec)"),
    EspMemoryRegion(0x40200000, 0x100000,    'r', 32, "SPI Flash Cache"),
    EspMemoryRegion(0x40300000, 0x1FD00000,  'r',  8, "unmapped? (reads 0x00800000)"),
    EspMemoryRegion(0x60000000, 0x10000000, 'rw',  8, "Memory-Mapped IO Ports"),
    EspMemoryRegion(0x70000000, 0x90000000,  'r',  8, "unmapped? (reads 0x00000000)")
]
