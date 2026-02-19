# RAYX Web App

A lightweight Flask-based web application for visualizing <a href="https://github.com/hz-b/rayx">RayX beamline simulations</a> .  
The app allows users to upload an `.rml` file, trace the beamline using the RayX Python bindings, and **interactively** inspect the resulting ray distributions as **2D histograms with per-element breakdowns**.

## Features

- Upload RayX `.rml` beamline definition files
- Trace beamlines using the **RayX Python package**
- Generate:
  - 2D histograms
  - Marginal 1D histograms
  - indicators (Full Width Half Maximum, Center of Mass)
- Render plots server-side using plotly
- Return plots as Base64-encoded string for easy web embedding

## Tech Stack

- **Python 3**
- **Flask** – web framework
- **RayX** – beamline tracing engine
- **Plotly** – plotting
- **NumPy** – numerical processing
- **Jinja2** – templating

## Getting started / Installation

### 1. Clone the repository
`git clone https://github.com/win-vid/rayx-webapp` <br>
`cd rayx-webapp`

### 2. Installing dependencies using uv
From the project root run: <br>
`uv venv` <br>
`uv sync`

This will:
* Create a virtual environment
* Install all dependencies defined by the project

### 3. Running a local server

Run the following to make the web app run locally:
`uv run python app.py`

You can then access the web app by entering the following address into your web-browser:
`http://localhost:5000`

## Tracing beamlines
You can find an example Metrix beamline under 
`example_beamline/METRIX_U41_G1_H1_318eV_PS_MLearn_v114.rml`.  
The application also works with any other beamline encoded in the **RayX `.rml` format**.
Select the beamline and click on "send". 
After a short amount of time the server will return the plots of the elements.
