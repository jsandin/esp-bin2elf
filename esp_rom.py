# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from struct import unpack

class EspRom(object):
    def __init__(self, rom_bytes_stream):
	self.contents = rom_bytes_stream.read()
	rom_bytes_stream.seek(0)
        self.header = EspRomHeader(rom_bytes_stream.read(EspRomHeader.ROM_HEADER_SIZE))

        self.sections = []
	for i in range(0, self.header.sect_count):
            section = EspRomSection(rom_bytes_stream)
	    self.sections.append(section)

    def __str__(self):
        repr = "EspRom("
        repr += "header: %s, " % (self.header)
        repr += "len(sections): %s, " % (len(self.sections))
        repr += "len(contents): %s)" % (len(self.contents))
   
        return repr

 
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
        repr = "EspRomHeader("
        repr += "magic: %02x, " % (self.magic)
        repr += "sect_count: %d, " % (self.sect_count)
        repr += "flags1: %02x, " % (self.flags1)
        repr += "flags2: %02x, " % (self.flags2)
        repr += "entry_addr: %04x)" % (self.entry_addr)
    
        return repr
    

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
        repr = "EspRomSection("
        repr += "address: %04x, " % (self.address)
        repr += "length: %d)" % (self.length)
   
        return repr


class RomParseException(object):
    pass
