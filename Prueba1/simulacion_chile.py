import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

def cargar_datos_chile():
    """Carga los datos de irradiación de Chile"""
    with open('datos_Chile.csv', 'r') as f:
        # Saltamos las líneas de metadatos
        for _ in range(9):
            next(f)
        
        # Leer el resto del archivo con polars
        df = pl.read_csv(
            'datos_Chile.csv',
            skip_rows=9,
            schema_overrides={
                'Year': pl.Int64,
                'Month': pl.Int64,
                'Day': pl.Int64,
                'Hour': pl.Int64,
                'Minute': pl.Int64,
                'DNI': pl.Float64,
                'GHI': pl.Float64,
                'DHI': pl.Float64
            }
        )
    
    # Crear columna de fecha y hora
    df = df.with_columns(
        pl.datetime(
            pl.col("Year"),
            pl.col("Month"),
            pl.col("Day"),
            pl.col("Hour"),
            pl.col("Minute")
        ).alias("datetime")
    )
    
    return df

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
    # Agrupar por mes y calcular promedios
    mensual = df.group_by('Month').agg(
        pl.col('GHI').mean().alias('GHI_promedio'),
        pl.col('DHI').mean().alias('DHI_promedio'),
        pl.col('DNI').mean().alias('DNI_promedio')
    ).sort('Month')
    
    return mensual

def crear_graficos(df, resultados_anuales, resultados_mensuales):
    """Crea los gráficos de análisis"""
    # Crear directorio de resultados si no existe
    os.makedirs('resultados_chile', exist_ok=True)
    
    # 1. Gráfico de irradiación diaria promedio por mes
    plt.figure(figsize=(12, 6))
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    plt.plot(meses, resultados_mensuales['GHI_promedio'], label='GHI', marker='o')
    plt.plot(meses, resultados_mensuales['DHI_promedio'], label='DHI', marker='s')
    plt.plot(meses, resultados_mensuales['DNI_promedio'], label='DNI', marker='^')
    
    plt.xlabel('Mes')
    plt.ylabel('Irradiancia Promedio (W/m²)')
    plt.title('Irradiancia Promedio Mensual en Chile')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('resultados_chile/irradiacion_mensual.png')
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
    
    # Mejorar el eje x
    plt.xticks(range(0, 24, 1))  # Mostrar todas las horas
    plt.gca().set_xticklabels([f'{h:02d}:00' for h in range(24)])  # Formato HH:00
    plt.xlabel('Hora del día (24h)')
    plt.ylabel('Irradiancia Promedio (W/m²)')
    plt.title('Distribución Horaria de la Irradiancia en Chile')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('resultados_chile/distribucion_horaria.png')
    plt.close()

def main():
    # Cargar datos
    print("Cargando datos de Chile...")
    df = cargar_datos_chile()
    
    # Análisis anual
    print("\nRealizando análisis anual...")
    resultados_anuales = analizar_irradiacion_anual(df)
    
    # Análisis mensual
    print("Realizando análisis mensual...")
    resultados_mensuales = analizar_irradiacion_mensual(df)
    
    # Crear gráficos
    print("Generando gráficos...")
    crear_graficos(df, resultados_anuales, resultados_mensuales)
    
    # Imprimir resultados
    print("\nResultados del análisis:")
    print("\nAnálisis Anual:")
    for tipo in ['GHI', 'DHI', 'DNI']:
        print(f"\n{tipo}:")
        print(f"  Promedio: {resultados_anuales[tipo]['promedio']:.2f} W/m²")
        print(f"  Máximo: {resultados_anuales[tipo]['maximo']:.2f} W/m²")
        print(f"  Mínimo: {resultados_anuales[tipo]['minimo']:.2f} W/m²")
        print(f"  Total anual: {resultados_anuales[tipo]['total']/1000:.2f} kWh/m²")
    
    print("\nLos gráficos se han guardado en el directorio 'resultados_chile'")

if __name__ == "__main__":
    main() 