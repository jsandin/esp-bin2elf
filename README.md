### esp-bin2elf

Converts a flash dump from an esp8266 device into an ELF executable file for analysis and reverse engineering.

For convenience, esp-bin2elf creates a flash section (**.irom0.text**) containing the complete dump, a section containing the bootrom (**.bootrom.text**), and includes all SDK symbols.

Tested in IDA Pro with the excellent [Xtensa processor plugin](https://github.com/themadinventor/ida-xtensa) from Fredrik Ahlberg.

Once you have your ELF loaded, you can + should leverage the [rizzo IDA plugin](https://github.com/devttys0/ida) to identify common functions from the SDK and RTOS examples.  Check my repo for ready-made signatures you can use, or create your own.

### Requirements:

Install the 'elffile' python module before using this.

### Usage:

```python
import esp_bin2elf
rom = esp_bin2elf.parse_rom('flashdump.bin', 'path/to/flashdump.bin')
section_names = esp_bin2elf.name_sections(rom)
elf = esp_bin2elf.convert_rom_to_elf(rom, section_names, 'flash_bin.elf')
```

Then run `readelf -a flash_bin.elf` and make sure things look ok.

### Feedback and issues:

Feel free to report an issue on github or contact me privately if you prefer.

### Thanks:

* Richard Burton for ROM format details: http://richard.burtons.org/2015/05/17/esp8266-boot-process/
* Max Filippov (**jcmvbkbc**) for bootrom.bin: https://github.com/jcmvbkbc/esp-elf-rom
* Fredrik Ahlberg (**themadinventor**) for the IDA plugin and esptool.
