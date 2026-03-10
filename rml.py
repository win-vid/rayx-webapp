import xml.etree.ElementTree as ET
from pathlib import Path

def generate_energy_rmls(template_path, output_dir, min_e=30, max_e=1000):
    """Generates RML files for a range of photon energies based on a template RML file."""

    template_path = Path(template_path)
    output_dir = Path(output_dir) / "energy_scan"
    output_dir.mkdir(parents=True, exist_ok=True)

    for energy in range(min_e, max_e + 1):

        tree = ET.parse(template_path)
        root = tree.getroot()

        # find photonEnergy parameter
        photon = root.find(".//param[@id='photonEnergy']")

        if photon is None:
            raise RuntimeError("photonEnergy parameter not found")

        photon.text = str(energy)

        out = output_dir / f"energy_{energy:04d}.rml"
        tree.write(out, encoding="UTF-8", xml_declaration=True)