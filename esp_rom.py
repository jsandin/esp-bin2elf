# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from esp_memory_map import find_region_for_address
from struct import unpack

class EspRom(object):
    def __init__(self, rom_name, rom_bytes_stream):
        self.name = rom_name
        self.contents = rom_bytes_stream.read()
        rom_bytes_stream.seek(0)
        self.header = EspRomHeader(rom_bytes_stream.read(EspRomHeader.ROM_HEADER_SIZE))

        self.sections = []
        for i in range(0, self.header.sect_count):
            section = EspRomSection(rom_bytes_stream)
            self.sections.append(section)

    def __str__(self):
        rep = "EspRom("
        rep += "name: %s, " % (self.name)
        rep += "header: %s, " % (self.header)
        rep += "len(sections): %s, " % (len(self.sections))
        rep += "len(contents): %s)" % (len(self.contents))
   
        return rep

 
class EspRomHeader(object):
    ROM_HEADER_SIZE = 8

    def __init__(self, rom_header_bytes):
        # typedef struct {
        #     uint8 magic;
        #     uint8 sect_count;
        #     uint8 flags1;
        #     uint8 flags2;
        #     uint32 entry_addr;
        # } rom_header;

        if len(rom_header_bytes) != EspRomHeader.ROM_HEADER_SIZE:
            raise RomParseException(
                "EspRomRomHeader.init(): len(rom_header_bytes) is %d bytes != 8 bytes."
                    % (len(rom_header_bytes)))
    
        if rom_header_bytes[0] != '\xe9':
            raise RomParseException(
                "EspRomRomHeader.init(): magic_number is %s != 0xe9."
                    % (rom_header_bytes[0]))

        self.magic = unpack('<B', rom_header_bytes[0])[0]
        self.sect_count = unpack('<B', rom_header_bytes[1])[0]
        self.flags1 = unpack('<B', rom_header_bytes[2])[0]
        self.flags2 = unpack('<B', rom_header_bytes[3])[0]
        self.entry_addr = unpack('<I', rom_header_bytes[4:8])[0]
    
    def __str__(self):
        rep = "EspRomHeader("
        rep += "magic: 0x%02x, " % (self.magic)
        rep += "sect_count: %d, " % (self.sect_count)
        rep += "flags1: 0x%02x, " % (self.flags1)
        rep += "flags2: 0x%02x, " % (self.flags2)
        rep += "entry_addr: 0x%04x)" % (self.entry_addr)
    
        return rep
    

class EspRomSection(object):
    SECTION_HEADER_SIZE = 8

    def __init__(self, rom_bytes_stream):
        # typedef struct {
        #     uint32 address;
        #     uint32 length;
        # } sect_header;

        section_header_bytes = rom_bytes_stream.read(EspRomSection.SECTION_HEADER_SIZE)
    
        if len(section_header_bytes) != EspRomSection.SECTION_HEADER_SIZE:
            raise RomParseException(
                "EspRomSection.init(): section_header_bytes is %d bytes != 8 bytes."
                    % (len(section_header_bytes)))
    
        self.address = unpack('<I', section_header_bytes[0:4])[0]
        self.length = unpack('<I', section_header_bytes[4:8])[0]
        self.contents = rom_bytes_stream.read(self.length)

        if len(self.contents) != self.length:
            raise RomParseException(
                "EspRomSection.init(): self.contents is %d bytes != self.length %d."
                    % (len(self.contents), self.length))
    
    def __str__(self):
        rep = "EspRomSection("
        rep += "address: 0x%04x, " % (self.address)
        rep += "length: %d)" % (self.length)
   
        return rep


class RomParseException(object):
    pass


def pretty_print_rom(esp_rom):
    print "EspRom:"
    print "\tname: %s\n" % (esp_rom.name)

    print "header:"
    print "\tmagic: 0x%02x" % (esp_rom.header.magic)
    print "\tsect_count: %d" % (esp_rom.header.sect_count)
    print "\tflags1: 0x%02x" % (esp_rom.header.flags1)
    print "\tflags2: 0x%02x" % (esp_rom.header.flags2)
    print "\tentry_addr: 0x%04x\n" % (esp_rom.header.entry_addr)
 
    print "sections:"
    for section in esp_rom.sections:
        pretty_print_esp_section(section)


def pretty_print_esp_section(section):
    (low_region, high_region) = find_region_for_address(section.address)

    if low_region:
        desc = low_region.description
        low_addr, high_addr = low_region.base_address, high_region.base_address 
        mem_desc = "%s (0x%04x - 0x%04x)" % (desc, low_addr, high_addr)
        print "\taddress: 0x%04x, part of %s" % (section.address, mem_desc)
    else:
        print "\taddress: 0x%04x, unknown memory region" % (section.address)
    print "\tlength: %d\n" % (section.length)
