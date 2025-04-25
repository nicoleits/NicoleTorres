import polars as pl
import matplotlib.pyplot as plt
import os
import numpy as np

def cargar_datos(archivo):
    # Primero leemos los metadatos manualmente
    with open(archivo, 'r') as f:
        # Saltamos las líneas de metadatos
        for _ in range(9):
            next(f)
        
        # Leer el resto del archivo con polars
        df = pl.read_csv(
            archivo,
            skip_rows=9,  # Saltamos las líneas de metadatos
            dtypes={
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
    
    # Imprimir información de depuración
    print(f"\nInformación del archivo {archivo}:")
    print("Columnas:", df.columns)
    print("Primeras filas:")
    print(df.head())
    
    return df

def main():
    # Crear directorio de resultados si no existe
    os.makedirs('resultados', exist_ok=True)
    
    # Cargar datos de cada país
    datos_chile = cargar_datos('datos_Chile.csv')
    datos_china = cargar_datos('datos_China.csv')
    datos_sudafrica = cargar_datos('datos_Sudafrica.csv')
    
    # Calcular promedios y máximos
    promedios = {
        'Chile': {
            'GHI': float(datos_chile.select(pl.col('GHI').mean())[0,0]),
            'DHI': float(datos_chile.select(pl.col('DHI').mean())[0,0]),
            'DNI': float(datos_chile.select(pl.col('DNI').mean())[0,0])
        },
        'China': {
            'GHI': float(datos_china.select(pl.col('GHI').mean())[0,0]),
            'DHI': float(datos_china.select(pl.col('DHI').mean())[0,0]),
            'DNI': float(datos_china.select(pl.col('DNI').mean())[0,0])
        },
        'Sudáfrica': {
            'GHI': float(datos_sudafrica.select(pl.col('GHI').mean())[0,0]),
            'DHI': float(datos_sudafrica.select(pl.col('DHI').mean())[0,0]),
            'DNI': float(datos_sudafrica.select(pl.col('DNI').mean())[0,0])
        }
    }
    
    maximos = {
        'Chile': {
            'GHI': float(datos_chile.select(pl.col('GHI').max())[0,0]),
            'DHI': float(datos_chile.select(pl.col('DHI').max())[0,0]),
            'DNI': float(datos_chile.select(pl.col('DNI').max())[0,0])
        },
        'China': {
            'GHI': float(datos_china.select(pl.col('GHI').max())[0,0]),
            'DHI': float(datos_china.select(pl.col('DHI').max())[0,0]),
            'DNI': float(datos_china.select(pl.col('DNI').max())[0,0])
        },
        'Sudáfrica': {
            'GHI': float(datos_sudafrica.select(pl.col('GHI').max())[0,0]),
            'DHI': float(datos_sudafrica.select(pl.col('DHI').max())[0,0]),
            'DNI': float(datos_sudafrica.select(pl.col('DNI').max())[0,0])
        }
    }
    
    # Calcular irradiación diaria (kWh/m²/día)
    irradiacion_diaria = {
        'Chile': float(datos_chile.select(pl.col('GHI').sum())[0,0]) / (1000 * 365),
        'China': float(datos_china.select(pl.col('GHI').sum())[0,0]) / (1000 * 365),
        'Sudáfrica': float(datos_sudafrica.select(pl.col('GHI').sum())[0,0]) / (1000 * 365)
    }
    
    # Crear gráficos
    paises = list(promedios.keys())
    tipos = ['GHI', 'DHI', 'DNI']
    
    # Gráfico de promedios
    plt.figure(figsize=(12, 6))
    x = np.arange(len(paises))
    width = 0.25
    
    for i, tipo in enumerate(tipos):
        valores = [promedios[pais][tipo] for pais in paises]
        plt.bar(x + i*width, valores, width, label=tipo)
    
    plt.xlabel('País')
    plt.ylabel('Irradiancia Promedio (W/m²)')
    plt.title('Comparación de Irradiancias Promedio por País')
    plt.xticks(x + width, paises)
    plt.legend()
    plt.tight_layout()
    plt.savefig('resultados/comparacion_irradiancias.png')
    plt.close()

    # Gráfico de máximos
    plt.figure(figsize=(12, 6))
    for i, tipo in enumerate(tipos):
        valores = [maximos[pais][tipo] for pais in paises]
        plt.bar(x + i*width, valores, width, label=tipo)
    
    plt.xlabel('País')
    plt.ylabel('Irradiancia Máxima (W/m²)')
    plt.title('Comparación de Irradiancias Máximas por País')
    plt.xticks(x + width, paises)
    plt.legend()
    plt.tight_layout()
    plt.savefig('resultados/comparacion_maximos.png')
    plt.close()
    
    # Gráfico de irradiación diaria
    plt.figure(figsize=(10, 6))
    plt.bar(paises, list(irradiacion_diaria.values()))
plt.xlabel('País')
    plt.ylabel('Irradiación Diaria Promedio (kWh/m²/día)')
    plt.title('Comparación de Irradiación Diaria Promedio por País')
plt.tight_layout()
    plt.savefig('resultados/comparacion_irradiaciones.png')
plt.close() 
    
    # Imprimir resultados
    print("\nResultados de la comparación:")
    for pais in paises:
        print(f"\n{pais}:")
        print(f"GHI promedio: {promedios[pais]['GHI']:.2f} W/m² (máximo: {maximos[pais]['GHI']:.0f} W/m²)")
        print(f"DHI promedio: {promedios[pais]['DHI']:.2f} W/m² (máximo: {maximos[pais]['DHI']:.0f} W/m²)")
        print(f"DNI promedio: {promedios[pais]['DNI']:.2f} W/m² (máximo: {maximos[pais]['DNI']:.0f} W/m²)")
        print(f"Irradiación diaria promedio: {irradiacion_diaria[pais]:.3f} kWh/m²/día (GHI)")

if __name__ == "__main__":
    main() 