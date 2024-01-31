import ast
from pathlib import Path
import pandas as pd
from shinywidgets import output_widget, register_widget
import folium

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

df = pd.read_csv("ski-resorts.csv")
regions = {'Østlandet': 'East',
        'Sørlandet': 'South',
        'Nord-Norge': 'North',
        'Nord-Vestlandet': 'North-west',
        'Midt-Norge':'Midlands',
        'Sør-Vestlandet': 'South-west'}
initial_selections = ['Østlandet', 'Sørlandet', 'Nord-Norge', 'Nord-Vestlandet', 'Midt-Norge', 'Sør-Vestlandet']


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider(
            'top_snow',
            'Snow on top (cm)',
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
        ui.output_text("value")          
    ),
)

def server(input: Inputs, output: Outputs, session: Session):
    
    # Apply filters to DataFrame
    @reactive.Calc
    def filtered_df():
        selections = input.region_checkboxes()
        filt_df = df
        filt_df = filt_df.loc[filt_df['Snow on Top (cm)'] > input.top_snow()]
        filt_df = filt_df.loc[filt_df['Region'].apply(filter_regions, args=(selections,))]
        if input.toggle():
            filt_df = filt_df.loc[filt_df['Resort Open'] == True]
        return filt_df

    # Render map.
    @render.ui
    def folium_map():
        display_df = filtered_df()
        return build_resort_map(display_df)
    
    @render.text
    def value():
        return f'{input.region_checkboxes()}'


def filter_regions(regions, selections):
    regions_list = ast.literal_eval(regions) # regions are initally in string format.
    intersection = set(regions_list) & set(selections)
    return len(intersection) > 0


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
        top_snow = row['Snow on Top (cm)']
        bottom_snow = str(row['Snow at Bottom (cm)'])
        if bottom_snow == 'nan':
            bottom_snow = 'n/a'
        marker_popup_content = f'''<h5>{name}</h5>
                                <p>Resort Details:</p>
                                <ul>
                                    <li><strong>Snow on top (cm):</strong> {top_snow}</li>
                                    <li><strong>Snow on bottom (cm):</strong> {bottom_snow}</li>
                                </ul>
                                <a href="https://www.example.com" target="_blank">Visit Example.com</a>'''

        # Add markers.
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(marker_popup_content, max_width=300),
            icon=folium.Icon(color=color)
        ).add_to(map)

    return map


app = App(app_ui, server)
