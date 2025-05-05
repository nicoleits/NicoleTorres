# app.py
import dash
# Intentar importar nuevo estilo, fallback al antiguo
try:
    from dash import dcc, html, Input, Output, State, callback, ALL # State, callback, y ALL importados
except ImportError:
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.dependencies import Input, Output, State
# Importar pvlib para análisis de recurso si es necesario
try:
    import pvlib
    PVLIB_AVAILABLE = True
except ImportError:
    PVLIB_AVAILABLE = False
    print("Advertencia: pvlib no está instalado. El análisis de recurso solar no estará disponible.")

import plotly.graph_objects as go
import plotly.express as px # Para heatmaps
import numpy as np
import pandas as pd
import simulation_logic as pv_logic # Renombrado para claridad
import csp_simulation_logic as csp_logic # Importar nuevo módulo CSP
import os
import time # Para medir duración

# --- Configuración Inicial ---
print("Cargando configuración de países PV...")
paises_config_pv_dict = {p['nombre']: p for p in pv_logic.get_paises_config()}
print(f"Países PV cargados: {list(paises_config_pv_dict.keys())}")

print("Cargando configuración de países CSP...")
paises_config_csp_dict = {p['nombre']: p for p in csp_logic.get_csp_paises_config()}
print(f"Países CSP cargados: {list(paises_config_csp_dict.keys())}")

# Usaremos los mismos nombres de país para la selección
nombres_paises_comunes = sorted(list(set(paises_config_pv_dict.keys()) | set(paises_config_csp_dict.keys())))
print(f"Países comunes disponibles: {[n.capitalize() for n in nombres_paises_comunes]}")

# --- Helper Function: Análisis Recurso Solar ---
def generar_graficos_recurso(archivo_tmy):
    """
    Genera gráficos de análisis de recurso solar (heatmap y perfiles mensuales)
    a partir de un archivo TMY. Devuelve un html.Div con los gráficos.
    Requiere pvlib y pandas.
    """
    if not PVLIB_AVAILABLE:
        return html.Div([html.P("La librería pvlib es necesaria para el análisis de recurso.")])
    if not archivo_tmy or not os.path.exists(archivo_tmy):
         return html.Div([html.P(f"Archivo TMY no encontrado o no especificado: {archivo_tmy}")])

    try:
        # Leer datos TMY usando pvlib
        tmy_data, tmy_meta = pvlib.iotools.read_tmy3(archivo_tmy)
        tmy_data.index.name = 'Timestamp' # Asegurar nombre del índice

        # Preparar datos para heatmap (promedio horario diario)
        heatmap_data = tmy_data.groupby([tmy_data.index.month, tmy_data.index.hour])[['GHI', 'DNI', 'DryBulb']].mean().unstack(level=1)

        # Crear Heatmaps
        fig_heatmap_ghi = px.imshow(heatmap_data['GHI'],
                                    labels=dict(x="Hora del Día", y="Mes", color="GHI (W/m²)"),
                                    x=heatmap_data['GHI'].columns,
                                    y=heatmap_data['GHI'].index,
                                    title=f"GHI Promedio Horario - {tmy_meta.get('city', 'Desconocido')}")
        fig_heatmap_dni = px.imshow(heatmap_data['DNI'],
                                    labels=dict(x="Hora del Día", y="Mes", color="DNI (W/m²)"),
                                    x=heatmap_data['DNI'].columns,
                                    y=heatmap_data['DNI'].index,
                                    title=f"DNI Promedio Horario - {tmy_meta.get('city', 'Desconocido')}")
        fig_heatmap_temp = px.imshow(heatmap_data['DryBulb'],
                                     labels=dict(x="Hora del Día", y="Mes", color="Temp (°C)"),
                                     x=heatmap_data['DryBulb'].columns,
                                     y=heatmap_data['DryBulb'].index,
                                     title=f"Temperatura Promedio Horaria - {tmy_meta.get('city', 'Desconocido')}")

        # Preparar datos para perfiles mensuales (promedio diario)
        monthly_profile = tmy_data.resample('D').mean() # Promedio diario
        monthly_profile = monthly_profile.groupby(monthly_profile.index.month)[['GHI', 'DNI', 'DryBulb']].mean() # Promedio mensual del promedio diario

        # Crear Gráficos de Perfil Mensual
        fig_profile_ghi = go.Figure()
        fig_profile_ghi.add_trace(go.Scatter(x=monthly_profile.index, y=monthly_profile['GHI'], mode='lines+markers', name='GHI'))
        fig_profile_ghi.update_layout(title=f"GHI Promedio Diario Mensual - {tmy_meta.get('city', 'Desconocido')}", xaxis_title="Mes", yaxis_title="GHI (W/m²)")

        fig_profile_dni = go.Figure()
        fig_profile_dni.add_trace(go.Scatter(x=monthly_profile.index, y=monthly_profile['DNI'], mode='lines+markers', name='DNI', marker_color='red'))
        fig_profile_dni.update_layout(title=f"DNI Promedio Diario Mensual - {tmy_meta.get('city', 'Desconocido')}", xaxis_title="Mes", yaxis_title="DNI (W/m²)")

        fig_profile_temp = go.Figure()
        fig_profile_temp.add_trace(go.Scatter(x=monthly_profile.index, y=monthly_profile['DryBulb'], mode='lines+markers', name='Temperatura', marker_color='green'))
        fig_profile_temp.update_layout(title=f"Temperatura Promedio Diaria Mensual - {tmy_meta.get('city', 'Desconocido')}", xaxis_title="Mes", yaxis_title="Temperatura (°C)")

        return html.Div([
            dcc.Graph(figure=fig_heatmap_ghi),
            dcc.Graph(figure=fig_heatmap_dni),
            dcc.Graph(figure=fig_heatmap_temp),
            dcc.Graph(figure=fig_profile_ghi),
            dcc.Graph(figure=fig_profile_dni),
            dcc.Graph(figure=fig_profile_temp)
        ])

    except Exception as e:
        print(f"Error generando gráficos de recurso para {archivo_tmy}: {e}")
        return html.Div([html.P(f"Error al procesar el archivo {archivo_tmy}: {e}")])


