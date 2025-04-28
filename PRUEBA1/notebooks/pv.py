import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr # Importar Lcoefcr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from mpl_toolkits.mplot3d import Axes3D # Importar Axes3D

# =============================================================================
# Función para Simulación Comparativa Energía Anual vs Capacidad
# =============================================================================
def simular_comparativa_energia_capacidad(paises, plantas, output_dir):
    """
    Realiza simulaciones PV para diferentes países y capacidades de planta,
    y genera un gráfico comparativo.
    """
    print("\n--- Iniciando Simulación Comparativa Energía Anual vs Capacidad ---")
    resultados_simulacion = [] # Lista para guardar todos los resultados

    # Iterar sobre cada país para la simulación comparativa
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        solar_resource_file = pais_info["archivo"]
        color_pais = pais_info["color"]

        # Determinar Azimut correcto para el país actual (para la comparativa)
        if pais_nombre in ["chile", "australia"]: # Hemisferio Sur
            azimuth_correcto = 0
        else: # Hemisferio Norte (España)
            azimuth_correcto = 180

        print(f"  Simulando para {pais_nombre.capitalize()} (Azimuth: {azimuth_correcto}°)...")

        for p in plantas:
            try:
                pv_model = pv.new()
                pv_model.SolarResource.solar_resource_file = solar_resource_file
                pv_model.SystemDesign.system_capacity = p["capacity_kw"]
                pv_model.SystemDesign.dc_ac_ratio = p["dc_ac_ratio"]
                pv_model.SystemDesign.array_type = 1
                pv_model.SystemDesign.azimuth = azimuth_correcto # Usar Azimut correcto
                pv_model.SystemDesign.tilt = p["tilt"]       # Tilt fijo (de la lista plantas) para la comparativa
                pv_model.SystemDesign.gcr = 0.4
                pv_model.SystemDesign.inv_eff = 96
                pv_model.SystemDesign.losses = 14.0
                pv_model.AdjustmentFactors.constant = 0 # Ajuste de pérdidas constantes

                # Ejecutar simulación
                pv_model.execute()

                # Obtener la energía anual [kWh]
                annual_energy = pv_model.Outputs.annual_energy

                # Guardar resultados en la lista general
                resultados_simulacion.append({
                    "pais": pais_nombre.capitalize(),
                    "capacidad_kw": p["capacity_kw"],
                    "energia_kwh": annual_energy,
                    "color": color_pais
                })
                # print(f"    - {p['nombre']}: {annual_energy:.2f} kWh") # Opcional: muy verboso

            except Exception as e:
                print(f"      Error simulando {p['nombre']} para {pais_nombre}: {e}")
                # Opcional: añadir marcador de error o saltar
                resultados_simulacion.append({
                    "pais": pais_nombre.capitalize(),
                    "capacidad_kw": p["capacity_kw"],
                    "energia_kwh": 0, # O np.nan
                    "color": color_pais
                })

    # Crear un único gráfico de línea con todos los resultados
    if resultados_simulacion:
        plt.figure(figsize=(10, 6))

        # Agrupar por país para asignar colores y leyendas
        paises_unicos = sorted(list(set(res["pais"] for res in resultados_simulacion))) # Ordenar países
        for pais in paises_unicos:
            # Filtrar datos para el país actual
            datos_pais = [res for res in resultados_simulacion if res["pais"] == pais]
            # Ordenar por capacidad para que la línea se dibuje correctamente
            datos_pais.sort(key=lambda x: x["capacidad_kw"])

            capacidades = [res["capacidad_kw"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"] # Obtener color del primer resultado

            plt.plot(capacidades, energias, label=pais, color=color, marker='o', linestyle='-', linewidth=2, markersize=6)

        plt.xlabel("Capacidad de Planta (kW)")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title("Energía Anual vs Capacidad de Planta por País")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0)) # Notación científica
        plt.tight_layout()

        # Guardar el gráfico
        output_filename = "pv_energia_vs_capacidad_all_countries.png"
        output_filepath = os.path.join(output_dir, output_filename)
        plt.savefig(output_filepath)
        print(f"\nGráfico comparativo Energía vs Capacidad guardado en: {output_filepath}")

        # Mostrar el gráfico antes de cerrarlo
        # plt.show() # Descomentar si se desea mostrar interactivamente
        plt.close()

    else:
        print("\nNo se generaron resultados para el gráfico Energía vs Capacidad.")

