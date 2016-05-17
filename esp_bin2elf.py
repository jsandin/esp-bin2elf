# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence
#
# based on the excellent reversing / writeup from Richard Burton:
# http://richard.burtons.org/2015/05/17/esp8266-boot-process/

from esp_rom import EspRom
from esp_elf import XtensaElf, EspElfSection

addr_to_section_name_mapping = {}

def parse_rom(rom_name, rom_filename):
    with open(rom_filename) as f:
        rom = EspRom(rom_name, f)

    return rom


def name_sections(rom):
    for section in rom.sections:
        name = raw_input("enter unique name for 0x%04x>" % (section.address))
        addr_to_section_name_mapping[section.address] = name


def convert_rom_to_elf(esp_rom):
    elf = XtensaElf(esp_rom.name + '.elf', esp_rom.header.entry_addr)

    null_section = EspElfSection('', 0x0, '')
    elf.add_section(null_section)

    flash_section = EspElfSection('.irom0.text', 0x40200000, esp_rom.contents)
    elf.add_section(flash_section)

    for section in esp_rom.sections:
        if section.address not in addr_to_section_name_mapping:
            print "generation failed: no name for 0x%04x." % (section.address)
            return None

        name = addr_to_section_name_mapping[section.address]
        elf_section = EspElfSection(name, section.address, section.contents)
        elf.add_section(elf_section)

    #elf.add_symtab()
    elf.populate_section_header_metadata()
    elf.generate_string_table()
    elf.generate_program_header()

    return elf
