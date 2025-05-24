# webapp/bledata/utils.py
# Utility function für mögliche Auswertung der MAC-Adressen und der Herstellerinformationen
def load_oui_database(file_path="static/oui.txt"):
    oui_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            if "(hex)" in line:
                parts = line.split("(hex)")
                oui = parts[0].strip().replace("-", ":").lower()
                vendor = parts[1].strip()
                oui_dict[oui] = vendor
    return oui_dict

# Utility function um den Hersteller anhand der MAC-Adresse zu ermitteln
def lookup_vendor(mac, oui_dict):
    oui = ':'.join(mac.lower().split(":")[:3])
    return oui_dict.get(oui, "Unbekannt")