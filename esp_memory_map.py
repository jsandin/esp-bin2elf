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
    EspMemoryRegion(0x00000000, 0x20000000,   '',  8, "protected region"),
    EspMemoryRegion(0x20000000, 0x1FF00000,  'r',  8, "unmapped? (reads 0x00800000)"),
    EspMemoryRegion(0x3FF00000, 0x10000,    'rw',  8, "dport0"),
    EspMemoryRegion(0x3FF10000, 0x10000,     'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FF20000, 0x10000,    'rw',  8, "wdev control registers"),
    EspMemoryRegion(0x3FF30000, 0x90000,     'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FFC0000, 0x20000,     'r',  8, "unknown region 1"),
    EspMemoryRegion(0x3FFE0000, 0x8000,      'r',  8, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x3FFE8000, 0x18000,    'rw',  8, "data RAM"),
    EspMemoryRegion(0x40000000, 0x10000,    'rx', 32, "boot ROM"),
    EspMemoryRegion(0x40010000, 0x10000,    'rx', 32, "boot ROM (repeated)"),
    EspMemoryRegion(0x40020000, 0xD0000,     'r', 32, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x40100000, 0x8000,    'rwx', 32, "instruction RAM"),
    EspMemoryRegion(0x40108000, 0x8000,    'rwx', 32, "mappable instruction RAM"),
    EspMemoryRegion(0x40110000, 0x30000,     'r', 32, "unmapped? (reads 0x00000000)"),
    EspMemoryRegion(0x40140000, 0xC0000,     'r', 32, "unmapped? (reads 0x5931d8ec)"),
    EspMemoryRegion(0x40200000, 0x100000,    'r', 32, "spi flash cache"),
    EspMemoryRegion(0x40300000, 0x1FD00000, 'rx',  8, "unmapped? (reads 0x00800000)"),
    EspMemoryRegion(0x60000000, 0x10000000, 'rw',  8, "Memory-Mapped IO Ports"),
    EspMemoryRegion(0x70000000, 0x90000000,  'r',  8, "unmapped? (reads 0x00000000)")
]

def find_region_for_address(address):
    for i in range(len(memory_regions)-1):
        low, high = memory_regions[i], memory_regions[i+1]
        if address >= low.base_address and address < high.base_address:
            return low, high
    return None, None

def is_code(address):
    low, high = find_region_for_address(address)
    if low and 'x' in low.permissions:
        return True
    return False

def is_data(address):
    low, high = find_region_for_address(address)
    if low and low.base_address == 0x3FFE8000:
        return True
    return False
