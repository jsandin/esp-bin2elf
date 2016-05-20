# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence
#
# based on the excellent reversing / writeup from Richard Burton:
# http://richard.burtons.org/2015/05/17/esp8266-boot-process/

from esp_rom import EspRom
from esp_elf import XtensaElf, EspElfSection, default_section_settings
from esp_bootrom import get_bootrom_contents

def parse_rom(rom_name, rom_filename):
    with open(rom_filename) as f:
        rom = EspRom(rom_name, f)

    return rom


def name_sections(rom):
    addr_to_section_name_mapping = {}

    print "select a unique name for each section in the rom."
    print "sensible defaults are available for the following common names:"
    print " ".join(default_section_settings.keys())
    print "if defaults are unavailable for a name, generic values will be used."

    for section in rom.sections:
        name = raw_input("enter a name for 0x%04x> " % (section.address))
        addr_to_section_name_mapping[section.address] = name

    return addr_to_section_name_mapping


def convert_rom_to_elf(esp_rom, name_mapping, filename_to_write):
    elf = XtensaElf(esp_rom.name + '.elf', esp_rom.header.entry_addr)

    flash_section = EspElfSection('.irom0.text', 0x40200000, esp_rom.contents)
    elf.add_section(flash_section, True)

    bootrom_bytes = get_bootrom_contents()
    bootrom_section = EspElfSection('.bootrom.text', 0x40000000, bootrom_bytes)
    elf.add_section(bootrom_section, True)

    for section in esp_rom.sections:
        if section.address not in addr_to_section_name_mapping:
            print "generation failed: no name for 0x%04x." % (section.address)
            return None

        name = addr_to_section_name_mapping[section.address]
        elf_section = EspElfSection(name, section.address, section.contents)
        elf.add_section(elf_section, True)

    #elf.add_symtab()
    elf.generate_elf()

    if filename_to_write:
        elf.write_to_file(filename_to_write)
 
    return elf
