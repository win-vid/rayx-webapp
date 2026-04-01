# region Imports
from flask import Flask, render_template, request, send_file, redirect, flash, url_for, session
from scripts.FileOperations import *
from dotenv import load_dotenv
import rayx, os, subprocess, traceback, io, base64, time, math
from scripts.Histogram import Histogram
from scripts.Curve import Curve
from pathlib import Path
from scripts.rml import *
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
# endregion

app = Flask(__name__)

# Upload- & Output folder, creates one if it doesn't exist
UPLOAD_FOLDER = Path("./uploads/")
UPLOAD_FOLDER.mkdir(exist_ok=True)

output_file_name = ""

# region Configurations
load_dotenv("config.env")                               # Load environment variables, if does not exist, create one
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")      # Secret Key is used to secure the session and temporarily store user form data
app.config["MAX_CONTENT_LENGTH"] = 10 * 1000 * 1000     # Limits rml_file size to 10 MB
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER             # Folder where rml files are stored during session
MATERIALS = {
    "H": 0.0000899, "He": 0.0001785,
    "Li": 0.534, "Be": 1.85, "B": 2.34, "C": 2.267, "N": 0.0012506, "O": 0.001429, "F": 0.001696, "Ne": 0.0009,
    "Na": 0.97, "Mg": 1.74, "Al": 2.70, "Si": 2.33, "P": 1.82, "S": 2.07, "Cl": 0.0032, "Ar": 0.00178,
    "K": 0.86, "Ca": 1.55, "Sc": 2.99, "Ti": 4.51, "V": 6.0, "Cr": 7.15, "Mn": 7.3, "Fe": 7.87, "Co": 8.86, "Ni": 8.90,
    "Cu": 8.96, "Zn": 7.14, "Ga": 5.91, "Ge": 5.32, "As": 5.78, "Se": 4.82, "Br": 3.12, "Kr": 0.0037,
    "Rb": 1.53, "Sr": 2.64, "Y": 4.47, "Zr": 6.52, "Nb": 8.57, "Mo": 10.2, "Tc": 11.0, "Ru": 12.1, "Rh": 12.4, "Pd": 12.0,
    "Ag": 10.49, "Cd": 8.65, "In": 7.31, "Sn": 7.26, "Sb": 6.68, "Te": 6.24, "I": 4.93, "Xe": 0.0059,
    "Cs": 1.93, "Ba": 3.59, "La": 6.15, "Ce": 6.77, "Pr": 6.77, "Nd": 7.01, "Pm": 7.26, "Sm": 7.52, "Eu": 5.24,
    "Gd": 7.90, "Tb": 8.23, "Dy": 8.55, "Ho": 8.80, "Er": 9.07, "Tm": 9.32, "Yb": 6.90, "Lu": 9.84,
    "Hf": 13.3, "Ta": 16.4, "W": 19.3, "Re": 20.8, "Os": 22.6, "Ir": 22.5, "Pt": 21.45, "Au": 19.32,
    "Hg": 13.55, "Tl": 11.85, "Pb": 11.34, "Bi": 9.78, "Po": 9.20, "At": 7.0, "Rn": 0.0097,
    "Fr": 1.87, "Ra": 5.5, "Ac": 10.07, "Th": 11.7, "Pa": 15.4, "U": 19.1
}

ALLOWED_EXTENSIONS = {"rml"}
# endregion

# Runs the app and starts the server
@app.route("/",)
def index():
    return render_template("displayPy.html")

@app.route("/reflectivity")
def reflectivity():
    """
    This function renders the web page for the "Reflectivity" tool.

    The "Reflectivity" tool is used to visualize the reflectivity of a material at a given angle and energy range.

    Returns:
        render_template: The rendered web page.
    """
    return render_template("reflectivity.html")

