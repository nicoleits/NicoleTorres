# app.py
import dash
# Intentar importar nuevo estilo, fallback al antiguo
try:
    from dash import dcc, html, Input, Output, State, callback # State y callback importados
except ImportError:
    import dash_core_components as dcc
    import dash_html_components as html
    from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import simulation_logic as pv_logic # Renombrado para claridad
import csp_simulation_logic as csp_logic # Importar nuevo módulo CSP
import os
import time # Para medir duración

# --- Configuración Inicial --- 
print("Cargando configuración de países PV...")
paises_config_pv_dict = {p['nombre']: p for p in pv_logic.get_paises_config()}
nombres_paises_pv = sorted([p.capitalize() for p in paises_config_pv_dict.keys()])
print(f"Países PV cargados: {nombres_paises_pv}")

print("Cargando configuración de países CSP...")
paises_config_csp_dict = {p['nombre']: p for p in csp_logic.get_csp_paises_config()}
# Usaremos los mismos nombres de país para la selección, asumiendo que los archivos existen para ambos
nombres_paises_comunes = sorted(list(set(paises_config_pv_dict.keys()) | set(paises_config_csp_dict.keys())))
print(f"Países comunes disponibles: {[n.capitalize() for n in nombres_paises_comunes]}")

# Valores por defecto y rangos para controles
DEFAULT_COUNTRY = 'chile'
DEFAULT_CAPACITY_KW = 1000
DEFAULT_TILT = 20.0
DEFAULT_AZIMUTH = 180.0
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
        # Selección de Tecnología
        html.Div([
            html.Label("Seleccionar Tecnología:"),
            dcc.RadioItems(
                id='tech-selector',
                options=[
                    {'label': 'Fotovoltaica', 'value': 'PV'},
                    {'label': 'CSP (Concentración Solar)', 'value': 'CSP'},
                ],
                value='PV', # Valor inicial
                labelStyle={'display': 'inline-block', 'margin-right': '10px'}
            )
        ], style={'width': '100%', 'marginBottom': '20px'}),

        # Selección de País (Común) - AHORA MULTI-SELECT
        html.Div([
            html.Label("Seleccionar País/Países:"),
            dcc.Dropdown(
                id='pais-dropdown',
                options=[{'label': nombre.capitalize(), 'value': nombre} for nombre in nombres_paises_comunes],
                value=[DEFAULT_COUNTRY], # Valor inicial es una lista
                multi=True # <<< PERMITIR SELECCIÓN MÚLTIPLE
            )
        ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '2%'}),

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
             # Capital cost se manejará diferente para PV y CSP

        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),

        # --- Controles Específicos PV --- 
        html.Div(id='pv-controls', children=[
            html.H4("Parámetros Fotovoltaicos", style={'marginTop': '15px'}),
            html.Div([
                html.Label("Capacidad (kW):", style={'display': 'block'}),
                dcc.Input(id='pv-capacidad-input', type='number', value=DEFAULT_CAPACITY_KW, style={'width': '100%'}),
                html.Label("Costo Capital PV ($/MW):", style={'display': 'block', 'marginTop': '5px'}),
                dcc.Input(id='pv-capital-cost-input', type='number', value=DEFAULT_CAPITAL_COST_MW, style={'width': '100%'}),
            ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '2%', 'marginBottom': '10px'}),
            html.Div([
                html.Label("Inclinación (Tilt):", style={'display': 'block'}),
                dcc.Slider(id='pv-tilt-slider', min=0, max=90, step=1, value=DEFAULT_TILT, marks={i: str(i) for i in range(0, 91, 10)}),
                html.Label("Ratio DC/AC:", style={'display': 'block', 'marginTop': '5px'}),
                dcc.Slider(id='pv-dcac-slider', min=1.0, max=2.0, step=0.05, value=DEFAULT_DCAC, marks={i/10: str(i/10) for i in range(10, 21, 2)}),
            ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'marginBottom': '10px'}),
            # Podríamos añadir más (Azimuth, GCR, Losses, Inv Eff)
        ], style={'display': 'block'}), # Se mostrará/ocultará con callback

        # --- Controles Específicos CSP --- 
        html.Div(id='csp-controls', children=[
            html.H4("Parámetros CSP", style={'marginTop': '15px'}),
             html.Div([
                html.Label("Rango Horas Almacenamiento:", style={'display': 'block'}),
                dcc.RangeSlider(id='csp-storage-slider', min=1, max=24, step=1, value=DEFAULT_CSP_STORAGE_HOURS_RANGE, marks={i: str(i) for i in range(1, 25, 3)}),
             ], style={'marginBottom': '10px'}),
             html.Div([
                html.Label("Rango FCR (Sensibilidad):", style={'display': 'block'}),
                dcc.RangeSlider(id='csp-fcr-sens-slider', min=0.01, max=0.15, step=0.01, value=DEFAULT_CSP_FCR_RANGE, marks={i/100: f'{i}%' for i in range(1, 16, 2)}),
             ], style={'marginBottom': '10px'}),
              html.Div([
                html.Label("Rango Múltiplo Solar (Sensibilidad):", style={'display': 'block'}),
                dcc.RangeSlider(id='csp-solarm-sens-slider', min=1.0, max=4.0, step=0.1, value=DEFAULT_CSP_SOLAR_MULT_RANGE, marks={i/2: str(i/2) for i in range(2, 9)}),
             ], style={'marginBottom': '10px'}),
              html.Div([
                html.Label("Horas Almac. Base (Sensibilidad):", style={'display': 'block'}),
                dcc.Input(id='csp-tshours-sens-input', type='number', value=DEFAULT_CSP_TSHOURS_SENS, style={'width': '100%'}),
             ], style={'marginBottom': '10px'}),
        ], style={'display': 'none'}), # Oculto inicialmente

        # Botón para ejecutar
        html.Button('Ejecutar Simulación', id='run-button', n_clicks=0, style={'marginTop': '20px'}),

    ], style={'marginBottom': '20px', 'border': '1px solid #eee', 'padding': '15px'}),

    html.Hr(), # Separador

    # --- Salidas --- 
    dcc.Loading(id="loading-output", children=[html.Div(id='output-container')], type="circle"),

])

