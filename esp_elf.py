# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from elffile import ElfFileIdent, ElfFileHeader32l, ElfFile32l, ElfSectionHeader32l, ElfProgramHeader32l
from esp_memory_map import is_code, is_data
from struct import pack

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
        self.elf.fileHeader = header

        self.program_headers = {}
        self.symbols = {}

    def add_section(self, esp_section, add_to_program_header=False):
        if(esp_section.header.name == ''):
            # null section must go in front of section list
            self.elf.sectionHeaders.insert(0, esp_section.header)
        else:
            self.elf.sectionHeaders.append(esp_section.header)

        if add_to_program_header:
            header = esp_section.generate_program_header()
            self.program_headers[esp_section.header.name] = header

        self.elf.fileHeader.shnum += 1

    def get_section_index_by_name(self, section_name):
        for index, header in enumerate(self.elf.sectionHeaders):
            if header.name == section_name:
                return index
        return None

    def add_symbol(self, symbol_name, symbol_address, section_name):
        self.symbols[symbol_name] = (symbol_address, section_name)

    def generate_elf(self):
        # layout = elfheader | section contents | sheaders | pheaders
        #
        # _beware_! elffile doesn't pack program headers, and will mess with
        # offsets when calling pack() if the order isn't exactly as in this
        # function
        self._generate_null_section_symtab_and_string_table()

        offset = self.elf.fileHeader.ehsize

        for section in self.elf.sectionHeaders:
            section.offset = offset

            if section.name in self.program_headers:
                program_header = self.program_headers[section.name]
                program_header.offset = offset
                self.elf.programHeaders.append(program_header)
                self.elf.fileHeader.phnum += 1

            offset += section.section_size

        self.elf.shoff = offset
        offset += self.elf.fileHeader.shentsize * self.elf.fileHeader.shnum
        self.elf.phoff = offset

    def _generate_null_section_symtab_and_string_table(self):
        # add null section
        null_section = ElfSection('', 0x0, '')
        self.add_section(null_section, True)

        # its not obvious, but since the null section is first in
        # the sections list, it gets a nameoffset of 0 as a result here
        shstrtab_contents = ''

        for section in self.elf.sectionHeaders:
            section.nameoffset = len(shstrtab_contents)
            shstrtab_contents += (section.name + '\00')

        # add symbols to .shstrtab
        symbol_names_to_offsets = {}
        for symbol_name in self.symbols.keys():
            symbol_names_to_offsets[symbol_name] = len(shstrtab_contents)
            shstrtab_contents += (symbol_name + '\00')

        # add .symtab to name string table
        nameoffset = len(shstrtab_contents)
        shstrtab_contents += ('.symtab' + '\00')

        # need to add the .shstrtab name as well
        nameoffset = len(shstrtab_contents)
        shstrtab_contents += ('.shstrtab' + '\00')

        # now we can add the .shstrtab section
        string_table = ElfSection('.shstrtab', 0x0, shstrtab_contents)
        string_table.header.nameoffset = nameoffset
        self.add_section(string_table)

        # set shstrndx to index of .shstrtab section
        self.elf.fileHeader.shstrndx = len(self.elf.sectionHeaders) - 1

        # add .symtab section
        symbols = []
        for symbol_name in self.symbols.keys():
            (address, section_name) = self.symbols[symbol_name]
            offset = symbol_names_to_offsets[symbol_name]
            index = self.get_section_index_by_name(section_name)
            if not index:
                raise Exception("can't find index for %s" % (section_name))
            symbols.append(Symbol(symbol_name, address, offset, index))

        symbol_table = ElfSymbolTable('.symtab', 0x0, symbols,
                                         self.elf.fileHeader.shstrndx)
        symbol_table.header.nameoffset = nameoffset
        self.add_section(symbol_table)

    def write_to_file(self, filename_to_write):
        with open(filename_to_write, 'w') as f:
            f.write(self.elf.pack())

            # BUG workaround: elffile doesn't pack program headers!
            f.seek(self.elf.phoff)
            for header in self.elf.programHeaders:
                f.write(header.pack())


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

    def generate_program_header(self):
        program_header = ElfProgramHeader32l()

        program_header.type = 1         # LOAD
        program_header.align = 0x1
        program_header.filesz = self.header.section_size
        program_header.memsz = self.header.section_size
        program_header.paddr = self.header.addr
        program_header.vaddr = self.header.addr
 	
        if is_code(self.header.addr):
            program_header.flags = 6    # R E
        elif is_data(self.header.addr):
            program_header.flags = 5    # RW
        else:
            program_header.flags = 0

        return program_header


class Symbol(object):
    def __init__(self, name, address, offset, section_index):
        self.name = name
        self.address = address
        self.offset = offset
        self.section_index = section_index


class ElfSymbolTable(ElfSection):
    def __init__(self, section_name, section_address, symbol_list, link):

        section_bytes = '\x00' * 16   # first entry is null symbol
        for symbol in symbol_list:
            offset = symbol.offset
            address = symbol.address
            section_index = symbol.section_index
            entry = SymbolTableEntry(offset, address, section_index)
            section_bytes += entry.pack()

        super(ElfSymbolTable, self).__init__(section_name,
                                             section_address,
                                             section_bytes)

        self.header.link = link       # index of .shstrtab
        self.header.entsize = 16      # sizeof(Elf32_sym)

 
class SymbolTableEntry(object):
    def __init__(self, symbol_name_offset, symbol_address, section_index):
        self.st_name = symbol_name_offset
        self.st_value = symbol_address
        self.st_size = 0
        self.st_info = (1 << 4) + 2   # STB_GLOBAL, STT_FUNC
        self.st_other = 0
        self.st_shndx = section_index

    def pack(self):
        entry_bytes = ''

        entry_bytes += pack('<I', self.st_name)
        entry_bytes += pack('<I', self.st_value)
        entry_bytes += pack('<I', self.st_size)
        entry_bytes += pack('<B', self.st_info)
        entry_bytes += pack('<B', self.st_other)
        entry_bytes += pack('<H', self.st_shndx)

        return entry_bytes


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
