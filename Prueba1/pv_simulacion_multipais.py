#!/usr/bin/env python3
"""
Simulación de sistema fotovoltaico para múltiples países usando PySAM
Este script realiza simulaciones de sistemas fotovoltaicos para Chile, China y Sudáfrica
con diferentes capacidades de sistema
"""

import PySAM.Pvwattsv7 as pv
import PySAM.Lcoefcr as Lcoefcr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configuración de parámetros del sistema
# ---------------------------------------
# Lista de países y sus archivos de recursos solares
paises = {
    "Chile": "datos_Chile.csv",
    "China": "datos_China.csv",
    "Sudafrica": "datos_Sudafrica.csv"
}

# Capacidades del sistema a simular (en kW)
capacidades = [500, 1000, 50000, 100000, 500000]

# Parámetros técnicos y económicos base
dc_ac_ratio = 1.2                 # Ratio DC/AC
tilt = 20                         # Inclinación de los paneles en grados
azimuth = 180                     # Azimut en grados (180 = orientación sur)
array_type = 1                    # 1 = montaje sobre techo con rack
gcr = 0.4                         # Ground Coverage Ratio
inv_eff = 96                      # Eficiencia del inversor (%)
losses = 14.0                     # Pérdidas del sistema (%)

# Parámetros económicos base
fixed_charge_rate = 0.07          # Tasa de carga fija (%)
fixed_operating_cost_base = 50_000     # Costo operativo fijo anual base ($/año)
variable_operating_cost = 0.01    # Costo operativo variable ($/kWh)

def calcular_costo_capital(capacidad_kw):
    """Calcula el costo de capital basado en la capacidad del sistema"""
    # Costo por kW disminuye con el tamaño del sistema
    costo_base_por_kw = 1000  # $/kW para sistemas pequeños
    factor_escala = 0.9  # Factor de reducción por escala
    costo_por_kw = costo_base_por_kw * (factor_escala ** np.log10(capacidad_kw/1000))
    return capacidad_kw * costo_por_kw

def calcular_costo_operativo_fijo(capacidad_kw):
    """Calcula el costo operativo fijo basado en la capacidad del sistema"""
    return fixed_operating_cost_base * (capacidad_kw / 1000) ** 0.8

def crear_directorio_resultados(pais, capacidad_kw):
    """Crea el directorio de resultados para un país y capacidad específica"""
    directorio = f"Resultados_{pais}/Capacidad_{capacidad_kw/1000:.0f}MW"
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    return directorio

def simular_sistema_pv(pais, archivo_recurso, capacidad_kw):
    """Ejecuta la simulación del sistema fotovoltaico para un país y capacidad específica"""
    
    print(f"\n======== SIMULACIÓN PARA {pais} - {capacidad_kw/1000:.0f}MW ========")
    
    # Calcular costos específicos para esta capacidad
    capital_cost = calcular_costo_capital(capacidad_kw)
    fixed_operating_cost = calcular_costo_operativo_fijo(capacidad_kw)
    
    # Crear directorio de resultados
    directorio_resultados = crear_directorio_resultados(pais, capacidad_kw)
    
    # 1. Crear un modelo PVWatts
    print("Creando modelo PVWatts...")
    pv_model = pv.new()
    
    # 2. Asignar el archivo de recurso solar
    print(f"Usando archivo de recurso solar: {archivo_recurso}")
    pv_model.SolarResource.solar_resource_file = archivo_recurso
    
    # 3. Configurar los parámetros del sistema PV
    print("Configurando parámetros del sistema...")
    pv_model.SystemDesign.system_capacity = capacidad_kw
    pv_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
    pv_model.SystemDesign.array_type = array_type
    pv_model.SystemDesign.azimuth = azimuth
    pv_model.SystemDesign.tilt = tilt
    pv_model.SystemDesign.gcr = gcr
    pv_model.SystemDesign.inv_eff = inv_eff
    pv_model.SystemDesign.losses = losses
    
    # 4. Ejecutar la simulación PVWatts
    print("Ejecutando simulación PVWatts...")
    pv_model.execute()
    
    # 5. Obtener los resultados
    print("Obteniendo resultados de la simulación...")
    annual_energy = pv_model.Outputs.annual_energy
    print(f"Generación anual de energía PV: {annual_energy:,.2f} kWh")
    
    # 6. Calcular el LCOE
    lcoe = calcular_lcoe(annual_energy, capital_cost, fixed_operating_cost)
    
    # 7. Guardar resultados en CSV
    guardar_resultados(annual_energy, lcoe, directorio_resultados, pais, capacidad_kw, capital_cost, fixed_operating_cost)
    
    # 8. Visualizar resultados mensuales
    visualizar_resultados_mensuales(pv_model, directorio_resultados, pais, capacidad_kw)
    
    # 9. Realizar análisis de sensibilidad
    analisis_sensibilidad_tilt(pv_model, directorio_resultados, pais, capacidad_kw)
    
    return pv_model, annual_energy, lcoe

