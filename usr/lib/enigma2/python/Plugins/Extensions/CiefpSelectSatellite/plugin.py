import os
import re
import sys
import shutil
import zipfile
import requests
from xml.etree import ElementTree
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from enigma import eConsoleAppContainer
from enigma import eDVBDB

PLUGIN_VERSION = "1.7"
PLUGIN_ICON = "plugin.png"
PLUGIN_NAME = "CiefpSelectSatellite"
PLUGIN_DESCRIPTION = "Satellite Selection Plugin"
TMP_DOWNLOAD = "/tmp/ciefp-E2-75E-34W"
TMP_SELECTED = "/tmp/CiefpSelectSatellite"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]


UPDATE_COMMAND = "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSelectSatellite/main/installer.sh -O - | /bin/sh"

class CiefpSelectSatellite(Screen):
    skin = """
        <screen position="center,center" size="1600,800" title="..:: Ciefp Satellite Selector ::..    (Version {version}) ">
            <!-- Prvi deo - Levi lista -->
            <widget name="left_list" position="0,0" size="620,700" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />

            <!-- Drugi deo - Desni lista -->
            <widget name="right_list" position="630,0" size="600,700" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />

            <!-- Treći deo - Background -->
            <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSelectSatellite/background.png" position="1240,0" size="360,800" />

            <!-- Status bar -->
            <widget name="status" position="0,710" size="840,50" font="Regular;24" />

            <!-- Dugmad na dnu -->
            <widget name="red_button" position="0,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
            <widget name="green_button" position="170,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
            <widget name="yellow_button" position="340,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
            <widget name="key_blue" position="500,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#13389F" foregroundColor="#000000" />
            <widget name="version_info" position="680,750" size="350,40" font="Regular;20" foregroundColor="#FFFFFF" />
        </screen>
    """.format(version=PLUGIN_VERSION)
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.selected_satellites = []
        self.bouquet_mapping = self.create_bouquet_mapping()
        
        # UI Components
        self["left_list"] = MenuList([])
        self["right_list"] = MenuList([])
        self["background"] = Pixmap()
        self["status"] = Label("Initializing...")
        self["green_button"] = Label("Copy")
        self["yellow_button"] = Label("Install")
        self["red_button"] = Label("Exit")
        self["key_blue"] = Label("Update")
        self["version_info"] = Label("") 
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
        {
            "ok": self.select_item,
            "cancel": self.exit,
            "green": self.copy_files,
            "yellow": self.install,
            "red": self.exit,
            "blue": self.confirm_update,
            "up": self.up,
            "down": self.down,
            "left": self.switch_left,
            "right": self.switch_right,
        }, -1)
        self.onLayoutFinish.append(self.fetch_version_info)
        self.download_settings()

    def confirm_update(self):
        self.session.openWithCallback(self.prompt_update, MessageBox,
                                      "Do you want to update the plugin?",
                                      MessageBox.TYPE_YESNO)

    def prompt_update(self, answer):
        if answer:
            self.update_plugin()

    def update_plugin(self):
        self["status"].setText("Updating plugin...")
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.update_finished)
        self.container.dataAvail.append(self.update_output)
        self.container.execute(UPDATE_COMMAND)

    def update_output(self, data):
        self["status"].setText(self["status"].getText() + "\n" + data.decode("utf-8"))

    def update_finished(self, retval):
        if retval == 0:
            self["status"].setText("The plugin has been successfully updated.")
        else:
            self["status"].setText("An error occurred while updating.")

    def create_bouquet_mapping(self):
        return {
            '80.0E': ['userbouquet.ciefp_80e.tv'],
            '75.0E': ['userbouquet.ciefp_68e.tv'],
            '70.5E': ['userbouquet.ciefp_68e.tv'],
            '68.5E': ['userbouquet.ciefp_68e.tv'],
            '66.0E': ['userbouquet.ciefp_62e.tv'],
            '62.0E': ['userbouquet.ciefp_62e.tv'],
            '54.9E': ['userbouquet.ciefp_55e.tv'],
            '53.0E': ['userbouquet.ciefp_53e.tv'],
            '52.5E': ['userbouquet.ciefp_53e.tv'],
            '52.0E': [
                'userbouquet.ciefp_52e.tv',
                'userbouquet.ciefp_52e_aref.tv'
            ],
            '51.5E': ['userbouquet.ciefp_51e.tv'],
            '46.0E': ['userbouquet.ciefp_46e.tv'],
            '45.0E': [
                'userbouquet.ciefp_45e.tv',
                'userbouquet.ciefp_45e_vivacom.tv'
            ],
            '42.0E': [
                'userbouquet.ciefp_42e_turksat.tv',
                'userbouquet.ciefp_42e_digiturk.tv',
                'userbouquet.ciefp_42e_dsmart.tv',
                'userbouquet.ciefp_42e_tivibu.tv'
            ],
            '39.0E': [
                'userbouquet.ciefp_39e_hellas.tv',
                'userbouquet.ciefp_39e_hellas_sport.tv',
                'userbouquet.ciefp_39e_ert.tv',
                'userbouquet.ciefp_39e_polaris.tv',
                'userbouquet.ciefp_39e_dolce.tv',
                'userbouquet.ciefp_39e_a1bg.tv'
            ],
            '36.0E': ['userbouquet.ciefp_36e.tv'],
            '31.0E': ['userbouquet.ciefp_31e.tv'],
            '28.2E': [
                'userbouquet.ciefp_28e_astra.tv',
                'userbouquet.ciefp_28e_skyuk_icam.tv',
                'userbouquet.ciefp_28e_skyukmovie.tv',
                'userbouquet.ciefp_28e_skyukdocuments.tv',
                'userbouquet.ciefp_28e_skyuksports.tv',
                'userbouquet.ciefp_28e_skyukkids.tv',
                'userbouquet.ciefp_28e_skyukgeneral.tv'
            ],
            '26.0E': [
                'userbouquet.ciefp_26e_badr.tv',
                'userbouquet.ciefp_26e_mbc.tv'
            ],
            '23.5E': [
                'userbouquet.ciefp_23e_astra.tv',
                'userbouquet.ciefp_23e_skylinkgeneral.tv',
                'userbouquet.ciefp_23e_skylink.tv',
                'userbouquet.ciefp_23e_canaldigital.tv',
                'userbouquet.ciefp_23e_sport.tv',
                'userbouquet.ciefp_23e_telekomsrbija.tv'
            ],
            '21.5E': ['userbouquet.ciefp_21e_eutelsat.tv'],
            '19.2E': [
                'userbouquet.ciefp_19e_astra.tv',
                'userbouquet.ciefp_19e_movistarsport.tv',
                'userbouquet.ciefp_19e_movistarmovies.tv',
                'userbouquet.ciefp_19e_movistardocu.tv',
                'userbouquet.ciefp_19e_skyde_icam.tv',
                'userbouquet.ciefp_19e_skydemovies.tv',
                'userbouquet.ciefp_19e_skydedocu.tv',
                'userbouquet.ciefp_19e_skydesport.tv',
                'userbouquet.ciefp_19e_hdplus.tv',
                'userbouquet.ciefp_19e_ORF.tv',
                'userbouquet.ciefp_19e_fta.tv',
                'userbouquet.ciefp_19e_canaldigitaal.tv',
                'userbouquet.ciefp_19e_canalsat.tv'
            ],
            '16.1E': [
                'userbouquet.ciefp_16e_rtsh.tv',
            ],
            '16.0E': [
                'userbouquet.ciefp_16e_eutelsat.tv',
                'userbouquet.ciefp_16e_oivzagreb.tv',
                'userbouquet.ciefp_16e_maxtv.tv',
                'userbouquet.ciefp_16e_pink.tv',
                'userbouquet.ciefp_16e_antiksat.tv',
                'userbouquet.ciefp_16e_sport.tv',
                'userbouquet.ciefp_16e_totaltv.tv',
                'userbouquet.ciefp_16e_vipnet.tv',
                'userbouquet.ciefp_16e_digitalbania.tv',
                'userbouquet.ciefp_16e_freesatromania.tv'
            ],
            '13.0E': [
                'userbouquet.ciefp_13e_hotbird.tv',
                'userbouquet.ciefp_13e_polandmovies.tv',
                'userbouquet.ciefp_13e_polanddocu.tv',
                'userbouquet.ciefp_13e_polandgeneral.tv',
                'userbouquet.ciefp_13e_polandsport.tv',
                'userbouquet.ciefp_13e_sfi.tv',
                'userbouquet.ciefp_13e_orangefrance.tv',
                'userbouquet.ciefp_13e_raimediaset.tv',
                'userbouquet.ciefp_13e_vivacom.tv',
                'userbouquet.ciefp_13e_skyitaliahd.tv',
                'userbouquet.ciefp_13e_skyitalia_icam.tv',
                'userbouquet.ciefp_13e_novagreece.tv'
            ],
            '10.0E': ['userbouquet.ciefp_10e_eutelsat.tv'],
            '9.0E': [
                'userbouquet.ciefp_9e_eutelsat.tv',
                'userbouquet.ciefp_9e_kabelkiosk.tv',
                'userbouquet.ciefp_9e_cosmote.tv',
                'userbouquet.ciefp_9e_afn.tv',
                'userbouquet.ciefp_9e_mediaset.tv',
                'userbouquet.ciefp_9e_persidera.tv'
            ],
            '7.0E': ['userbouquet.ciefp_7e_eutelsat.tv'],
            '4.8E': [
                'userbouquet.ciefp_5e_fta_powervu.tv',
                'userbouquet.ciefp_5e_ukraina.tv',
                'userbouquet.ciefp_5e_brt_t2mi.tv'
            ],
            '3.0E': ['userbouquet.ciefp_3e_eutelsat.tv'],
            '1.9E': [
                'userbouquet.ciefp_2e_bulgariasat1.tv',
                'userbouquet.ciefp_2e_neosat.tv'
            ],
            '0.8W': [
                'userbouquet.ciefp_08w_thor.tv',
                'userbouquet.ciefp_08w_sport.tv',
                'userbouquet.ciefp_08w_docu.tv',
                'userbouquet.ciefp_08w_music.tv',
                'userbouquet.ciefp_08w_allente_sve_den.tv',
                'userbouquet.ciefp_08w_allente_movie_music.tv',
                'userbouquet.ciefp_08w_directone_svk.tv',
                'userbouquet.ciefp_08w_directone_movies.tv',
                'userbouquet.ciefp_08w_focussat.tv',
                'userbouquet.ciefp_08w_focussat_movies.tv',
                'userbouquet.ciefp_08w_digitv.tv',
                'userbouquet.ciefp_08w_slovaktelekom.tv'
            ],
            '4.0W': ['userbouquet.ciefp_4w_amos.tv'],
            '5.0W': [
                'userbouquet.ciefp_5w_eutelsat.tv',
                'userbouquet.ciefp_5w_rai.tv',
                'userbouquet.ciefp_5w_france_multistream.tv',
                'userbouquet.ciefp_5w_francesat.tv',
            ],
            '7.0W': ['userbouquet.ciefp_7w.tv'],
            '14.0W': ['userbouquet.ciefp_14w.tv'],
            '22.0W': ['userbouquet.ciefp_15w.tv'],
            '24.5W': ['userbouquet.ciefp_15w.tv'],
            '30.0W': [
                'userbouquet.ciefp_30w_hispasat.tv',
                'userbouquet.ciefp_30w_hispasatsport.tv',
                'userbouquet.ciefp_30w_nos.tv',
                'userbouquet.ciefp_30w_meotv.tv',
                'userbouquet.ciefp_30w_abertis.tv'
            ],
            '34.5W': ['userbouquet.ciefp_35w.tv'],
            'DVBT/T2': [
                'userbouquet.ciefp_terrestrial_fta.tv',
                'userbouquet.ciefp_terrestrial_paytv.tv'
            ]
        }


    def find_satellite_bouquet(self, naziv_satelita):
        match = re.search(r'(\d+\.\d+[EW])', naziv_satelita)
        if match:
            pozicija = match.group(1)
            if pozicija in self.bouquet_mapping:
                return self.bouquet_mapping[pozicija]
        return None

    def parse_satellites(self):
        xml_path = os.path.join(TMP_DOWNLOAD, "satellites.xml")
        if not fileExists(xml_path):
            self["status"].setText("Error: satellites.xml not found!")
            return
        try:
            with open(xml_path, 'r', encoding='iso-8859-1') as f:
                xml_content = f.read()
            root = ElementTree.fromstring(xml_content)
            satellites = [sat.get('name') for sat in root.findall('sat')]
            # Filter satellites
            filtered_satellites = []
            for sat in satellites:
                for key in self.bouquet_mapping.keys():
                    if key in sat:
                        filtered_satellites.append(sat)
                        break
            self["left_list"].setList(filtered_satellites)
            self["status"].setText("Satellites loaded successfully.")
        except Exception as e:
            self["status"].setText(f"Error parsing XML: {str(e)}")

    def download_settings(self):
        self["status"].setText("Fetching file list from GitHub...")
        try:
            # Query GitHub API for available files
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()  # Raise error for bad response
            files = response.json()
            # Find desired ZIP file
            zip_url = None
            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    zip_url = file["download_url"]
                    break
            if not zip_url:
                raise Exception("No matching ZIP file found on GitHub.")
            # Download ZIP file
            self["status"].setText("Downloading settings from GitHub...")
            zip_path = os.path.join("/tmp", "latest.zip")
            zip_response = requests.get(zip_url)
            with open(zip_path, 'wb') as f:
                f.write(zip_response.content)
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                temp_extract_path = "/tmp/temp_extract"
                if not os.path.exists(temp_extract_path):
                    os.makedirs(temp_extract_path)
                zip_ref.extractall(temp_extract_path)
                extracted_root = os.path.join(temp_extract_path, os.listdir(temp_extract_path)[0])
                if os.path.exists(TMP_DOWNLOAD):
                    shutil.rmtree(TMP_DOWNLOAD)
                shutil.move(extracted_root, TMP_DOWNLOAD)
            self["status"].setText("Settings downloaded and extracted successfully.")
            self.parse_satellites()
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")

    def fetch_version_info(self):
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            files = response.json()

            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    version_with_date = file["name"].replace(".zip", "")
                    self["version_info"].setText(f"({version_with_date})")
                    return

            self["version_info"].setText(f"(Date not available)")
        except Exception as e:
            self["version_info"].setText(f"(Error fetching date)")

    def select_item(self):
        selected = self["left_list"].getCurrent()
        if selected:
            # Izdvoji numerički deo iz selektovanog satelita
            numeric_selected = re.findall(r'\d+\.\d+[EW]', selected)
            if numeric_selected:
                numeric_selected = numeric_selected[0]
                if numeric_selected in [re.findall(r'\d+\.\d+[EW]', sat)[0] for sat in self.selected_satellites if
                                        re.findall(r'\d+\.\d+[EW]', sat)]:
                    self.selected_satellites.remove(selected)
                    print(f"[DEBUG] Uklonjen satelit: {selected}")
                else:
                    self.selected_satellites.append(selected)
                    print(f"[DEBUG] Dodat satelit: {selected}")
            else:
                if selected in self.selected_satellites:
                    self.selected_satellites.remove(selected)
                    print(f"[DEBUG] Uklonjen satelit: {selected}")
                else:
                    self.selected_satellites.append(selected)
                    print(f"[DEBUG] Dodat satelit: {selected}")
            self["right_list"].setList(self.selected_satellites)
            print(f"[DEBUG] Trenutna lista satelita: {self.selected_satellites}")

    def copy_files(self):
        try:
            if not os.path.exists(TMP_SELECTED):
                os.makedirs(TMP_SELECTED)

            # Lista zajedničkih fajlova
            common_files = [
                'satellites.xml',
                'lamedb',
                'bouquets.tv',
                'userbouquet.buket_exyu.tv',
                'userbouquet.buket_pinktv.tv',
                'userbouquet.buket_maxtv.tv',
                'userbouquet.buket_sport.tv',
                'userbouquet.buket_kids.tv',
                'userbouquet.buket_docu.tv',
                'userbouquet.buket_movie.tv',
                'userbouquet.buket_music.tv',
                'userbouquet.buket_uhd.tv',
                'userbouquet.buket_adult.tv',
                'userbouquet.buket_multistream.tv',
                'userbouquet.buket_emu.tv',
                'userbouquet.marker_vod_exyu.tv',
                'userbouquet.ciefp_terrestrial_fta.tv',
                'userbouquet.ciefp_terrestrial_paytv.tv',
                'userbouquet.ciefpsettings_iptv_webcam.tv',
                'userbouquet.ciefpsettings_iptv_exyu.tv',
                'userbouquet.ciefpsettings_iptv_exyu2.tv',
                'userbouquet.ciefpsettings_iptv_news_music.tv',
                'userbouquet.ciefpsettings_iptv_mix.tv',
                'userbouquet.ciefpsettings_iptv_mix2.tv',
                'userbouquet.ciefpsettings_iptv_sport.tv',
                'userbouquet.ciefpsettings_iptv_movies.tv',
                'userbouquet.ciefpsettings_iptv_movies2.tv',
                'userbouquet.link_0_marker.tv',
                'userbouquet.link_5.tv',
                'userbouquet.link_3.tv',
                'userbouquet.LastScanned.tv',
                'userbouquet.favourites.tv',
                'bouquets.radio',
                'userbouquet.dbe00.radio',
                'userbouquet.ciefpsettings_exyu.radio',
                'userbouquet.ciefpsettings_slovakia.radio',
                'userbouquet.ciefpsettings_czech.radio',
                'userbouquet.ciefpsettings_germany.radio',
                'userbouquet.ciefpsettings_romania.radio',
                'userbouquet.favourites.radio" ORDER BY bouquet'
            ]

            # Kopiranje zajedničkih fajlova
            for f in common_files:
                src = os.path.join(TMP_DOWNLOAD, f)
                if os.path.exists(src):
                    shutil.copy(src, TMP_SELECTED)

            # Kopiranje buketa za selektovane satelite
            for sat in self.selected_satellites:
                bouquets = self.find_satellite_bouquet(sat)
                if bouquets:
                    for bouquet_file in bouquets:
                        src = os.path.join(TMP_DOWNLOAD, bouquet_file)
                        if os.path.exists(src):
                            shutil.copy(src, TMP_SELECTED)
                        else:
                            print(f"[WARNING] Fajl {bouquet_file} ne postoji u {TMP_DOWNLOAD}")

            # Filtriraj tematske bukete prema selektovanim satelitima
            theme_bouquets = [
                'userbouquet.buket_exyu.tv',
                'userbouquet.buket_sport.tv',
                'userbouquet.buket_kids.tv',
                'userbouquet.buket_docu.tv',
                'userbouquet.buket_movie.tv',
                'userbouquet.buket_music.tv',
                'userbouquet.buket_uhd.tv',
                'userbouquet.buket_adult.tv',
                'userbouquet.buket_multistream.tv',
                'userbouquet.buket_emu.tv'
            ]
            for theme_bouquet in theme_bouquets:
                src = os.path.join(TMP_DOWNLOAD, theme_bouquet)
                if os.path.exists(src):
                    # Ekstrahuju se samo numerički delovi selektovanih satelita
                    numeric_selected_satellites = [re.findall(r'\d+\.\d+[EW]', sat)[0] for sat in
                                                   self.selected_satellites if re.findall(r'\d+\.\d+[EW]', sat)]
                    if not self.filter_channels_by_satellite(os.path.join(TMP_SELECTED, theme_bouquet),
                                                             numeric_selected_satellites):
                        print(f"Failed to filter {theme_bouquet}. Keeping original content.")
                else:
                    print(f"[WARNING] Theme bouquet {theme_bouquet} does not exist in {TMP_DOWNLOAD}")

            self["status"].setText("Files copied successfully!")
        except Exception as e:
            self["status"].setText(f"Copy error: {str(e)}")

    def parse_bouquets_file(self, bouquets_path):
        """Vraća listu tuplova (originalna_linija, ime_fajla)."""
        bouquets = []
        try:
            with open(bouquets_path, 'r') as file:
                for line in file:
                    line = line.strip()  # Ukloni whitespace
                    if not line or line.startswith("#NAME"):
                        bouquets.append((line + "\n", None))  # Zadrži komentare
                    elif "FROM BOUQUET" in line:
                        # Ekstraktuj tačno ime fajla iz linije
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if start != -1 and end != -1:
                            bouquet_file = line[start:end]
                            bouquets.append((line + "\n", bouquet_file))
                        else:
                            print(f"Nevalidna linija: {line}")
        except Exception as e:
            print(f"Greška pri čitanju bouquets.tv: {e}")
        return bouquets

    def remove_missing_bouquets(self, bouquets_path, bouquets, check_path):
        """Proverava postojanje fajlova i briše linije bez fajlova."""
        try:
            valid_lines = []
            for line, bouquet_file in bouquets:
                if bouquet_file is None:  # Zadrži komentare (npr. #NAME)
                    valid_lines.append(line)
                    continue

                full_path = os.path.join(check_path, bouquet_file)
                if os.path.isfile(full_path):
                    valid_lines.append(line)
                    print(f"Zadržana linija: {bouquet_file}")
                else:
                    print(f"Obrisana linija: {bouquet_file}")

            # Snimi ažurirani bouquets.tv
            with open(bouquets_path, 'w') as file:
                file.writelines(valid_lines)
        except Exception as e:
            self["status"].setText(f"Greška prilikom ažuriranja bouquets.tv: {str(e)}")

    def process_and_copy_bouquets(self, bouquets_file_path, source_dir, enigma2_dir):
        try:
            # Pročitaj i filtriraj bouquets.tv
            bouquets = self.parse_bouquets_file(bouquets_file_path)
            if not bouquets:
                self["status"].setText("Nema validnih buketa!")
                return

            # Obriši nepostojeće reference
            self.remove_missing_bouquets(bouquets_file_path, bouquets, source_dir)

            # Kopiraj ažurirani bouquets.tv u /etc/enigma2
            shutil.copy(bouquets_file_path, enigma2_dir)
            print(f"Bouquets.tv ažuriran i kopiran u {enigma2_dir}")

        except Exception as e:
            self["status"].setText(f"Greška: {str(e)}")

    def extract_filename_from_line(self, line):
        """
        Ekstraktuje naziv fajla iz linije koja sadrži "#SERVICE".
        Pretpostavljamo da je fajl tipa "userbouquet.*.tv".
        """
        # Na osnovu formata linije, tražimo deo nakon "userbouquet." i pre ".tv"
        if "userbouquet." in line and ".tv" in line:
            start = line.find("userbouquet.") + len("userbouquet.")
            end = line.find(".tv", start)
            if start != -1 and end != -1:
                return line[start:end] + ".tv"  # Vraćamo samo ime fajla
        return None

    def update_bouquets(tv_bouquet_file, tmp_folder):
        # Čitanje svih fajlova u /tmp/CiefpSelectSatellite
        print(f"Učitavam fajlove iz foldera: {tmp_folder}")
        tmp_files = set(os.listdir(tmp_folder))  # Kreiraj skup fajlova u tmp folderu
        print(f"Fajlovi pronađeni u tmp folderu: {tmp_files}")

        # Čitanje linija iz bouquets.tv fajla
        print(f"Učitavam fajl: {tv_bouquet_file}")
        with open(tv_bouquet_file, 'r') as file:
            lines = file.readlines()

        print(f"Broj linija u fajlu {tv_bouquet_file}: {len(lines)}")

        updated_lines = []

        # Prolazimo kroz sve linije u bouquets.tv
        for line in lines:
            if 'FROM BOUQUET' in line:  # Tražimo linije koje sadrže fajl iz tmp foldera
                # Ekstraktujemo ime fajla iz linije
                start_idx = line.find('"') + 1
                end_idx = line.find('"', start_idx)
                bouquet_file = line[start_idx:end_idx]

                # Ako fajl postoji u tmp folderu, zadržavamo liniju, inače je brišemo
                if bouquet_file in tmp_files:
                    updated_lines.append(line)
                    print(f"Zadržana linija: {line.strip()}")
                else:
                    print(f"Obrisana linija: {line.strip()} (fajl '{bouquet_file}' ne postoji u tmp folderu)")
            # Dodajemo proveru za greške vezane za fajlove
            elif "Can't open" in line or "Can't load bouquet" in line:
                # Linije koje sadrže greške u vezi sa fajlovima se brišu
                print(f"Obrisana linija: {line.strip()} (greška u otvaranju fajla)")
            else:
                updated_lines.append(line)

        # Upisujemo ažurirani sadržaj u bouquets.tv
        print(f"Ažuriranje fajla {tv_bouquet_file}...")
        with open(tv_bouquet_file, 'w') as file:
            file.writelines(updated_lines)

        print(f"Ažurirani fajl {tv_bouquet_file} je sačuvan.")

        # Pozivanje funkcije sa odgovarajućim argumentima
        update_bouquets('/etc/enigma2/bouquets.tv', '/tmp/CiefpSelectSatellite')

    def filter_channels_by_satellite(self, filename, selected_satellites):
        if not os.path.exists(filename):
            print(f"File {filename} does not exist.")
            return False

        with open(filename, 'r') as f:
            lines = f.readlines()

        filtered_lines = []
        current_satellite = None
        keep_lines = False
        SAT_MARKER_REGEX = r'#SERVICE \d+:\d+:[\w\d]+:.*::\| (.+?) \|::'
        NUMERIC_SAT_REGEX = r'(\d+\.\d+[EW])'

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Dodaj prvu liniju (#NAME) bez uslova
            if line.startswith('#NAME'):
                filtered_lines.append(line)
                print(f"Adding NAME line: {line}")
                i += 1
                continue

            # Pronađi marker satelita ako postoji
            if line.startswith('#SERVICE 1:64'):
                match = re.search(SAT_MARKER_REGEX, line)
                if match:
                    satellite_name = match.group(1).strip()
                    numeric_match = re.search(NUMERIC_SAT_REGEX, satellite_name)
                    if numeric_match:
                        numeric_satellite = numeric_match.group(1)
                        print(f"Found satellite marker: {line}, Numeric Satellite: {numeric_satellite}")
                        # Proveri da li je satelit jedan od onih koje tražimo
                        keep_lines = any(sat in numeric_satellite for sat in selected_satellites)
                        if keep_lines:
                            current_satellite = numeric_satellite
                            filtered_lines.append(line)
                            print(f"Adding satellite marker: {line}")
                            i += 1

                            # Dodaj opis ako postoji
                            if i < len(lines) and lines[i].startswith('#DESCRIPTION'):
                                description_line = lines[i].strip()
                                filtered_lines.append(description_line)
                                print(f"Adding satellite description: {description_line}")
                                i += 1

                            # Kopiraj sve pripadajuće #SERVICE 1:0 linije dok ne naiđemo na sledeći #SERVICE 1:64
                            while i < len(lines) and not lines[i].startswith('#SERVICE 1:64'):
                                if lines[i].startswith('#SERVICE 1:0') or lines[i].startswith('#DESCRIPTION'):
                                    filtered_lines.append(lines[i].strip())
                                    print(f"Adding service line: {lines[i].strip()}")
                                i += 1
                            continue  # Preskoči na sledeći marker

            i += 1

        # Snimi ažurirani sadržaj natrag u fajl
        if filtered_lines:
            with open(filename, 'w') as f:
                f.writelines([line + "\n" for line in filtered_lines])
            print(f"Filtered {filename} for satellites: {', '.join(selected_satellites)}")
        else:
            print(f"No lines matched the selected satellites for {filename}. Keeping original content.")
            return False

        return True

    def install(self):
        self.session.openWithCallback(
            self.install_confirmed,
            MessageBox,
            "Install selected settings?",
            MessageBox.TYPE_YESNO
        )

    def install_confirmed(self, result):
        if result:
            try:
                enigma2_dir = "/etc/enigma2"
                tuxbox_dir = "/etc/tuxbox"
                source_dir = "/tmp/CiefpSelectSatellite"

                # Proveri da li je direktorijum sa selektovanim fajlovima prazan
                if not os.path.exists(source_dir) or not os.listdir(source_dir):
                    self["status"].setText("Greška: Nema fajlova za instalaciju!")
                    return

                # 1. Prvo obradi bouquets.tv pre nego što ga kopiramo
                bouquets_tv_path = os.path.join(source_dir, "bouquets.tv")
                if os.path.exists(bouquets_tv_path):
                    self.process_and_copy_bouquets(bouquets_tv_path, source_dir, enigma2_dir)

                # 2. Kopiraj sve ostale zajedničke fajlove
                for f in os.listdir(source_dir):
                    src = os.path.join(source_dir, f)
                    if f == "satellites.xml":
                        shutil.copy(src, tuxbox_dir)
                    elif f == "bouquets.tv":
                        continue  # Već je obrađeno iznad
                    elif f.endswith(('.tv', '.radio', 'lamedb')):
                        shutil.copy(src, enigma2_dir)

                # 3. Kopiraj bukete za selektovane satelite
                for sat in self.selected_satellites:
                    bouquets = self.find_satellite_bouquet(sat)
                    if bouquets:
                        for bouquet_file in bouquets:
                            src = os.path.join(source_dir, bouquet_file)
                            if os.path.exists(src):
                                shutil.copy(src, enigma2_dir)
                            else:
                                print(f"[WARNING] Fajl {bouquet_file} ne postoji u {source_dir}")

                # 4. Reload Enigma2 nakon instalacije
                self.reload_settings()
                self["status"].setText("Instalacija uspešna!")
            except Exception as e:
                self["status"].setText(f"Greška: {str(e)}")

    def remove_existing_files(self, enigma2_dir, tuxbox_dir):
        # Brisanje fajlova pre kopiranja novih
        try:
            # Brisanje fajlova u enigma2_dir
            for f in os.listdir(enigma2_dir):
                if f.endswith(('.tv', '.radio')):
                    os.remove(os.path.join(enigma2_dir, f))
            
            # Brisanje lamedb fajla
            lamedb_path = os.path.join(enigma2_dir, 'lamedb')
            if os.path.exists(lamedb_path):
                os.remove(lamedb_path)
            
            # Brisanje fajla satellites.xml u tuxbox_dir
            satellites_xml_path = os.path.join(tuxbox_dir, 'satellites.xml')
            if os.path.exists(satellites_xml_path):
                os.remove(satellites_xml_path)
        
        except Exception as e:
            self["status"].setText(f"Error removing old files: {str(e)}")

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful! New settings are now active.  .::ciefpsettings::.", MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            self.session.open(MessageBox, "Reload failed: " + str(e), MessageBox.TYPE_ERROR, timeout=5)

    def up(self):
        self["left_list"].up()

    def down(self):
        self["left_list"].down()

    def switch_left(self):
        self["left_list"].selectionEnabled(True)

    def switch_right(self):
        self["left_list"].selectionEnabled(False)

    def exit(self):
        self.close()

def main(session, **kwargs):
    session.open(CiefpSelectSatellite)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="{0} v{1}".format(PLUGIN_NAME, PLUGIN_VERSION),
            description="Select satellite to install",
            icon=PLUGIN_ICON,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main
        )
    ]