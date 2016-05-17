# esp-bin2elf written by Joel Sandin <jsandin@gmail.com>
#
# MIT licence
#
# based on the excellent reversing / writeup from Richard Burton:
# http://richard.burtons.org/2015/05/17/esp8266-boot-process/

from esp_rom import EspRom
from esp_elf import XtensaElf, EspElfSection

def prompt_for_section_name():
    return raw_input("what should this section be called?  If you don't know what the section is for, press enter to pick a generic name (and corresponding values) based on the physical memory region\n>")

def convert_rom_to_elf(rom_filename):
    with open(rom_filename) as f:
        rom = EspRom(f)
	elf = XtensaElf(rom_filename + '.elf', rom.header.entry_addr)

	null_section = EspElfSection('', 0x0, '')
	elf.add_section(null_section)

        flash_section = EspElfSection('.irom0.text', 0x40200000, rom.contents)
	elf.add_section(flash_section)

        for section in rom.sections:
            print section, section.contents
            section_name = prompt_for_section_name()
            elf_section = EspElfSection(section_name, section.address, section.contents)
	    elf.add_section(elf_section)

        #elf.add_symtab()
        elf.generate_string_table()
        elf.generate_program_header()
        elf.populate_section_header_metadata()

    return elf
