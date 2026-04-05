# Talking Clock

An accessible clock that announces the time on demand or automatically at regular intervals. Designed to be built from off-the-shelf components and localized to any language that has a [Piper TTS](https://github.com/rhasspy/piper) voice model.

![Clock Enclosure Rendering](./enclosure/assets/enclosure_00.png)

## Overview

The clock is built around a Raspberry Pi Pico running CircuitPython. Three buttons provide the entire user interface: one to announce the time, and two for navigating settings. All audio is pre-generated and stored on an SD card, making the clock fully offline with no network dependency.

The project has three main components:

| Component | Location | Description |
| --------- | -------- | ----------- |
| Firmware | [`./clock_code/`](./clock_code/) | CircuitPython code that runs on the Pico |
| Audio tooling | [`./talking-clock-audio/`](./talking-clock-audio/) | Python CLI for generating and deploying voice packages |
| Hardware | [`./circuit/`](./circuit/) and [`./enclosure/`](./enclosure/) | Bill of materials, wiring, and laser-cut enclosure design |

## Fast Track

This is the shortest path from parts to a working clock. Each step links to the relevant README for full details.

### 1. Assemble the hardware

Build the circuit from the bill of materials and wiring diagram in the [electronics README](./electronics/README.md). The enclosure design is in the [enclosure README](./enclosure/README.md) and is optional -- the clock works without one.

### 2. Install CircuitPython and firmware

Follow the [clock firmware README](./clock_code/README.md) to install CircuitPython 10.x on the Pico, copy the firmware files, and prepare the SD card with the bundled audio assets.

### 3. Deploy a voice package

Voice packages are included in the repository. Connect the SD card to your computer and run:

```bash
cd talking-clock-audio
python -m venv venv
source venv/bin/activate
pip install -e .
tca deploy
```

Select the SD card volume and choose the packages to copy. The default firmware configuration expects a voice package named `en_US_lessac_medium`. See the [talking-clock-audio README](./talking-clock-audio/README.md) for the full workflow including generating packages for other languages.

### 4. First boot

Insert the SD card and power on the clock. The firmware will create a default `config.json` on the SD card automatically. Press ANNOUNCE to hear the time. Hold PLUS or MINUS for 1.5 seconds to open the settings menu and set the correct time.

## Localization

The clock supports any language that has a Piper TTS voice model on Hugging Face. Adding a new language requires creating a YAML phrase configuration file and generating a voice package with the `tca` tool. See the [talking-clock-audio README](./talking-clock-audio/README.md) for the full workflow, including an LLM-assisted tool for building YAML configurations for languages you are not fluent in.

## Repository Structure

```text
talking-clock/
  clock_code/              # CircuitPython firmware and SD card audio assets
  talking-clock-audio/     # tca CLI for generating and deploying voice packages
  electronics/             # Bill of materials, wiring, and schematics
  enclosure/               # Laser-cut enclosure OpenSCAD design and assets
```

## Attributions

### Audio Files

| Asset | Attribution |
| ----- | ----------- |
| [volume_boop.wav](./clock_code/sd_card/audio_assets/volume_boop.wav) | [546974__finix473__ui_click](https://freesound.org/people/finix473/sounds/546974/) |
| [alarms/accepted-sweet.wav](./clock_code/sd_card/audio_assets/alarms/accepted-sweet.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/adventure-harp.wav](./clock_code/sd_card/audio_assets/alarms/adventure-harp.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/bell-motif.wav](./clock_code/sd_card/audio_assets/alarms/bell-motif.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/sine-aww.wav](./clock_code/sd_card/audio_assets/alarms/sine-aww.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/sine-cellular.wav](./clock_code/sd_card/audio_assets/alarms/sine-cellular.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/welcome-home-synth.wav](./clock_code/sd_card/audio_assets/alarms/welcome-home-synth.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/xd-mewtwo.wav](./clock_code/sd_card/audio_assets/alarms/xd-mewtwo.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
| [alarms/xmas-miracle.wav](./clock_code/sd_card/audio_assets/alarms/xmas-miracle.wav) | [akelley6](https://freesound.org/people/akelley6/packs/44231/) |
## License

GPL-3.0-or-later

## Contributing

Contributions are welcome, especially new language configurations, voice model recommendations, hardware improvements, and enclosure designs. Open an issue or pull request on [GitHub](https://github.com/txoof/talking-clock).