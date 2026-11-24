"""NEC commands captured from the 24-button Fluval Flex 2.0 handset."""

from typing import Final

ADDRESS: Final = 0xEF00

# Physical keypad order, left to right across each row.
COMMANDS: Final[dict[str, int]] = {
    "rgb_brighter": 0x00,
    "rgb_dimmer": 0x01,
    "rgb_power": 0x02,
    "white_power": 0x03,
    "red": 0x04,
    "green": 0x05,
    "blue": 0x06,
    "white_brighter": 0x07,
    "color_r3c1": 0x08,
    "color_r3c2": 0x09,
    "color_r3c3": 0x0A,
    "white_dimmer": 0x0B,
    "color_r4c1": 0x0C,
    "color_r4c2": 0x0D,
    "color_r4c3": 0x0E,
    "moon_cloud": 0x0F,
    "color_r5c1": 0x10,
    "color_r5c2": 0x11,
    "color_r5c3": 0x12,
    "storm": 0x13,
    "color_r6c1": 0x14,
    "color_r6c2": 0x15,
    "color_r6c3": 0x16,
    "color_cycle": 0x17,
}
