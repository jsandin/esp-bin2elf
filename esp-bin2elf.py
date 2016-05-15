# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence
#
# based on the excellent reversing / writeup from Richard Burton:
# http://richard.burtons.org/2015/05/17/esp8266-boot-process/

from elffile import ElfFileIdent, ElfFileHeader32l, ElfFile32l, ElfSectionHeader32l
from sys import exit
from struct import unpack

class RomHeader(object):
    ROM_HEADER_SIZE = 8

    def __init__(self, rom_header_bytes):
        # typedef struct {
        #     uint8 magic;
        #     uint8 sect_count;
        #     uint8 flags1;
        #     uint8 flags2;
        #     uint32 entry_addr;
        # } rom_header;
    
        if len(rom_header_bytes) != RomHeader.ROM_HEADER_SIZE:
            print "RomHeader.init(): rom_header_bytes %d bytes long != 64 bytes." % (len(rom_header_bytes))
            exit(1)
    
        if rom_header_bytes[0] != '\xe9':
            print "RomHeader.init(): magic_number %s, doesn't match the expected 0xe9." % (rom_header_bytes[0])
            exit(1)

	self.magic = unpack('<B', rom_header_bytes[0])[0]
        self.sect_count = unpack('<B', rom_header_bytes[1])[0]
        self.flags1 = unpack('<B', rom_header_bytes[2])[0]
        self.flags2 = unpack('<B', rom_header_bytes[3])[0]
        self.entry_addr = unpack('<I', rom_header_bytes[4:8])[0]
    
    def __str__(self):
        repr = "rom header("
        repr += "magic: %02x, " % (self.magic)
        repr += "sect_count: %d, " % (self.sect_count)
        repr += "flags1: %02x, " % (self.flags1)
        repr += "flags2: %02x, " % (self.flags2)
        repr += "entry_addr: %04x)" % (self.entry_addr)
    
        return repr
    

class SectionHeader(object):
    SECTION_HEADER_SIZE = 8

    def __init__(self, section_header_bytes):
        # typedef struct {
        #     uint32 address;
        #     uint32 length;
        # } sect_header;
    
        if len(section_header_bytes) != SectionHeader.SECTION_HEADER_SIZE:
            print "SectionHeader.init(): section_header_bytes %d bytes != 64 bytes." % (len(section_header_bytes))
            exit(1)
    
        self.address = unpack('<I', section_header_bytes[0:4])[0]
        self.length = unpack('<I', section_header_bytes[4:8])[0]

    def __str__(section_header):
        repr = "section header("
        repr += "address: %04x, " % (section_header.address)
        repr += "length: %d)" % (section_header.length)
   
        return repr


def make_xtensa_elf(elf_name, entry_addr):
    ident = ElfFileIdent()

    ident.abiversion = 0         # 0
    ident.elfClass =  1          # ELFCLASS32
    ident.elfData = 1            # ELFDATA2LSB
    ident.fileVersion = 1        # 1
    ident.magic = '\x7fELF'      # ELF'
    ident.osabi = 0              # 0

    header = ElfFileHeader32l()

    header.entry = entry_addr
    header.flags = 0x300         # 0x300 (IDA complains about this)
    header.machine = 94          # EM_XTENSA
    header.type = 2              # ET_EXEC
    header.version = 1           # 1
    header.ehsize = 52           # sizeof(struct elfhdr)
    header.shentsize = 40
    header.phentsize = 0
    header.phnum = 0
    header.phoff = 0
    header.shoff = 0

    elf = ElfFile32l(elf_name, ident)
    elf.fileHeader = header

    return elf


def set_section_attributes_by_name(section_name, section_address, header):
    if section_name == '':
        header.type = 0       # SHT_NULL
        header.addralign = 0
        header.flags = 0x0

    elif section_name == '.data':
        header.type = 1       # SHT_PROGBITS 
        header.addralign = 16
        header.flags = 0x3
    
    elif section_name == '.rodata':
        header.type = 1       # SHT_PROGBITS 
        header.addralign = 16
        header.flags = 0x2

    elif section_name == '.bss':
        header.type = 8       # SHT_NOBITS
        header.addralign = 16
        header.flags = 0x3

    elif section_name == '.text':
        header.type = 1       # SHT_PROGBITS
        header.addralign = 4
        header.flags = 0x6

    elif section_name == '.irom0.text':
        header.type = 1       # SHT_PROGBITS
        header.addralign = 4
        header.flags = 0x6

    elif section_name == '.shstrtab':
        header.type = 3       # SHT_STRTAB
        header.addralign = 1
        header.flags = 0x0

    else:
        print "set_section_attributes_by_name: don't know settings for %s." % (section_name)
        exit(1)
 
 
def prompt_for_section_name():
    return raw_input("what should this section be called?  If you don't know what the section is for, press enter to pick a generic name (and corresponding values) based on the physical memory region\n>")


def add_section_to_elf(elf, section_name, section_address, section_bytes):
    header = ElfSectionHeader32l()

    header.addr = section_address
    header.name = section_name
    set_section_attributes_by_name(section_name, section_address, header)
    header.link = 0
    header.info = 0
    header.entsize = 0

    header.content = section_bytes
    header.section_size = len(section_bytes)
    elf.sectionHeaders.append(header)


def add_symtab_to_elf(elf):
    pass

def add_string_table(elf):
    shstrtab_contents = ''
    nameoffset = 0

    for section in elf.sectionHeaders:
	section.nameoffset = nameoffset
        shstrtab_contents += '\x00' + section.name
	nameoffset = len(shstrtab_contents)
    shstrtab_contents += '\x00'

    add_section_to_elf(elf, '.shstrtab', 0x0, shstrtab_contents)

    elf.fileHeader.shnum = len(elf.sectionHeaders)
    elf.fileHeader.shstrndx = len(elf.sectionHeaders) - 1


def convert_rom_to_elf(rom_filename):
    with open(rom_filename) as f:
        rom_header = RomHeader(f.read(RomHeader.ROM_HEADER_SIZE))
	print rom_header
	elf = make_xtensa_elf(rom_filename + '.elf', rom_header.entry_addr)

        add_section_to_elf(elf, '', 0x0, '')

        for i in range(0, rom_header.sect_count):
            section_header = SectionHeader(f.read(SectionHeader.SECTION_HEADER_SIZE))
            print section_header
	    section_bytes = f.read(section_header.length)
            print section_bytes
            section_name = prompt_for_section_name()
	    add_section_to_elf(elf, section_name, section_header.address, section_bytes) 

        #add_symtab_to_elf(elf)
    add_string_table(elf)

    return elf



# block offset nameoffset type flags addr offset section size link info addralign entsize
