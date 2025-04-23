#!/usr/bin/env python3
"""
Simulación de sistema fotovoltaico para múltiples países usando PySAM
Este script realiza simulaciones de sistemas fotovoltaicos para Chile, China y Sudáfrica
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

# Parámetros técnicos y económicos
system_capacity_kw = 1000.0       # Capacidad del sistema en kW
dc_ac_ratio = 1.2                 # Ratio DC/AC
tilt = 20                         # Inclinación de los paneles en grados
azimuth = 180                     # Azimut en grados (180 = orientación sur)
array_type = 1                    # 1 = montaje sobre techo con rack
gcr = 0.4                         # Ground Coverage Ratio
inv_eff = 96                      # Eficiencia del inversor (%)
losses = 14.0                     # Pérdidas del sistema (%)

# Parámetros económicos
fixed_charge_rate = 0.07          # Tasa de carga fija (%)
capital_cost = 1_000_000          # Costo total de capital ($)
fixed_operating_cost = 50_000     # Costo operativo fijo anual ($/año)
variable_operating_cost = 0.01    # Costo operativo variable ($/kWh)

def crear_directorio_resultados(pais):
    """Crea el directorio de resultados para un país"""
    directorio = f"Resultados_{pais}"
    if not os.path.exists(directorio):
        os.makedirs(directorio)
    return directorio

def simular_sistema_pv(pais, archivo_recurso):
    """Ejecuta la simulación del sistema fotovoltaico para un país específico"""
    
    print(f"\n======== SIMULACIÓN PARA {pais} ========")
    
    # Crear directorio de resultados
    directorio_resultados = crear_directorio_resultados(pais)
    
    # 1. Crear un modelo PVWatts
    print("Creando modelo PVWatts...")
    pv_model = pv.new()
    
    # 2. Asignar el archivo de recurso solar
    print(f"Usando archivo de recurso solar: {archivo_recurso}")
    pv_model.SolarResource.solar_resource_file = archivo_recurso
    
    # 3. Configurar los parámetros del sistema PV
    print("Configurando parámetros del sistema...")
    pv_model.SystemDesign.system_capacity = system_capacity_kw
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
    lcoe = calcular_lcoe(annual_energy)
    
    # 7. Guardar resultados en CSV
    guardar_resultados(annual_energy, lcoe, directorio_resultados, pais)
    
    # 8. Visualizar resultados mensuales
    visualizar_resultados_mensuales(pv_model, directorio_resultados, pais)
    
    # 9. Realizar análisis de sensibilidad
    analisis_sensibilidad_tilt(pv_model, directorio_resultados, pais)
    
    return pv_model

def calcular_lcoe(annual_energy):
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

def guardar_resultados(annual_energy, lcoe, directorio, pais):
    """Guarda los resultados en un archivo CSV"""
    
    print("Guardando resultados en CSV...")
    # Crear un DataFrame con los resultados
    df_results = pd.DataFrame({
        "Pais": [pais],
        "System_Capacity_kW": [system_capacity_kw],
        "Annual_Energy_kWh": [annual_energy],
        "Capital_Cost_$": [capital_cost],
        "Fixed_Charge_Rate": [fixed_charge_rate],
        "Fixed_Operating_Cost_$/yr": [fixed_operating_cost],
        "Variable_Operating_Cost_$/kWh": [variable_operating_cost],
        "LCOE_$/kWh": [lcoe]
    })
    
    # Guardar en CSV
    ruta_archivo = os.path.join(directorio, f"resultados_{pais.lower()}.csv")
    df_results.to_csv(ruta_archivo, index=False)
    print(f"Resultados guardados en {ruta_archivo}")

def visualizar_resultados_mensuales(pv_model, directorio, pais):
    """Visualiza la generación mensual de energía"""
    
    try:
        # Obtener generación mensual
        monthly_energy = pv_model.Outputs.monthly_energy
        
        # Crear gráfico de barras
        plt.figure(figsize=(10, 6))
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        plt.bar(meses, monthly_energy)
        plt.title(f'Generación Mensual de Energía - {pais} - Sistema FV de {system_capacity_kw} kW')
        plt.xlabel('Mes')
        plt.ylabel('Energía (kWh)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Guardar gráfico
        ruta_grafico = os.path.join(directorio, f'generacion_mensual_{pais.lower()}.png')
        plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
        print(f"Gráfico de generación mensual guardado como '{ruta_grafico}'")
        
        plt.close()
    except Exception as e:
        print(f"No se pudo generar el gráfico: {e}")

def analisis_sensibilidad_tilt(pv_model, directorio, pais):
    """Realiza un análisis de sensibilidad variando la inclinación"""
    
    print(f"\nRealizando análisis de sensibilidad para la inclinación de los paneles en {pais}...")
    inclinaciones = [0, 10, 20, 30, 40]
    energias = []
    
    for tilt_value in inclinaciones:
        # Crear modelo para cada inclinación
        test_model = pv.new()
        test_model.SolarResource.solar_resource_file = pv_model.SolarResource.solar_resource_file
        
        # Configurar parámetros
        test_model.SystemDesign.system_capacity = system_capacity_kw
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
    plt.title(f'Análisis de sensibilidad - Inclinación de paneles - {pais}')
    plt.xlabel('Inclinación (grados)')
    plt.ylabel('Energía anual (kWh)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Guardar gráfico
    ruta_grafico = os.path.join(directorio, f'analisis_inclinacion_{pais.lower()}.png')
    plt.savefig(ruta_grafico, dpi=300, bbox_inches='tight')
    print(f"Gráfico de análisis de sensibilidad guardado como '{ruta_grafico}'")
    
    plt.close()

def comparar_paises(resultados):
    """Compara los resultados entre países y genera gráficos comparativos"""
    
    print("\nGenerando comparación entre países...")
    
    # Crear directorio para comparaciones
    directorio_comparacion = "Comparacion_Paises"
    if not os.path.exists(directorio_comparacion):
        os.makedirs(directorio_comparacion)
    
    # Preparar datos para comparación
    paises = []
    energias = []
    lcoes = []
    
    for pais, datos in resultados.items():
        paises.append(pais)
        energias.append(datos['annual_energy'])
        lcoes.append(datos['lcoe'])
    
    # Gráfico de comparación de energía anual
    plt.figure(figsize=(12, 6))
    plt.bar(paises, energias)
    plt.title('Comparación de Generación Anual de Energía por País')
    plt.xlabel('País')
    plt.ylabel('Energía anual (kWh)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(directorio_comparacion, 'comparacion_energia_anual.png'), dpi=300)
    plt.close()
    
    # Gráfico de comparación de LCOE
    plt.figure(figsize=(12, 6))
    plt.bar(paises, lcoes)
    plt.title('Comparación de LCOE por País')
    plt.xlabel('País')
    plt.ylabel('LCOE ($/kWh)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(directorio_comparacion, 'comparacion_lcoe.png'), dpi=300)
    plt.close()
    
    print(f"Gráficos de comparación guardados en el directorio '{directorio_comparacion}'")

if __name__ == "__main__":
    print("======== SIMULACIÓN DE SISTEMAS FOTOVOLTAICOS PARA MÚLTIPLES PAÍSES ========")
    
    resultados = {}
    
    # Simular para cada país
    for pais, archivo in paises.items():
        modelo = simular_sistema_pv(pais, archivo)
        resultados[pais] = {
            'annual_energy': modelo.Outputs.annual_energy,
            'lcoe': calcular_lcoe(modelo.Outputs.annual_energy)
        }
    
    # Generar comparación entre países
    comparar_paises(resultados)
    
    print("\n======== SIMULACIONES COMPLETADAS ========")
    print("Los resultados se han guardado en los respectivos directorios de cada país")
    print("y se ha generado una comparación general en el directorio 'Comparacion_Paises'") 