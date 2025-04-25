import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configuración del estilo de matplotlib
plt.style.use('default')
sns.set_theme()

# Rutas de los archivos
archivos = {
    'Chile': 'resultados/datos_Chile.csv',
    'Sudáfrica': 'resultados/datos_Sudáfrica.csv',
    'China': 'resultados/datos_China.csv'
}

def procesar_datos(archivo):
    """
    Procesa los datos de irradiancia de un archivo CSV.
    
    Args:
        archivo (str): Ruta al archivo CSV
        
    Returns:
        pl.DataFrame: DataFrame con la irradiación diaria
    """
    # Leer el archivo CSV
    df = pl.read_csv(archivo)
    
    # Calcular irradiación diaria (kWh/m²)
    df = df.with_columns([
        (pl.col('DNI') * 0.001).alias('DNI_kWh_m2'),  # Convertir W/m² a kWh/m²
        (pl.col('GHI') * 0.001).alias('GHI_kWh_m2')   # Convertir W/m² a kWh/m²
    ])
    
    # Agrupar por día y calcular la irradiación diaria
    irradiacion_diaria = df.groupby(['Year', 'Month', 'Day']).agg([
        pl.col('DNI_kWh_m2').sum().alias('DNI_diario'),
        pl.col('GHI_kWh_m2').sum().alias('GHI_diario')
    ])
    
    return irradiacion_diaria

def calcular_estadisticas(df, pais):
    """
    Calcula estadísticas básicas de irradiación.
    
    Args:
        df (pl.DataFrame): DataFrame con irradiación diaria
        pais (str): Nombre del país
        
    Returns:
        dict: Diccionario con estadísticas
    """
    stats = {
        'País': pais,
        'DNI promedio diario (kWh/m²)': df['DNI_diario'].mean(),
        'GHI promedio diario (kWh/m²)': df['GHI_diario'].mean(),
        'DNI máximo diario (kWh/m²)': df['DNI_diario'].max(),
        'GHI máximo diario (kWh/m²)': df['GHI_diario'].max(),
        'DNI mínimo diario (kWh/m²)': df['DNI_diario'].min(),
        'GHI mínimo diario (kWh/m²)': df['GHI_diario'].min(),
        'DNI desviación estándar (kWh/m²)': df['DNI_diario'].std(),
        'GHI desviación estándar (kWh/m²)': df['GHI_diario'].std()
    }
    return stats

def graficar_irradiacion_diaria(datos_por_pais):
    """
    Genera gráficos de irradiación diaria por país.
    
    Args:
        datos_por_pais (dict): Diccionario con DataFrames de irradiación por país
    """
    # Crear figura con subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Gráfico de DNI diario
    for pais, df in datos_por_pais.items():
        ax1.plot(range(len(df)), df['DNI_diario'], label=pais, alpha=0.7)
    
    ax1.set_title('Irradiación Normal Directa (DNI) Diaria')
    ax1.set_xlabel('Día del año')
    ax1.set_ylabel('DNI (kWh/m²)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico de GHI diario
    for pais, df in datos_por_pais.items():
        ax2.plot(range(len(df)), df['GHI_diario'], label=pais, alpha=0.7)
    
    ax2.set_title('Irradiación Global Horizontal (GHI) Diaria')
    ax2.set_xlabel('Día del año')
    ax2.set_ylabel('GHI (kWh/m²)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('resultados/comparacion_irradiaciones.png')
    plt.close()

def graficar_maximos_diarios(datos_por_pais):
    """
    Genera gráfico de barras con máximos diarios por país.
    
    Args:
        datos_por_pais (dict): Diccionario con DataFrames de irradiación por país
    """
    paises = list(datos_por_pais.keys())
    dni_maximos = [df['DNI_diario'].max() for df in datos_por_pais.values()]
    ghi_maximos = [df['GHI_diario'].max() for df in datos_por_pais.values()]
    
    x = np.arange(len(paises))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, dni_maximos, width, label='DNI')
    rects2 = ax.bar(x + width/2, ghi_maximos, width, label='GHI')
    
    ax.set_ylabel('Irradiación (kWh/m²)')
    ax.set_title('Máxima Irradiación Diaria por País')
    ax.set_xticks(x)
    ax.set_xticklabels(paises)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('resultados/comparacion_maximos.png')
    plt.close()

def main():
    # Procesar datos y calcular estadísticas
    datos_por_pais = {}
    estadisticas = []
    
    for pais, archivo in archivos.items():
        print(f"\nProcesando datos para {pais}...")
        
        # Procesar datos de irradiancia
        irradiacion = procesar_datos(archivo)
        datos_por_pais[pais] = irradiacion
        
        # Calcular y mostrar estadísticas
        stats = calcular_estadisticas(irradiacion, pais)
        estadisticas.append(stats)
        
        print(f"\nEstadísticas de irradiación para {pais}:")
        print(f"DNI promedio diario: {stats['DNI promedio diario (kWh/m²)']:.2f} kWh/m²")
        print(f"GHI promedio diario: {stats['GHI promedio diario (kWh/m²)']:.2f} kWh/m²")
        print(f"DNI máximo diario: {stats['DNI máximo diario (kWh/m²)']:.2f} kWh/m²")
        print(f"GHI máximo diario: {stats['GHI máximo diario (kWh/m²)']:.2f} kWh/m²")
    
    # Generar gráficos
    print("\nGenerando gráficos...")
    graficar_irradiacion_diaria(datos_por_pais)
    graficar_maximos_diarios(datos_por_pais)
    print("Gráficos guardados en la carpeta 'resultados'")

if __name__ == "__main__":
    main() 