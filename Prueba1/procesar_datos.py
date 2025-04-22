import polars as pl
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import os

# Definir los pares de archivos por ubicación
ubicaciones = {
    'Sudafrica': {
        'lat': -29.19,
        'lon': 21.30,
        'elev': 0,  # Elevación por defecto
        'tz': 2,    # Zona horaria por defecto
        'archivos': ['1155731_-29.19_21.30_2018.csv', '1155731_-29.19_21.30_2019.csv']
    },
    'China': {
        'lat': 44.73,
        'lon': 87.66,
        'elev': 0,
        'tz': 8,
        'archivos': ['3480150_44.73_87.66_2018.csv', '3480150_44.73_87.66_2018.csv']
    },
    'Chile': {
        'lat': -23.84,
        'lon': -69.89,
        'elev': 735,  # Elevación real de Chile
        'tz': -4,
        'archivos': ['5815755_-23.84_-69.89_2018.csv', '5815755_-23.84_-69.89_2019.csv']
    }
}

def analizar_irradiacion_anual(df):
    """Analiza la irradiación anual por tipo"""
    resultados = {
        'GHI': {
            'promedio': float(df.select(pl.col('GHI').mean())[0,0]),
            'maximo': float(df.select(pl.col('GHI').max())[0,0]),
            'minimo': float(df.select(pl.col('GHI').min())[0,0]),
            'total': float(df.select(pl.col('GHI').sum())[0,0])
        },
        'DHI': {
            'promedio': float(df.select(pl.col('DHI').mean())[0,0]),
            'maximo': float(df.select(pl.col('DHI').max())[0,0]),
            'minimo': float(df.select(pl.col('DHI').min())[0,0]),
            'total': float(df.select(pl.col('DHI').sum())[0,0])
        },
        'DNI': {
            'promedio': float(df.select(pl.col('DNI').mean())[0,0]),
            'maximo': float(df.select(pl.col('DNI').max())[0,0]),
            'minimo': float(df.select(pl.col('DNI').min())[0,0]),
            'total': float(df.select(pl.col('DNI').sum())[0,0])
        }
    }
    return resultados

def analizar_irradiacion_mensual(df):
    """Analiza la irradiación mensual"""
    mensual = df.group_by('Month').agg(
        pl.col('GHI').mean().alias('GHI_promedio'),
        pl.col('DHI').mean().alias('DHI_promedio'),
        pl.col('DNI').mean().alias('DNI_promedio')
    ).sort('Month')
    return mensual

