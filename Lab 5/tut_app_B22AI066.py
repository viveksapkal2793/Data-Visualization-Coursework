from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the mpg dataset from seaborn
data = sns.load_dataset('mpg')

# Convert unique cylinder values to a list of strings
cylinder_choices = sorted([str(x) for x in data['cylinders'].unique()])
origin_choices = sorted(data['origin'].unique())

# Define UI
app_ui = ui.page_fluid(
    ui.h2("Vehicle Data Analysis Dashboard"),
    
    # Plot and table with widget
    ui.card(
        ui.card_header("Vehicle Performance Analysis"),
        ui.row(
            ui.column(8, ui.output_plot("plot")),
            ui.column(4, 
                ui.input_select("select", "Select Cylinder:", choices=cylinder_choices),
                ui.input_radio_buttons(
                    "plot_type", 
                    "Plot type:",
                    choices=["MPG by Cylinders", "Weight vs MPG", "Horsepower Distribution"]
                ),
                ui.output_table("table")
            )
        )
    ),
    
    # Example of sidebar layout
    ui.h3("Sidebar Layout Example"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.h4("Controls"),
            ui.input_slider("mpg_range", "MPG Range:", min=int(data['mpg'].min()), 
                            max=int(data['mpg'].max()), 
                            value=[15, 25]),
            ui.input_checkbox_group(
                "origins",
                "Filter by Origin:",
                choices=origin_choices,
                selected=origin_choices
            ),
            ui.input_action_button("update", "Update Analysis", class_="btn-primary")
        ),
        ui.card(
            ui.card_header("MPG Analysis by Origin"),
            ui.output_plot("sidebar_plot"),
            ui.p("This analysis shows how fuel efficiency (MPG) varies across different vehicle origins and model years.")
        )
    ),
    
    # Example of multi-page layout
    ui.h3("Multi-page Layout Example"),
    ui.navset_tab(
        ui.nav_panel("Data Summary", 
            ui.row(
                ui.column(6, ui.output_plot("summary_pie")),
                ui.column(6, ui.output_table("summary_stats"))
            ),
            ui.p("This page provides an overview of the dataset including distribution of vehicles by cylinder count and basic statistics.")
        ),
        ui.nav_panel("Time Trends", 
            ui.output_plot("year_trend"),
            ui.p("This page shows how vehicle metrics have changed over time.")
        )
    ),
    
    # Example of multi-column layout
    ui.h3("Multi-column Layout Example"),
    ui.layout_columns(
        ui.column(4, ui.card(
            ui.card_header("Average MPG"),
            ui.value_box(
                title="Overall Average MPG",
                value=ui.output_text("avg_mpg"),
                theme=ui.value_box_theme(bg="lightblue")
            ),
            "Fuel efficiency is a critical factor in vehicle performance."
        )),
        ui.column(4, ui.card(
            ui.card_header("Horsepower"),
            ui.output_plot("hp_hist"),
            "Horsepower distribution across the fleet."
        )),
        ui.column(4, ui.card(
            ui.card_header("Weight Impact"),
            ui.output_plot("weight_impact"),
            "There's a strong relationship between vehicle weight and efficiency."
        ))
    ),
    
    # Example of multi-panel layout
    ui.h3("Multi-panel Layout Example - Cylinder Analysis"),
    ui.panel_conditional("input.select == '4'", ui.card(
        ui.card_header("4-Cylinder Vehicles"),
        ui.output_plot("cyl4_plot"),
        "4-cylinder vehicles typically offer better fuel economy but less power."
    )),
    ui.panel_conditional("input.select == '6'", ui.card(
        ui.card_header("6-Cylinder Vehicles"),
        ui.output_plot("cyl6_plot"),
        "6-cylinder vehicles balance power and efficiency for mid-size applications."
    )),
    ui.panel_conditional("input.select == '8'", ui.card(
        ui.card_header("8-Cylinder Vehicles"),
        ui.output_plot("cyl8_plot"),
        "8-cylinder vehicles typically offer the most power but consume more fuel."
    ))
)

