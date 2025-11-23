# CiefpSelectSatellite

![Bouquet](https://github.com/ciefp/CiefpSelectSatellite/blob/main/ciefpselectsatellite.jpg)

A lightweight and intuitive Enigma2 plugin designed for quick satellite selection and management. Perfect for users with multi-satellite setups (e.g., motorized dishes, DiSEqC switches, or USALS systems), this plugin provides a simple interface to switch between satellites without digging through menus. It supports both manual selection and favorites, making it essential for satellite enthusiasts tuning into DVB-S/S2 transponders across Europe, Balkans, and beyond.

Built with efficiency in mind, it runs smoothly on all major Enigma2 images like OpenATV, OpenPLi, OpenViX, PurE2, VTi, and OpenBH – no bloat, just fast access.

## Features

- **Quick Satellite Picker**: One-click access to a searchable list of 100+ popular satellites (e.g., Hotbird 13E, Astra 19.2E, Eutelsat 9E, Turksat 42E).
- **Favorites System**: Save your most-used satellites (up to 20) for instant switching – ideal for Ex-Yu, UK, German, or sports packages.
- **DiSEqC & USALS Support**: Full compatibility with motorized setups, positioners, and switch configurations.
- **Transponder Scan Integration**: Jump directly to blind scan or service scan after selecting a satellite.
- **Customizable List**: Add/remove satellites or edit details (name, longitude, frequency) via simple config.
- **Background Operation**: No GUI clutter – launches from Plugins menu or via hotkey (configurable).

*(Features based on plugin version 1.0+. For exact capabilities, check the in-plugin help or source code.)*

## Requirements

- Enigma2-based receiver (e.g., VU+, Dreambox, Octagon, Gigablue).
- Compatible image: OpenATV 7.0+, OpenPLi 8.0+, or equivalents.
- Python 2.7/3.x (standard in Enigma2).
- Optional: Motorized dish with USALS/DiSEqC for full functionality.

No external dependencies – pure Enigma2 components.

## Installation (Under 1 Minute)

1. **Download the Plugin**:
   - Clone the repo: `git clone https://github.com/ciefp/CiefpSelectSatellite.git`
   - Or download ZIP from the Releases page.

2. **Transfer via FTP**:
   - Connect to your receiver (e.g., using FileZilla).
   - Navigate to `/usr/lib/enigma2/python/Plugins/Extensions/`.
   - Create folder `CiefpSelectSatellite` if needed.
   - Upload all files (primarily `plugin.py` and any `*.py` or icons).

3. **Restart Enigma2**:
   - Reboot the box or run `init 4 && init 3` via SSH/Telnet.
   - The plugin will appear in **Plugins > Extensions > CiefpSelectSatellite**.

4. **IPK Option** (if available):
   - Download `.ipk` from Releases and install via Opkg or Enigma's Software Manager.

## Usage

1. **Launch the Plugin**:
   - From Plugins menu: Select **CiefpSelectSatellite > Quick Select**.
   - Or assign a hotkey (e.g., Blue button) in plugin settings.

2. **Select a Satellite**:
   - Browse the alphabetical list or search by name/longitude (e.g., type "13" for Hotbird).
   - Choose from favorites (starred items) for speed.
   - Confirm to move the dish (if motorized) and update services.

3. **Add to Favorites**:
   - After selection, press OK on a satellite → **Add to Favorites**.
   - Edit favorites in **Settings > Manage Favorites**.

4. **Advanced Options**:
   - **Scan After Select**: Enable to auto-start a transponder scan.
   - **Custom Satellites**: In Settings, add new entries like "Thor 0.8W" with details.

Pro Tip: Pair with CiefpSatelliteAnalyzer for automated bouquet creation post-scan!

## Configuration

Access via **Plugin > Settings**:

- **Favorites List**: Add/edit/remove up to 20 satellites.
- **Search Mode**: Enable/disable fuzzy search.
- **Auto-Move Dish**: Toggle for non-motorized setups.
- **Default Scan Type**: Blind scan, service search, or none.
- **Hotkey Assignment**: Bind to remote buttons.

Changes apply immediately – no restart needed.

## Known Issues

- On very old images (pre-6.0), DiSEqC 1.2 may require manual tuner config.
- Large satellite lists (>200) might slow search on low-RAM boxes (e.g., <512MB).
- USALS accuracy depends on dish setup – calibrate in Enigma's Tuner Config first.

## Contributing

Love this plugin? Help make it better!

1. Fork the repo.
2. Create a branch: `git checkout -b feature/new-satellite`.
3. Commit changes: `git commit -m 'Add support for new satellite'`.
4. Push: `git push origin feature/new-satellite`.
5. Open a Pull Request.

Suggestions for new satellites or features? Open an Issue!

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) – see [LICENSE](LICENSE) for details. Free as in freedom, just like Enigma2.

## Support

- **Issues**: Report bugs or request features at [GitHub Issues](https://github.com/ciefp/CiefpSelectSatellite/issues).
- **Community**: Discuss on Enigma2 forums like LinuxSat, OpenPLi.org, or Satelitski Forum.
- **More Plugins**: Check out my other tools like [CiefpIPTVBouquets](https://github.com/ciefp/CiefpIPTVBouquets) for IPTV magic.

Thanks to the Enigma2 community for the amazing open-source foundation!

---

*Last updated: November 23, 2025*  
Enjoy effortless satellite hopping! 🛰️