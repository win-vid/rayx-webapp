from flask import Flask, render_template, request, send_file
import rayx, os

test = Flask(__name__)

@test.route("/")
def index():
    print("cwd:", os.getcwd())
    test_rayx()
    return render_template("test.html")

def test_rayx():
    

    bl = rayx.import_beamline("./resources/METRIX_U41_G1_H1_318eV_PS_MLearn_v114.rml")

    rays = bl.trace()

    print(rays)


if __name__ == "__main__":
    test.run(host="0.0.0.0", port=5000, debug=True)