def calcular_lcoe(annual_energy, capital_cost, fixed_operating_cost):
    """Calcula el LCOE (Levelized Cost of Energy)"""
    
    print("Calculando LCOE...")
    # Crear el modelo para cálculo de LCOE
    lcoe_model = Lcoefcr.new()

    # Asignar valores para el cálculo del LCOE
    lcoe_model.SimpleLCOE.annual_energy = annual_energy
    lcoe_model.SimpleLCOE.capital_cost = capital_cost
    lcoe_model.SimpleLCOE.fixed_charge_rate = fixed_charge_rate
    lcoe_model.SimpleLCOE.fixed_operating_cost = fixed_operating_cost
    lcoe_model.SimpleLCOE.variable_operating_cost = variable_operating_cost
    
    # Ejecutar el cálculo del LCOE
    lcoe_model.execute()
    
    # Obtener el LCOE calculado
    lcoe = lcoe_model.Outputs.lcoe_fcr
    print(f"LCOE: {lcoe:,.4f} $/kWh")
    
    return lcoe

def guardar_resultados(annual_energy, lcoe, directorio, pais, capacidad_kw, capital_cost, fixed_operating_cost):
    """Guarda los resultados en un archivo CSV"""
    
    print("Guardando resultados en CSV...")
    # Crear un DataFrame con los resultados
    df_results = pd.DataFrame({
        "Pais": [pais],
        "Capacidad_MW": [capacidad_kw/1000],
        "Annual_Energy_kWh": [annual_energy],
        "Capital_Cost_$": [capital_cost],
        "Fixed_Charge_Rate": [fixed_charge_rate],
        "Fixed_Operating_Cost_$/yr": [fixed_operating_cost],
        "Variable_Operating_Cost_$/kWh": [variable_operating_cost],
        "LCOE_$/kWh": [lcoe]
    })
    
    # Guardar en CSV
    ruta_archivo = os.path.join(directorio, f"resultados_{pais.lower()}_{capacidad_kw/1000:.0f}MW.csv")
    df_results.to_csv(ruta_archivo, index=False)
    print(f"Resultados guardados en {ruta_archivo}")