# Valores por defecto y rangos para controles
DEFAULT_COUNTRY = 'chile'
DEFAULT_CAPACITY_KW = 1000
DEFAULT_TILT = 20.0
DEFAULT_AZIMUTH = 180.0 # Se ajustará por país
DEFAULT_INV_EFF = 96.0
DEFAULT_LOSSES = 14.0
DEFAULT_DCAC = 1.2
DEFAULT_GCR = 0.4
DEFAULT_CAPITAL_COST_MW = 1_000_000 # $/MW
DEFAULT_FIXED_OP_COST_MW_YR = 50_000 # $/MW/yr
DEFAULT_VAR_OP_COST_KWH = 0.01 # $/kWh
DEFAULT_FCR = 0.07

# CSP Defaults
DEFAULT_CSP_STORAGE_HOURS_RANGE = [4, 18] # Min, Max
DEFAULT_CSP_FCR_RANGE = [0.05, 0.10]
DEFAULT_CSP_SOLAR_MULT_RANGE = [1.5, 3.0]
DEFAULT_CSP_TSHOURS_SENS = 12


# --- Crear la App Dash ---
app = dash.Dash(__name__)
server = app.server # Para despliegue

# --- Layout de la App ---
app.layout = html.Div([
    html.H1("Dashboard Interactivo Simulación PV y CSP"),

    # --- Controles ---
    html.Div([
        # Eliminado: Selección de Tecnología (RadioItems)

        # Selección de País (Común) - AHORA MULTI-SELECT
        html.Div([
            html.Label("Seleccionar País/Países:"),
            dcc.Dropdown(
                id='pais-dropdown',
                options=[{'label': nombre.capitalize(), 'value': nombre} for nombre in nombres_paises_comunes],
                value=[DEFAULT_COUNTRY], # Valor inicial es una lista
                multi=True # <<< PERMITIR SELECCIÓN MÚLTIPLE
            )
        ], style={'width': '100%', 'marginBottom': '10px'}), # Ocupa todo el ancho ahora

        # Parámetros Económicos (Comunes)
        html.Div([
             html.H4("Parámetros Económicos Base (Comunes)", style={'marginTop': '15px'}),
             html.Div([
                 html.Label("Tasa Carga Fija (FCR):", style={'display': 'block'}),
                 dcc.Slider(id='fcr-slider', min=0.01, max=0.15, step=0.01, value=DEFAULT_FCR, marks={i/100: f'{i}%' for i in range(1, 16, 2)}),
             ], style={'marginBottom': '10px'}),
             html.Div([
                 html.Label("Costo Op. Fijo ($/MW/año):", style={'display': 'block'}),
                 dcc.Input(id='fixed-op-cost-input', type='number', value=DEFAULT_FIXED_OP_COST_MW_YR, style={'width': '100%'}),
             ], style={'marginBottom': '10px'}),
             html.Div([
                 html.Label("Costo Op. Variable ($/kWh):", style={'display': 'block'}),
                 dcc.Input(id='var-op-cost-input', type='number', value=DEFAULT_VAR_OP_COST_KWH, step=0.001, style={'width': '100%'}),
             ], style={'marginBottom': '10px'}),

        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '2%'}), # Izquierda

        # Controles Específicos (lado derecho)
        html.Div([
             # --- Controles Específicos PV ---
            html.Div(id='pv-controls', children=[
                html.H4("Parámetros Fotovoltaicos", style={'marginTop': '15px'}),
                html.Div([
                    html.Label("Capacidad PV (kW):", style={'display': 'block'}),
                    dcc.Input(id='pv-capacidad-input', type='number', value=DEFAULT_CAPACITY_KW, style={'width': '100%'}),
                    html.Label("Costo Capital PV ($/MW):", style={'display': 'block', 'marginTop': '5px'}),
                    dcc.Input(id='pv-capital-cost-input', type='number', value=DEFAULT_CAPITAL_COST_MW, style={'width': '100%'}),
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Label("Inclinación PV (Tilt):", style={'display': 'block'}),
                    dcc.Slider(id='pv-tilt-slider', min=0, max=90, step=1, value=DEFAULT_TILT, marks={i: str(i) for i in range(0, 91, 10)}),
                    html.Label("Ratio DC/AC PV:", style={'display': 'block', 'marginTop': '5px'}),
                    dcc.Slider(id='pv-dcac-slider', min=1.0, max=2.0, step=0.05, value=DEFAULT_DCAC, marks={i/10: str(i/10) for i in range(10, 21, 2)}),
                ], style={'marginBottom': '10px'}),
                # Podríamos añadir más (Azimuth, GCR, Losses, Inv Eff)
            ], style={'display': 'block', 'border': '1px solid #ddd', 'padding': '10px', 'marginBottom': '15px'}), # Siempre visible ahora

            # --- Controles Específicos CSP ---
            html.Div(id='csp-controls', children=[
                html.H4("Parámetros CSP", style={'marginTop': '15px'}),
                 html.Div([
                    html.Label("Rango Horas Almacenamiento CSP:", style={'display': 'block'}),
                    dcc.RangeSlider(id='csp-storage-slider', min=1, max=24, step=1, value=DEFAULT_CSP_STORAGE_HOURS_RANGE, marks={i: str(i) for i in range(1, 25, 3)}),
                 ], style={'marginBottom': '10px'}),
                 html.Div([
                    html.Label("Rango FCR CSP (Sensibilidad):", style={'display': 'block'}),
                    dcc.RangeSlider(id='csp-fcr-sens-slider', min=0.01, max=0.15, step=0.01, value=DEFAULT_CSP_FCR_RANGE, marks={i/100: f'{i}%' for i in range(1, 16, 2)}),
                 ], style={'marginBottom': '10px'}),
                  html.Div([
                    html.Label("Rango Múltiplo Solar CSP (Sensibilidad):", style={'display': 'block'}),
                    dcc.RangeSlider(id='csp-solarm-sens-slider', min=1.0, max=4.0, step=0.1, value=DEFAULT_CSP_SOLAR_MULT_RANGE, marks={i/2: str(i/2) for i in range(2, 9)}),
                 ], style={'marginBottom': '10px'}),
                  html.Div([
                    html.Label("Horas Almac. Base CSP (Sensibilidad):", style={'display': 'block'}),
                    dcc.Input(id='csp-tshours-sens-input', type='number', value=DEFAULT_CSP_TSHOURS_SENS, style={'width': '100%'}),
                 ], style={'marginBottom': '10px'}),
            ], style={'display': 'block', 'border': '1px solid #ddd', 'padding': '10px'}), # Siempre visible ahora
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}), # Derecha

        # Botón para ejecutar
        html.Button('Ejecutar Simulación y Comparación', id='run-button', n_clicks=0, style={'marginTop': '20px', 'width': '100%'}),

    ], style={'marginBottom': '20px', 'border': '1px solid #eee', 'padding': '15px'}),

    html.Hr(), # Separador

    # --- Sección Análisis de Recurso Solar ---
    html.Div([
        html.H3("Análisis del Recurso Solar"),
        html.Div([
            html.Label("Seleccionar País para Análisis de Recurso:", style={'marginRight': '10px'}),
            dcc.Dropdown(id='recurso-pais-selector', options=[], value=None, style={'width': '300px', 'display': 'inline-block'}),
            html.Button('Mostrar Recurso Solar', id='show-recurso-button', n_clicks=0, style={'marginLeft': '10px', 'display': 'inline-block'})
        ]),
        dcc.Loading(id="loading-recurso", children=[html.Div(id='recurso-output-container')], type="circle"),
    ], style={'marginBottom': '20px', 'border': '1px solid #eee', 'padding': '15px'}),


    html.Hr(), # Separador

    # --- Salidas de Simulación y Comparación ---
    dcc.Loading(id="loading-output", children=[
        html.Div(id='output-container', children=[
            # Contenedores para cada sección de resultados
            html.Div(id='pv-results-container'),
            html.Hr(),
            html.Div(id='csp-results-container'),
            html.Hr(),
            html.Div(id='comparison-results-container'),
        ])
    ], type="circle"),

])

