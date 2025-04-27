import PySAM.Pvwattsv7 as pv
# import PySAM.Lcoefcr as Lcoefcr # Importar Lcoefcr <-- Eliminado
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os # Importar el módulo os

def main():
    # Base de datos y directorio de salida
    datos_base_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/Datos"
    output_dir = "/home/nicole/proyecto/NicoleTorres/PRUEBA1/graficos/simulacion_pv"
    os.makedirs(output_dir, exist_ok=True) # Crear directorio de salida si no existe

    # --- Sección 1: Simulación comparativa por país y capacidad --- 
    print("--- Iniciando Simulación Comparativa Energía Anual ---")
    # Lista de países y sus archivos de recursos solares con nuevos colores
    paises = [
        {"nombre": "australia", "archivo": os.path.join(datos_base_dir, "australia.csv"), "color": "deeppink"},
        {"nombre": "chile", "archivo": os.path.join(datos_base_dir, "chile.csv"), "color": "mediumpurple"},
        {"nombre": "espana", "archivo": os.path.join(datos_base_dir, "espana.csv"), "color": "turquoise"}
    ]

    # Conjunto de distintas "plantas" (o configuraciones) para comparar
    plantas = [
        {"nombre": "Planta 0.5 MW",  "capacity_kw": 500,   "dc_ac_ratio": 1.2, "tilt": 20, "azimuth": 180},
        {"nombre": "Planta 1 MW",    "capacity_kw": 1000,  "dc_ac_ratio": 1.2, "tilt": 20, "azimuth": 180},
        {"nombre": "Planta 2 MW",    "capacity_kw": 2000,  "dc_ac_ratio": 1.2, "tilt": 20, "azimuth": 180},
        {"nombre": "Planta 5 MW",    "capacity_kw": 5000,  "dc_ac_ratio": 1.2, "tilt": 20, "azimuth": 180},
        {"nombre": "Planta 10 MW",   "capacity_kw": 10000, "dc_ac_ratio": 1.2, "tilt": 20, "azimuth": 180}
    ]

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

        print(f"\nSimulando Comparativa para {pais_nombre.capitalize()} (Azimuth: {azimuth_correcto}°)...")

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
                print(f"  - {p['nombre']}: {annual_energy:.2f} kWh")

            except Exception as e:
                print(f"Error simulando {p['nombre']} para {pais_nombre}: {e}")
                # Opcional: añadir marcador de error o saltar
                resultados_simulacion.append({
                    "pais": pais_nombre.capitalize(),
                    "capacidad_kw": p["capacity_kw"],
                    "energia_kwh": 0, # O np.nan
                    "color": color_pais
                })

    # Crear un único gráfico de dispersión con todos los resultados
    if resultados_simulacion:
        plt.figure(figsize=(10, 6))

        # Agrupar por país para asignar colores y leyendas
        paises_unicos = set(res["pais"] for res in resultados_simulacion)
        for pais in paises_unicos:
            # Filtrar datos para el país actual
            datos_pais = [res for res in resultados_simulacion if res["pais"] == pais]
            capacidades = [res["capacidad_kw"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"] # Obtener color del primer resultado (todos tienen el mismo)

            # Cambiado a plt.plot para conectar puntos y añadir marcador
            plt.plot(capacidades, energias, label=pais, color=color, marker='o', linestyle='-', linewidth=2, markersize=6)

        plt.xlabel("Capacidad de Planta (kW)")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title("Energía Anual vs Capacidad de Planta por País")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.tight_layout()

        # Guardar el gráfico de dispersión
        output_filename = "pv_scatter_all_countries.png"
        output_filepath = os.path.join(output_dir, output_filename)
        plt.savefig(output_filepath)
        plt.close()
        print(f"\nGráfico de dispersión guardado en: {output_filepath}")
    else:
        print("\nNo se generaron resultados para el gráfico de dispersión.")

    # --- Sección 2: Análisis de Sensibilidad de Inclinación (Tilt) --- 
    print("\n--- Iniciando Análisis de Sensibilidad de Inclinación (Todos los países, 1MW) ---")

    # Parámetros fijos para el análisis de sensibilidad (planta 1MW)
    sens_capacity_kw = 1000.0
    sens_dc_ac_ratio = 1.2
    # sens_azimuth = 180 # Azimuth ahora se define por país
    sens_gcr = 0.4
    sens_inv_eff = 96
    sens_losses = 14.0
    sens_adjust_constant = 0
    sens_array_type = 1 # Asumir tipo de array fijo para sensibilidad

    tilt_angles = np.arange(0, 91, 5) # Rango de inclinaciones más fino (pasos de 5 grados)
    tilt_sensitivity_results_all = [] # Lista para todos los resultados

    # Iterar sobre cada país para el análisis de sensibilidad
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        sens_solar_resource_file = pais_info["archivo"]
        color_pais = pais_info["color"]
        
        # Determinar Azimut correcto para el país actual
        if pais_nombre in ["chile", "australia"]: # Hemisferio Sur
            sens_azimuth = 0
        else: # Hemisferio Norte (España)
            sens_azimuth = 180
        
        print(f"  Calculando sensibilidad para {pais_nombre.capitalize()} (Azimuth: {sens_azimuth}°)...")

        # resultados_pais_tilt = [] # No es necesario si se guardan en lista general
        for tilt in tilt_angles:
            try:
                # Crear modelo PVWatts para esta inclinación y país
                pv_sens_model = pv.new()
                pv_sens_model.SolarResource.solar_resource_file = sens_solar_resource_file
                
                # Configurar parámetros
                pv_sens_model.SystemDesign.system_capacity = sens_capacity_kw
                pv_sens_model.SystemDesign.dc_ac_ratio = sens_dc_ac_ratio
                pv_sens_model.SystemDesign.array_type = sens_array_type # Usar parámetro definido
                pv_sens_model.SystemDesign.azimuth = sens_azimuth # Usar Azimut correcto
                pv_sens_model.SystemDesign.tilt = float(tilt)
                pv_sens_model.SystemDesign.gcr = sens_gcr
                pv_sens_model.SystemDesign.inv_eff = sens_inv_eff
                pv_sens_model.SystemDesign.losses = sens_losses
                pv_sens_model.AdjustmentFactors.constant = sens_adjust_constant

                # Ejecutar simulación
                pv_sens_model.execute()
                annual_energy_tilt = pv_sens_model.Outputs.annual_energy
                
                # Guardar resultado específico
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

    # Crear un único gráfico de sensibilidad de inclinación para todos los países
    if tilt_sensitivity_results_all:
        plt.figure(figsize=(10, 6))

        paises_sens_unicos = set(res["pais"] for res in tilt_sensitivity_results_all)
        for pais in paises_sens_unicos:
            # Filtrar datos para el país actual
            datos_pais = [res for res in tilt_sensitivity_results_all if res["pais"] == pais]
            # Ordenar por inclinación para que la línea se dibuje correctamente
            datos_pais.sort(key=lambda x: x["tilt"])
            
            tilts = [res["tilt"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"] # Asumiendo que el color es consistente por país

            plt.plot(tilts, energias, marker='o', linestyle='-', color=color, label=pais, linewidth=2, markersize=6)

        plt.xlabel("Ángulo de Inclinación (grados)")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title(f"Sensibilidad Energía Anual a Inclinación por País ({sens_capacity_kw} kW)")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.tight_layout()

        # Guardar el gráfico combinado de sensibilidad
        tilt_sens_filename = f"tilt_sensitivity_all_countries_{int(sens_capacity_kw)}kW.png"
        tilt_sens_filepath = os.path.join(output_dir, tilt_sens_filename)
        plt.savefig(tilt_sens_filepath)
        plt.close()
        print(f"\nGráfico combinado de sensibilidad de inclinación guardado en: {tilt_sens_filepath}")
    else:
        print("\nNo se generaron resultados para el gráfico de sensibilidad de inclinación.")

    # --- Sección 3: Comparación de Azimut 0° vs 180° --- 
    print("\n--- Iniciando Comparación de Azimut (Todos los países, 1MW, Tilt 20°) ---")

    # Parámetros fijos para la comparación de azimut
    az_comp_capacity_kw = 1000.0
    az_comp_tilt = 20.0 # Inclinación fija para esta comparación
    az_comp_dc_ac_ratio = 1.2
    az_comp_gcr = 0.4
    az_comp_inv_eff = 96
    az_comp_losses = 14.0
    az_comp_adjust_constant = 0
    az_comp_array_type = 1
    azimuth_values = [0, 180]

    azimuth_comparison_results = []

    # Iterar sobre cada país y cada azimut
    for pais_info in paises:
        pais_nombre = pais_info["nombre"]
        az_comp_solar_file = pais_info["archivo"]
        print(f"  Calculando comparación de azimut para {pais_nombre.capitalize()}...")

        for az in azimuth_values:
            try:
                # Crear modelo PVWatts
                pv_az_model = pv.new()
                pv_az_model.SolarResource.solar_resource_file = az_comp_solar_file
                
                # Configurar parámetros
                pv_az_model.SystemDesign.system_capacity = az_comp_capacity_kw
                pv_az_model.SystemDesign.dc_ac_ratio = az_comp_dc_ac_ratio
                pv_az_model.SystemDesign.array_type = az_comp_array_type
                pv_az_model.SystemDesign.azimuth = float(az) # Azimut actual
                pv_az_model.SystemDesign.tilt = az_comp_tilt # Tilt fijo
                pv_az_model.SystemDesign.gcr = az_comp_gcr
                pv_az_model.SystemDesign.inv_eff = az_comp_inv_eff
                pv_az_model.SystemDesign.losses = az_comp_losses
                pv_az_model.AdjustmentFactors.constant = az_comp_adjust_constant

                # Ejecutar simulación
                pv_az_model.execute()
                annual_energy_az = pv_az_model.Outputs.annual_energy
                
                # Guardar resultado
                azimuth_comparison_results.append({
                    "pais": pais_nombre.capitalize(),
                    "azimuth": az,
                    "energia_kwh": annual_energy_az
                })
                print(f"    - Azimuth {az}°: {annual_energy_az:.2f} kWh")
            except Exception as e:
                print(f"      Error en Azimuth {az}° para {pais_nombre}: {e}")
                azimuth_comparison_results.append({
                    "pais": pais_nombre.capitalize(), "azimuth": az, "energia_kwh": 0
                })

    # Crear gráfico de barras agrupadas para comparación de azimut
    if azimuth_comparison_results:
        # Preparar datos para el gráfico
        df_az = pd.DataFrame(azimuth_comparison_results)
        pivot_df_az = df_az.pivot(index='pais', columns='azimuth', values='energia_kwh')
        
        # Configuración del gráfico
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
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0)) # Notación científica para eje Y

        fig.tight_layout()

        # Guardar el gráfico
        az_comp_filename = f"azimuth_comparison_{int(az_comp_capacity_kw)}kW_tilt{int(az_comp_tilt)}.png"
        az_comp_filepath = os.path.join(output_dir, az_comp_filename)
        plt.savefig(az_comp_filepath)
        plt.close()
        print(f"\nGráfico de comparación de azimut guardado en: {az_comp_filepath}")
    else:
        print("\nNo se generaron resultados para el gráfico de comparación de azimut.")

    # --- Sección 4: Análisis de Sensibilidad del Ratio DC/AC --- 
    print("\n--- Iniciando Análisis de Sensibilidad del Ratio DC/AC (Todos los países, 1MW, Tilt 20°) ---")

    # Parámetros fijos para el análisis de sensibilidad DC/AC
    dcac_sens_capacity_kw = 1000.0
    dcac_sens_tilt = 20.0
    # Azimut se determinará por país
    dcac_sens_gcr = 0.4
    dcac_sens_inv_eff = 96
    dcac_sens_losses = 14.0
    dcac_sens_adjust_constant = 0
    dcac_sens_array_type = 1

    dc_ac_ratios = np.arange(1.0, 2.01, 0.05) # Rango: 1.0, 1.05, ..., 2.0 (Paso cambiado a 0.05)
    dcac_sensitivity_results = []

    # Iterar sobre cada país para el análisis de sensibilidad DC/AC
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
                # Crear modelo PVWatts
                pv_dcac_model = pv.new()
                pv_dcac_model.SolarResource.solar_resource_file = dcac_sens_solar_file
                
                # Configurar parámetros
                pv_dcac_model.SystemDesign.system_capacity = dcac_sens_capacity_kw
                pv_dcac_model.SystemDesign.dc_ac_ratio = round(ratio, 2) # Usar ratio actual, redondear por precisión float
                pv_dcac_model.SystemDesign.array_type = dcac_sens_array_type
                pv_dcac_model.SystemDesign.azimuth = dcac_sens_azimuth
                pv_dcac_model.SystemDesign.tilt = dcac_sens_tilt
                pv_dcac_model.SystemDesign.gcr = dcac_sens_gcr
                pv_dcac_model.SystemDesign.inv_eff = dcac_sens_inv_eff
                pv_dcac_model.SystemDesign.losses = dcac_sens_losses
                pv_dcac_model.AdjustmentFactors.constant = dcac_sens_adjust_constant

                # Ejecutar simulación
                pv_dcac_model.execute()
                annual_energy_dcac = pv_dcac_model.Outputs.annual_energy
                
                # Guardar resultado
                dcac_sensitivity_results.append({
                    "pais": pais_nombre.capitalize(),
                    "dc_ac_ratio": ratio,
                    "energia_kwh": annual_energy_dcac,
                    "color": color_pais
                })
                # print(f"    - Ratio DC/AC {ratio:.1f}: {annual_energy_dcac:.2f} kWh") # Opcional: muy verboso
            except Exception as e:
                print(f"      Error en Ratio DC/AC {ratio:.1f} para {pais_nombre}: {e}")
                dcac_sensitivity_results.append({
                    "pais": pais_nombre.capitalize(), "dc_ac_ratio": ratio, "energia_kwh": 0, "color": color_pais
                })

    # Crear un único gráfico de sensibilidad de ratio DC/AC para todos los países
    if dcac_sensitivity_results:
        plt.figure(figsize=(10, 7)) # Ajustar tamaño si es necesario para anotaciones

        paises_dcac_unicos = set(res["pais"] for res in dcac_sensitivity_results)
        for pais in paises_dcac_unicos:
            # Filtrar y ordenar datos
            datos_pais = [res for res in dcac_sensitivity_results if res["pais"] == pais]
            datos_pais.sort(key=lambda x: x["dc_ac_ratio"])
            
            ratios = [res["dc_ac_ratio"] for res in datos_pais]
            energias = [res["energia_kwh"] for res in datos_pais]
            color = datos_pais[0]["color"]

            # Graficar la línea
            plt.plot(ratios, energias, marker='.', linestyle='-', color=color, label=pais, linewidth=2, markersize=6)

            # Encontrar y marcar el máximo
            if energias and max(energias) > 0: 
                max_energia = max(energias)
                # Encontrar el primer índice del máximo
                try: # Usar try-except por si energias no es lista estándar (aunque debería serlo)
                    max_index = energias.index(max_energia)
                    max_ratio = ratios[max_index]

                    # Añadir un marcador de estrella en el máximo
                    plt.plot(max_ratio, max_energia, marker='*', color=color, markersize=12, linestyle='') 
                    
                    # Añadir anotación de texto con el valor del ratio
                    plt.annotate(f'{max_ratio:.2f}', 
                                 (max_ratio, max_energia),
                                 textcoords="offset points", 
                                 xytext=(0,10), # Desplazamiento vertical pequeño
                                 ha='center', 
                                 fontsize=9,
                                 color=color)
                except ValueError:
                    print(f"Advertencia: No se pudo encontrar el índice del máximo para {pais}")

        plt.xlabel("Ratio DC/AC")
        plt.ylabel("Energía Anual Generada (kWh)")
        plt.title(f"Sensibilidad Energía Anual a Ratio DC/AC por País ({dcac_sens_capacity_kw} kW, Tilt {dcac_sens_tilt}°)")
        plt.legend(title="País")
        plt.grid(True, linestyle='--')
        plt.tight_layout()

        # Guardar el gráfico combinado de sensibilidad
        dcac_sens_filename = f"dcac_sensitivity_all_countries_{int(dcac_sens_capacity_kw)}kW.png"
        dcac_sens_filepath = os.path.join(output_dir, dcac_sens_filename)
        plt.savefig(dcac_sens_filepath)
        plt.close()
        print(f"\nGráfico combinado de sensibilidad DC/AC guardado en: {dcac_sens_filepath}")
    else:
        print("\nNo se generaron resultados para el gráfico de sensibilidad DC/AC.")

if __name__ == "__main__":
    main() 