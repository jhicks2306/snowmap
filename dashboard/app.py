import ast
from pathlib import Path
import pandas as pd
from shinywidgets import output_widget, register_widget
import folium

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

here = Path(__file__).parent

# Read data and set default values for filters.
df = pd.read_csv("ski-resorts.csv")
regions = {'Østlandet': 'East',
        'Nord-Norge': 'North',
        'Nord-Vestlandet': 'North-west',
        'Midt-Norge':'Midlands',
        'Sørlandet': 'South',
        'Sør-Vestlandet': 'South-west'}
initial_selections = ['Østlandet', 'Sørlandet', 'Nord-Norge', 'Nord-Vestlandet', 'Midt-Norge', 'Sør-Vestlandet']
weather = sorted(df['Weekend Forecast'].unique().tolist())


# Define frontend components for the app.
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.tags.h4("About"),
        ui.tags.p(
        """
        This app helps you find a Norwegion ski resort
        to visit. Use the filters below to narrow your search
        and select the pins for more resort information.
        """,
        style="""
        text-align: left;
        word-break:break-word;
        hyphens: auto;
        """,
        ),
        ui.tags.hr(),
        ui.input_slider(
            'top_snow',
            'Snow on top (cm):',
            0,
            200,
            50,
        ),
        ui.input_checkbox_group(  
            "region_checkboxes",  
            "Regions:",  
            choices=regions,
            selected=initial_selections,  
        ),
        ui.input_checkbox_group(  
            "weather_checkboxes",  
            "Weekend forecast:",  
            choices=weather,
            selected=weather,  
        ), 
        ui.input_switch(
            'toggle',
            'Hide closed resorts',
            value=False),
    ),
    ui.row(
        ui.card(
            ui.card_header("Norwegian Ski Resorts"),
            ui.output_ui('folium_map'),
            height='95vh',   
        ),
    ),
    ui.row(
        ui.tags.p('Data for this dashboard is provided by the Fnugg API.', display='inline'),
        ui.tags.a(ui.output_image('fnugg_logo'), href='https://api.fnugg.no/'         
        ),
    ),
)

def server(input: Inputs, output: Outputs, session: Session):
    
    # Apply filters to DataFrame
    @reactive.Calc
    def filtered_df():
        regions_selected = input.region_checkboxes()
        forecasts_selected = input.weather_checkboxes()
        filt_df = df
        filt_df = filt_df.loc[filt_df['Snow on Top (cm)'] > input.top_snow()]
        filt_df = filt_df.loc[filt_df['Region'].apply(filter_regions, args=(regions_selected,))]
        filt_df = filt_df.loc[filt_df['Weekend Forecast'].apply(filter_weather, args=(forecasts_selected,))]
        if input.toggle():
            filt_df = filt_df.loc[filt_df['Resort Open'] == True]
        return filt_df

    # Render map.
    @render.ui
    def folium_map():
        display_df = filtered_df()
        return build_resort_map(display_df)
    
    @render.image
    def fnugg_logo():
        img = {"src": here / "Fnugg_logo.svg", "width": "100px"}
        return img

def filter_weather(forecast, selections):
    intersection = set([forecast]) & set(selections)
    return len(intersection) > 0

def filter_regions(regions, selections):
    regions_list = ast.literal_eval(regions) # regions are initally in string format.
    intersection = set(regions_list) & set(selections)
    return len(intersection) > 0

def check_nan(item):
    if pd.isna(item):
        return "n/a"
    else:
        return int(item)


def build_resort_map(df):
    """
    Builds map of Ski resorts with markers.
    """
    
    # Create map and center.
    avg_lat = df['Latitude'].mean()
    avg_lon = df['Longitude'].mean()
    map = folium.Map(location=[avg_lat, avg_lon], zoom_start=6, height='100%')

    for index, row in df.iterrows():

        # Show green if resort is open.
        if row['Resort Open'] == True:
            color = 'green'
        else:
            color = 'red'

        # Collate information for marker.
        name = row['Name']
        top_snow = check_nan(row['Snow on Top (cm)'])
        bottom_snow = check_nan(row['Snow at Bottom (cm)'])
        open_lifts = row['Lifts Open']
        total_lifts = row['Total Lifts']
        open_slopes = row['Slopes Open']
        total_slopes = row['Total Slopes']
        weekend_forecast = row['Weekend Forecast']
        url = row['Url']
        if bottom_snow == 'nan':
            bottom_snow = 'n/a'
        marker_popup_content = f'''<h5>{name}</h5>
                                <p>Resort Details:</p>
                                <ul>
                                    <li><strong>Snow on top (cm):</strong> {top_snow}</li>
                                    <li><strong>Snow on bottom (cm):</strong> {bottom_snow}</li>
                                    <li><strong>Lifts open:</strong> {open_lifts} of {total_lifts}</li>
                                    <li><strong>Lifts open:</strong> {open_slopes} of {total_slopes}</li>
                                    <li><strong>Weekend forecast:</strong> {weekend_forecast}</li>
                                </ul>
                                <a href="{url}" target="_blank">Visit website</a>'''

        # Add markers.
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(marker_popup_content, max_width=300),
            icon=folium.Icon(color=color)
        ).add_to(map)

    return map


app = App(app_ui, server)
