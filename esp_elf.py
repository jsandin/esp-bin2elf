# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

from elffile import ElfFileIdent, ElfFileHeader32l, ElfFile32l, ElfSectionHeader32l

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
        header.ehsize = 52           # sizeof(struct elfhdr)

        header.shnum = 0             # 0 sections initially
   
        self.elf = ElfFile32l(elf_name, ident)
        self.elf.fileHeader = header

    def generate_program_header(self):
        self.elf.fileHeader.phentsize = 0
        self.elf.fileHeader.phnum = 0
        self.elf.fileHeader.phoff = 0

    def populate_section_header_metadata(self):
        self.elf.fileHeader.shentsize = 40
        self.elf.fileHeader.shoff = 0

    def generate_string_table(self):
        shstrtab_contents = ''

        # its not obvious, but the null section is first in the
        # headers list,and gets a nameoffset of 0 as a result here.
        for section in self.elf.sectionHeaders:
            section.nameoffset = len(shstrtab_contents)
            shstrtab_contents += (section.name + '\00')

        string_table = EspElfSection('.shstrtab', 0x0, shstrtab_contents)
        self.add_section(string_table)
        self.elf.fileHeader.shstrndx = len(self.elf.sectionHeaders) - 1

    def add_section(self, esp_section):
        self.elf.sectionHeaders.append(esp_section.header)
        self.elf.fileHeader.shnum = self.elf.fileHeader.shnum + 1

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
            default_settings = default_section_settings[section_name]
            header.type = default_settings.type
            header.addralign = default_settings.addralign
            header.flags = default_settings.flags

        else:
            pass
	    # generate settings based on address range

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

default_section_settings = {
  '':            SectionSettings(type=SHT_NULL,     addralign= 0, flags=0x0),
  '.data':       SectionSettings(type=SHT_PROGBITS, addralign=16, flags=0x3),
  '.rodata':     SectionSettings(type=SHT_PROGBITS, addralign=16, flags=0x2),
  '.bss':        SectionSettings(type=SHT_NOBITS,   addralign=16, flags=0x3),
  '.text':       SectionSettings(type=SHT_PROGBITS, addralign= 4, flags=0x6),
  '.irom0.text': SectionSettings(type=SHT_PROGBITS, addralign=16, flags=0x6),
  '.shstrtab':   SectionSettings(type=SHT_STRTAB,   addralign= 1, flags=0x0)
}
