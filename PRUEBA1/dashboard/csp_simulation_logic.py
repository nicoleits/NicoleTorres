import PySAM.TcsmoltenSalt as TCSMS
import PySAM.Lcoefcr as Lcoefcr
import pandas as pd
import os
import numpy as np
# Matplotlib ya no es necesario para generar gráficos aquí, pero PySAM puede depender de él
# import matplotlib.pyplot as plt
# import matplotlib.ticker as mticker

# Constante para la ruta base de datos, relativa a este script
# Sube un nivel desde 'dashboard' a 'PRUEBA1', luego entra a 'Datos'
DATOS_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Datos'))

# Configuración de países (similar a simulation_logic.py)
# Se puede mover a un archivo config compartido si se desea
PAISES_CONFIG_CSP = [
    {"nombre": "australia", "archivo_sufijo": "australia", "color": "blue"},
    {"nombre": "chile", "archivo_sufijo": "chile", "color": "red"},
    {"nombre": "espana", "archivo_sufijo": "espana", "color": "green"}
]

def get_csp_paises_config():
    """Devuelve la configuración de países CSP con rutas absolutas a los archivos."""
    config_completa = []
    for pais in PAISES_CONFIG_CSP:
        config_completa.append({
            "nombre": pais["nombre"],
            "archivo_solar": os.path.join(DATOS_BASE_DIR, f"{pais['archivo_sufijo']}.csv"),
            "color": pais["color"]
        })
    return config_completa


# --- Funciones de Simulación CSP (Adaptadas) ---

def cargar_recurso_solar_csp(pais_nombre, archivo_solar):
    """Carga los datos del recurso solar desde archivo CSV para CSP, con manejo especial para Australia."""
    # (Misma lógica que antes, pero sin prints innecesarios para módulo)
    resource_input = {}
    if not os.path.exists(archivo_solar):
        print(f"ERROR CSP: Archivo solar no encontrado en {archivo_solar}")
        return None

    if pais_nombre == "australia":
        try:
            meta_df = pd.read_csv(archivo_solar, nrows=1, header=None, skiprows=1)
            lat = meta_df.iloc[0, 5]
            lon = meta_df.iloc[0, 6]
            tz = meta_df.iloc[0, 9]
            elev = meta_df.iloc[0, 8]
            data_df = pd.read_csv(archivo_solar, skiprows=2)

            required_cols = {
                'Year': 'year', 'Month': 'month', 'Day': 'day',
                'Hour': 'hour', 'Minute': 'minute', 'DNI': 'dn',
                'DHI': 'df', 'GHI': 'gh', 'Temperature': 'tdry',
                'Wind Speed': 'wspd'
            }
            optional_cols = {'Dew Point': 'tdew', 'Pressure': 'pres'}
            resource_data = {'lat': lat, 'lon': lon, 'tz': tz, 'elev': elev, 'location': pais_nombre}
            cols_to_extract = {}

            for orig_col, sam_col in required_cols.items():
                if orig_col not in data_df.columns:
                    raise ValueError(f"Columna requerida '{orig_col}' no encontrada en {archivo_solar}")
                cols_to_extract[sam_col] = data_df[orig_col].tolist()

            for orig_col, sam_col in optional_cols.items():
                if orig_col in data_df.columns:
                    cols_to_extract[sam_col] = data_df[orig_col].tolist()

            resource_data.update(cols_to_extract)
            resource_input = {"solar_resource_data": resource_data}
            # print(f"Debug CSP: Datos de {pais_nombre} cargados manualmente.")
            return resource_input

        except Exception as e:
            print(f"ERROR CSP al leer manualmente {archivo_solar}: {e}.")
            return None # Indicar fallo
    else:
        # Para otros países, usar referencia de archivo
        # print(f"Debug CSP: Usando referencia de archivo para {pais_nombre}: {archivo_solar}")
        return {"solar_resource_file": archivo_solar}