# Define server logic
def server(input, output, session):
    # Reactive filtered data
    @reactive.Calc
    def filtered_data():
        df = data[data['cylinders'] == int(input.select())]
        return df
    
    @reactive.Effect
    @reactive.event(input.update)
    def _():
        # This forces sidebar_plot to update when the update button is clicked
        output.sidebar_plot.invalidate()
        
    @reactive.Calc
    def sidebar_filtered_data():
        df = data.copy()
        # Filter by MPG range
        df = df[(df['mpg'] >= input.mpg_range()[0]) & (df['mpg'] <= input.mpg_range()[1])]
        # Filter by origin
        if input.origins():
            df = df[df['origin'].isin(input.origins())]
        return df
    
    # Main plot
    @output
    @render.plot
    def plot():
        plt.figure(figsize=(10, 6))
        
        plot_type = input.plot_type()
        df = filtered_data()
        
        if plot_type == "MPG by Cylinders":
            sns.barplot(x='cylinders', y='mpg', data=df)
            plt.title(f'Miles per Gallon for {input.select()} Cylinders')
            
        elif plot_type == "Weight vs MPG":
            sns.scatterplot(x='weight', y='mpg', hue='origin', data=df)
            plt.title(f'Weight vs MPG for {input.select()}-Cylinder Vehicles')
            
        else:  # Horsepower Distribution
            sns.histplot(df['horsepower'], kde=True)
            plt.title(f'Horsepower Distribution for {input.select()}-Cylinder Vehicles')
        
        fig = plt.gcf()
        return fig

    # Sidebar plot
    @output
    @render.plot
    def sidebar_plot():
        df = sidebar_filtered_data()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x='model_year', y='mpg', hue='origin', data=df, markers=True, ax=ax)
        plt.title('MPG Trends by Origin and Year')
        return fig
    
    # Summary pie chart
    @output
    @render.plot
    def summary_pie():
        fig, ax = plt.subplots(figsize=(8, 8))
        cyl_counts = data['cylinders'].value_counts()
        ax.pie(cyl_counts, labels=cyl_counts.index, autopct='%1.1f%%')
        ax.set_title('Distribution of Vehicles by Cylinder Count')
        return fig
    
    # Year trend plot
    @output
    @render.plot
    def year_trend():
        yearly = data.groupby('model_year').agg({
            'mpg': 'mean', 
            'horsepower': 'mean', 
            'weight': 'mean'
        }).reset_index()
        
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        ax1.set_xlabel('Model Year')
        ax1.set_ylabel('Average MPG', color='tab:blue')
        ax1.plot(yearly['model_year'], yearly['mpg'], color='tab:blue', marker='o')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('Average Horsepower', color='tab:red')
        ax2.plot(yearly['model_year'], yearly['horsepower'], color='tab:red', marker='s')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        plt.title('Trends in MPG and Horsepower Over Time')
        fig.tight_layout()
        return fig
    
    # Average MPG text
    @output
    @render.text
    def avg_mpg():
        return f"{data['mpg'].mean():.1f}"
    
    # Horsepower histogram
    @output
    @render.plot
    def hp_hist():
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(data['horsepower'], kde=True, ax=ax)
        ax.set_title('Horsepower Distribution')
        return fig
    
    # Weight impact plot
    @output
    @render.plot
    def weight_impact():
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.regplot(x='weight', y='mpg', data=data, ax=ax)
        ax.set_title('Weight vs. MPG')
        return fig
    
    # Cylinder specific plots
    @output
    @render.plot
    def cyl4_plot():
        fig, ax = plt.subplots(figsize=(8, 5))
        cyl4 = data[data['cylinders'] == 4]
        sns.scatterplot(x='horsepower', y='mpg', hue='origin', data=cyl4, ax=ax)
        ax.set_title('Horsepower vs MPG for 4-cylinder Vehicles')
        return fig
    
    @output
    @render.plot
    def cyl6_plot():
        fig, ax = plt.subplots(figsize=(8, 5))
        cyl6 = data[data['cylinders'] == 6]
        sns.scatterplot(x='displacement', y='mpg', hue='origin', size='horsepower', data=cyl6, ax=ax)
        ax.set_title('Displacement vs MPG for 6-cylinder Vehicles')
        return fig
    
    @output
    @render.plot
    def cyl8_plot():
        fig, ax = plt.subplots(figsize=(8, 5))
        cyl8 = data[data['cylinders'] == 8]
        years = sorted(cyl8['model_year'].unique())
        avg_mpg = [cyl8[cyl8['model_year']==year]['mpg'].mean() for year in years]
        ax.bar(years, avg_mpg)
        ax.set_title('Average MPG by Year for 8-cylinder Vehicles')
        ax.set_xlabel('Model Year')
        ax.set_ylabel('Average MPG')
        return fig
    
    # Table output
    @output
    @render.table
    def table():
        df = filtered_data()
        return df[['name', 'mpg', 'horsepower', 'weight', 'origin']].head(5)
    
    # Summary statistics table
    @output
    @render.table
    def summary_stats():
        stats = data.groupby('cylinders').agg({
            'mpg': ['mean', 'min', 'max'],
            'horsepower': ['mean', 'min', 'max'],
            'weight': ['mean', 'min', 'max']
        })
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        return stats.reset_index()

# Create app
app = App(app_ui, server)

# Run the app
if __name__ == "__main__":
    app.run()