# region Standard Beamline Tracing
# Handles the post on the server, displays the content of the rml file on the site
@app.route("/display/handle_post", methods=["POST"])
def display_handle_post():
    """
    This function handles the post request from the displayPy.html page.
    
    It receives an rml file from the user, traces the beamline,
    and then plots the beamline distribution in a series of 2D histograms.
    
    Returns:
        render_template: The rendered web page.
    """
    
    plot_data = []

    t = time.time()

    if request.method == "POST":
        
        # Check if the post request has the file part
        if "rmlFile" not in request.files:
            return redirect(request.url)

        rml_file = request.files["rmlFile"]

        # If the user does not select a file, the browser submits an
        # empty file without a filename. User is redirected to the home page
        if rml_file.filename == '':
            return render_template("displayPy.html")
        
        # Check if file is allowed and save it, if it is
        if rml_file and allowed_file(rml_file.filename):
            filename = secure_filename(rml_file.filename)
            rml_file.filename = filename
            save_file(UPLOAD_FOLDER, rml_file)

        output_file_name = rml_file.filename
        
        try:
            # Trace beamline
            beamline = get_beamline(rml_file)
            traced_beamline = beamline.trace()

            # Create pandas dataframe
            columns = [
                "direction_x", "direction_y", "direction_z",
                "electric_field_x", "electric_field_y", "electric_field_z",
                "energy", "event_type",
                "last_element_id", "order", "path_length",
                "position_x", "position_y", "position_z",
                "ray_id", "source_id",
            ]

            df = pd.DataFrame({col: getattr(traced_beamline, col) for col in columns})

            # Remove file from server
            remove_file(UPLOAD_FOLDER, rml_file)

            # Plot the traced beamline
            last_element = df["last_element_id"]
            pos_x = df["position_x"]
            pos_y = df["position_y"]
            pos_z = df["position_z"]

            # Creates an array that holds all of the beamlines elements as a 2D histogram
            for source in range(len(beamline.sources)):
                mask = last_element == source
                plot = Histogram(pos_x[mask], pos_y[mask], xLabel="x / mm", yLabel="y / mm", title=(beamline.sources[source].name))
                
                plot_data.append(plot)

            # If the beamline has only one element, plot the whole beamline, prevents the histogram from being empty
            if len(beamline.elements) <= 1:
                plot = Histogram(pos_x, pos_z, xLabel="x / mm", yLabel="z / mm", title="")
                
                plot_data.append(plot)
            else:
                index = 1
                try:
                    for element in range(len(beamline.elements)):
                        mask = last_element == element + len(beamline.sources)

                        plot = Histogram(pos_x[mask], pos_z[mask], xLabel="x / mm", yLabel="z / mm", title=(beamline.elements[element].name))

                        plot_data.append(plot)
                except:
                    print("Index out of range" + str(index))
                    pass
        except Exception as e:
            traceback.print_exc()
            return render_template("displayPy.html", exception=e)
      
    return render_template(
        "displayPy.html", 
        RMLFileName=get_cleaned_filename(output_file_name), 
        plot_data=plot_data,
    )

# endregion

# region Reflectivity