def ejecutar_simulacion_principal_csp(paises_seleccionados, storage_hours_range, params_economicos):
    """
    Ejecuta la simulación principal CSP variando las horas de almacenamiento
    para los países seleccionados.
    Devuelve un DataFrame con los resultados.
    """
    results_all = []
    print(f"CSP Main Sim: Paises={paises_seleccionados}, Storage={storage_hours_range}, Econ={params_economicos}")

    for pais_info in paises_seleccionados: # Recibe la lista de diccionarios de países a simular
        pais_nombre = pais_info["nombre"]
        archivo_solar = pais_info["archivo_solar"] # Usa la ruta ya construida
        print(f"  Procesando CSP principal para: {pais_nombre}...")

        resource_input = cargar_recurso_solar_csp(pais_nombre, archivo_solar)
        if resource_input is None:
             print(f"    Saltando simulación principal CSP para {pais_nombre} (error recurso solar).")
             continue

        for tshours in storage_hours_range:
            # print(f"    Simulando CSP con {tshours}h...")
            try:
                csp_model = TCSMS.default("MSPTSingleOwner")
                csp_model.SolarResource.assign(resource_input)
                csp_model.SystemDesign.assign({"tshours": float(tshours)}) # Asegurar float
                csp_model.execute()

                annual_energy = csp_model.Outputs.annual_energy
                total_installed_cost = csp_model.Outputs.total_installed_cost

                lcoe_model = Lcoefcr.default("GenericCSPSystemLCOECalculator")
                lcoe_model.SimpleLCOE.assign({
                    "annual_energy": annual_energy,
                    "capital_cost": total_installed_cost, # El costo de CSP se calcula internamente
                    "fixed_charge_rate": params_economicos["fixed_charge_rate"],
                    "fixed_operating_cost": params_economicos["fixed_operating_cost"],
                    "variable_operating_cost": params_economicos["variable_operating_cost"]
                })
                lcoe_model.execute()
                lcoe = lcoe_model.Outputs.lcoe_fcr
                # print(f"      CSP Res: Energía={annual_energy:.0f}, Costo=${total_installed_cost:,.0f}, LCOE={lcoe:.4f}")

                results_all.append({
                    'Pais': pais_nombre,
                    'Horas_almacenamiento': tshours,
                    'Generacion_energia_kWh': annual_energy,
                    'Costo_total_planta_$': total_installed_cost,
                    'LCOE_$/kWh': lcoe,
                    'Color': pais_info.get('color', 'gray') # Añadir color para graficar
                })

            except Exception as e:
                print(f"      ERROR CSP Simulación ({pais_nombre}, {tshours}h): {e}")
                results_all.append({
                    'Pais': pais_nombre, 'Horas_almacenamiento': tshours,
                    'Generacion_energia_kWh': np.nan, 'Costo_total_planta_$': np.nan,
                    'LCOE_$/kWh': np.nan, 'Color': pais_info.get('color', 'gray')
                })

    df_results = pd.DataFrame(results_all)
    # df_results.dropna(subset=['LCOE_$/kWh'], inplace=True) # No eliminar aquí, manejar NaNs al graficar
    print(f"CSP Main Sim: Finalizado. {len(df_results)} resultados generados.")
    return df_results


def ejecutar_sensibilidad_fcr_csp(paises_seleccionados, tshours_base, fcr_range, params_economicos):
    """
    Ejecuta el análisis de sensibilidad FCR para CSP.
    Devuelve un DataFrame con los resultados.
    """
    results_all = []
    print(f"CSP FCR Sens: Paises={paises_seleccionados}, TShours={tshours_base}, FCRs={fcr_range}, Econ={params_economicos}")

    for pais_info in paises_seleccionados:
        pais_nombre = pais_info["nombre"]
        archivo_solar = pais_info["archivo_solar"]
        print(f"  Procesando Sensibilidad FCR CSP para: {pais_nombre} ({tshours_base}h)... ")

        resource_input = cargar_recurso_solar_csp(pais_nombre, archivo_solar)
        if resource_input is None:
            print(f"    Saltando sensibilidad FCR CSP para {pais_nombre} (error recurso solar).")
            continue

        # Simular una vez para obtener energía y costo base
        base_annual_energy = np.nan
        base_total_cost = np.nan
        try:
            csp_model_base = TCSMS.default("MSPTSingleOwner")
            csp_model_base.SolarResource.assign(resource_input)
            csp_model_base.SystemDesign.assign({"tshours": float(tshours_base)})
            csp_model_base.execute()
            base_annual_energy = csp_model_base.Outputs.annual_energy
            base_total_cost = csp_model_base.Outputs.total_installed_cost
            # print(f"    Energía base CSP ({tshours_base}h): {base_annual_energy:.0f}, Costo base: ${base_total_cost:,.0f}")
        except Exception as e:
            print(f"    ERROR CSP al obtener base para sensibilidad FCR ({pais_nombre}): {e}.")
            # Continuar intentando calcular LCOE con FCRs si es posible (aunque energía/costo base sean NaN?)
            # Mejor saltar si la base falla catastróficamente
            continue


        for fcr in fcr_range:
            lcoe_sens = np.nan
            try:
                if not np.isnan(base_annual_energy) and base_annual_energy > 0:
                    lcoe_model_sens = Lcoefcr.default("GenericCSPSystemLCOECalculator")
                    lcoe_model_sens.SimpleLCOE.assign({
                        "annual_energy": base_annual_energy,
                        "capital_cost": base_total_cost,
                        "fixed_charge_rate": float(fcr), # Usar el FCR del loop
                        "fixed_operating_cost": params_economicos["fixed_operating_cost"],
                        "variable_operating_cost": params_economicos["variable_operating_cost"]
                    })
                    lcoe_model_sens.execute()
                    lcoe_sens = lcoe_model_sens.Outputs.lcoe_fcr
                    # print(f"      LCOE CSP (FCR={fcr:.3f}): {lcoe_sens:.4f}")
                else:
                     print(f"      Skipping LCOE calc for FCR={fcr:.3f} due to invalid base energy/cost")


            except Exception as e:
                print(f"      ERROR CSP calculando LCOE para FCR={fcr:.3f} ({pais_nombre}): {e}")
                lcoe_sens = np.nan # Asegurarse que es NaN si falla

            results_all.append({
                'Pais': pais_nombre,
                'Tasa_carga_fija': fcr,
                'Generacion_energia_kWh': base_annual_energy, # Mismo valor base para todas las FCR
                'Costo_total_planta_$': base_total_cost, # Mismo valor base
                'LCOE_$/kWh': lcoe_sens,
                'Color': pais_info.get('color', 'gray')
            })

    df_results = pd.DataFrame(results_all)
    print(f"CSP FCR Sens: Finalizado. {len(df_results)} resultados generados.")
    return df_results