def visualizar_resultados_mensuales(pv_model, directorio, pais, capacidad_kw):
    """Visualiza la generación mensual de energía"""
    
    try:
        # Obtener generación mensual
        monthly_energy = pv_model.Outputs.monthly_energy
        
        # Crear gráfico de barras
        plt.figure(figsize=(10, 6))
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        plt.bar(meses, monthly_energy)
        plt.title(f'Generación Mensual de Energía - {pais} - Sistema FV de {capacidad_kw/1000:.0f}MW')
        plt.xlabel('Mes')
        plt.ylabel('Energía (kWh)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Guardar gráfico
        ruta_grafico = os.path.join(directorio, f'generacion_mensual_{pais.lower()}_{capacidad_kw/1000:.0f}MW.png')
        plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
        print(f"Gráfico de generación mensual guardado como '{ruta_grafico}'")
        
        plt.close()
    except Exception as e:
        print(f"No se pudo generar el gráfico: {e}")

def analisis_sensibilidad_tilt(pv_model, directorio, pais, capacidad_kw):
    """Realiza un análisis de sensibilidad variando la inclinación"""
    
    print(f"\nRealizando análisis de sensibilidad para la inclinación de los paneles en {pais}...")
    inclinaciones = [0, 10, 20, 30, 40]
    energias = []
    
    for tilt_value in inclinaciones:
        # Crear modelo para cada inclinación
        test_model = pv.new()
        test_model.SolarResource.solar_resource_file = pv_model.SolarResource.solar_resource_file
        
        # Configurar parámetros
        test_model.SystemDesign.system_capacity = capacidad_kw
        test_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
        test_model.SystemDesign.array_type = array_type
        test_model.SystemDesign.azimuth = azimuth
        test_model.SystemDesign.tilt = tilt_value
        test_model.SystemDesign.gcr = gcr
        test_model.SystemDesign.inv_eff = inv_eff
        test_model.SystemDesign.losses = losses
        
        # Ejecutar simulación
        test_model.execute()
        
        # Obtener energía anual
        annual_energy = test_model.Outputs.annual_energy
        energias.append(annual_energy)
        print(f"  Inclinación: {tilt_value}°, Energía anual: {annual_energy:,.2f} kWh")
    
    # Crear gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(inclinaciones, energias, marker='o', linestyle='-', linewidth=2)
    plt.title(f'Análisis de sensibilidad - Inclinación de paneles - {pais} - {capacidad_kw/1000:.0f}MW')
    plt.xlabel('Inclinación (grados)')
    plt.ylabel('Energía anual (kWh)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Guardar gráfico
    ruta_grafico = os.path.join(directorio, f'analisis_inclinacion_{pais.lower()}_{capacidad_kw/1000:.0f}MW.png')
    plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
    print(f"Gráfico de análisis de sensibilidad guardado como '{ruta_grafico}'")
    
    plt.close()

def comparar_capacidades(resultados):
    """Compara los resultados entre diferentes capacidades y genera gráficos comparativos"""
    
    print("\nGenerando comparación entre capacidades...")
    
    # Crear directorio para comparaciones
    directorio_comparacion = "Comparacion_Capacidades"
    if not os.path.exists(directorio_comparacion):
        os.makedirs(directorio_comparacion)
    
    # Definir colores para cada país
    colores = {'Chile': 'b', 'China': 'g', 'Sudafrica': 'r'}
    
    # Crear un gráfico que combine todos los países para energía vs capacidad
    plt.figure(figsize=(12, 8))
    
    for pais in paises.keys():
        # Preparar datos para comparación
        capacidades_mw = []
        energias = []
        
        for capacidad_kw in capacidades:
            if pais in resultados and capacidad_kw in resultados[pais]:
                capacidades_mw.append(capacidad_kw/1000)
                energias.append(resultados[pais][capacidad_kw]['annual_energy'])
        
        # Agregar curva al gráfico de energía
        plt.plot(capacidades_mw, energias, 
                color=colores[pais],
                marker='o', 
                linestyle='-', 
                linewidth=2,
                label=pais)
    
    # Configurar el gráfico de energía
    plt.title('Generación Anual de Energía vs Capacidad - Comparación entre Países')
    plt.xlabel('Capacidad (MW)')
    plt.ylabel('Energía anual (kWh)')
    plt.grid(True, alpha=0.3)
    plt.legend(title='País', loc='best')
    plt.tight_layout()
    
    # Guardar el gráfico de energía
    ruta_grafico = os.path.join(directorio_comparacion, 'energia_vs_capacidad_combinado.png')
    plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
    print(f"Gráfico de energía vs capacidad combinado guardado como '{ruta_grafico}'")
    
    plt.close()
    
    # Crear un gráfico que combine todos los países para LCOE vs capacidad
    plt.figure(figsize=(12, 8))
    
    for pais in paises.keys():
        # Preparar datos para comparación
        capacidades_mw = []
        lcoes = []
        
        for capacidad_kw in capacidades:
            if pais in resultados and capacidad_kw in resultados[pais]:
                capacidades_mw.append(capacidad_kw/1000)
                lcoes.append(resultados[pais][capacidad_kw]['lcoe'])
        
        # Agregar curva al gráfico de LCOE
        plt.plot(capacidades_mw, lcoes, 
                color=colores[pais],
                marker='o', 
                linestyle='-', 
                linewidth=2,
                label=pais)
    
    # Configurar el gráfico de LCOE
    plt.title('LCOE vs Capacidad - Comparación entre Países')
    plt.xlabel('Capacidad (MW)')
    plt.ylabel('LCOE ($/kWh)')
    plt.grid(True, alpha=0.3)
    plt.legend(title='País', loc='best')
    plt.tight_layout()
    
    # Guardar el gráfico de LCOE
    ruta_grafico = os.path.join(directorio_comparacion, 'lcoe_vs_capacidad_combinado.png')
    plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
    print(f"Gráfico de LCOE vs capacidad combinado guardado como '{ruta_grafico}'")
    
    plt.close()
    
    print(f"Gráficos de comparación guardados en el directorio '{directorio_comparacion}'")

def grafico_sensibilidad_combinado(resultados):
    """Genera un gráfico combinado de sensibilidad de inclinación para todas las capacidades de cada país"""
    
    print("\nGenerando gráficos combinados de sensibilidad de inclinación...")
    
    # Crear directorio para gráficos combinados
    directorio_combinado = "Graficos_Sensibilidad_Combinados"
    if not os.path.exists(directorio_combinado):
        os.makedirs(directorio_combinado)
    
    inclinaciones = [0, 10, 20, 30, 40]
    
    for pais in paises.keys():
        plt.figure(figsize=(12, 8))
        
        # Crear un gráfico para cada capacidad
        for capacidad_kw in capacidades:
            if pais in resultados and capacidad_kw in resultados[pais]:
                # Obtener datos de sensibilidad para esta capacidad
                energias = []
                for tilt_value in inclinaciones:
                    # Crear modelo para cada inclinación
                    test_model = pv.new()
                    test_model.SolarResource.solar_resource_file = paises[pais]
                    
                    # Configurar parámetros
                    test_model.SystemDesign.system_capacity = capacidad_kw
                    test_model.SystemDesign.dc_ac_ratio = dc_ac_ratio
                    test_model.SystemDesign.array_type = array_type
                    test_model.SystemDesign.azimuth = azimuth
                    test_model.SystemDesign.tilt = tilt_value
                    test_model.SystemDesign.gcr = gcr
                    test_model.SystemDesign.inv_eff = inv_eff
                    test_model.SystemDesign.losses = losses
                    
                    # Ejecutar simulación
                    test_model.execute()
                    
                    # Obtener energía anual
                    annual_energy = test_model.Outputs.annual_energy
                    energias.append(annual_energy)
                
                # Agregar curva al gráfico
                plt.plot(inclinaciones, energias, marker='o', linestyle='-', linewidth=2,
                        label=f'{capacidad_kw/1000:.0f}MW')
        
        # Configurar el gráfico
        plt.title(f'Análisis de Sensibilidad - Inclinación de Paneles - {pais}')
        plt.xlabel('Inclinación (grados)')
        plt.ylabel('Energía anual (kWh)')
        plt.grid(True, alpha=0.3)
        plt.legend(title='Capacidad del Sistema', loc='best')
        plt.tight_layout()
        
        # Guardar el gráfico
        ruta_grafico = os.path.join(directorio_combinado, f'sensibilidad_combinada_{pais.lower()}.png')
        plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
        print(f"Gráfico de sensibilidad combinada guardado como '{ruta_grafico}'")
        
        plt.close()

if __name__ == "__main__":
    print("======== SIMULACIÓN DE SISTEMAS FOTOVOLTAICOS PARA MÚLTIPLES PAÍSES Y CAPACIDADES ========")
    
    resultados = {}
    
    # Simular para cada país y cada capacidad
    for pais, archivo in paises.items():
        resultados[pais] = {}
        for capacidad_kw in capacidades:
            modelo, annual_energy, lcoe = simular_sistema_pv(pais, archivo, capacidad_kw)
            resultados[pais][capacidad_kw] = {
                'annual_energy': annual_energy,
                'lcoe': lcoe
            }
    
    # Generar comparación entre capacidades
    comparar_capacidades(resultados)
    
    # Generar gráficos combinados de sensibilidad
    grafico_sensibilidad_combinado(resultados)
    
    print("\n======== SIMULACIONES COMPLETADAS ========")
    print("Los resultados se han guardado en los respectivos directorios de cada país y capacidad")
    print("y se ha generado una comparación general en el directorio 'Comparacion_Capacidades'")
    print("Los gráficos combinados de sensibilidad se han guardado en el directorio 'Graficos_Sensibilidad_Combinados'") 