# --- Callback Principal (Simulación y Comparación) ---
@callback(
    Output('pv-results-container', 'children'),
    Output('csp-results-container', 'children'),
    Output('comparison-results-container', 'children'),
    Output('recurso-pais-selector', 'options'), # Actualizar opciones del dropdown
    Output('recurso-pais-selector', 'value'),   # Resetear valor del dropdown
    Input('run-button', 'n_clicks'),
    State('pais-dropdown', 'value'), # Ahora es una lista
    # Estados Controles Comunes
    State('fcr-slider', 'value'),
    State('fixed-op-cost-input', 'value'),
    State('var-op-cost-input', 'value'),
    # Estados Controles PV
    State('pv-capacidad-input', 'value'),
    State('pv-capital-cost-input', 'value'),
    State('pv-tilt-slider', 'value'),
    State('pv-dcac-slider', 'value'),
    # Estados Controles CSP
    State('csp-storage-slider', 'value'),
    State('csp-fcr-sens-slider', 'value'),
    State('csp-solarm-sens-slider', 'value'),
    State('csp-tshours-sens-input', 'value'),
    prevent_initial_call=True # No ejecutar al cargar la página
)
def update_dashboard(n_clicks, selected_paises_nombres, # <<< Cambiado a lista
                     # Comunes
                     fcr_base, fixed_op_cost_mw, var_op_cost_kwh,
                     # PV
                     pv_cap_kw, pv_cap_cost_mw, pv_tilt, pv_dcac,
                     # CSP
                     csp_storage_range, csp_fcr_sens_range, csp_solarm_sens_range, csp_tshours_sens):

    start_time = time.time() # Iniciar cronómetro
    print(f"\n--- Ejecutando Simulación y Comparación (Click {n_clicks}) --- Paises: {selected_paises_nombres}")

    # Inicializar contenedores de salida
    pv_output = html.Div([html.H3("Resultados PV"), html.P("Ejecutando...")])
    csp_output = html.Div([html.H3("Resultados CSP"), html.P("Ejecutando...")])
    comparison_output = html.Div([html.H3("Comparación PV vs CSP"), html.P("Ejecutando...")])
    recurso_options = []
    recurso_value = None # Reset dropdown value

    if not selected_paises_nombres:
        error_msg = html.Div([html.H3("Entrada Inválida"), html.P("Por favor, seleccione al menos un país.")])
        return error_msg, error_msg, error_msg, [], None # Return error for all outputs

    # Validar entradas numéricas comunes
    try:
        fcr_base = float(fcr_base)
        fixed_op_cost_mw = float(fixed_op_cost_mw)
        var_op_cost_kwh = float(var_op_cost_kwh)
    except (ValueError, TypeError):
        error_msg = html.Div([html.H3("Error"), html.P("Valores económicos inválidos.")])
        return error_msg, error_msg, error_msg, [], None

    params_economicos_base = {
        "fixed_charge_rate": fcr_base,
        "fixed_operating_cost": fixed_op_cost_mw, # Por MW
        "variable_operating_cost": var_op_cost_kwh
    }

    # Almacenar resultados para comparación
    comparison_data = []
    processed_paises = set() # Para las opciones del dropdown de recurso

    # --- 1. Lógica PV ---
    print(" Iniciando lógica PV para múltiples países...")
    try:
        pv_cap_kw = float(pv_cap_kw)
        pv_cap_cost_mw = float(pv_cap_cost_mw)
        pv_tilt = float(pv_tilt)
        pv_dcac = float(pv_dcac)
    except (ValueError, TypeError):
        pv_output = html.Div([html.H3("Error PV"), html.P("Parámetros PV inválidos.")])
        # Continuar con CSP si es posible, la comparación estará incompleta
    else:
        # Inicializar figuras PV
        fig_tilt_pv = go.Figure()
        fig_dcac_pv = go.Figure()
        fig_lcoe_fcr_pv = go.Figure()
        all_pv_metrics = [] # Para almacenar métricas base de cada país

        for pais_nombre in selected_paises_nombres:
            print(f"  Procesando PV para: {pais_nombre}...")
            pais_info_pv = paises_config_pv_dict.get(pais_nombre)
            if not pais_info_pv:
                 print(f"    Advertencia: Configuración PV no encontrada para {pais_nombre}, saltando.")
                 continue # Saltar a siguiente país PV

            processed_paises.add(pais_nombre) # Marcar como procesado
            azimuth_pv = 0 if pais_nombre in ["chile", "australia"] else 180

            # Ajustar costos económicos a escala de planta PV
            cap_mw_pv = pv_cap_kw / 1000.0
            capital_cost_pv_total = pv_cap_cost_mw * cap_mw_pv
            fixed_op_cost_pv_total = fixed_op_cost_mw * cap_mw_pv # Asumir escala lineal para simpleza

            config_pv_lcoe = {
                **params_economicos_base,
                'capacity_kw': pv_cap_kw,
                'tilt': pv_tilt,
                'capital_cost': capital_cost_pv_total,
                'fixed_operating_cost': fixed_op_cost_pv_total,
                'dc_ac_ratio': pv_dcac
                # Podríamos añadir más parámetros aquí si los exponemos como controles
            }

            # Calcular métricas base PV
            pv_model_base = pv_logic.run_single_simulation(
                solar_file=pais_info_pv['archivo'], capacity_kw=pv_cap_kw, tilt=pv_tilt,
                azimuth=azimuth_pv, dc_ac_ratio=pv_dcac
            )
            annual_energy_pv = pv_model_base.Outputs.annual_energy if pv_model_base else 0
            lcoe_pv_base = pv_logic.calculate_lcoe_point(
                annual_energy_pv, config_pv_lcoe['capital_cost'], config_pv_lcoe['fixed_charge_rate'],
                config_pv_lcoe['fixed_operating_cost'], config_pv_lcoe['variable_operating_cost']
            ) if annual_energy_pv > 0 else np.nan

            all_pv_metrics.append({
                'Pais': pais_nombre.capitalize(),
                'Energia_kWh': f"{annual_energy_pv:,.0f}",
                'LCOE_$/kWh': f"{lcoe_pv_base:.4f}" if not np.isnan(lcoe_pv_base) else "N/A"
            })
            # Añadir a datos de comparación
            comparison_data.append({'Pais': pais_nombre.capitalize(), 'Tecnologia': 'PV', 'LCOE': lcoe_pv_base})

            # Calcular y añadir trazas a gráficos de sensibilidad PV
            # Tilt
            tilt_data_pv = pv_logic.get_tilt_sensitivity_data(pais_info_pv, config_pv_lcoe)
            if tilt_data_pv["tilts"] and any(not np.isnan(e) for e in tilt_data_pv["energies"]):
                fig_tilt_pv.add_trace(go.Scatter(x=tilt_data_pv['tilts'], y=tilt_data_pv['energies'],
                                                 mode='lines+markers', name=pais_nombre.capitalize(),
                                                 marker_color=tilt_data_pv['color']))
            # DC/AC
            dcac_data_pv = pv_logic.get_dcac_sensitivity_data(pais_info_pv, config_pv_lcoe)
            if dcac_data_pv["ratios"] and any(not np.isnan(e) for e in dcac_data_pv["energies"]):
                fig_dcac_pv.add_trace(go.Scatter(x=dcac_data_pv['ratios'], y=dcac_data_pv['energies'],
                                                 mode='lines+markers', name=pais_nombre.capitalize(),
                                                 marker_color=dcac_data_pv['color']))
            # LCOE vs FCR
            lcoe_fcr_data_pv = pv_logic.get_lcoe_vs_fcr_data(pais_info_pv, config_pv_lcoe)
            if lcoe_fcr_data_pv["fcrs"] and any(not np.isnan(l) for l in lcoe_fcr_data_pv["lcoes"]):
                 fig_lcoe_fcr_pv.add_trace(go.Scatter(x=lcoe_fcr_data_pv['fcrs'], y=lcoe_fcr_data_pv['lcoes'],
                                                      mode='lines+markers', name=pais_nombre.capitalize(),
                                                      marker_color=lcoe_fcr_data_pv['color']))

        # Actualizar layout de figuras PV
        fig_tilt_pv.update_layout(title=f"PV: Sensibilidad a Inclinación", xaxis_title="Inclinación (grados)", yaxis_title="Energía Anual (kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
        fig_dcac_pv.update_layout(title=f"PV: Sensibilidad a Ratio DC/AC", xaxis_title="Ratio DC/AC", yaxis_title="Energía Anual (kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
        fig_lcoe_fcr_pv.update_layout(title=f"PV: LCOE vs Tasa Carga Fija", xaxis_title="Tasa Carga Fija (FCR)", yaxis_title="LCOE ($/kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')

        # Crear tabla de métricas base PV
        metrics_table_header = [html.Thead(html.Tr([html.Th("País"), html.Th("Energía Anual (kWh)"), html.Th("LCOE Base ($/kWh)")]))]
        metrics_table_body = [html.Tbody([html.Tr([html.Td(m['Pais']), html.Td(m['Energia_kWh']), html.Td(m['LCOE_$/kWh'])]) for m in all_pv_metrics])] if all_pv_metrics else []
        metrics_pv_display = html.Table(metrics_table_header + metrics_table_body, style={'width': '100%', 'textAlign': 'left'})

        # Contenedor de salida PV
        pv_output = html.Div([
            html.H3("Resultados PV"),
            metrics_pv_display,
            html.Hr(),
            html.H4("Análisis Sensibilidad PV"),
            dcc.Graph(figure=fig_tilt_pv),
            dcc.Graph(figure=fig_dcac_pv),
            dcc.Graph(figure=fig_lcoe_fcr_pv),
        ])

    # --- 2. Lógica CSP ---
    print(" Iniciando lógica CSP para múltiples países...")
    try:
        csp_tshours_sens = float(csp_tshours_sens)
    except (ValueError, TypeError):
        csp_output = html.Div([html.H3("Error CSP"), html.P("Horas base de almacenamiento CSP inválidas.")])
        # Continuar, la comparación estará incompleta
    else:
        # Preparar rangos numéricos desde sliders
        storage_hours_sim_range = list(np.arange(csp_storage_range[0], csp_storage_range[1] + 1, 1))
        fcr_sens_sim_range = list(np.round(np.arange(csp_fcr_sens_range[0], csp_fcr_sens_range[1] + 0.01, 0.01), 2))
        solarm_sens_sim_range = list(np.round(np.arange(csp_solarm_sens_range[0], csp_solarm_sens_range[1] + 0.1, 0.1), 2))

        # Obtener config de los países seleccionados para CSP
        paises_info_csp_seleccionados = []
        for pais_nombre in selected_paises_nombres:
            pais_info_csp = paises_config_csp_dict.get(pais_nombre)
            if pais_info_csp:
                paises_info_csp_seleccionados.append(pais_info_csp)
                processed_paises.add(pais_nombre) # Marcar como procesado
            else:
                print(f"    Advertencia: Configuración CSP no encontrada para {pais_nombre}, saltando.")

        if not paises_info_csp_seleccionados:
             csp_output = html.Div([html.H3("Error CSP"), html.P("No se encontró configuración CSP para ninguno de los países seleccionados.")])
        else:
            # Usar parámetros económicos directamente (costo capital CSP se calcula en PySAM)
            params_economicos_csp = params_economicos_base.copy()
            # Asumir 100 MW para el costo fijo anual total (simplificación!)
            params_economicos_csp["fixed_operating_cost"] = params_economicos_csp["fixed_operating_cost"] * 100

            print("  CSP: Ejecutando simulación principal (horas almacenamiento)...")
            df_main_csp = csp_logic.ejecutar_simulacion_principal_csp(
                paises_seleccionados=paises_info_csp_seleccionados,
                storage_hours_range=storage_hours_sim_range,
                params_economicos=params_economicos_csp
            )

            print("  CSP: Ejecutando sensibilidad FCR...")
            df_fcr_csp = csp_logic.ejecutar_sensibilidad_fcr_csp(
                paises_seleccionados=paises_info_csp_seleccionados,
                tshours_base=csp_tshours_sens,
                fcr_range=fcr_sens_sim_range,
                params_economicos=params_economicos_csp
            )

            print("  CSP: Ejecutando sensibilidad Múltiplo Solar...")
            df_solarm_csp = csp_logic.ejecutar_sensibilidad_multiplo_solar_csp(
                paises_seleccionados=paises_info_csp_seleccionados,
                tshours_base=csp_tshours_sens,
                solarm_range=solarm_sens_sim_range,
                params_economicos=params_economicos_csp
            )

            # --- Crear Gráficos CSP con Plotly (Multi-Trace) ---
            print("  CSP: Creando gráficos...")
            figs_csp = {}

            # Helper para añadir trazas agrupadas
            def add_traces_by_country(fig, df, x_col, y_col):
                if not df.empty:
                    for pais, group in df.groupby('Pais'):
                        df_plot = group.dropna(subset=[y_col])
                        if not df_plot.empty:
                            color = df_plot['Color'].iloc[0] # Obtener color del grupo
                            fig.add_trace(go.Scatter(x=df_plot[x_col], y=df_plot[y_col],
                                                     mode='lines+markers', name=pais.capitalize(),
                                                     marker_color=color))
                return fig

            # 1. LCOE vs Horas Almacenamiento
            fig_lcoe_horas = go.Figure()
            add_traces_by_country(fig_lcoe_horas, df_main_csp, 'Horas_almacenamiento', 'LCOE_$/kWh')
            fig_lcoe_horas.update_layout(title=f"CSP: LCOE vs Horas Almacenamiento", xaxis_title="Horas Almacenamiento", yaxis_title="LCOE ($/kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
            figs_csp['lcoe_vs_horas'] = fig_lcoe_horas

            # 2. Energía vs Horas Almacenamiento
            fig_energia_horas = go.Figure()
            add_traces_by_country(fig_energia_horas, df_main_csp, 'Horas_almacenamiento', 'Generacion_energia_kWh')
            fig_energia_horas.update_layout(title=f"CSP: Energía vs Horas Almacenamiento", xaxis_title="Horas Almacenamiento", yaxis_title="Generación Anual (kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
            figs_csp['energia_vs_horas'] = fig_energia_horas

            # 3. Costo Planta vs Horas Almacenamiento
            fig_costo_horas = go.Figure()
            add_traces_by_country(fig_costo_horas, df_main_csp, 'Horas_almacenamiento', 'Costo_total_planta_$')
            fig_costo_horas.update_layout(title=f"CSP: Costo Total Planta vs Horas Almacenamiento", xaxis_title="Horas Almacenamiento", yaxis_title="Costo Total Planta ($)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
            figs_csp['costo_vs_horas'] = fig_costo_horas

            # 4. Sensibilidad LCOE vs FCR
            fig_sens_fcr = go.Figure()
            add_traces_by_country(fig_sens_fcr, df_fcr_csp, 'Tasa_carga_fija', 'LCOE_$/kWh')
            fig_sens_fcr.update_layout(title=f"CSP: Sensibilidad LCOE vs FCR ({csp_tshours_sens}h)", xaxis_title="Tasa Carga Fija (FCR)", yaxis_title="LCOE ($/kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
            figs_csp['sens_lcoe_fcr'] = fig_sens_fcr

            # 5. Sensibilidad LCOE vs Múltiplo Solar
            fig_sens_solarm = go.Figure()
            add_traces_by_country(fig_sens_solarm, df_solarm_csp, 'Multiplo_Solar', 'LCOE_$/kWh')
            fig_sens_solarm.update_layout(title=f"CSP: Sensibilidad LCOE vs Múltiplo Solar ({csp_tshours_sens}h, FCR={fcr_base:.2f})", xaxis_title="Múltiplo Solar", yaxis_title="LCOE ($/kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
            figs_csp['sens_lcoe_solarm'] = fig_sens_solarm

            # Métricas Base CSP (Simplificado: Mostrar LCOE base para cada país)
            all_csp_metrics = []
            if not df_fcr_csp.empty:
                for pais_info_csp in paises_info_csp_seleccionados: # Usar la lista de info procesada
                    pais_nombre = pais_info_csp['nombre']
                    df_pais_fcr = df_fcr_csp[(df_fcr_csp['Pais'] == pais_nombre) &
                                             (df_fcr_csp['Tasa_carga_fija'].round(2) == round(fcr_base, 2))]
                    lcoe_csp_base = df_pais_fcr['LCOE_$/kWh'].iloc[0] if not df_pais_fcr.empty else np.nan

                    all_csp_metrics.append({
                        'Pais': pais_nombre.capitalize(),
                        'LCOE_$/kWh': f"{lcoe_csp_base:.4f}" if not np.isnan(lcoe_csp_base) else "N/A"
                    })
                    # Añadir a datos de comparación
                    comparison_data.append({'Pais': pais_nombre.capitalize(), 'Tecnologia': 'CSP', 'LCOE': lcoe_csp_base})

            metrics_table_header_csp = [html.Thead(html.Tr([html.Th("País"), html.Th(f"LCOE Base ($/kWh @ {csp_tshours_sens}h, FCR {fcr_base:.2f})")]))]
            metrics_table_body_csp = [html.Tbody([html.Tr([html.Td(m['Pais']), html.Td(m['LCOE_$/kWh'])]) for m in all_csp_metrics])] if all_csp_metrics else []
            metricas_csp_display = html.Table(metrics_table_header_csp + metrics_table_body_csp, style={'width': '100%', 'textAlign': 'left'})

            # Contenedor de salida CSP
            csp_output = html.Div([
                html.H3("Resultados CSP"),
                metricas_csp_display,
                html.Hr(),
                html.H4("Análisis CSP"),
                # Mostrar gráficos CSP
                dcc.Graph(figure=figs_csp.get('lcoe_vs_horas', go.Figure())),
                dcc.Graph(figure=figs_csp.get('energia_vs_horas', go.Figure())),
                dcc.Graph(figure=figs_csp.get('costo_vs_horas', go.Figure())),
                dcc.Graph(figure=figs_csp.get('sens_lcoe_fcr', go.Figure())),
                dcc.Graph(figure=figs_csp.get('sens_lcoe_solarm', go.Figure())),
            ])

    # --- 3. Comparación ---
    print(" Generando gráfico de comparación...")
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        df_comparison_pivot = df_comparison.pivot(index='Pais', columns='Tecnologia', values='LCOE').reset_index()

        fig_comparison = go.Figure()
        # Añadir barras para PV si existen
        if 'PV' in df_comparison_pivot.columns:
            fig_comparison.add_trace(go.Bar(
                x=df_comparison_pivot['Pais'],
                y=df_comparison_pivot['PV'],
                name='PV LCOE',
                marker_color='blue' # Color para PV
            ))
        # Añadir barras para CSP si existen
        if 'CSP' in df_comparison_pivot.columns:
             fig_comparison.add_trace(go.Bar(
                x=df_comparison_pivot['Pais'],
                y=df_comparison_pivot['CSP'],
                name='CSP LCOE',
                marker_color='orange' # Color para CSP
            ))

        fig_comparison.update_layout(
            title=f"Comparación LCOE Base PV vs CSP (FCR={fcr_base:.2f})",
            xaxis_title="País",
            yaxis_title="LCOE ($/kWh)",
            barmode='group', # Agrupar barras por país
            height=400,
            margin=dict(l=40, r=10, t=40, b=40)
        )
        comparison_output = html.Div([
            html.H3("Comparación PV vs CSP"),
            dcc.Graph(figure=fig_comparison)
        ])
    else:
        comparison_output = html.Div([html.H3("Comparación PV vs CSP"), html.P("No hay suficientes datos para comparar.")])

    # Actualizar opciones del dropdown de recurso
    recurso_options = [{'label': p.capitalize(), 'value': p} for p in sorted(list(processed_paises))]
    if recurso_options:
        recurso_value = recurso_options[0]['value'] # Seleccionar el primero por defecto

    end_time = time.time() # Finalizar cronómetro
    duration = end_time - start_time
    print(f"Simulación y Comparación completadas en {duration:.2f} segundos")

    # Añadir mensaje de duración al final
    duration_msg = html.P(f"Simulaciones completadas en {duration:.2f} segundos", style={'fontSize': 'small', 'color': 'grey', 'marginTop': '15px', 'textAlign': 'center'})

    return pv_output, csp_output, html.Div([comparison_output, duration_msg]), recurso_options, recurso_value


# --- Callback para Análisis de Recurso Solar ---
@callback(
    Output('recurso-output-container', 'children'),
    Input('show-recurso-button', 'n_clicks'),
    State('recurso-pais-selector', 'value'),
    prevent_initial_call=True
)
def show_solar_resource(n_clicks, selected_pais):
    print(f"--- Solicitud Análisis de Recurso (Click {n_clicks}) --- País: {selected_pais}")
    if not selected_pais:
        return html.P("Por favor, seleccione un país y ejecute la simulación primero.")

    # Intentar obtener la ruta del archivo TMY de cualquiera de las configuraciones
    archivo_tmy = None
    if selected_pais in paises_config_pv_dict:
        archivo_tmy = paises_config_pv_dict[selected_pais].get('archivo')
    elif selected_pais in paises_config_csp_dict:
        archivo_tmy = paises_config_csp_dict[selected_pais].get('archivo') # Asume misma clave 'archivo'

    if not archivo_tmy:
         return html.P(f"No se encontró la ruta del archivo TMY para {selected_pais}.")

    print(f"  Generando gráficos de recurso para: {archivo_tmy}")
    return generar_graficos_recurso(archivo_tmy)


# --- Ejecutar la App ---
if __name__ == '__main__':
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    # Verificar disponibilidad de pvlib al inicio
    if not PVLIB_AVAILABLE:
         print("ADVERTENCIA: La librería 'pvlib' no se encontró. El análisis de recurso solar estará deshabilitado.")
         print("Instálala con: pip install pvlib")
    print(f"Ejecutando servidor Dash...")
    app.run(debug=True) 