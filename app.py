from flask import Flask, render_template, request, send_file
from H5Reader import H5Reader
from FileOperations import *
import rayx, os, subprocess, traceback, io, base64, time
from Histogram import Histogram
import pandas as pd
import numpy as np

# Runs RayX as a subprocess and returns the output as a downloadable .h5 file
# TODO: Rework the error handling logic
# TODO: Rework .h5 and rayx-package logic. Maybe keep both as separate functions

app = Flask(__name__)

# Upload- & Output folder, creates one if it doesn't exist
UPLOAD_PATH = "./uploads/"
OUTPUT_PATH = "./output/"
RAYX_PATH = "./rayx/rayx"
os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

output_file_name = ""

# Runs the app and starts the server
@app.route("/",)
def index():
    return render_template("displayPy.html")

# Handles the post on the server, displays the content of the rml file on the site
@app.route("/display/handle_post", methods=["POST"])
def display_handle_post():

    plot_data = []

    t = time.time()

    if request.method == "POST":
        
        rml_file = request.files["rmlFile"]

        output_file_name = rml_file.filename
            
        save_file(UPLOAD_PATH, rml_file)
        
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
            remove_file(UPLOAD_PATH, rml_file)

            # Plot the traced beamline
            last_element = traced_beamline.last_element_id
            pos_x = traced_beamline.position_x
            pos_y = traced_beamline.position_y
            pos_z = traced_beamline.position_z

            # Creates an array that holds all of the beamlines elements as a 2D histogram
            print(beamline.sources)
            for source in range(len(beamline.sources)):
                mask = last_element == source
                plot = Histogram(pos_x[mask], pos_y[mask], xLabel="x / mm", yLabel="y / mm", title=(beamline.sources[source].name))
                plot_data.append(plot.GetPlotDataBase64())

            # If the beamline has only one element, plot the whole beamline, prevents the histogram from being empty
            if len(beamline.elements) <= 1:
                plot = Histogram(pos_x, pos_z, xLabel="x / mm", yLabel="z / mm", title="")
                
                plot_data.append(plot.GetPlotDataBase64())
            else:
                index = 1
                try:
                    for element in range(len(beamline.elements)):
                        mask = last_element == element + len(beamline.sources)

                        plot = Histogram(pos_x[mask], pos_z[mask], xLabel="x / mm", yLabel="z / mm", title=(beamline.elements[element].name))

                        plot_data.append(plot.GetPlotDataBase64())
                except:
                    print("Index out of range" + str(index))
                    pass
        except Exception as e:
            traceback.print_exc()
            return render_template("displayH5.html", exception=e)
      
    return render_template(
        "displayPy.html", 
        RMLFileName=output_file_name, 
        #traced_beamline_content=rows, 
        plot_data=plot_data,
        )

# Returns a traced beamline using the RayX python package
def get_beamline(rml_file) -> rayx.Rays:

    # Get the absolute path
    base_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(base_dir, "uploads", rml_file.filename)

    # Import the beamline   
    beamLine = rayx.import_beamline(path)
    return beamLine

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)