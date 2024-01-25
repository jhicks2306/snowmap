from pathlib import Path

import pandas as pd
import seaborn as sns
from ipyleaflet import GeoJSON, Map
from shinywidgets import output_widget, register_widget
import folium

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

sns.set_theme(style="white")
df = pd.read_csv(Path(__file__).parent / "penguins.csv", na_values="NA")
df_resorts = pd.read_csv("ski-resorts.csv")
species = ["Adelie", "Gentoo", "Chinstrap"]


def make_value_box(penguin):
    return ui.value_box(
        title=penguin, value=ui.output_text(f"{penguin}_count".lower()), theme="primary"
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider(
            "mass",
            "Mass",
            2000,
            6000,
            3400,
        ),
        ui.input_checkbox_group(
            "species", "Filter by species", species, selected=species
        ),
    ),
    ui.row(
        ui.layout_columns(
            *[make_value_box(penguin) for penguin in species],
        )
    ),
    ui.row(
        ui.layout_columns(
            ui.card(
                ui.card_header("Summary statistics"),
                ui.output_data_frame("summary_statistics"),
            ),
            ui.card(
                ui.card_header("Penguin bills"),
                ui.output_plot("length_depth"),
            ),
        ),
    ),
    ui.row(
        ui.card(
            ui.card_header("Norwegian Ski Resorts"),
            ui.output_ui('folium_map')
        )          
    ),
    ui.row(
        ui.card(
            ui.card_header("Resorts"),
            ui.output_data_frame("resort_summary"),
        ),         
    ),
)


def server(input: Inputs, output: Outputs, session: Session):
    @reactive.Calc
    def filtered_df() -> pd.DataFrame:
        filt_df = df[df["Species"].isin(input.species())]
        filt_df = filt_df.loc[filt_df["Body Mass (g)"] > input.mass()]
        return filt_df
    

    @render.text
    def adelie_count():
        return count_species(filtered_df(), "Adelie")

    @render.text
    def chinstrap_count():
        return count_species(filtered_df(), "Chinstrap")

    @render.text
    def gentoo_count():
        return count_species(filtered_df(), "Gentoo")

    @render.plot
    def length_depth():
        return sns.scatterplot(
            data=filtered_df(),
            x="Bill Length (mm)",
            y="Bill Depth (mm)",
            hue="Species",
        )

    @render.data_frame
    def summary_statistics():
        display_df = filtered_df()[
            [
                "Species",
                "Island",
                "Bill Length (mm)",
                "Bill Depth (mm)",
                "Body Mass (g)",
            ]
        ]
        return render.DataGrid(display_df, filters=True)
    
    @render.data_frame
    def resort_summary():
        return render.DataGrid(df_resorts, width='100%')
    

    @render.ui
    def folium_map():
        return build_resort_map(df_resorts)


def count_species(df, species):
    return df[df["Species"] == species].shape[0]

def build_resort_map(df):
    avg_lat = df['Latitude'].mean()
    avg_lon = df['Longitude'].mean()
    map = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)

    for index, row in df.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Name']
        ).add_to(map)

    return map


app = App(app_ui, server)
