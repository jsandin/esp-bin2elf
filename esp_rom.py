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
        HeaderClass = EspRomHeader.get_header_type(self.contents[0])
        self.header = HeaderClass(rom_bytes_stream.read(HeaderClass.ROM_HEADER_SIZE))

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
    @staticmethod
    def get_header_type(header_byte):
        if header_byte == '\xe9':
            return EspRomE9Header
        elif header_byte == '\xe4':
            return EspRomE4Header
        else:
            raise RomParseException(
                "EspRomHeader.get_header_type: unrecognized magic_number %s"
                    % (header_byte))

    def __init__(self):
        pass


class EspRomE9Header(EspRomHeader):
    ROM_HEADER_SIZE = 8

    def __init__(self, rom_header_bytes):
        # typedef struct {
        #     uint8 magic;
        #     uint8 sect_count;
        #     uint8 flags1;
        #     uint8 flags2;
        #     uint32 entry_addr;
        # } rom_header;

        if len(rom_header_bytes) != EspRomE9Header.ROM_HEADER_SIZE:
            raise RomParseException(
                "EspRomE9Header.init(): len(rom_header_bytes) is %d bytes != 8 bytes."
                    % (len(rom_header_bytes)))

        if rom_header_bytes[0] != '\xe9':
            raise RomParseException(
                "EspRomE9Header.init(): magic_number is %s != 0xe9."
                    % (rom_header_bytes[0]))

        self.magic = unpack('<B', rom_header_bytes[0])[0]
        self.sect_count = unpack('<B', rom_header_bytes[1])[0]
        self.flags1 = unpack('<B', rom_header_bytes[2])[0]
        self.flags2 = unpack('<B', rom_header_bytes[3])[0]
        self.entry_addr = unpack('<I', rom_header_bytes[4:8])[0]

        super(EspRomE9Header, self).__init__()

    def __str__(self):
        rep = "EspRomE9Header("
        rep += "magic: 0x%02x, " % (self.magic)
        rep += "sect_count: %d, " % (self.sect_count)
        rep += "flags1: 0x%02x, " % (self.flags1)
        rep += "flags2: 0x%02x, " % (self.flags2)
        rep += "entry_addr: 0x%04x)" % (self.entry_addr)

        return rep


class EspRomE4Header(EspRomHeader):
    ROM_HEADER_SIZE = 16

    def __init__(self, rom_header_bytes):
        # typedef struct {
        #     uint8 magic1;
        #     uint8 magic2;
        #     uint8 config[2];
        #     uint32 entry_addr;
        #     uint8 unused[4];
        #     uint32 length;
        # } rom_header;

        if len(rom_header_bytes) != EspRomE4Header.ROM_HEADER_SIZE:
            raise RomParseException(
                "EspRomE4Header.init(): len(rom_header_bytes) is %d bytes != 16 bytes."
                    % (len(rom_header_bytes)))

        if rom_header_bytes[0] != '\xe4':
            raise RomParseException(
                "EspRomE4Header.init(): magic1 is %s != 0xe4."
                    % (rom_header_bytes[0]))

        if rom_header_bytes[1] != '\x04':
            raise RomParseException(
                "EspRomE4Header.init(): magic2 is %s != 0x04."
                    % (rom_header_bytes[1]))

        self.magic1 = unpack('<B', rom_header_bytes[0])[0]
        self.magic2 = unpack('<B', rom_header_bytes[1])[0]
        self.config = unpack('<BB', rom_header_bytes[2:4])
        self.entry_addr = unpack('<I', rom_header_bytes[4:8])[0]
        self.unused = unpack('<BBBB', rom_header_bytes[8:12])
        self.length = unpack('<I', rom_header_bytes[12:16])[0]

        super(EspRomE4Header, self).__init__()

    def __str__(self):
        rep = "EspRomE4Header("
        rep += "magic1: 0x%02x, " % (self.magic1)
        rep += "magic2: 0x%02x, " % (self.magic2)
        rep += "config: %d, " % (self.config)
        rep += "entry_addr: 0x%04x, " % (self.entry_addr)
        rep += "unused: 0x%02x, " % (self.unused)
        rep += "length: %d)" % (self.length)

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
