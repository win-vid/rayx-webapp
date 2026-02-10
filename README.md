# RAYX Web Visualization App

A lightweight Flask-based web application for visualizing <a href="https://github.com/hz-b/rayx">RayX beamline simulations</a> .  
The app allows users to upload an `.rml` file, trace the beamline using the RayX Python bindings, and interactively inspect the resulting ray distributions as **2D histograms with per-element breakdowns**.

---

## Features

- Upload RayX `.rml` beamline definition files
- Trace beamlines using the **RayX Python package**
- Generate:
  - 2D histograms (X–Z)
  - Marginal 1D histograms for X and Z
  - indicators
- Render plots server-side using Matplotlib
- Return plots as Base64-encoded PNGs for easy web embedding

---

## Tech Stack

- **Python 3**
- **Flask** – web framework
- **RayX** – beamline tracing engine
- **Matplotlib** – plotting
- **NumPy** – numerical processing
- **Jinja2** – templating

---

## Getting started / Installation

### 1. Clone the repository
`git clone https://github.com/win-vid/rayx-webapp`
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
`uv run python ap.py`

You can then access the web app by entering the following address into your web-browser:
`http://localhost:5000`
