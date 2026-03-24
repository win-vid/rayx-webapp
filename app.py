# region Imports
from flask import Flask, render_template, request, send_file, redirect, flash, url_for, session
from FileOperations import *
from dotenv import load_dotenv
import rayx, os, subprocess, traceback, io, base64, time
from Histogram import Histogram
from Curve import Curve
from pathlib import Path
from rml import *
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
MATERIALS = [
    "Ac","Ag","Al","Ar","As","At","Au","B","Ba","Be","Bi","Br","C","Ca","Cd","Ce","Cl","Co","Cr","Cs","Cu","Dy","Er","Eu","F","Fe",
    "Fr","Ga","Gd","Ge","H","He","Hf","Hg","Ho","I","In","Ir","K","Kr","La","Li","Lu","Mg","Mn","Mo","N","Na","Nb","Nd","Ne","Ni",
    "O","Os","P","Pa","Pb","Pd","Pm","Po","Pr","Pt","Ra","Rb","Re","Rh","Rn","Ru","S","Sb","Sc","Se","Si","Sm","Sn","Sr","Ta","Tb",
    "Tc","Te","Th","Ti","Tl","Tm","U","V","W","Xe","Y","Yb","Zn","Zr"
]
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
    The function takes the rml file and copies it x-times so that the **Photon Energy (eV) ranges from 0 to 1000 eV**.<br>
    Then for each beamline, the function traces it and then calculates the **electric field** strength for the source and the mirror. 
    It calculates the reflectivity by **dividing the electric field strength of the mirror by that of the source** and plots 
    them in a curve.<br> 
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
        
        # Flag for unallowed materials
        if material == "" or isMaterialAllowed(material) == False:
            return render_template("reflectivity.html")
        
        density = int(request.form["density"])
        roughness = int(request.form["roughness"])

        set_value_in_rml(path, "grazingIncAngle", angle)
        set_value_in_rml(path, "elementSubstrate", material)
        set_value_in_rml(path, "densitySubstrate", density)
        set_value_in_rml(path, "roughnessSubstrate", roughness)

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
                beamline = beamlines[beamlines.index(beamline)]
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

                # If the beamline has only one element or more than two, redirect to avoid errors
                if len(beamline.elements) <= 1 or len(beamline.elements) > 2:
                    print("Beamline has only one element or more than two, redirecting to home page.")
                    redirect(url_for("index"))
                else:
                    index = 1
                    try:
                        # Get the electric field strength for the mirror
                        for element in range(len(beamline.elements)):
                            mask = last_element == element + len(beamline.sources)

                            electric_field_mirror = get_n_electric_field(df[mask])
                    except:
                        print("Index out of range" + str(index))
                        pass
                    
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
        material=request.form.get("material", "Si")
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
    
    return magnitudes.sum() # Source: Claude, Formerly this was magnitudes.sum()

def generate_energy_beamlines(template_path, min_e=30, max_e=1000) -> list:
    """Generates diffrent beamlines for a range of photon energies based on a template RML file."""

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