# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from elffile import ElfFileIdent, ElfFileHeader32l, ElfFile32l, ElfSectionHeader32l, ElfProgramHeader32l
from esp_elf_pack import pack_elf, pack_symbol
from esp_memory_map import is_code, is_data

class XtensaElf(object):
    def __init__(self, elf_name, entry_addr):
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
        header.ehsize = 52           # sizeof(Elf32_Ehdr)

        header.shnum = 0             # 0 sections initially
        header.shentsize = 40        # sizeof(Elf32_Shdr)

        header.phnum = 0             # 0 program headers initially
        header.phentsize = 32        # sizeof(Elf32_Phdr)
   
        self.elf = ElfFile32l(elf_name, ident)
        self.elf.ident = ident
        self.elf.fileHeader = header

        self.string_table = ElfStringTable()
        self.symbol_table = ElfSymbolTable()

        self.sections = []
        self.add_section(NullSection(), True) # generate null ph entry
        self.add_section(self.string_table)
        self.add_section(self.symbol_table)

        string_table_offset = self.get_index_for_section('.shstrtab')
        self.symbol_table.set_link(string_table_offset)
        self.elf.fileHeader.shstrndx = string_table_offset
 
    def add_section(self, esp_section, add_to_program_header=False):
        nameoffset = self.string_table.add_string(esp_section.header.name)
        esp_section.header.nameoffset = nameoffset

        self.sections.append(esp_section)
        self.elf.sectionHeaders.append(esp_section.header)
        self.elf.fileHeader.shnum += 1

        if add_to_program_header:
            esp_section.generate_program_header()
            self.elf.programHeaders.append(esp_section.program_header)
            self.elf.fileHeader.phnum += 1

    def add_symbol(self, symbol_name, symbol_address, section_name):
        self.symbol_table.add_symbol(symbol_name, symbol_address, section_name)

    def get_index_for_section(self, section_name):
        for index, section in enumerate(self.elf.sectionHeaders):
            if section.name == section_name:
                return index

        raise Exception("Symbol added for unknown section %s" % section_name)

    def generate_elf(self):
        # layout = elfheader | section contents | sheaders | pheaders
       
        # generate symbol table
        self.symbol_table.generate_content(self)

        # compute offsets for section contents, sections, and program headers
        offset = self.elf.fileHeader.ehsize

        for section in self.sections:
            section.header.offset = offset

            if section.program_header:
                section.program_header.offset = offset

            offset += section.header.section_size

        # write section and program headers after contents
        self.elf.fileHeader.shoff = offset
        offset += self.elf.fileHeader.shentsize * self.elf.fileHeader.shnum
        self.elf.fileHeader.phoff = offset
       
    def write_to_file(self, filename_to_write):
        with open(filename_to_write, 'w') as f:
            f.write(pack_elf(self.elf))


class ElfSection(object):
    def __init__(self, section_name, section_address, section_bytes):
        header = ElfSectionHeader32l()
    
        header.name = section_name
        header.addr = section_address
        header.link = 0
        header.info = 0
        header.entsize = 0
    
        header.content = section_bytes
        header.section_size = len(section_bytes)

        if section_name in default_section_settings:
            settings_to_use = default_section_settings[section_name]
        elif is_code(section_address):
            settings_to_use = codeSettings
        elif is_data(section_address):
            settings_to_use = dataSettings
        else:
            raise Exception("can't find settings for %x" % (section_adddress))

        header.type = settings_to_use.type
        header.addralign = settings_to_use.addralign
        header.flags = settings_to_use.flags

        self.header = header
        self.program_header = None

    def append_to_content(self, string):
        self.header.content += string
        self.header.section_size = len(self.header.content)

    def generate_program_header(self):
        program_header = ElfProgramHeader32l()

        program_header.type = 1         # LOAD
        program_header.align = 0x1
        program_header.filesz = self.header.section_size
        program_header.memsz = self.header.section_size
        program_header.paddr = self.header.addr
        program_header.vaddr = self.header.addr
 	
        if is_code(self.header.addr):
            program_header.flags = 5    # R E
        elif is_data(self.header.addr):
            program_header.flags = 6    # RW
        else:
            program_header.flags = 0

        self.program_header = program_header


class NullSection(ElfSection):
    def __init__(self):
        super(NullSection, self).__init__('', 0x0, '')


class ElfStringTable(ElfSection):
    def __init__(self):
        self.string_to_offset = {'': 0}

        super(ElfStringTable, self).__init__('.shstrtab', 0x0, '\x00')

    def add_string(self, string):
        if string not in self.string_to_offset:
            self.string_to_offset[string] = len(self.header.content)
            self.append_to_content(string + '\x00')

        return self.get_index(string)

    def get_index(self, string):
        return self.string_to_offset[string]


class ElfSymbolTable(ElfSection):
    def __init__(self):
        super(ElfSymbolTable, self).__init__('.symtab', 0x0, '')

        self.append_to_content('\x00' * 16)   # first entry is null symbol
        self.header.entsize = 16              # sizeof(Elf32_sym)
        self.symbols = []

    def set_link(self, link):
        self.header.link = link               # index of .shstrtab

    def add_symbol(self, name, address, section_name):
        self.symbols.append((name, address, section_name)) 

    def generate_content(self, elf):
        for symbol in self.symbols:
            name, address, section_name = symbol
            offset = elf.string_table.add_string(name)
            section_index = elf.get_index_for_section(section_name)
            entry = SymbolTableEntry(offset, address, section_index)
            self.append_to_content(entry.pack())


class SymbolTableEntry(object):
    def __init__(self, symbol_name_offset, symbol_address, section_index):
        self.st_name = symbol_name_offset
        self.st_value = symbol_address
        self.st_size = 0
        self.st_info = (1 << 4) + 2   # STB_GLOBAL, STT_FUNC
        self.st_other = 0
        self.st_shndx = section_index

    def pack(self):
        return pack_symbol(self)


class SectionSettings(object):
    def __init__(self, type, addralign, flags):
        self.type = type
        self.addralign = addralign
        self.flags = flags

# section_types:
SHT_NULL     = 0
SHT_PROGBITS = 1
SHT_SYMTAB   = 2
SHT_STRTAB   = 3
SHT_NOBITS   = 8

codeSettings = SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6)
dataSettings = SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x3)

default_section_settings = {
  '':              SectionSettings(type=SHT_NULL,     addralign=1, flags=0x0),
  '.data':         SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x3),
  '.rodata':       SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x2),
  '.bss':          SectionSettings(type=SHT_NOBITS,   addralign=1, flags=0x3),
  '.text':         SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6),
  '.irom0.text':   SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6),
  '.bootrom.text': SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6),
  '.shstrtab':     SectionSettings(type=SHT_STRTAB,   addralign=1, flags=0x0),
  '.symtab':       SectionSettings(type=SHT_SYMTAB,   addralign=1, flags=0x0)
}
