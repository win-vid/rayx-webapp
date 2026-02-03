from flask import Flask, render_template, request, send_file
from H5Reader import H5Reader
from FileOperations import *
import rayx, os, subprocess, traceback, io, base64, time
from Histogram import Histogram

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
# Result of the traced beamline will be stored in a local dictionary
@app.route("/display/handle_post", methods=["POST"])
def display_handle_post():

    plot_data = []

    t = time.time()

    if request.method == "POST":
        
        rml_file = request.files["rmlFile"]

        output_file_name = rml_file.filename
            
        save_file(UPLOAD_PATH, rml_file)
        
        try:    
            beamline = get_beamline(rml_file)
            traced_beamline = beamline.trace()

            """
            # Creates a dictionary from the traced beamline that will be used to display the table
            traced_beamline_dictionary = {
                "Direction X": traced_beamline.direction_x,
                "Direction Y": traced_beamline.direction_y,
                "Direction Z": traced_beamline.direction_z,
                "Electric Field X": traced_beamline.electric_field_x,
                "Electric Field Y": traced_beamline.electric_field_y,
                "Electric Field Z": traced_beamline.electric_field_z,
                "Energy": traced_beamline.energy,
                "Event Type": traced_beamline.event_type,
                "Last Element ID": traced_beamline.last_element_id,
                "Order": traced_beamline.order,
                "Path Length": traced_beamline.path_length,
                "Position X": traced_beamline.position_x,
                "Position Y": traced_beamline.position_y,
                "Position Z": traced_beamline.position_z,
                "Ray ID": traced_beamline.ray_id,
                "Source ID": traced_beamline.source_id
            }

            keys = list(traced_beamline_dictionary.keys())
            n = len(traced_beamline_dictionary[keys[0]])
            
            # For '#'-row on the table
            rows = [
                {key: traced_beamline_dictionary[key][i] for key in keys}
                for i in range(n)
            ]
            """

            remove_file(UPLOAD_PATH, rml_file)

            last_element = traced_beamline.last_element_id
            pos_x = traced_beamline.position_x
            pos_z = traced_beamline.position_z

            # Creates an array that holds all of the beamlines elements as a 2D histogram

            # If the beamline has only one element, plot the whole beamline, prevents the histogram from being empty
            if len(beamline.elements) <= 1:
                plot = Histogram(pos_x, pos_z, xLabel="x / mm", yLabel="y / mm", title="")
                
                plot_data.append(plot.GetPlotDataBase64())
            else:
                index = 0
                for element in range(len(beamline.elements)):
                    mask = last_element == element
                    
                    plot = Histogram(pos_x[mask], pos_z[mask], xLabel="x / mm", yLabel="y / mm", title=(beamline.elements[element].name))
                    
                    plot_data.append(plot.GetPlotDataBase64())
                    index += 1
            
        except Exception as e:
            traceback.print_exc()
            return render_template("displayH5.html", exception=e)
      
    return render_template(
        "displayPy.html", 
        RMLFileName=output_file_name, 
        #traced_beamline_content=rows, 
        plot_data=plot_data,
        execution_time= round((time.time() - t) * 1e3, 3),
        )

# Returns a traced beamline using the RayX python package
def get_beamline(rml_file) -> rayx.Rays:

    # Get the absolute path
    base_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(base_dir, "uploads", rml_file.filename)

    # Import the beamline   
    beamLine = rayx.import_beamline(path)
    return beamLine

# ===============================================================================================================
# Due to the python bindings now working the following functions have become obsolete. Will be kept just in case.
# ===============================================================================================================

# Calls RayX as a subprocess and saves the output as a .h5 file in the output folder
# call_rayx is obsolete now because RayX is called with the python package
def call_rayx(rml_path: str) -> None:

        rayx_cmd = [RAYX_PATH, "-i", rml_path]
        rayx_cmd += ['-o', OUTPUT_PATH + output_file_name]

        result = subprocess.run(rayx_cmd, capture_output=True, text=True)
        
        if result.stderr:
            print("STDERR:\n", result.stderr)

        if result.returncode != 0:
            print("Error occurred while running rayx.")
            raise Exception(result.stderr) 

# Handles the post on the server, sends the output .h5 file to the client
# Originally used to display the data of the traced beamline on a table on the website
# obsolete
@app.route("/handle_post", methods=["POST"])
def handle_post():
    
    if request.method == "POST":
        try:
            rml_file = request.files["rmlFile"]
            output_file_name = os.path.splitext(rml_file.filename)[0] + ".h5"
            
            save_file(UPLOAD_PATH, rml_file)
        except Exception as e:
            print("File missing or could not be read", e)
            return render_template("index.html", exception=e)
        
        call_rayx(UPLOAD_PATH + rml_file.filename)

        remove_file(UPLOAD_PATH, rml_file)    
    
    return send_file(OUTPUT_PATH + output_file_name, as_attachment=True, download_name=output_file_name, mimetype="application/octet-stream")

# Renders the displayH5.html
# obsolete
@app.route("/display")
def display_h5():
    return render_template("displayH5.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)