# TODO: Refactor this function, it is almost identical to the one above, only difference is the template that is rendered at the end
@app.route("/reflectivity/handle_post", methods=["POST"])
def handle_post_reflectivity():
    """
    Receives one **rml file** with **two elements**: A point source that emits **x-amount of rays**, and a mirror.<br>
    The function takes the rml file, applies user settings and copies the file x-times so that the **Photon Energy (eV) ranges from 0 to 1000 eV**.<br>
    Then for each beamline, the function traces it and then calculates the **electric field** strength for the source and the mirror. 
    It calculates the reflectivity by **dividing the electric field strength of the mirror by that of the source** and plots them in a curve.<br> 
    The x-axis is the photon energy (eV) and the y-axis is the reflectivity.<br> 
    The curve is then plotted on the website. 
    """

    if request.method == "POST":

        # Create a list of all the beamlines
        beamlines = []

        #region POST Handling

        # Check if the post request has the file part
        if "rmlFile" not in request.files:
            return redirect(request.url)

        rml_file = request.files["rmlFile"]

        # If the user submits nothing, the server defaults to the last uploaded file, if one exists
        # If there is no last uploaded file, the user is redirected to the reflectivity page
        if rml_file.filename == '':
            try:
                rml_file = filename = session.get("last_rml_filename") 
                path = os.path.join(UPLOAD_FOLDER, filename)
            except:
                return render_template("reflectivity.html") 
        
        # Else if the user submits a file, check if file is allowed and save it, if it is
        elif rml_file and allowed_file(rml_file.filename):
            filename = secure_filename(rml_file.filename)
            session["last_rml_filename"] = filename
            path = os.path.join(UPLOAD_FOLDER, filename)
            rml_file.save(path)
        # endregion

        # region RML-File Handling

        # Change and store params depending on POST request
        angle = int(request.form["angle"])
        material = request.form.get("material", type=str)
        
        # Flag for illegal materials
        if material == "" or isMaterialAllowed(material) == False:
            return render_template("reflectivity.html")
        
        density = float(request.form["density"])

        # If density is -1, set it to the default density
        if density < 0:
            density = MATERIALS[material]
        
        roughness = int(request.form["roughness"])

        angle_rad = math.radians(angle)

        direction = {
            "x": math.cos(angle_rad),
            "y": 0.0,
            "z": math.sin(angle_rad),
        }

        linearPol_0 = float(request.form["linearPol_0"])
        linearPol_45 = float(request.form["linearPol_45"])
        circularPol = float(request.form["circularPol"])

        set_value_in_rml(path, "worldXdirection", direction)
        set_value_in_rml(path, "grazingIncAngle", angle)
        set_value_in_rml(path, "elementSubstrate", material)
        set_value_in_rml(path, "densitySubstrate", density)
        set_value_in_rml(path, "roughnessSubstrate", roughness)
        set_value_in_rml(path, "linearPol_0", linearPol_0)
        set_value_in_rml(path, "linearPol_45", linearPol_45)
        set_value_in_rml(path, "circularPol", circularPol)

        beamlines = generate_energy_beamlines(
            path, 
            min_e=int(request.form["min_e"]), 
            max_e=int(request.form["max_e"])
        )
        # endregion

        output_file_name = filename

        # Dataframe to hold the electric field strength (eV) for each element as well as the reflectivity used to plot the reflectivity curve
        columns = ["eV", "reflectivity"]
        electric_fields = pd.DataFrame(columns=columns)

        # Variable to hold the plot data, will be passed to the template
        plot_data = ""

        # region Beamline Tracing
        # Loop through the generated rml file
        for beamline in beamlines:
            
            try:
                # Trace beamline using RAYX depending on the index    
                # beamline = beamlines[beamlines.index(beamline)]
                traced_beamline = beamline.trace()

                # Create a pandas dataframe for the traced beamline
                columns = [
                    "direction_x", "direction_y", "direction_z",
                    "electric_field_x", "electric_field_y", "electric_field_z",
                    "energy", "event_type",
                    "last_element_id", "order", "path_length",
                    "position_x", "position_y", "position_z",
                    "ray_id", "source_id",
                ]

                df = pd.DataFrame({col: getattr(traced_beamline, col) for col in columns})

                last_element = df["last_element_id"]

                # region Reflectivity Calculations
                electric_field_source = 0
                electric_field_mirror = 0

                # Get the electric field strength for the source
                for source in range(len(beamline.sources)):
                    mask = last_element == source

                    electric_field_source = get_n_electric_field(df[mask])

                # TODO: Add a check to validate that the elements is a mirror
                print(f"Sources: {len(beamline.sources)}, Elements: {len(beamline.elements)}")
                for e in beamline.elements:
                    print(f"  - {e.name}")
                # If the beamline has only one element or more than two, redirect to avoid errors
                # ✅ Remove the >2 restriction, just ensure mirror exists
                if len(beamline.elements) < 1:
                    print("No elements in beamline")
                else:
                    mask = last_element == len(beamline.sources)  # first element after source = mirror
                    electric_field_mirror = get_n_electric_field(df[mask])
                    
                # Calculate the reflectivity by dividing the electric field strength of the mirror by that of the source
                reflectivity = np.abs(electric_field_mirror / electric_field_source)

                # Add the electric field strength and reflectivity to the dataframe
                electric_fields = pd.concat(
                    [
                        electric_fields,
                        pd.DataFrame([{
                            "eV": beamline.sources[0].energy,
                            "reflectivity": reflectivity
                        }])
                    ],
                    ignore_index=True
                )
                # endregion

                # region Reflectivity Debugging
                mask_source = last_element == 0
                mask_mirror = last_element == len(beamline.sources)

                print(f"eV={beamline.sources[0].energy:.1f} | "
                    f"source_rays={mask_source.sum()} | "
                    f"mirror_rays={mask_mirror.sum()} | "
                    f"ratio={mask_mirror.sum()/mask_source.sum():.3f} | "
                    f"reflectivity={reflectivity:.4f}")

                # endregion

            except Exception as e:
                traceback.print_exc()
                return render_template("displayPy.html", exception=e)
    
    electric_fields = electric_fields.sort_values("eV")
    # endregion

    # region Plotting & Cleanup
    try:
        # Construct the curve plot using the electric field strength and reflectivity data.
        plot_data = Curve(
            electric_fields["eV"],
            electric_fields["reflectivity"],
            xLabel="Photon Energy (eV)",
            yLabel="Reflectivity",
            title=f"Reflectivity Curve, {material}, Density = {density}, Angle = {angle}°"
        ).GetPlotHTML()
    except Exception as e:
        # If plotting fails, print the error and return an empty plot.
        traceback.print_exc()
        plot_data = ""
    finally:
        # Always clean up (delete constructed rml-files), even if plotting failed
        # TODO: Delete rml-file when connection gets terminated
        pass
    # endregion
    
    return render_template(
        "reflectivity.html", 
        RMLFileName=get_cleaned_filename(output_file_name), 
        plot_data=plot_data,
        min_e=request.form.get("min_e", 30),
        max_e=request.form.get("max_e", 100),
        angle=request.form.get("angle", 10),
        density=request.form.get("density", 1),
        roughness=request.form.get("roughness", 1),
        material=request.form.get("material", "Si"),
        linearPol_0=request.form.get("linearPol_0", 0),
        linearPol_45=request.form.get("linearPol_45", 0),
        circularPol=request.form.get("circularPol", 0)
    )

