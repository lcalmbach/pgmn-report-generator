# PGMN-report-generator
## Introduction
Generates water level reports for the Ontario Provincial Monitoring Network (PGMN). The app currently includes three options:
- Info: displays general information on the app.
- Metadata: displays the following tables in the browser:
    - station information
    - statistics on water levels per station (min, max, mean and std for waterlevels)
    - statistics on precipitation per station (min, max, mean and std for daily precipitation)
- Explore waterlevels: In this option, plots showing the water level for the selected years and wells are displayed. If precipitation data is available, it will also be shown on the plot. Years can be shown as separate plots. 
- Generate pdf reports: Generates a pdf report page for every selected well and year. This option does not work properly on the public heroku site, unfortunately there is a blank page after every report page. This will be fixed in the next version. however, if you install the app on a windows machine and run the application locally, the report is generated correctly.

## Components
The following main components are used in this application:
- webinterface: [streamlit](https://streamlit.io/)
- Plotting: [Altair](https://altair-viz.github.io/)
- pdf-reports: [pdfkit](https://pypi.org/project/pdfkit/), [Jinja2](https://pypi.org/project/Jinja2/), [wkhtmltopdf](https://wkhtmltopdf.org/)
## Data
The original waterlevels, precipitation and station information data can be downloaded from the [Ontario Data Catalogue](https://data.ontario.ca/dataset/provincial-groundwater-monitoring-network). The data used in the app is filtered and reduces hourly measurements to daily averages for water levels and daily sums for precipitation data. Also, the orginal dataset stores the data in one scv file per station. To speed up data read operations, the data has been combined in a single file for this app. 

## Installation  
To install the app locally on your workstation, a python version < 3.9 and > 3.6 must be installed on your machine. You also need git installed on your machine. We recommend the following installation procedure:
```
> cd <install_folder>
> git clone https://github.com/lcalmbach/pgmn-report-generator.git
> cd pgmn-report-generator
> python -m venv env
> env\scripts\activate
> pip install -r requirements.txt
```

to run the application, run the following command from the `pgmn-report-generator` folder   
```
> streamlit run app.py
```

The application will open in the browser on port 8501, you may also type the url `localhost:8501` into your browser address-bar. 
