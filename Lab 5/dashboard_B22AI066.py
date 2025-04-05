from shiny import App, reactive, ui, render
import pandas as pd
import numpy as np
import plotly.express as px

# Define a color scheme
app_ui = ui.page_fluid(
    ui.tags.style("""
        body {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .app-header {
            background-color: #3498db;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .section-card {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .section-header {
            background-color: #2c3e50;
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        .upload-section {
            background-color: #eaf2f8;
        }
        .preview-container {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            background-color: white;
        }
        .metrics-table {
            background-color: white;
        }
        .plot-container {
            background-color: white;
            padding: 10px;
            border-radius: 6px;
        }
    """),
    
    ui.div(
        ui.h1("CSV Explorer", class_="text-center"),
        class_="app-header"
    ),
    
    ui.row(
        ui.column(
            6,
            ui.div(
                ui.h4("Upload CSV File", class_="mb-3"),
                ui.input_file("file", label=None, multiple=False),
                class_="section-card upload-section"
            )
        ),
        ui.column(
            6,
            ui.div(
                ui.h4("Distribution Plot Column", class_="mb-3"),
                ui.output_ui("dist_col_ui"),
                class_="section-card upload-section"
            )
        )
    ),

    ui.div(
        ui.h3("CSV Preview", class_="section-header"),
        ui.div(
            ui.output_ui("csv_table_html"),
            class_="preview-container",
            style="height:300px; overflow-y:scroll; padding:15px;"
        ),
        class_="section-card"
    ),

    ui.div(
        ui.h3("Select Columns for EDA", class_="section-header"),
        ui.output_ui("eda_col_ui"),
        class_="section-card"
    ),

    ui.div(
        ui.h3("Basic Metrics for Selected Columns", class_="section-header"),
        ui.output_table("metrics_table", class_="metrics-table"),
        class_="section-card"
    ),

    ui.div(
        ui.h3("Plots for Selected Columns", class_="section-header"),
        ui.div(
            ui.output_ui("eda_plot"),
            class_="plot-container"
        ),
        class_="section-card"
    ),

    ui.div(
        ui.h3("Distribution Plot of Chosen Column", class_="section-header"),
        ui.div(
            ui.output_ui("dist_plot"),
            class_="plot-container"
        ),
        class_="section-card"
    )
)

def server(input, output, session):
    @reactive.Calc
    def df():
        file_info = input.file()
        if not file_info:
            return pd.DataFrame()
        fpath = file_info[0]["datapath"]
        return pd.read_csv(fpath)

    @output
    @render.ui
    def dist_col_ui():
        if df().empty:
            return ui.div("No data loaded.")
        cols = list(df().columns)
        return ui.input_select("dist_col", "Select a column:", choices={c: c for c in cols})

    @reactive.Calc
    def selected_dist_col():
        return input.dist_col()

    @output
    @render.ui
    def csv_table_html():
        # Properly render table as HTML
        if df().empty:
            return ui.div("No file loaded.")
        return ui.HTML(df().head(50).to_html(index=False))

    @output
    @render.ui
    def eda_col_ui():
        if df().empty:
            return ui.div("No data loaded.")
        # Provide multi-column selection using input_select
        return ui.input_select(
            "eda_cols",
            "Select columns:",
            choices={c: c for c in df().columns},
            multiple=True
        )

    def column_type(series):
        # Simple check to categorize numeric vs. categorical
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"
        else:
            unique_vals = series.nunique()
            if unique_vals <= 20:
                return "categorical"
            return "numeric"  # naive fallback

    @reactive.Calc
    def selected_columns():
        return input.eda_cols()

    @output
    @render.table
    def metrics_table():
        # Keep this table render the same
        data = df()
        cols = selected_columns()
        if data.empty or not cols:
            return pd.DataFrame({"Info": ["No columns selected."]})
        metrics_list = []
        for col in cols:
            col_type = column_type(data[col])
            if col_type == "numeric":
                values = data[col].dropna()
                metrics_list.append({
                    "Column": col,
                    "Type": "Numeric",
                    "Mean": round(values.mean(), 2),
                    "Median": round(values.median(), 2),
                    "Mode": values.mode().iloc[0] if not values.mode().empty else None,
                    "Std": round(values.std(), 2)
                })
            else:
                mode_val = data[col].mode().iloc[0] if not data[col].mode().empty else None
                metrics_list.append({
                    "Column": col,
                    "Type": "Categorical",
                    "Count": len(data[col]),
                    "Unique": data[col].nunique(),
                    "Mode": mode_val
                })
        return pd.DataFrame(metrics_list)

    @output
    @render.ui
    def eda_plot():
        data = df()
        cols = selected_columns()
        if data.empty or not cols:
            return ui.div("No columns selected.")
        numeric_cols = [c for c in cols if column_type(data[c]) == "numeric"]

        if len(numeric_cols) > 1:
            fig = px.scatter_matrix(data, dimensions=numeric_cols)
        elif len(numeric_cols) == 1:
            fig = px.histogram(data, x=numeric_cols[0])
        else:
            # If there's any categorical column, plot bar chart of the first one
            cat_cols = [c for c in cols if column_type(data[c]) == "categorical"]
            if cat_cols:
                fig = px.bar(data, x=cat_cols[0])
            else:
                return ui.div("No valid columns to plot.")

        # Return as Plotly HTML
        return ui.HTML(fig.to_html(include_plotlyjs="cdn"))

    @output
    @render.ui
    def dist_plot():
        data = df()
        dist_col = selected_dist_col()
        if data.empty or not dist_col or dist_col not in data.columns:
            return ui.div("No column chosen.")
        if column_type(data[dist_col]) == "numeric":
            fig = px.histogram(data, x=dist_col)
        else:
            fig = px.bar(data, x=dist_col)

        return ui.HTML(fig.to_html(include_plotlyjs="cdn"))

app = App(app_ui, server)