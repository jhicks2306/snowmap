from pathlib import Path
import pandas as pd
from shinywidgets import output_widget, register_widget
import folium

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

df = pd.read_csv("ski-resorts.csv")


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider(
            'top_snow',
            'Snow on top (cm)',
            0,
            200,
            50,
        ),
        ui.input_switch(
            'toggle',
            'Hide closed resorts',
            value=False)
    ),
    ui.row(
        ui.card(
            ui.card_header("Norwegian Ski Resorts"),
            ui.output_ui('folium_map')
        )          
    ),
)

def server(input: Inputs, output: Outputs, session: Session):
    
    # Apply filters to DataFrame
    @reactive.Calc
    def filtered_df():
        filt_df = df
        filt_df = filt_df.loc[filt_df['Snow on Top (cm)'] > input.top_snow()]
        return filt_df

    # Render map.
    @render.ui
    def folium_map():
        display_df = filtered_df()
        return build_resort_map(display_df)


def build_resort_map(df):
    """
    Builds map of Ski resorts with markers.
    """
    
    # Create map and center.
    avg_lat = df['Latitude'].mean()
    avg_lon = df['Longitude'].mean()
    map = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)

    for index, row in df.iterrows():

        # Show green if resort is open.
        if row['Resort Open'] == True:
            color = 'green'
        else:
            color = 'red'

        # Add markers.
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Name'],
            icon=folium.Icon(color=color)
        ).add_to(map)

    return map


app = App(app_ui, server)