def crear_graficos(df, resultados_anuales, resultados_mensuales, ubicacion):
    """Crea los gráficos de análisis para una ubicación específica"""
    # Crear directorio de resultados si no existe
    os.makedirs('resultados', exist_ok=True)
    
    # 1. Gráfico de irradiación diaria promedio por mes
    plt.figure(figsize=(12, 6))
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    plt.plot(meses, resultados_mensuales['GHI_promedio'], label='GHI', marker='o')
    plt.plot(meses, resultados_mensuales['DHI_promedio'], label='DHI', marker='s')
    plt.plot(meses, resultados_mensuales['DNI_promedio'], label='DNI', marker='^')
    
    plt.xlabel('Mes')
    plt.ylabel('Irradiancia Promedio (W/m²)')
    plt.title(f'Irradiancia Promedio Mensual en {ubicacion}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'resultados/irradiacion_mensual_{ubicacion}.png')
    plt.close()
    
    # 2. Gráfico de distribución horaria
    horaria = df.group_by('Hour').agg(
        pl.col('GHI').mean().alias('GHI_promedio'),
        pl.col('DHI').mean().alias('DHI_promedio'),
        pl.col('DNI').mean().alias('DNI_promedio')
    ).sort('Hour')
    
    plt.figure(figsize=(12, 6))
    horas = range(24)
    
    plt.plot(horas, horaria['GHI_promedio'], label='GHI', marker='o')
    plt.plot(horas, horaria['DHI_promedio'], label='DHI', marker='s')
    plt.plot(horas, horaria['DNI_promedio'], label='DNI', marker='^')
    
    plt.xticks(range(0, 24, 1))
    plt.gca().set_xticklabels([f'{h:02d}:00' for h in range(24)])
    plt.xlabel('Hora del día (24h)')
    plt.ylabel('Irradiancia Promedio (W/m²)')
    plt.title(f'Distribución Horaria de la Irradiancia en {ubicacion}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'resultados/distribucion_horaria_{ubicacion}.png')
    plt.close()

# Procesar cada ubicación
for id_ubicacion, info in ubicaciones.items():
    print(f"\nProcesando ubicación {id_ubicacion} ({info['lat']}, {info['lon']})")
    
    # Lista para almacenar los DataFrames de cada año
    dfs = []
    
    # Procesar cada archivo de la ubicación
    for archivo in info['archivos']:
        # Leer el archivo CSV, saltando las primeras 2 filas que contienen metadatos
        df = pl.read_csv(archivo, skip_rows=2)
        
        # Seleccionar solo las columnas necesarias para PySAM
        df = df.select([
            pl.col('Year'),
            pl.col('Month'),
            pl.col('Day'),
            pl.col('Hour'),
            pl.col('Minute'),
            pl.col('DNI'),
            pl.col('GHI'),
            pl.col('DHI')
        ])
        
        # Agregar el DataFrame a la lista
        dfs.append(df)
    
    # Combinar los DataFrames de los dos años
    df_final = pl.concat(dfs)
    
    # Ordenar por fecha y hora
    df_final = df_final.sort(['Year', 'Month', 'Day', 'Hour', 'Minute'])
    
    # Realizar análisis de irradiación
    print(f"\nAnalizando irradiación para {id_ubicacion}...")
    resultados_anuales = analizar_irradiacion_anual(df_final)
    resultados_mensuales = analizar_irradiacion_mensual(df_final)
    
    # Crear gráficos
    print(f"Generando gráficos para {id_ubicacion}...")
    crear_graficos(df_final, resultados_anuales, resultados_mensuales, id_ubicacion)
    
    # Imprimir resultados
    print(f"\nResultados del análisis para {id_ubicacion}:")
    for tipo in ['GHI', 'DHI', 'DNI']:
        print(f"\n{tipo}:")
        print(f"  Promedio: {resultados_anuales[tipo]['promedio']:.2f} W/m²")
        print(f"  Máximo: {resultados_anuales[tipo]['maximo']:.2f} W/m²")
        print(f"  Mínimo: {resultados_anuales[tipo]['minimo']:.2f} W/m²")
        print(f"  Total anual: {resultados_anuales[tipo]['total']/1000:.2f} kWh/m²")
    
    # Crear el archivo de salida con el formato PySAM
    nombre_archivo = f'datos_{id_ubicacion}.csv'
    
    # Escribir los metadatos y los datos en un solo paso
    with open(nombre_archivo, 'w') as f:
        # Escribir metadatos en formato PySAM
        f.write(f"# Source: Solar Data for {id_ubicacion}\n")
        f.write(f"# Location: {id_ubicacion}\n")
        f.write(f"# Lat: {info['lat']}\n")
        f.write(f"# Lon: {info['lon']}\n")
        f.write(f"# Elev: {info['elev']}\n")
        f.write(f"# Time Zone: {info['tz']}\n")
        f.write(f"# Local Time Zone: {info['tz']}\n")
        f.write(f"# Data Format: TMY3\n\n")
        
        # Escribir encabezados y datos
        df_final.write_csv(f)
    
    print(f"\nLos datos han sido guardados en '{nombre_archivo}' en formato PySAM")
    print(f"Los gráficos se han guardado en el directorio 'resultados'")

print("\nProcesamiento completado para todas las ubicaciones") 