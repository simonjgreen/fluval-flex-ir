# Fluval Flex IR for Home Assistant

![Aquarium and infrared signal](custom_components/fluval_flex_ir/brand/icon.png)

Control a Fluval Flex 2.0 aquarium light with any Home Assistant infrared emitter pointed at the tank. The integration adds all 24 buttons on the Flex 2.0 handset, including separate RGB and white controls. Each button sends one infrared command. Its state in Home Assistant is the time it was last pressed. The aquarium provides no feedback about its current colour, brightness or power.

## Install

1. In Home Assistant 2026.11.1 or later, open **Settings → Marketplace → Add from link**. Enter `https://github.com/simonjgreen/fluval-flex-ir` and select **Add**. Connect GitHub if prompted.
2. Open **Fluval Flex IR** in Marketplace and select **Install**.
3. In **Settings → Devices & services → Add integration**, select **Fluval Flex IR**. Name the aquarium and choose the infrared **emitter** facing the lamp's receiver. For the optional ESPHome build, choose **Mini IR Emitter** if the external Mini IR Unit faces the tank.
4. Open the new aquarium device and press **Blue** to test. A line of sight from the emitter to the tank's IR receiver is required. You can use **Reconfigure** on the integration to select another emitter later.

For a manual installation, copy [custom_components/fluval_flex_ir](custom_components/fluval_flex_ir) into your Home Assistant configuration's `custom_components` directory, restart Home Assistant, and continue at step 3. [Home Assistant infrared setup](https://www.home-assistant.io/connectivity/infrared/)

## Handset

The table follows the physical remote from the top left. Swatch names describe the printed buttons. The RGB and white power buttons each toggle their own channel, so pressing one twice returns that channel to its original state.

| Left | Centre left | Centre right | Right |
| --- | --- | --- | --- |
| RGB brightness up | RGB brightness down | Toggle RGB | Toggle white |
| Red | Green | Blue | White brightness up |
| Coral red | Light green | Medium blue | White brightness down |
| Red-orange | Mint green | Indigo | Moon/cloud |
| Orange | Turquoise | Purple | Storm |
| Yellow | Deep teal | Pink | Colour cycle |

Use **Perform action → Button: Press** in an automation and select the desired button. A colour preset is a repeatable target. The power toggles and brightness steps depend on the lamp's previous state.

## Optional ESPHome proxy and case

The [ESPHome firmware](esphome/fluval-ir-proxy.yaml) is for an M5Stack ATOM Lite with a U002 Mini IR Unit. With USB power disconnected, wire a Grove-to-DuPont lead to the ATOM's rear header.

| Mini IR Unit wire | ATOM Lite header |
| --- | --- |
| Black | GND |
| Red | 3V3 |
| Yellow · transmitter | G23 |
| White · receiver | G33 |

The U002 pulls its receiver output up to its supply voltage. Use the 3V3 header for this build. A direct Grove-to-Grove cable supplies 5 V. The ATOM's onboard IR emitter is available as a second transmitter. [M5Stack Unit IR schematic](https://static-cdn.m5stack.com/resource/docs/products/unit/ir/ir_sch_01.webp)

To build your own proxy, generate an API encryption key with `openssl rand -base64 32` and save it as `fluval_api_key` in a private `secrets.yaml` next to the ESPHome file. Flash that configuration using ESPHome 2026.11.0 or later, provision Wi-Fi over USB using Improv Serial, and add the ESPHome device to Home Assistant. The [printable enclosure](case/README.md) has a horizontal USB-C exit.

## Verification

The command table was recorded from a physical Fluval Flex 2.0 handset. The [captured waveforms](tests/fixtures/fluval_flex_2_0.json) are extended NEC at address `0xEF00`. The integration uses Home Assistant's native infrared platform to send the corresponding command at 38 kHz. The offline tests run in Docker from the repository root.

```sh
sh tests/run.sh -v
```