# =============================================================================
# Función para Análisis de Sensibilidad de Inclinación (Tilt)
# =============================================================================
def analizar_sensibilidad_inclinacion(paises, output_dir, config):
    """
    Realiza un análisis de sensibilidad variando la inclinación de los paneles
    para una configuración de planta fija en diferentes países.
    """
    print("\n--- Iniciando Análisis de Sensibilidad de Inclinación ---")

    # Parámetros fijos del diccionario de configuración
    sens_capacity_kw = config.get("capacity_kw", 1000.0)
    sens_dc_ac_ratio = config.get("dc_ac_ratio", 1.2)
    sens_gcr = config.get("gcr", 0.4)
    sens_inv_eff = config.get("inv_eff", 96)
    sens_losses = config.get("losses", 14.0)
    sens_adjust_constant = config.get("adjust_constant", 0)
    sens_array_type = config.get("array_type", 1)

    tilt_angles = np.arange(0, 91, 5) # Rango de inclinaciones
    tilt_sensitivity_results_all = [] # Lista para todos los resultados

    # Iterar sobre cada país
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        sens_solar_resource_file = pais_info["archivo"]
        color_pais = pais_info["color"]

        # Determinar Azimut correcto para el país actual
        if pais_nombre in ["chile", "australia"]: # Hemisferio Sur
            sens_azimuth = 0
        else: # Hemisferio Norte (España)
            sens_azimuth = 180

        print(f"  Calculando sensibilidad de inclinación para {pais_nombre.capitalize()} (Azimuth: {sens_azimuth}°)...")

        for tilt in tilt_angles:
            try:
                pv_sens_model = pv.new()
                pv_sens_model.SolarResource.solar_resource_file = sens_solar_resource_file
                pv_sens_model.SystemDesign.system_capacity = sens_capacity_kw
                pv_sens_model.SystemDesign.dc_ac_ratio = sens_dc_ac_ratio
                pv_sens_model.SystemDesign.array_type = sens_array_type
                pv_sens_model.SystemDesign.azimuth = sens_azimuth
                pv_sens_model.SystemDesign.tilt = float(tilt)
                pv_sens_model.SystemDesign.gcr = sens_gcr
                pv_sens_model.SystemDesign.inv_eff = sens_inv_eff
                pv_sens_model.SystemDesign.losses = sens_losses
                pv_sens_model.AdjustmentFactors.constant = sens_adjust_constant

                pv_sens_model.execute()
                annual_energy_tilt = pv_sens_model.Outputs.annual_energy

                tilt_sensitivity_results_all.append({
                    "pais": pais_nombre.capitalize(),
                    "tilt": tilt,
                    "energia_kwh": annual_energy_tilt,
                    "color": color_pais
                })
            except Exception as e:
                print(f"    Error en Tilt {tilt}° para {pais_nombre}: {e}")
                tilt_sensitivity_results_all.append({
                    "pais": pais_nombre.capitalize(), "tilt": tilt, "energia_kwh": 0, "color": color_pais
                })

    # Crear gráfico combinado de sensibilidad de inclinación
    if tilt_sensitivity_results_all:
        plt.figure(figsize=(10, 6))

        paises_sens_unicos = sorted(list(set(res["pais"] for res in tilt_sensitivity_results_all)))
        for pais in paises_sens_unicos:
            datos_pais = [res for res in tilt_sensitivity_results_all if res["pais"] == pais]
            datos_pais.sort(key=lambda x: x["tilt"])

            tilts = [res["tilt"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"]

            plt.plot(tilts, energias, marker='o', linestyle='-', color=color, label=pais, linewidth=2, markersize=5)

        plt.xlabel("Ángulo de Inclinación (grados)")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title(f"Sensibilidad Energía Anual a Inclinación ({sens_capacity_kw} kW)")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        plt.tight_layout()

        tilt_sens_filename = f"tilt_sensitivity_all_countries_{int(sens_capacity_kw)}kW.png"
        tilt_sens_filepath = os.path.join(output_dir, tilt_sens_filename)
        plt.savefig(tilt_sens_filepath)
        print(f"\nGráfico de sensibilidad de inclinación guardado en: {tilt_sens_filepath}")
        # plt.show()
        plt.close()
    else:
        print("\nNo se generaron resultados para el gráfico de sensibilidad de inclinación.")

# =============================================================================
# Función para Comparación de Azimut (0° vs 180°)
# =============================================================================
def comparar_azimut(paises, output_dir, config):
    """
    Compara la generación de energía anual para azimut 0° (Norte) y 180° (Sur)
    para una configuración de planta fija en diferentes países.
    """
    print("\n--- Iniciando Comparación de Azimut (0° vs 180°) ---")

    # Parámetros fijos del diccionario de configuración
    az_comp_capacity_kw = config.get("capacity_kw", 1000.0)
    az_comp_tilt = config.get("tilt", 20.0)
    az_comp_dc_ac_ratio = config.get("dc_ac_ratio", 1.2)
    az_comp_gcr = config.get("gcr", 0.4)
    az_comp_inv_eff = config.get("inv_eff", 96)
    az_comp_losses = config.get("losses", 14.0)
    az_comp_adjust_constant = config.get("adjust_constant", 0)
    az_comp_array_type = config.get("array_type", 1)
    azimuth_values = [0, 180]

    azimuth_comparison_results = []

    # Iterar sobre cada país y cada azimut
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        az_comp_solar_file = pais_info["archivo"]
        print(f"  Calculando comparación de azimut para {pais_nombre.capitalize()}...")

        for az in azimuth_values:
            try:
                pv_az_model = pv.new()
                pv_az_model.SolarResource.solar_resource_file = az_comp_solar_file
                pv_az_model.SystemDesign.system_capacity = az_comp_capacity_kw
                pv_az_model.SystemDesign.dc_ac_ratio = az_comp_dc_ac_ratio
                pv_az_model.SystemDesign.array_type = az_comp_array_type
                pv_az_model.SystemDesign.azimuth = float(az)
                pv_az_model.SystemDesign.tilt = az_comp_tilt
                pv_az_model.SystemDesign.gcr = az_comp_gcr
                pv_az_model.SystemDesign.inv_eff = az_comp_inv_eff
                pv_az_model.SystemDesign.losses = az_comp_losses
                pv_az_model.AdjustmentFactors.constant = az_comp_adjust_constant

                pv_az_model.execute()
                annual_energy_az = pv_az_model.Outputs.annual_energy

                azimuth_comparison_results.append({
                    "pais": pais_nombre.capitalize(),
                    "azimuth": az,
                    "energia_kwh": annual_energy_az
                })
                # print(f"    - Azimuth {az}°: {annual_energy_az:.2f} kWh") # Opcional
            except Exception as e:
                print(f"      Error en Azimuth {az}° para {pais_nombre}: {e}")
                azimuth_comparison_results.append({
                    "pais": pais_nombre.capitalize(), "azimuth": az, "energia_kwh": 0
                })

    # Crear gráfico de barras agrupadas
    if azimuth_comparison_results:
        df_az = pd.DataFrame(azimuth_comparison_results)
        pivot_df_az = df_az.pivot(index='pais', columns='azimuth', values='energia_kwh').sort_index() # Ordenar por país

        n_paises = len(pivot_df_az.index)
        bar_width = 0.35
        index = np.arange(n_paises)

        fig, ax = plt.subplots(figsize=(10, 6))
        bar1 = ax.bar(index - bar_width/2, pivot_df_az[0], bar_width, label='Azimut 0° (Norte)')
        bar2 = ax.bar(index + bar_width/2, pivot_df_az[180], bar_width, label='Azimut 180° (Sur)')

        ax.set_xlabel('País')
        ax.set_ylabel('Energía Anual Generada (kWh)')
        ax.set_title(f'Comparación Energía Anual por Azimut ({az_comp_capacity_kw} kW, Tilt {az_comp_tilt}°)')
        ax.set_xticks(index)
        ax.set_xticklabels(pivot_df_az.index)
        ax.legend()
        ax.grid(True, axis='y', linestyle='--')
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        fig.tight_layout()

        az_comp_filename = f"azimuth_comparison_{int(az_comp_capacity_kw)}kW_tilt{int(az_comp_tilt)}.png"
        az_comp_filepath = os.path.join(output_dir, az_comp_filename)
        plt.savefig(az_comp_filepath)
        print(f"\nGráfico de comparación de azimut guardado en: {az_comp_filepath}")
        # plt.show()
        plt.close()
    else:
        print("\nNo se generaron resultados para el gráfico de comparación de azimut.")

# =============================================================================
# Función para Análisis de Sensibilidad del Ratio DC/AC
# =============================================================================
def analizar_sensibilidad_dcac(paises, output_dir, config):
    """
    Realiza un análisis de sensibilidad variando el ratio DC/AC para una
    configuración de planta fija en diferentes países.
    """
    print("\n--- Iniciando Análisis de Sensibilidad del Ratio DC/AC ---")

    # Parámetros fijos del diccionario de configuración
    dcac_sens_capacity_kw = config.get("capacity_kw", 1000.0)
    dcac_sens_tilt = config.get("tilt", 20.0)
    dcac_sens_gcr = config.get("gcr", 0.4)
    dcac_sens_inv_eff = config.get("inv_eff", 96)
    dcac_sens_losses = config.get("losses", 14.0)
    dcac_sens_adjust_constant = config.get("adjust_constant", 0)
    dcac_sens_array_type = config.get("array_type", 1)

    dc_ac_ratios = np.arange(1.0, 2.01, 0.05) # Rango de ratios
    dcac_sensitivity_results = []

    # Iterar sobre cada país
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        dcac_sens_solar_file = pais_info["archivo"]
        color_pais = pais_info["color"]

        # Determinar Azimut correcto para el país actual
        if pais_nombre in ["chile", "australia"]: # Hemisferio Sur
            dcac_sens_azimuth = 0
        else: # Hemisferio Norte (España)
            dcac_sens_azimuth = 180

        print(f"  Calculando sensibilidad DC/AC para {pais_nombre.capitalize()} (Azimuth: {dcac_sens_azimuth}°)...")

        for ratio in dc_ac_ratios:
            try:
                pv_dcac_model = pv.new()
                pv_dcac_model.SolarResource.solar_resource_file = dcac_sens_solar_file
                pv_dcac_model.SystemDesign.system_capacity = dcac_sens_capacity_kw
                pv_dcac_model.SystemDesign.dc_ac_ratio = round(ratio, 2) # Usar ratio actual
                pv_dcac_model.SystemDesign.array_type = dcac_sens_array_type
                pv_dcac_model.SystemDesign.azimuth = dcac_sens_azimuth
                pv_dcac_model.SystemDesign.tilt = dcac_sens_tilt
                pv_dcac_model.SystemDesign.gcr = dcac_sens_gcr
                pv_dcac_model.SystemDesign.inv_eff = dcac_sens_inv_eff
                pv_dcac_model.SystemDesign.losses = dcac_sens_losses
                pv_dcac_model.AdjustmentFactors.constant = dcac_sens_adjust_constant

                pv_dcac_model.execute()
                annual_energy_dcac = pv_dcac_model.Outputs.annual_energy

                dcac_sensitivity_results.append({
                    "pais": pais_nombre.capitalize(),
                    "dc_ac_ratio": ratio,
                    "energia_kwh": annual_energy_dcac,
                    "color": color_pais
                })
            except Exception as e:
                print(f"      Error en Ratio DC/AC {ratio:.2f} para {pais_nombre}: {e}")
                dcac_sensitivity_results.append({
                    "pais": pais_nombre.capitalize(), "dc_ac_ratio": ratio, "energia_kwh": 0, "color": color_pais
                })

    # Crear gráfico combinado de sensibilidad DC/AC
    if dcac_sensitivity_results:
        plt.figure(figsize=(10, 7))

        paises_dcac_unicos = sorted(list(set(res["pais"] for res in dcac_sensitivity_results)))
        for pais in paises_dcac_unicos:
            datos_pais = [res for res in dcac_sensitivity_results if res["pais"] == pais]
            datos_pais.sort(key=lambda x: x["dc_ac_ratio"])

            ratios = [res["dc_ac_ratio"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"]

            plt.plot(ratios, energias, marker='.', linestyle='-', color=color, label=pais, linewidth=2, markersize=6)

            # Marcar el máximo
            if energias and max(energias) > 0:
                max_energia = max(energias)
                try:
                    max_index = energias.index(max_energia)
                    max_ratio = ratios[max_index]
                    plt.plot(max_ratio, max_energia, marker='*', color=color, markersize=12, linestyle='')
                    plt.annotate(f'{max_ratio:.2f}', (max_ratio, max_energia), textcoords="offset points",
                                 xytext=(0,10), ha='center', fontsize=9, color=color)
                except ValueError:
                     print(f"Advertencia: No se pudo encontrar el índice del máximo para {pais} en sensibilidad DC/AC")


        plt.xlabel("Ratio DC/AC")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title(f"Sensibilidad Energía Anual a Ratio DC/AC ({dcac_sens_capacity_kw} kW, Tilt {dcac_sens_tilt}°)")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        plt.tight_layout()

        dcac_sens_filename = f"dcac_sensitivity_all_countries_{int(dcac_sens_capacity_kw)}kW_tilt{int(dcac_sens_tilt)}.png"
        dcac_sens_filepath = os.path.join(output_dir, dcac_sens_filename)
        plt.savefig(dcac_sens_filepath)
        print(f"\nGráfico de sensibilidad DC/AC guardado en: {dcac_sens_filepath}")
        # plt.show()
        plt.close()
    else:
        print("\nNo se generaron resultados para el gráfico de sensibilidad DC/AC.")

# =============================================================================
# Función para Análisis de LCOE vs Fixed Charge Rate (FCR)
# =============================================================================
def analizar_lcoe_vs_fcr(paises, output_dir, config_lcoe):
    """
    Calcula y grafica el LCOE para diferentes tasas de carga fija (FCR)
    para una configuración de planta y país específicos.
    """
    print("\n--- Iniciando Análisis LCOE vs FCR ---")

    fcr_values_range = np.arange(0.01, 0.11, 0.01) # Rango de FCR a evaluar

    # Diccionario para guardar resultados por país
    lcoe_fcr_results = {pais["nombre"]: [] for pais in paises}
    fcr_values_plot = list(fcr_values_range)

    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        solar_resource_file = pais_info["archivo"]
        print(f"  Calculando LCOE vs FCR para {pais_nombre.capitalize()}...")

        # Parámetros fijos del sistema PV y económicos desde config
        capacity_kw = config_lcoe.get("capacity_kw", 1000.0)
        tilt = config_lcoe.get("tilt", 20.0)
        dc_ac_ratio = config_lcoe.get("dc_ac_ratio", 1.2)
        gcr = config_lcoe.get("gcr", 0.4)
        inv_eff = config_lcoe.get("inv_eff", 96)
        losses = config_lcoe.get("losses", 14.0)
        adjust_constant = config_lcoe.get("adjust_constant", 0)
        array_type = config_lcoe.get("array_type", 1)
        capital_cost = config_lcoe.get("capital_cost", 1_000_000)
        fixed_operating_cost = config_lcoe.get("fixed_operating_cost", 50_000)
        variable_operating_cost = config_lcoe.get("variable_operating_cost", 0.01)

        # Determinar Azimut correcto
        azimuth = 0 if pais_nombre in ["chile", "australia"] else 180

        try:
            # Calcular energía anual base una vez por país
            pv_model_base = pv.new()
            pv_model_base.SolarResource.solar_resource_file = solar_resource_file
            pv_model_base.SystemDesign.system_capacity = capacity_kw
            pv_model_base.SystemDesign.dc_ac_ratio = dc_ac_ratio
            pv_model_base.SystemDesign.array_type = array_type
            pv_model_base.SystemDesign.azimuth = azimuth
            pv_model_base.SystemDesign.tilt = tilt
            pv_model_base.SystemDesign.gcr = gcr
            pv_model_base.SystemDesign.inv_eff = inv_eff
            pv_model_base.SystemDesign.losses = losses
            pv_model_base.AdjustmentFactors.constant = adjust_constant
            pv_model_base.execute()
            annual_energy = pv_model_base.Outputs.annual_energy

            if annual_energy <= 0:
                print(f"    Advertencia: Energía anual es 0 para {pais_nombre}. Saltando análisis LCOE.")
                lcoe_fcr_results[pais_nombre] = [np.nan] * len(fcr_values_range) # Llenar con NaN
                continue

            temp_lcoe_results = []
            for fcr in fcr_values_range:
                lcoe_model = Lcoefcr.new()
                lcoe_model.SimpleLCOE.annual_energy = annual_energy
                lcoe_model.SimpleLCOE.capital_cost = capital_cost
                lcoe_model.SimpleLCOE.fixed_charge_rate = round(fcr, 2)
                lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_operating_cost
                lcoe_model.SimpleLCOE.variable_operating_cost = variable_operating_cost
                lcoe_model.execute()
                lcoe = lcoe_model.Outputs.lcoe_fcr
                temp_lcoe_results.append(lcoe)
            lcoe_fcr_results[pais_nombre] = temp_lcoe_results

        except Exception as e:
            print(f"    Error durante análisis LCOE vs FCR para {pais_nombre}: {e}")
            lcoe_fcr_results[pais_nombre] = [np.nan] * len(fcr_values_range) # Llenar con NaN

    # Graficar LCOE vs FCR para todos los países juntos
    plt.figure(figsize=(9, 6))
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        if pais_nombre in lcoe_fcr_results and lcoe_fcr_results[pais_nombre]:
            plt.plot(fcr_values_plot, lcoe_fcr_results[pais_nombre],
                     marker='o', linestyle='-', color=pais_info["color"],
                     label=pais_nombre.capitalize(), linewidth=2, markersize=5)

    plt.xlabel("Tasa de Carga Fija (Fixed Charge Rate)")
    plt.ylabel("LCOE ($/kWh)")
    plt.title(f"LCOE vs FCR por País ({int(config_lcoe.get('capacity_kw', 1000))} kW)")
    plt.legend(title="País")
    plt.grid(True, linestyle='--')
    plt.tight_layout()

    lcoe_filename = f"lcoe_vs_fcr_all_countries_{int(config_lcoe.get('capacity_kw', 1000))}kW.png"
    lcoe_filepath = os.path.join(output_dir, lcoe_filename)
    plt.savefig(lcoe_filepath)
    print(f"\nGráfico combinado LCOE vs FCR guardado en: {lcoe_filepath}")
    # plt.show()
    plt.close()

# =============================================================================
# Función para Análisis de Sensibilidad del LCOE
# =============================================================================
def analizar_sensibilidad_lcoe(paises, output_dir, config_base, sens_ranges):
    """
    Realiza un análisis de sensibilidad del LCOE variando parámetros clave.
    Genera un gráfico combinado por parámetro mostrando todos los países.
    """
    print("\n--- Iniciando Análisis de Sensibilidad del LCOE --- ")

    # Estructura para guardar resultados: {param_name: {pais_nombre: {values: [], lcoes: [], color: ''}}}
    lcoe_sens_by_param = {param: {} for param in sens_ranges.keys()}

    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        solar_resource_file = pais_info["archivo"]
        color_pais = pais_info["color"]
        print(f"  Calculando sensibilidad LCOE para {pais_nombre.capitalize()}...")

        # Determinar Azimut correcto
        azimuth = 0 if pais_nombre in ["chile", "australia"] else 180

        try:
            # Calcular energía anual base inicial (usando eficiencia base del inversor)
            pv_model_sens_base = pv.new()
            pv_model_sens_base.SolarResource.solar_resource_file = solar_resource_file
            pv_model_sens_base.SystemDesign.system_capacity = config_base.get("capacity_kw", 1000.0)
            pv_model_sens_base.SystemDesign.dc_ac_ratio = config_base.get("dc_ac_ratio", 1.2)
            pv_model_sens_base.SystemDesign.array_type = config_base.get("array_type", 1)
            pv_model_sens_base.SystemDesign.azimuth = azimuth
            pv_model_sens_base.SystemDesign.tilt = config_base.get("tilt", 20.0)
            pv_model_sens_base.SystemDesign.gcr = config_base.get("gcr", 0.4)
            pv_model_sens_base.SystemDesign.inv_eff = config_base.get("inv_eff", 96) # Usa eficiencia base
            pv_model_sens_base.SystemDesign.losses = config_base.get("losses", 14.0)
            pv_model_sens_base.AdjustmentFactors.constant = config_base.get("adjust_constant", 0)
            pv_model_sens_base.execute()
            annual_energy_base = pv_model_sens_base.Outputs.annual_energy

            if annual_energy_base <= 0:
                print(f"    Advertencia: Energía anual base es 0 para {pais_nombre}. Saltando sensibilidad LCOE.")
                continue

            # Iterar sobre cada parámetro sensible
            for param_name, param_range in sens_ranges.items():
                print(f"    - Sensibilidad a: {param_name}")
                lcoe_values_sens = []
                param_values_used = []

                for param_value in param_range:
                    current_config = config_base.copy()
                    current_annual_energy = annual_energy_base

                    # Actualizar el parámetro y recalcular energía si es inv_eff
                    if param_name == "inv_eff":
                        pv_model_temp = pv.new()
                        pv_model_temp.assign(pv_model_sens_base.export())
                        pv_model_temp.SystemDesign.inv_eff = float(param_value)
                        try:
                            pv_model_temp.execute()
                            current_annual_energy = pv_model_temp.Outputs.annual_energy
                            if current_annual_energy <= 0:
                                current_annual_energy = 1e-9 # Evitar div por cero
                        except Exception as pv_err:
                            print(f"      Error recalculando energía para inv_eff={param_value}: {pv_err}. Saltando.")
                            continue
                        current_config[param_name] = float(param_value)
                    # Actualizar otros parámetros económicos/FCR que están en la config base
                    elif param_name in current_config:
                         current_config[param_name] = param_value
                    # Manejar capital_cost que puede no estar explícitamente en config_base si se pasó de lcoe_config
                    elif param_name == 'capital_cost':
                         current_config['capital_cost'] = param_value
                    else:
                         print(f"     Advertencia: Parámetro {param_name} no manejado.")
                         continue

                    # Calcular LCOE
                    lcoe_model_sens = Lcoefcr.new()
                    lcoe_model_sens.SimpleLCOE.annual_energy = current_annual_energy
                    # Asegurarse de que todos los costos estén presentes
                    lcoe_model_sens.SimpleLCOE.capital_cost = current_config.get("capital_cost", 1_000_000)
                    lcoe_model_sens.SimpleLCOE.fixed_charge_rate = current_config.get("fixed_charge_rate", 0.07)
                    lcoe_model_sens.SimpleLCOE.fixed_operating_cost = current_config.get("fixed_operating_cost", 50_000)
                    lcoe_model_sens.SimpleLCOE.variable_operating_cost = current_config.get("variable_operating_cost", 0.01)
                    lcoe_model_sens.execute()
                    lcoe = lcoe_model_sens.Outputs.lcoe_fcr
                    lcoe_values_sens.append(lcoe)
                    param_values_used.append(param_value)

                # Guardar resultados en estructura por parámetro
                if pais_nombre not in lcoe_sens_by_param[param_name]:
                     lcoe_sens_by_param[param_name][pais_nombre] = {}
                lcoe_sens_by_param[param_name][pais_nombre]["values"] = param_values_used
                lcoe_sens_by_param[param_name][pais_nombre]["lcoes"] = lcoe_values_sens
                lcoe_sens_by_param[param_name][pais_nombre]["color"] = color_pais

        except Exception as e:
            print(f"    Error general durante análisis LCOE sens para {pais_nombre}: {e}")

    # --- Graficar resultados de sensibilidad (UN GRÁFICO POR PARÁMETRO) --- 
    print("\n  Generando gráficos combinados de sensibilidad LCOE...")
    for param_name, country_data in lcoe_sens_by_param.items():
        if not country_data:
            continue
            
        plt.figure(figsize=(9, 6))
        all_empty = True
        for pais_nombre, data in country_data.items():
            if data.get("values") and data.get("lcoes"):
                all_empty=False
                plt.plot(data["values"], data["lcoes"], marker='o', linestyle='-',
                         color=data["color"], label=pais_nombre.capitalize(), 
                         linewidth=2, markersize=5)
            else:
                 print(f"    Advertencia: Faltan datos LCOE sens para {pais_nombre} en {param_name}.")
        
        if all_empty:
            print(f"    No hay datos válidos para graficar la sensibilidad a {param_name}")
            plt.close() # Cerrar figura vacía
            continue

        # Configurar títulos y etiquetas
        xlabel = param_name.replace("_", " ").title()
        if param_name == "inv_eff": xlabel = "Eficiencia Inversor (%)"
        elif param_name == "fixed_charge_rate": xlabel = "Tasa de Carga Fija (FCR)"
        elif param_name == "fixed_operating_cost": 
            xlabel = "Costo Operativo Fijo ($/año)"
            plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        elif param_name == "variable_operating_cost": xlabel = "Costo Operativo Variable ($/kWh)"
        elif param_name == "capital_cost":
            xlabel = "Costo Capital ($)"
            plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
            
        plt.xlabel(xlabel)
        plt.ylabel("LCOE ($/kWh)")
        plt.title(f"Sensibilidad LCOE a {xlabel}")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.tight_layout()

        # Guardar el gráfico
        sens_filename = f"lcoe_sensitivity_vs_{param_name}_all_countries.png"
        sens_filepath = os.path.join(output_dir, sens_filename)
        plt.savefig(sens_filepath)
        print(f"    Gráfico LCOE sens vs {param_name} guardado en: {sens_filepath}")
        # plt.show()
        plt.close()

# =============================================================================
# Función Principal (main)
# =============================================================================
def main():
    """
    Función principal que configura y prepara las diferentes simulaciones y análisis.
    Las llamadas a las funciones de análisis están comentadas para ejecución manual.
    """
    # --- Configuración General ---
    datos_base_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos"
    output_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/graficos/simulacion_pv"
    os.makedirs(output_dir, exist_ok=True) # Crear directorio de salida

    # Lista de países y sus archivos de recursos solares
    paises = [
        {"nombre": "australia", "archivo": os.path.join(datos_base_dir, "australia.csv"), "color": "deeppink"},
        {"nombre": "chile", "archivo": os.path.join(datos_base_dir, "chile.csv"), "color": "mediumpurple"},
        {"nombre": "espana", "archivo": os.path.join(datos_base_dir, "espana.csv"), "color": "turquoise"}
    ]

    # Conjunto de distintas "plantas" (configuraciones) para la simulación comparativa
    plantas = [
        {"nombre": "Planta 0.5 MW",  "capacity_kw": 500,   "dc_ac_ratio": 1.2, "tilt": 20},
        {"nombre": "Planta 1 MW",    "capacity_kw": 1000,  "dc_ac_ratio": 1.2, "tilt": 20},
        {"nombre": "Planta 2 MW",    "capacity_kw": 2000,  "dc_ac_ratio": 1.2, "tilt": 20},
        {"nombre": "Planta 5 MW",    "capacity_kw": 5000,  "dc_ac_ratio": 1.2, "tilt": 20},
        {"nombre": "Planta 10 MW",   "capacity_kw": 10000, "dc_ac_ratio": 1.2, "tilt": 20}
        # Azimuth se define dinámicamente en la función
    ]

    # Configuraciones para los análisis específicos
    config_sens_tilt = {
        "capacity_kw": 1000.0, "dc_ac_ratio": 1.2, "gcr": 0.4, "inv_eff": 96,
        "losses": 14.0, "adjust_constant": 0, "array_type": 1
    }
    config_azimut = {
        "capacity_kw": 1000.0, "tilt": 20.0, "dc_ac_ratio": 1.2, "gcr": 0.4,
        "inv_eff": 96, "losses": 14.0, "adjust_constant": 0, "array_type": 1
    }
    config_dcac = {
        "capacity_kw": 1000.0, "tilt": 20.0, "gcr": 0.4, "inv_eff": 96,
        "losses": 14.0, "adjust_constant": 0, "array_type": 1
    }
    # Configuración para el análisis LCOE vs FCR
    config_lcoe_base = {
        "capacity_kw": 1000.0, "tilt": 20.0, "dc_ac_ratio": 1.2,
        "gcr": 0.4, "inv_eff": 96, "losses": 14.0, "adjust_constant": 0, "array_type": 1,
        "capital_cost": 1_000_000, "fixed_operating_cost": 50_000,
        "variable_operating_cost": 0.01, "fixed_charge_rate": 0.07 # FCR base
    }
    # Rangos para sensibilidad LCOE
    lcoe_sens_ranges = {
        "fixed_charge_rate": np.arange(0.01, 0.11, 0.01),
        "fixed_operating_cost": np.linspace(config_lcoe_base["fixed_operating_cost"] * 0.5, 
                                            config_lcoe_base["fixed_operating_cost"] * 1.5, 11),
        "variable_operating_cost": np.linspace(0.005, 0.015, 11),
        "inv_eff": np.arange(90, 99, 1),
        "capital_cost": np.linspace(config_lcoe_base["capital_cost"] * 0.7, 
                                       config_lcoe_base["capital_cost"] * 1.3, 11)
    }

    print("--- Configuración Cargada ---")
    print(f"Directorio de datos: {datos_base_dir}")
    print(f"Directorio de salida para gráficos: {output_dir}")
    print("Para ejecutar una sección, descomenta la llamada a la función correspondiente debajo.")

    # --- Ejecución Manual de las Secciones ---

    # print("\nPara ejecutar la Sección 1: Simulación Comparativa Energía Anual vs Capacidad, descomenta la línea siguiente:")
    # simular_comparativa_energia_capacidad(paises, plantas, output_dir)

    # print("\nPara ejecutar la Sección 2: Análisis de Sensibilidad de Inclinación, descomenta la línea siguiente:")
    # analizar_sensibilidad_inclinacion(paises, output_dir, config_sens_tilt)

    # print("\nPara ejecutar la Sección 3: Comparación de Azimut, descomenta la línea siguiente:")
    # comparar_azimut(paises, output_dir, config_azimut)

    # print("\nPara ejecutar la Sección 4: Análisis de Sensibilidad del Ratio DC/AC, descomenta la línea siguiente:")
    # analizar_sensibilidad_dcac(paises, output_dir, config_dcac)

    # print("\nPara ejecutar la Sección 5: Análisis LCOE vs FCR, descomenta la línea siguiente:")
    # analizar_lcoe_vs_fcr(paises, output_dir, config_lcoe_base)

    # print("\nPara ejecutar la Sección 6: Análisis de Sensibilidad del LCOE, descomenta la línea siguiente:")
    # analizar_sensibilidad_lcoe(paises, output_dir, config_lcoe_base, lcoe_sens_ranges)

    # --- Sección 5: Gráfico 3D (Ratio DC/AC, Energía, LCOE) --- <-- Eliminada
    # print("\n--- Iniciando Análisis para Gráfico 3D (España, Tilt 20°) ---") <-- Eliminada
    # ... todo el bloque 3D eliminado ...

    print("\n--- Fin de la configuración en main. Descomenta las funciones/bucles para ejecutarlas. ---")

# =============================================================================
# Punto de Entrada del Script
# =============================================================================
if __name__ == "__main__":
    # Llama a main() para configurar todo, pero las ejecuciones están comentadas dentro.
    main()