def ejecutar_sensibilidad_multiplo_solar_csp(paises_seleccionados, tshours_base, solarm_range, params_economicos):
    """
    Ejecuta el análisis de sensibilidad del Múltiplo Solar para CSP.
    Devuelve un DataFrame con los resultados.
    """
    results_all = []
    fcr_base = params_economicos["fixed_charge_rate"] # Usar el FCR base para este análisis
    print(f"CSP SolarMult Sens: Paises={paises_seleccionados}, TShours={tshours_base}, SMs={solarm_range}, FCR={fcr_base}, Econ={params_economicos}")


    for pais_info in paises_seleccionados:
        pais_nombre = pais_info["nombre"]
        archivo_solar = pais_info["archivo_solar"]
        print(f"  Procesando Sensibilidad Múltiplo Solar CSP para: {pais_nombre} ({tshours_base}h, FCR={fcr_base})... ")

        resource_input = cargar_recurso_solar_csp(pais_nombre, archivo_solar)
        if resource_input is None:
            print(f"    Saltando sensibilidad Múltiplo Solar CSP para {pais_nombre} (error recurso solar).")
            continue

        for solarm in solarm_range:
            # print(f"    Simulando CSP con Múltiplo Solar = {solarm:.2f}...")
            annual_energy_solarm = np.nan
            total_installed_cost_solarm = np.nan
            lcoe_solarm = np.nan
            try:
                csp_model_solarm = TCSMS.default("MSPTSingleOwner")
                csp_model_solarm.SolarResource.assign(resource_input)
                # Pasar solarm aquí
                csp_model_solarm.SystemDesign.assign({"tshours": float(tshours_base), "solarm": float(solarm)})
                csp_model_solarm.execute()

                annual_energy_solarm = csp_model_solarm.Outputs.annual_energy
                total_installed_cost_solarm = csp_model_solarm.Outputs.total_installed_cost

                if not np.isnan(annual_energy_solarm) and annual_energy_solarm > 0:
                    lcoe_model_solarm = Lcoefcr.default("GenericCSPSystemLCOECalculator")
                    lcoe_model_solarm.SimpleLCOE.assign({
                        "annual_energy": annual_energy_solarm,
                        "capital_cost": total_installed_cost_solarm,
                        "fixed_charge_rate": fcr_base, # FCR fijo para este análisis
                        "fixed_operating_cost": params_economicos["fixed_operating_cost"],
                        "variable_operating_cost": params_economicos["variable_operating_cost"]
                    })
                    lcoe_model_solarm.execute()
                    lcoe_solarm = lcoe_model_solarm.Outputs.lcoe_fcr
                    # print(f"      CSP Res (SM={solarm:.2f}): Energía={annual_energy_solarm:.0f}, Costo=${total_installed_cost_solarm:,.0f}, LCOE={lcoe_solarm:.4f}")
                else:
                    print(f"      Skipping LCOE calc for SM={solarm:.2f} due to invalid energy/cost")


            except Exception as e:
                print(f"      ERROR CSP Simulación (Múltiplo Solar={solarm:.2f}, {pais_nombre}): {e}")
                # lcoe_solarm ya sería NaN

            results_all.append({
                'Pais': pais_nombre,
                'Multiplo_Solar': solarm,
                'Generacion_energia_kWh': annual_energy_solarm,
                'Costo_total_planta_$': total_installed_cost_solarm,
                'LCOE_$/kWh': lcoe_solarm,
                'Color': pais_info.get('color', 'gray')
            })

    df_results = pd.DataFrame(results_all)
    print(f"CSP SolarMult Sens: Finalizado. {len(df_results)} resultados generados.")
    return df_results


# --- Fin del Módulo CSP ---
# (Se eliminó configurar_entorno, generar_graficos_comparativos y el bloque if __name__ == '__main__')
