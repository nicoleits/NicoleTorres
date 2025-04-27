# app.py
import dash
# Intentar importar nuevo estilo, fallback al antiguo
try:
    from dash import dcc, html
except ImportError:
    import dash_core_components as dcc
    import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import simulation_logic as sl # Nuestro módulo refactorizado
import os

# --- Configuración Inicial --- 
print("Cargando configuración de países...")
paises_config = sl.get_paises_config()
nombres_paises = [p['nombre'].capitalize() for p in paises_config]
print(f"Países cargados: {nombres_paises}")

# --- Crear la App Dash ---
app = dash.Dash(__name__)
server = app.server # Para despliegue

# --- Layout de la App ---
app.layout = html.Div([
    html.H1("Dashboard Interactivo Simulación PV"),

    # --- Controles --- 
    html.Div([
        # Selección de País
        html.Div([
            html.Label("Seleccionar País:"),
            dcc.Dropdown(
                id='pais-dropdown',
                options=[{'label': nombre, 'value': nombre.lower()} for nombre in nombres_paises],
                value='chile' # Valor inicial
            )
        ], style={'width': '30%', 'display': 'inline-block', 'paddingRight': '10px'}),

        # Selección de Capacidad
        html.Div([
            html.Label("Capacidad (kW):"),
            dcc.Dropdown(
                id='capacidad-dropdown',
                options=[
                    {'label': '0.5 MW', 'value': 500},
                    {'label': '1 MW', 'value': 1000},
                    {'label': '2 MW', 'value': 2000},
                    {'label': '5 MW', 'value': 5000},
                    {'label': '10 MW', 'value': 10000}
                ],
                value=1000 # Valor inicial
            )
        ], style={'width': '30%', 'display': 'inline-block', 'paddingRight': '10px'}),
        
        # Podrías añadir más controles aquí (Sliders para tilt, costos, etc.)

    ], style={'marginBottom': '20px'}),

    html.Hr(), # Separador

    # --- Salidas --- 
    html.Div([
        # Métricas Clave
        html.Div([
            html.H3("Resultados Base"),
            html.Div(id='metricas-output', children="Seleccione parámetros para ver resultados.")
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        # Gráficos
        html.Div([
            html.H3("Análisis de Sensibilidad"),
            dcc.Graph(id='tilt-sensitivity-graph'),
            dcc.Graph(id='dcac-sensitivity-graph'),
            dcc.Graph(id='lcoe-fcr-graph'),
            # Podríamos añadir gráficos para sensibilidad LCOE aquí o en otra sección
        ], style={'width': '65%', 'display': 'inline-block'}),
    ])
])

# --- Callbacks --- 
@app.callback(
    [
        Output('metricas-output', 'children'),
        Output('tilt-sensitivity-graph', 'figure'),
        Output('dcac-sensitivity-graph', 'figure'),
        Output('lcoe-fcr-graph', 'figure')
        # Añadir más Outputs para otros gráficos si se implementan
    ],
    [
        Input('pais-dropdown', 'value'),
        Input('capacidad-dropdown', 'value')
        # Añadir más Inputs si añades más controles
    ]
)
def update_dashboard(selected_pais_nombre, selected_capacidad_kw):
    print(f"\nCallback: País={selected_pais_nombre}, Cap={selected_capacidad_kw}")

    # Encontrar info del país seleccionado
    pais_info = next((p for p in paises_config if p['nombre'] == selected_pais_nombre), None)
    if not pais_info:
        msg = f"Error: No se encontró información para el país '{selected_pais_nombre}'."
        empty_fig = go.Figure() # Figura vacía
        return msg, empty_fig, empty_fig, empty_fig # Devolver para todas las salidas

    # --- Cálculos --- 
    # Configuración base simple para los análisis (puedes hacerla más compleja)
    config_base = {
        'capacity_kw': selected_capacidad_kw,
        'tilt': 20.0, # Tilt base por defecto
        # Parámetros económicos base (usados en LCOE)
        "capital_cost": 1_000_000 * (selected_capacidad_kw / 1000.0), # Escalar costo capital simple
        "fixed_operating_cost": 50_000 * (selected_capacidad_kw / 1000.0)**0.8, # Escalar costo fijo
        "variable_operating_cost": 0.01,
        "fixed_charge_rate": 0.07
    }
    azimuth_base = 0 if selected_pais_nombre in ["chile", "australia"] else 180

    # 1. Métrica Principal (Energía Anual Base)
    print("Calculando energía anual base...")
    pv_model_base = sl.run_single_simulation(
        solar_file=pais_info['archivo'], 
        capacity_kw=selected_capacidad_kw, 
        tilt=config_base['tilt'], 
        azimuth=azimuth_base
    )
    annual_energy = pv_model_base.Outputs.annual_energy if pv_model_base else 0
    print(f"Energía base: {annual_energy}")

    # 2. Métrica Secundaria (LCOE Base)
    print("Calculando LCOE base...")
    lcoe_base = sl.calculate_lcoe_point(
        annual_energy,
        config_base['capital_cost'],
        config_base['fixed_charge_rate'],
        config_base['fixed_operating_cost'],
        config_base['variable_operating_cost']
    )
    print(f"LCOE base: {lcoe_base}")
    
    # Formatear texto de métricas
    metricas_children = [
        html.P(f"Energía Anual ({selected_capacidad_kw} kW): {annual_energy:,.0f} kWh"),
        html.P(f"LCOE Base: ${lcoe_base:.4f}/kWh" if not np.isnan(lcoe_base) else "LCOE Base: N/A")
    ]

    # 3. Datos y Figura: Sensibilidad Tilt
    print("Calculando datos de sensibilidad tilt...")
    tilt_data = sl.get_tilt_sensitivity_data(pais_info, config_base)
    fig_tilt = go.Figure()
    if tilt_data["tilts"] and any(not np.isnan(e) for e in tilt_data["energies"]):
        fig_tilt.add_trace(go.Scatter(
            x=tilt_data['tilts'], y=tilt_data['energies'], 
            mode='lines+markers', name='Energía', marker_color=tilt_data['color']
        ))
    fig_tilt.update_layout(
        title=f"Sensibilidad a Inclinación",
        xaxis_title="Inclinación (grados)", yaxis_title="Energía Anual (kWh)",
        height=300, margin=dict(l=40, r=10, t=40, b=40) # Más compacto
    )
    print("Figura Tilt creada.")

    # 4. Datos y Figura: Sensibilidad DC/AC
    print("Calculando datos de sensibilidad DC/AC...")
    dcac_data = sl.get_dcac_sensitivity_data(pais_info, config_base)
    fig_dcac = go.Figure()
    if dcac_data["ratios"] and any(not np.isnan(e) for e in dcac_data["energies"]):
        fig_dcac.add_trace(go.Scatter(
            x=dcac_data['ratios'], y=dcac_data['energies'],
            mode='lines+markers', name='Energía', marker_color=dcac_data['color']
        ))
    fig_dcac.update_layout(
        title=f"Sensibilidad a Ratio DC/AC",
        xaxis_title="Ratio DC/AC", yaxis_title="Energía Anual (kWh)",
        height=300, margin=dict(l=40, r=10, t=40, b=40)
    )
    print("Figura DC/AC creada.")

    # 5. Datos y Figura: LCOE vs FCR
    print("Calculando datos LCOE vs FCR...")
    lcoe_fcr_data = sl.get_lcoe_vs_fcr_data(pais_info, config_base)
    fig_lcoe_fcr = go.Figure()
    if lcoe_fcr_data["fcrs"] and any(not np.isnan(l) for l in lcoe_fcr_data["lcoes"]):
        fig_lcoe_fcr.add_trace(go.Scatter(
            x=lcoe_fcr_data['fcrs'], y=lcoe_fcr_data['lcoes'],
            mode='lines+markers', name='LCOE', marker_color=lcoe_fcr_data['color']
        ))
    fig_lcoe_fcr.update_layout(
        title=f"LCOE vs Tasa de Carga Fija",
        xaxis_title="Tasa de Carga Fija (FCR)", yaxis_title="LCOE ($/kWh)",
        height=300, margin=dict(l=40, r=10, t=40, b=40)
    )
    print("Figura LCOE vs FCR creada.")

    print("Callback finalizado.")
    return metricas_children, fig_tilt, fig_dcac, fig_lcoe_fcr

# --- Ejecutar la App --- 
if __name__ == '__main__':
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Ejecutando servidor Dash...")
    app.run(debug=True) 