# region Imports
from flask import Flask, render_template, request, send_file, redirect, flash, url_for
from FileOperations import *
import rayx, os, subprocess, traceback, io, base64, time
from rml import *
from Histogram import Histogram
from Curve import Curve
from pathlib import Path
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
# endregion

app = Flask(__name__)

# Upload- & Output folder, creates one if it doesn't exist
UPLOAD_FOLDER = Path("./uploads/")
UPLOAD_FOLDER.mkdir(exist_ok=True)

output_file_name = ""

# Configurations
app.config["MAX_CONTENT_LENGTH"] = 10 * 1000 * 1000     # Limits rml_file size to 10 MB
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"rml"}

# Runs the app and starts the server
@app.route("/",)
def index():
    return render_template("reflectivity.html")     # TODO: Standard would be "display.py"

# Handles the post on the server, displays the content of the rml file on the site
@app.route("/display/handle_post", methods=["POST"])
def display_handle_post():

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

    # TODO: identical to the one in display_handle_post, only difference is the template that is rendered at the end
    # ==============================
    if request.method == "POST":
        
        # Check if the post request has the file part
        if "rmlFile" not in request.files:
            return redirect(request.url)

        rml_file = request.files["rmlFile"]

        # If the user does not select a file, the browser submits an
        # empty file without a filename. User is redirected to the home page.
        if rml_file.filename == '':
            return render_template("displayPy.html")
        
        # Check if file is allowed and save it, if it is
        if rml_file and allowed_file(rml_file.filename):
            filename = secure_filename(rml_file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)

            rml_file.save(path)

            generate_energy_rmls(path, UPLOAD_FOLDER)

        output_file_name = rml_file.filename

        # Dataframe to hold the electric field strength (eV) for each element, used to plot the reflectivity curve
        columns = ["eV", "reflectivity"]
        electric_fields = pd.DataFrame(columns=columns)
        
        path_to_energy_scan = os.path.join(UPLOAD_FOLDER, "energy_scan/")

        plot_data = ""

        # Loop through the generated rml files
        for rml in os.listdir(path_to_energy_scan):
            
            try:
                # Trace beamline    
                beamline = rayx.import_beamline(os.path.join(path_to_energy_scan, rml))
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
                # remove_file(path_to_energy_scan, rml)

                # =====================
                # identical until here

                # Plot the traced beamline
                last_element = df["last_element_id"]


                # TODO: Put Below in an for each loop for every rml. This needs to happen to each rml
                electric_field_source = 0
                electric_field_mirror = 0

                # Get the electric field strength for the source
                for source in range(len(beamline.sources)):
                    mask = last_element == source

                    electric_field_source = get_n_electric_field(df[mask])

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

            except Exception as e:
                traceback.print_exc()
                return render_template("displayPy.html", exception=e)
      
    electric_fields = electric_fields.sort_values("eV")  # ensure X axis is ordered
    
    # Plot the reflectivity curve
    plot_data = Curve(
        electric_fields["eV"], 
        electric_fields["reflectivity"], 
        xLabel="Energy (eV)", 
        yLabel="Reflectivity", 
        title="Reflectivity Curve"
    ).GetPlotHTML()

    return render_template(
        "reflectivity.html", 
        RMLFileName=get_cleaned_filename(output_file_name), 
        plot_data=plot_data,
    )

# Returns a traced beamline using the RayX python package
def get_beamline(rml_file) -> rayx.Rays:

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

# Checks if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Calculates the electric field strength from the electric field components
def get_n_electric_field(df):
    magnitudes = np.sqrt(
        df["electric_field_x"]**2 + 
        df["electric_field_y"]**2 + 
        df["electric_field_z"]**2
    )
    return magnitudes.sum()

# Runs the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)