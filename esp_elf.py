# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from elffile import ElfFileIdent, ElfFileHeader32l, ElfFile32l, ElfSectionHeader32l, ElfProgramHeader32l
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
        header.type = 1              # ET_REL
        header.version = 1           # 1
        header.ehsize = 52           # sizeof(Elf32_Ehdr)

        header.shnum = 0             # 0 sections initially
        header.shentsize = 40        # sizeof(Elf32_Shdr)

        header.phnum = 0             # 0 program headers
        header.phentsize = 32        # sizeof(Elf32_Phdr)
   
        self.elf = ElfFile32l(elf_name, ident)
        self.elf.fileHeader = header

    def add_section(self, esp_section, add_to_program_header=False):
        if(esp_section.header.name == ''):
            # null section must go in front of section list
            self.elf.sectionHeaders.insert(0, esp_section.header)
        else:
            self.elf.sectionHeaders.append(esp_section.header)

        self.elf.fileHeader.shnum += 1

    def generate_elf(self):
        # layout = elfheader | section contents | sheaders
        self._generate_null_section_and_string_table()

        offset = self.elf.fileHeader.ehsize

        for section in self.elf.sectionHeaders:
            section.offset = offset
            offset += section.section_size

        self.elf.shoff = offset
        offset += self.elf.fileHeader.shentsize  * self.elf.fileHeader.shnum

    def _generate_null_section_and_string_table(self):
        null_section = EspElfSection('', 0x0, '')
        self.add_section(null_section, True)

        # its not obvious, but since the null section is first in
        # the sections list, it gets a nameoffset of 0 as a result here
        shstrtab_contents = ''

        for section in self.elf.sectionHeaders:
            section.nameoffset = len(shstrtab_contents)
            shstrtab_contents += (section.name + '\00')

        # need to add the shstrtab name as well
        nameoffset = len(shstrtab_contents)
        shstrtab_contents += ('.shstrtab' + '\00')

        # now we can add the shstrtab section
        string_table = EspElfSection('.shstrtab', 0x0, shstrtab_contents)
        string_table.nameoffset = nameoffset
        self.add_section(string_table)

        # set shstrndx to index of shstrtab section
        self.elf.fileHeader.shstrndx = len(self.elf.sectionHeaders) - 1

    def write_to_file(self, filename_to_write):
        with open(filename_to_write, 'w') as f:
            f.write(self.elf.pack())

    def add_symtab(self):
        pass


class EspElfSection(object):
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


class SectionSettings(object):
    def __init__(self, type, addralign, flags):
        self.type = type
        self.addralign = addralign
        self.flags = flags


# section_types:
SHT_NULL=0
SHT_PROGBITS=1
SHT_STRTAB=3
SHT_NOBITS=8

codeSettings = SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6)
dataSettings = SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x3)

default_section_settings = {
  '':            SectionSettings(type=SHT_NULL,     addralign=1, flags=0x0),
  '.data':       SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x3),
  '.rodata':     SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x2),
  '.bss':        SectionSettings(type=SHT_NOBITS,   addralign=1, flags=0x3),
  '.text':       SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6),
  '.irom0.text': SectionSettings(type=SHT_PROGBITS, addralign=1, flags=0x6),
  '.shstrtab':   SectionSettings(type=SHT_STRTAB,   addralign=1, flags=0x0)
}
