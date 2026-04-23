# RAYX WebApp

<img width="800" height="450" alt="rayx-webapp" src="https://github.com/user-attachments/assets/39e6d50b-7e4a-4ae6-9eed-ecb1b76cf238" />


A lightweight Flask-based web application for visualizing <a href="https://github.com/hz-b/rayx">RAYX beamline simulations</a> .  
The app allows users to upload an `.rml` file, trace the beamline using the RAYX Python bindings, and **interactively** inspect the resulting ray distributions as **2D histograms with per-element breakdowns**.

## Features

- Upload RAYX `.rml` beamline definition files
- Trace beamlines using the **RAYX Python package**
- Generate:
  - 2D histograms
  - Marginal 1D histograms
  - indicators (Full Width Half Maximum, Center of Mass)
- Render plots server-side using plotly
- Return plots as Base64-encoded string for easy web embedding

## Tech Stack

- **Python 3**
- **Flask** – web framework
- **RAYX** – beamline tracing engine
- **Plotly** – plotting
- **NumPy** – numerical processing
- **Jinja2** – templating

## Getting started / Installation & Setup

### 1. Clone the repository
`git clone https://github.com/win-vid/rayx-webapp` <br>
`cd rayx-webapp`

Use the main branch for the most stable version.

### 2. Installing dependencies using uv
From the project root run: <br>
`uv venv` <br>
`uv sync`

This will:
* Create a virtual environment
* Install all dependencies defined by the project

### 3. Create a 'config.env' file
The server uses sessions to temporarily store the users submitted rml-files. Therefore, you need to create a `config.env` file in the **root directory** containing the following content:

``SECRET_KEY=some_secret_key``

### 4. Running a local server

Run the following to make the web app run locally:
`uv run python app.py`

You can then access the web app by entering the following address into your web-browser: <br>
`http://localhost:5000`

## Tracing beamlines
You can find an example Metrix beamline under 
`example_beamline/METRIX_U41_G1_H1_318eV_PS_MLearn_v114.rml`.  
The application also works with any other beamline encoded in the **RAYX `.rml` format**.
Select the beamline and click on "send". 
After a short amount of time the server will return the plots of the elements.

## Plot Controls
The plots are **fully interactive**.<br>
**Click and drag** to pan the view.<br> 
Use the **mouse wheel** to zoom in and out centered on the cursor position.<br> 
**Double-click** anywhere inside the plot to reset the view.<br> 
The marginal histograms and main 2D histogram stay synchronized while zooming and panning, allowing for intuitive exploration of the beam distribution.<br>
Additionally, plotly allows you to easily download the plot.

## Docker
### Creating a Docker Container
Requirements
* either <a href="https://www.docker.com/">**Docker**</a> or <a href="https://podman.io/">**Podman**</a>
* for better management also install **Docker Desktop** or **Podman Desktop**

If you want to make changes to the workflow you have to edit the `Dockerfile` config in the root directory. 

To build a container run the following (this also works with Docker):

``podman build . -t rayx-web-app``

Afterwards run the following to run the container on port 5000:

``podman run -it rayx-web-app:latest -p 5000:5000``

You can change the ip-address or the port-number the web-app will run on inside the `Dockerfile`. 

### Saving and running Docker-Files / Images

To distribute the WebApp to another user or to test it on a different machine you need to build an image. To build one simply type:

```podman save -o rayx-web-app.tar rayx-web-app```

Next you can load the image on a different machine that has podman/docker installed:

```podman load -i rayx-web-app.tar```

Then run it with:

```podman run -it rayx-web-app:latest -p 5000:5000```