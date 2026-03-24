import xml.etree.ElementTree as ET
from pathlib import Path

def set_value_in_rml(path, param_id, value):
    """
    Set the value of a parameter in an RML file.

    Args:
        path (Path): Path to the RML file.
        param_id (str): ID of the parameter to set.
        value (str): Value to set the parameter to.

    Raises:
        RuntimeError: If the parameter is not found.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # find parameter
    param = root.find(".//param[@id='" + param_id + "']")

    if param is None:
        raise RuntimeError(f"Parameter {param_id} not found")

    # set value
    param.text = str(value)

    # save
    tree.write(path, encoding="UTF-8", xml_declaration=True)
