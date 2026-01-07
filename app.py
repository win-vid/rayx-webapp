from flask import Flask, render_template, request, send_file
from H5Reader import H5Reader
import rayx, os, subprocess, traceback

# Runs RayX as a subprocess and returns the output as a downloadable .h5 file

app = Flask(__name__)

# Upload folder, creates one if it doesn't exist
UPLOAD_PATH = "./uploads/"
OUTPUT_PATH = "./output/"
os.makedirs(UPLOAD_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

output_file_name = ""

# Runs the app
@app.route("/",)
def index():
    return render_template("index.html")

# Handles the post on the server, sends the output .h5 file to the client
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
        
        # get_traced_beamline(rml_file)
        
        call_rayx(UPLOAD_PATH + rml_file.filename)

        remove_file(UPLOAD_PATH, rml_file)    
    
    return send_file(OUTPUT_PATH + output_file_name, as_attachment=True, download_name=output_file_name, mimetype="application/octet-stream")

@app.route("/display")
def display_h5():
    return render_template("displayH5.html")

# Handles the post on the server, displays the content of the .h5 file on the site
@app.route("/display/handle_post", methods=["POST"])
def display_handle_post():
    if request.method == "POST":
        try:
            rml_file = request.files["rmlFile"]
            output_file_name = os.path.splitext(rml_file.filename)[0] + ".h5"
            
            save_file(UPLOAD_PATH, rml_file)

        except Exception as e:
            traceback.print_exc()
            return render_template("displayH5.html", exception=e)
        
        call_rayx(UPLOAD_PATH + rml_file.filename)

        
        h5reader = H5Reader(OUTPUT_PATH + output_file_name)
        H5Content = h5reader.get_all_events_data()
        

        remove_file(UPLOAD_PATH, rml_file)
    return render_template("displayH5.html", H5FileName=output_file_name, H5Content=H5Content)

@app.route("/handle_get", methods=["GET"])
def handle_get():
    return render_template("received.html")

# Returns the traced beamline
def get_traced_beamline(rml_file):
    
    try:
        path = os.path.join(UPLOAD_PATH, rml_file.filename)

        beamLine = rayx.import_beamline(path)

        #element = beamLine.elements[0]
        #element.position.x = 10
        #print(element.position.x)

        rays = beamLine.trace()
    except:
        print("Beamline Failed to Trace")
    return rays

# Calls RayX as a subprocess and saves the output as a .h5 file in the output folder
def call_rayx(rml_path: str) -> None:

        rayx_cmd = ["./resources/rayx", "-i", rml_path]
        rayx_cmd += ['-o', OUTPUT_PATH + output_file_name]

        result = subprocess.run(rayx_cmd, capture_output=True, text=True)
        
        if result.stderr:
            print("STDERR:\n", result.stderr)

        if result.returncode != 0:
            print("Error occurred while running rayx.")
            raise Exception(result.stderr) 

# Saves a file on the server
def save_file(savePath, rml_file):
    path = os.path.join(savePath, rml_file.filename)
    rml_file.save(path)

# Removes a file from the server
def remove_file(savePath, rml_file):
    path = os.path.join(savePath, rml_file.filename)
    
    try:
        os.remove(path)
    except:
        print("File could not be found or removed.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)