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

def lookup_vendor(mac, oui_dict):
    oui = ':'.join(mac.lower().split(":")[:3])
    return oui_dict.get(oui, "Unbekannt")