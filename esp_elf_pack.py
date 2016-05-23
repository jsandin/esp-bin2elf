# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence

# The elffile module provides a pack() function that unfortunately
# has bugs and limitations.
#
# elffile.pack():
#
#   1) Doesn't pack program headers, and instead ignores them silently
#   2) Changes header offsets after they've been set
#   3) Computes the strtab nameoffset incorrectly 
# 
# esp_elf.py originally contained confusing workarounds for these
# issues, but these workarounds have been removed and a simpler pack
# function with fewer surprises is instead implemented here.

from struct import pack

Elf32_Ehdr = [  
                         # unsigned char e_ident[EI_NIDENT] 
    ('type',      '<H'), # Elf32_Half e_type;
    ('machine',   '<H'), # Elf32_Half e_machine;
    ('version',   '<I'), # Elf32_Word e_version;
    ('entry',     '<I'), # Elf32_Addr e_entry;
    ('phoff',     '<I'), # Elf32_Off e_phoff;
    ('shoff',     '<I'), # Elf32_Off e_shoff;
    ('flags',     '<I'), # Elf32_Word e_flags;
    ('ehsize',    '<H'), # Elf32_Half e_ehsize;
    ('phentsize', '<H'), # Elf32_Half e_phentsize;
    ('phnum',     '<H'), # Elf32_Half e_phnum;
    ('shentsize', '<H'), # Elf32_Half e_shentsize;
    ('shnum',     '<H'), # Elf32_Half e_shnum;
    ('shstrndx',  '<H')  # Elf32_Half e_shstrndx;
] # } Elf32_Shdr;

Elf32_Shdr = [
    ('nameoffset',   '<I'), # Elf32_Word sh_name;
    ('type',         '<I'), # Elf32_Word sh_type;
    ('flags',        '<I'), # Elf32_Word sh_flags;
    ('addr',         '<I'), # Elf32_Addr sh_addr;
    ('offset',       '<I'), # Elf32_Off sh_offset;
    ('section_size', '<I'), # Elf32_Word sh_size;
    ('link',         '<I'), # Elf32_Word sh_link;
    ('info',         '<I'), # Elf32_Word sh_info;
    ('addralign',    '<I'), # Elf32_Word sh_addralign;
    ('entsize',      '<I')  # Elf32_Word sh_entsize;
]

Elf32_Phdr = [
    ('type',   '<I'), # Elf32_Word p_type;
    ('offset', '<I'), # Elf32_Off p_offset;
    ('vaddr',  '<I'), # Elf32_Addr p_vaddr;
    ('paddr',  '<I'), # Elf32_Addr p_paddr;
    ('filesz', '<I'), # Elf32_Word p_filesz;
    ('memsz',  '<I'), # Elf32_Word p_memsz;
    ('flags',  '<I'), # Elf32_Word p_flags;
    ('align',  '<I')  # Elf32_Word p_align;
]

Elf32_Sym = [
    ('st_name',  '<I'), # Elf32_Word st_name;
    ('st_value', '<I'), # Elf32_Addr st_value;
    ('st_size',  '<I'), # Elf32_Word st_size;
    ('st_info',  '<B'), # unsigned char st_info;
    ('st_other', '<B'), # unsigned char st_other;
    ('st_shndx', '<H')  # Elf32_Half st_shndx;
]

# we handle a few fields manually in pack_ident below:
e_ident = [
                              # EI_MAG0-MAG4: File identification
    ('elfClass',    '<B'),    # EI_CLASS:     File class
    ('elfData',     '<B'),    # EI_DATA:      Data encoding
    ('fileVersion', '<B')     # EI_VERSION:   File version
                              # EI_PAD:       Start of padding bytes
                              # EI_NIDENT:    Size of e_ident[]
]

def pack_elf(xtensa_elf):
    packed_elf = pack_ident(xtensa_elf.ident)
    packed_elf += pack_fileheader(xtensa_elf.fileHeader)

    for header in xtensa_elf.sectionHeaders:
        packed_elf += header.content

    for header in xtensa_elf.sectionHeaders:
        packed_elf += pack_section_header(header)

    for header in xtensa_elf.programHeaders:
        packed_elf += pack_program_header(header)

    return packed_elf

def pack_fileheader(file_header):
    return _pack_struct(file_header, Elf32_Ehdr)
   
def pack_section_header(section_header):
    return _pack_struct(section_header, Elf32_Shdr)

def pack_program_header(program_header):
    return _pack_struct(program_header, Elf32_Phdr)

def pack_symbol(symbol):
    return _pack_struct(symbol, Elf32_Sym)

def pack_ident(ident):   
    header = '\x7fELF'                     # magic number
    header += _pack_struct(ident, e_ident) # pack fields in e_ident
    return header + '\x00' * 9             # pad to 16 bytes


def _pack_struct(struct, struct_fields):
    packed = ''

    for (field, size) in struct_fields:
        field_value = getattr(struct, field)
        packed += pack(size, field_value)

    return packed