# endregion

def get_beamline(rml_file) -> rayx.Rays:
    """
    Takes an RML file and returns a traced beamline using the RayX python package.
    """
    try:
        # Get the absolute path
        base_dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(base_dir, "uploads", rml_file.filename)

        # Import the beamline   
        beamLine = rayx.import_beamline(path)
        return beamLine
    except Exception as e:
        traceback.print_exc()
        return render_template("displayPy.html", exception=e)

def allowed_file(filename):
    """
    Checks if the uploaded file is allowed based on its extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# region Math
# TODO: Check out what happens if return returns return magnitudes.sum() or return magnitudes.mean() or return np.sqrt((magnitudes**2).mean())
def get_n_electric_field(df):
    """
    Calculates the electric field strength from the electric field components in the dataframe. 
    It sums the magnitudes of the electric field components to get the total electric field strength.
    """

    if df.empty:
        return 0

    try:
        # Calculate the electric field strength by summing the magnitudes of the electric field components
        magnitudes = np.sqrt(
            np.abs(df["electric_field_x"])**2 + 
            np.abs(df["electric_field_y"])**2 + 
            np.abs(df["electric_field_z"])**2
        )
    except Exception as e:
        traceback.print_exc()
        return 0
    
    return magnitudes.mean() # Source: Claude, Formerly this was magnitudes.sum()

def generate_energy_beamlines(template_path, min_e=30, max_e=1000) -> list:
    """
    Generates diffrent beamlines for a range of photon energies based on a template RML file.
    Sets the energy of each source to the current energy.
    Returns:
        A list of beamline objects.
    """

    # Check if min_e and max_e are valid
    if min_e >= max_e or max_e <= min_e:
        print("Invalid energy range")
        return []

    template_path = template_path
    beamlines = []

    for energy in range(min_e, max_e + 1):
        bl = rayx.import_beamline(template_path)
        bl.sources[0].energy = energy
        beamlines.append(bl)

    return beamlines

# endregion

def isMaterialAllowed(material) -> bool:
    return material in MATERIALS

# Runs the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
