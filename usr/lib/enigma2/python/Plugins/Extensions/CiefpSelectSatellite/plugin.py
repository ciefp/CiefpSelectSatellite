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

PLUGIN_VERSION = "1.9"
PLUGIN_ICON = "plugin.png"
PLUGIN_NAME = "CiefpSelectSatellite"
PLUGIN_DESCRIPTION = "Satellite Selection Plugin"
TMP_DOWNLOAD = "/tmp/ciefp-E2-75E-34W"
TMP_SELECTED = "/tmp/CiefpSelectSatellite"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]

UPDATE_COMMAND = "wget -q --no-check-certificate https://raw.githubusercontent.com/ciefp/CiefpSelectSatellite/main/installer.sh -O - | /bin/sh"

class CiefpSelectSatellite(Screen):
    """Satellite Selector - FHD Version (1920x1080)"""
    
    skin = """
        <screen position="center,center" size="1920,1080"  backgroundColor="#011a2e">
            <!-- Naslov -->
            <widget name="title" position="0,20" size="1920,50" font="Bold;40" halign="center" title="..:: Ciefp Satellite Selector ::.." backgroundColor="#012e01" foregroundColor="#FFFFFF" zPosition="1" />
            
            <!-- Pozadinska slika -->
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSelectSatellite/background.png" position="1500,90" size="400,850" zPosition="0" />
            
            <!-- Lijeva lista - sateliti -->
            <widget name="left_list" position="50,90" size="750,850" scrollbarMode="showOnDemand" itemHeight="35" font="Regular;28" backgroundColor="#011a2e" foregroundColor="#FFFFFF" zPosition="1" />
            
            <!-- Desna lista - odabrani sateliti -->
            <widget name="right_list" position="820,90" size="650,850" scrollbarMode="showOnDemand" itemHeight="35" font="Regular;28" backgroundColor="#011a2e" foregroundColor="#00FF00" zPosition="1" />
            
            <!-- Status bar -->
            <widget name="status" position="50,960" size="1820,50" font="Regular;26" halign="center" valign="center" foregroundColor="#00FF00" backgroundColor="#011a2e" transparent="1" zPosition="1" />
            
            <!-- Informacije o verziji -->
            <widget name="version_info" position="1000,1020" size="900,30" font="Regular;24" halign="center" foregroundColor="#00FF00" backgroundColor="#011a2e" zPosition="1" />
            
            <!-- Donje dugmad -->
            <widget name="red_button" position="50,1010" size="200,45" font="Bold;30" halign="center" backgroundColor="#9F1313" foregroundColor="#FFFFFF" zPosition="1" />
            <widget name="green_button" position="270,1010" size="200,45" font="Bold;30" halign="center" backgroundColor="#1F771F" foregroundColor="#FFFFFF" zPosition="1" />
            <widget name="yellow_button" position="490,1010" size="200,45" font="Bold;30" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" zPosition="1" />
            <widget name="key_blue" position="710,1010" size="200,45" font="Bold;30" halign="center" backgroundColor="#13389F" foregroundColor="#FFFFFF" zPosition="1" />
        </screen>
    """.format(version=PLUGIN_VERSION)
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.selected_satellites = []
        self.bouquet_mapping = self.create_bouquet_mapping()
        
        # UI Components
        self["title"] = Label("..:: Ciefp Satellite Selector ::..")
        self["left_list"] = MenuList([])
        self["right_list"] = MenuList([])
        self["status"] = Label("Initializing...")
        self["version_info"] = Label(f"Version {PLUGIN_VERSION} - Loading...")
        self["red_button"] = Label("Exit")
        self["green_button"] = Label("Copy")
        self["yellow_button"] = Label("Install")
        self["key_blue"] = Label("Update")
        
        # Provjera pozadinske slike (samo debug)
        img_path = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSelectSatellite/background.png"
        if os.path.exists(img_path):
            print(f"[DEBUG] Background image found at: {img_path}")
        else:
            print(f"[DEBUG] Background image NOT found at: {img_path}")
        
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
            self["version_info"].setText(f"Version {PLUGIN_VERSION} - Update successful!")
        else:
            self["status"].setText("An error occurred while updating.")
            self["version_info"].setText(f"Version {PLUGIN_VERSION} - Update failed!")

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
            filtered_satellites = []
            for sat in satellites:
                for key in self.bouquet_mapping.keys():
                    if key in sat:
                        filtered_satellites.append(sat)
                        break
            self["left_list"].setList(filtered_satellites)
            self["status"].setText("Satellites loaded successfully.")
            self["version_info"].setText(f"Version {PLUGIN_VERSION} - {len(filtered_satellites)} satellites found")
        except Exception as e:
            self["status"].setText(f"Error parsing XML: {str(e)}")

    def download_settings(self):
        self["status"].setText("Fetching file list from GitHub...")
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            files = response.json()
            zip_url = None
            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    zip_url = file["download_url"]
                    break
            if not zip_url:
                raise Exception("No matching ZIP file found on GitHub.")
            
            self["status"].setText("Downloading settings from GitHub...")
            zip_path = os.path.join("/tmp", "latest.zip")
            zip_response = requests.get(zip_url)
            with open(zip_path, 'wb') as f:
                f.write(zip_response.content)
            
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
                    self["version_info"].setText(f"Plugin Version {PLUGIN_VERSION} - Settings Version {version_with_date}")
                    return

            self["version_info"].setText(f"Version {PLUGIN_VERSION} - Date not available")
        except Exception as e:
            self["version_info"].setText(f"Version {PLUGIN_VERSION} - Error fetching date")

    def select_item(self):
        selected = self["left_list"].getCurrent()
        if selected:
            numeric_selected = re.findall(r'\d+\.\d+[EW]', selected)
            if numeric_selected:
                numeric_selected = numeric_selected[0]
                if numeric_selected in [re.findall(r'\d+\.\d+[EW]', sat)[0] for sat in self.selected_satellites if
                                        re.findall(r'\d+\.\d+[EW]', sat)]:
                    self.selected_satellites.remove(selected)
                else:
                    self.selected_satellites.append(selected)
            else:
                if selected in self.selected_satellites:
                    self.selected_satellites.remove(selected)
                else:
                    self.selected_satellites.append(selected)
            self["right_list"].setList(self.selected_satellites)
            self["status"].setText(f"Selected {len(self.selected_satellites)} satellites")

    def copy_files(self):
        try:
            if not os.path.exists(TMP_SELECTED):
                os.makedirs(TMP_SELECTED)

            common_files = [
                'satellites.xml', 'lamedb', 'bouquets.tv',
                'userbouquet.buket_exyu.tv', 'userbouquet.buket_pinktv.tv',
                'userbouquet.buket_maxtv.tv', 'userbouquet.buket_sport.tv',
                'userbouquet.buket_kids.tv', 'userbouquet.buket_docu.tv',
                'userbouquet.buket_movie.tv', 'userbouquet.buket_music.tv',
                'userbouquet.buket_uhd.tv', 'userbouquet.buket_adult.tv',
                'userbouquet.buket_multistream.tv', 'userbouquet.buket_emu.tv',
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
                'userbouquet.link_0_marker.tv', 'userbouquet.link_5.tv',
                'userbouquet.link_3.tv', 'userbouquet.LastScanned.tv',
                'userbouquet.favourites.tv', 'bouquets.radio',
                'userbouquet.dbe00.radio', 'userbouquet.ciefpsettings_exyu.radio',
                'userbouquet.ciefpsettings_slovakia.radio',
                'userbouquet.ciefpsettings_czech.radio',
                'userbouquet.ciefpsettings_germany.radio',
                'userbouquet.ciefpsettings_romania.radio',
                'userbouquet.favourites.radio'
            ]

            for f in common_files:
                src = os.path.join(TMP_DOWNLOAD, f)
                if os.path.exists(src):
                    shutil.copy(src, TMP_SELECTED)

            for sat in self.selected_satellites:
                bouquets = self.find_satellite_bouquet(sat)
                if bouquets:
                    for bouquet_file in bouquets:
                        src = os.path.join(TMP_DOWNLOAD, bouquet_file)
                        if os.path.exists(src):
                            shutil.copy(src, TMP_SELECTED)

            theme_bouquets = [
                'userbouquet.buket_exyu.tv', 'userbouquet.buket_sport.tv',
                'userbouquet.buket_kids.tv', 'userbouquet.buket_docu.tv',
                'userbouquet.buket_movie.tv', 'userbouquet.buket_music.tv',
                'userbouquet.buket_uhd.tv', 'userbouquet.buket_adult.tv',
                'userbouquet.buket_multistream.tv', 'userbouquet.buket_emu.tv'
            ]
            for theme_bouquet in theme_bouquets:
                src = os.path.join(TMP_DOWNLOAD, theme_bouquet)
                if os.path.exists(src):
                    numeric_selected_satellites = [re.findall(r'\d+\.\d+[EW]', sat)[0] for sat in
                                                   self.selected_satellites if re.findall(r'\d+\.\d+[EW]', sat)]
                    if not self.filter_channels_by_satellite(os.path.join(TMP_SELECTED, theme_bouquet),
                                                             numeric_selected_satellites):
                        print(f"Failed to filter {theme_bouquet}. Keeping original content.")

            self["status"].setText("Files copied successfully!")
            self["version_info"].setText(f"Version {PLUGIN_VERSION} - {len(self.selected_satellites)} satellites copied")
        except Exception as e:
            self["status"].setText(f"Copy error: {str(e)}")

    def parse_bouquets_file(self, bouquets_path):
        bouquets = []
        try:
            with open(bouquets_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#NAME"):
                        bouquets.append((line + "\n", None))
                    elif "FROM BOUQUET" in line:
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if start != -1 and end != -1:
                            bouquet_file = line[start:end]
                            bouquets.append((line + "\n", bouquet_file))
        except Exception as e:
            print(f"Greška pri čitanju bouquets.tv: {e}")
        return bouquets

    def remove_missing_bouquets(self, bouquets_path, bouquets, check_path):
        try:
            valid_lines = []
            for line, bouquet_file in bouquets:
                if bouquet_file is None:
                    valid_lines.append(line)
                    continue
                full_path = os.path.join(check_path, bouquet_file)
                if os.path.isfile(full_path):
                    valid_lines.append(line)
            with open(bouquets_path, 'w') as file:
                file.writelines(valid_lines)
        except Exception as e:
            self["status"].setText(f"Greška prilikom ažuriranja bouquets.tv: {str(e)}")

    def process_and_copy_bouquets(self, bouquets_file_path, source_dir, enigma2_dir):
        try:
            bouquets = self.parse_bouquets_file(bouquets_file_path)
            if not bouquets:
                self["status"].setText("Nema validnih buketa!")
                return
            self.remove_missing_bouquets(bouquets_file_path, bouquets, source_dir)
            shutil.copy(bouquets_file_path, enigma2_dir)
        except Exception as e:
            self["status"].setText(f"Greška: {str(e)}")

    def filter_channels_by_satellite(self, filename, selected_satellites):
        if not os.path.exists(filename):
            print(f"File {filename} does not exist.")
            return False

        with open(filename, 'r') as f:
            lines = f.readlines()

        filtered_lines = []
        keep_lines = False
        SAT_MARKER_REGEX = r'#SERVICE \d+:\d+:[\w\d]+:.*::\| (.+?) \|::'
        NUMERIC_SAT_REGEX = r'(\d+\.\d+[EW])'

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('#NAME'):
                filtered_lines.append(line)
                i += 1
                continue

            if line.startswith('#SERVICE 1:64'):
                match = re.search(SAT_MARKER_REGEX, line)
                if match:
                    satellite_name = match.group(1).strip()
                    numeric_match = re.search(NUMERIC_SAT_REGEX, satellite_name)
                    if numeric_match:
                        numeric_satellite = numeric_match.group(1)
                        keep_lines = any(sat in numeric_satellite for sat in selected_satellites)
                        if keep_lines:
                            filtered_lines.append(line)
                            i += 1
                            if i < len(lines) and lines[i].startswith('#DESCRIPTION'):
                                filtered_lines.append(lines[i].strip())
                                i += 1
                            while i < len(lines) and not lines[i].startswith('#SERVICE 1:64'):
                                if lines[i].startswith('#SERVICE 1:0') or lines[i].startswith('#DESCRIPTION'):
                                    filtered_lines.append(lines[i].strip())
                                i += 1
                            continue
            i += 1

        if filtered_lines:
            with open(filename, 'w') as f:
                f.writelines([line + "\n" for line in filtered_lines])
            return True
        return False

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

                if not os.path.exists(source_dir) or not os.listdir(source_dir):
                    self["status"].setText("Greška: Nema fajlova za instalaciju!")
                    return

                bouquets_tv_path = os.path.join(source_dir, "bouquets.tv")
                if os.path.exists(bouquets_tv_path):
                    self.process_and_copy_bouquets(bouquets_tv_path, source_dir, enigma2_dir)

                for f in os.listdir(source_dir):
                    src = os.path.join(source_dir, f)
                    if f == "satellites.xml":
                        shutil.copy(src, tuxbox_dir)
                    elif f == "bouquets.tv":
                        continue
                    elif f.endswith(('.tv', '.radio', 'lamedb')):
                        shutil.copy(src, enigma2_dir)

                for sat in self.selected_satellites:
                    bouquets = self.find_satellite_bouquet(sat)
                    if bouquets:
                        for bouquet_file in bouquets:
                            src = os.path.join(source_dir, bouquet_file)
                            if os.path.exists(src):
                                shutil.copy(src, enigma2_dir)

                self.reload_settings()
                self["status"].setText("Instalacija uspešna!")
                self["version_info"].setText(f"Version {PLUGIN_VERSION} - Installation complete!")
            except Exception as e:
                self["status"].setText(f"Greška: {str(e)}")

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(MessageBox, "Reload successful! New settings are now active.\n.::ciefpsettings::.", MessageBox.TYPE_INFO, timeout=5)
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