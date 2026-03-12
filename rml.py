import xml.etree.ElementTree as ET
from pathlib import Path

def set_value_in_rml(path, param_id, value):
    tree = ET.parse(path)
    root = tree.getroot()

    # find parameter
    param = root.find(".//param[@id='" + param_id + "']")

    if param is None:
        raise RuntimeError(f"Parameter {param_id} not found")

    param.text = str(value)

    tree.write(path, encoding="UTF-8", xml_declaration=True)