# --- Callback para mostrar/ocultar controles específicos ---
@callback(
    Output('pv-controls', 'style'),
    Output('csp-controls', 'style'),
    Input('tech-selector', 'value')
)
def toggle_controls(selected_tech):
    if selected_tech == 'PV':
        return {'display': 'block'}, {'display': 'none'}
    elif selected_tech == 'CSP':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'} # Por defecto ocultar ambos

# --- Callback Principal --- 
@callback(
    Output('output-container', 'children'),
    Input('run-button', 'n_clicks'),
    State('tech-selector', 'value'),
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
def update_dashboard(n_clicks, tech, selected_paises_nombres, # <<< Cambiado a lista
                     # Comunes
                     fcr_base, fixed_op_cost_mw, var_op_cost_kwh,
                     # PV
                     pv_cap_kw, pv_cap_cost_mw, pv_tilt, pv_dcac,
                     # CSP
                     csp_storage_range, csp_fcr_sens_range, csp_solarm_sens_range, csp_tshours_sens):

    start_time = time.time() # Iniciar cronómetro
    print(f"\n--- Ejecutando Simulación (Click {n_clicks}) --- Tech: {tech}, Paises: {selected_paises_nombres}")

    if not selected_paises_nombres:
        return html.Div([html.H3("Entrada Inválida"), html.P("Por favor, seleccione al menos un país.")])

    # Validar entradas numéricas comunes
    try:
        fcr_base = float(fcr_base)
        fixed_op_cost_mw = float(fixed_op_cost_mw)
        var_op_cost_kwh = float(var_op_cost_kwh)
    except (ValueError, TypeError):
        return html.Div([html.H3("Error"), html.P("Valores económicos inválidos.")])

    params_economicos_base = {
        "fixed_charge_rate": fcr_base,
        "fixed_operating_cost": fixed_op_cost_mw, # Por MW
        "variable_operating_cost": var_op_cost_kwh
    }

    # --- Lógica PV --- 
    if tech == 'PV':
        print("Iniciando lógica PV para múltiples países...")
        try:
            pv_cap_kw = float(pv_cap_kw)
            pv_cap_cost_mw = float(pv_cap_cost_mw)
            pv_tilt = float(pv_tilt)
            pv_dcac = float(pv_dcac)
        except (ValueError, TypeError):
            return html.Div([html.H3("Error PV"), html.P("Parámetros PV inválidos.")])

        # Inicializar figuras
        fig_tilt_pv = go.Figure()
        fig_dcac_pv = go.Figure()
        fig_lcoe_fcr_pv = go.Figure()
        all_pv_metrics = [] # Para almacenar métricas base de cada país

        for pais_nombre in selected_paises_nombres:
            print(f"  Procesando PV para: {pais_nombre}...")
            pais_info_pv = paises_config_pv_dict.get(pais_nombre)
            if not pais_info_pv:
                 print(f"    Advertencia: Configuración PV no encontrada para {pais_nombre}, saltando.")
                 continue # Saltar a siguiente país

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
            azimuth_pv = 0 if pais_nombre in ["chile", "australia"] else 180

            # Calcular métricas base PV
            pv_model_base = pv_logic.run_single_simulation(
                solar_file=pais_info_pv['archivo'], capacity_kw=pv_cap_kw, tilt=pv_tilt,
                azimuth=azimuth_pv, dc_ac_ratio=pv_dcac
            )
            annual_energy_pv = pv_model_base.Outputs.annual_energy if pv_model_base else 0
            lcoe_pv_base = pv_logic.calculate_lcoe_point(
                annual_energy_pv, config_pv_lcoe['capital_cost'], config_pv_lcoe['fixed_charge_rate'],
                config_pv_lcoe['fixed_operating_cost'], config_pv_lcoe['variable_operating_cost']
            )
            all_pv_metrics.append({
                'Pais': pais_nombre.capitalize(),
                'Energia_kWh': f"{annual_energy_pv:,.0f}",
                'LCOE_$/kWh': f"{lcoe_pv_base:.4f}" if not np.isnan(lcoe_pv_base) else "N/A"
            })

            # Calcular y añadir trazas a gráficos de sensibilidad
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

        # Actualizar layout de figuras
        fig_tilt_pv.update_layout(title=f"PV: Sensibilidad a Inclinación", xaxis_title="Inclinación (grados)", yaxis_title="Energía Anual (kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
        fig_dcac_pv.update_layout(title=f"PV: Sensibilidad a Ratio DC/AC", xaxis_title="Ratio DC/AC", yaxis_title="Energía Anual (kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')
        fig_lcoe_fcr_pv.update_layout(title=f"PV: LCOE vs Tasa Carga Fija", xaxis_title="Tasa Carga Fija (FCR)", yaxis_title="LCOE ($/kWh)", height=350, margin=dict(l=40, r=10, t=40, b=40), legend_title_text='País')

        # Crear tabla de métricas base
        metrics_table_header = [html.Thead(html.Tr([html.Th("País"), html.Th("Energía Anual (kWh)"), html.Th("LCOE Base ($/kWh)")]))]
        metrics_table_body = [html.Tbody([html.Tr([html.Td(m['Pais']), html.Td(m['Energia_kWh']), html.Td(m['LCOE_$/kWh'])]) for m in all_pv_metrics])] if all_pv_metrics else []
        metrics_pv_display = html.Div([
            html.H3("Resultados Base PV"),
            html.Table(metrics_table_header + metrics_table_body, style={'width': '100%', 'textAlign': 'left'})
        ])

        end_time = time.time() # Finalizar cronómetro
        duration = end_time - start_time
        # Contenedor de salida PV
        return html.Div([
            metrics_pv_display,
            html.Hr(),
            html.H3("Análisis Sensibilidad PV"),
            dcc.Graph(figure=fig_tilt_pv),
            dcc.Graph(figure=fig_dcac_pv),
            dcc.Graph(figure=fig_lcoe_fcr_pv),
            html.P(f"Simulación PV completada en {duration:.2f} segundos", style={'fontSize': 'small', 'color': 'grey', 'marginTop': '15px'})
        ])

    # --- Lógica CSP --- 
    elif tech == 'CSP':
        print("Iniciando lógica CSP para múltiples países...")
        try:
            csp_tshours_sens = float(csp_tshours_sens)
        except (ValueError, TypeError):
             return html.Div([html.H3("Error CSP"), html.P("Horas base de almacenamiento CSP inválidas.")])

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
            else:
                print(f"    Advertencia: Configuración CSP no encontrada para {pais_nombre}, saltando.")
        
        if not paises_info_csp_seleccionados:
             return html.Div([html.H3("Error CSP"), html.P("No se encontró configuración CSP para ninguno de los países seleccionados.")])

        # Usar parámetros económicos directamente (costo capital CSP se calcula en PySAM)
        # Escalar costos operativos a MW (asumiendo planta base 100MW para escala?) - Simplificación!
        params_economicos_csp = params_economicos_base.copy()
        # Ajustamos el costo fijo a $/planta/año en lugar de $/MW/año ya que CSP Trough no tiene input de capacidad nominal fácilmente accesible aquí
        params_economicos_csp["fixed_operating_cost"] = params_economicos_csp["fixed_operating_cost"] * 100 # Asumir 100 MW para el costo fijo anual total

        print("CSP: Ejecutando simulación principal (horas almacenamiento)...")
        df_main_csp = csp_logic.ejecutar_simulacion_principal_csp(
            paises_seleccionados=paises_info_csp_seleccionados,
            storage_hours_range=storage_hours_sim_range,
            params_economicos=params_economicos_csp
        )

        print("CSP: Ejecutando sensibilidad FCR...")
        df_fcr_csp = csp_logic.ejecutar_sensibilidad_fcr_csp(
            paises_seleccionados=paises_info_csp_seleccionados,
            tshours_base=csp_tshours_sens,
            fcr_range=fcr_sens_sim_range,
            params_economicos=params_economicos_csp
        )

        print("CSP: Ejecutando sensibilidad Múltiplo Solar...")
        df_solarm_csp = csp_logic.ejecutar_sensibilidad_multiplo_solar_csp(
            paises_seleccionados=paises_info_csp_seleccionados,
            tshours_base=csp_tshours_sens,
            solarm_range=solarm_sens_sim_range,
            params_economicos=params_economicos_csp
        )

        # --- Crear Gráficos CSP con Plotly (Multi-Trace) --- 
        print("CSP: Creando gráficos...")
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
            for pais_nombre in selected_paises_nombres:
                lcoe_csp_base = df_fcr_csp[(df_fcr_csp['Pais'] == pais_nombre) & (df_fcr_csp['Tasa_carga_fija'].round(2) == round(fcr_base, 2))]['LCOE_$/kWh'].iloc[0] if not df_fcr_csp[(df_fcr_csp['Pais'] == pais_nombre) & (df_fcr_csp['Tasa_carga_fija'].round(2) == round(fcr_base, 2))].empty else np.nan
                all_csp_metrics.append({
                    'Pais': pais_nombre.capitalize(),
                    'LCOE_$/kWh': f"{lcoe_csp_base:.4f}" if not np.isnan(lcoe_csp_base) else "N/A"
                })

        metrics_table_header_csp = [html.Thead(html.Tr([html.Th("País"), html.Th(f"LCOE Base ($/kWh @ {csp_tshours_sens}h, FCR {fcr_base:.2f})")]))]
        metrics_table_body_csp = [html.Tbody([html.Tr([html.Td(m['Pais']), html.Td(m['LCOE_$/kWh'])]) for m in all_csp_metrics])] if all_csp_metrics else []
        metricas_csp_display = html.Div([
            html.H3("Resultados Base CSP"),
            html.Table(metrics_table_header_csp + metrics_table_body_csp, style={'width': '100%', 'textAlign': 'left'})
        ])

        end_time = time.time() # Finalizar cronómetro
        duration = end_time - start_time
        # Contenedor de salida CSP
        return html.Div([
            metricas_csp_display,
            html.Hr(),
            html.H3("Análisis CSP"),
            # Mostrar gráficos en dos columnas
            html.Div([
                dcc.Graph(figure=figs_csp.get('lcoe_vs_horas', go.Figure())),
                dcc.Graph(figure=figs_csp.get('energia_vs_horas', go.Figure())),
                dcc.Graph(figure=figs_csp.get('costo_vs_horas', go.Figure())),
            ], style={'width': '49%', 'display': 'inline-block'}),
            html.Div([
                dcc.Graph(figure=figs_csp.get('sens_lcoe_fcr', go.Figure())),
                dcc.Graph(figure=figs_csp.get('sens_lcoe_solarm', go.Figure())),
            ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            html.P(f"Simulación CSP completada en {duration:.2f} segundos", style={'fontSize': 'small', 'color': 'grey', 'marginTop': '15px'})
        ])

    # Si no es PV ni CSP (no debería pasar con RadioItems)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Error: Tecnología no reconocida. Tiempo: {duration:.2f}s")
    return html.Div([html.H3("Error"), html.P("Tecnología no reconocida.")])


# --- Ejecutar la App --- 
if __name__ == '__main__':
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Ejecutando servidor Dash...")
    app.run(debug=True) 