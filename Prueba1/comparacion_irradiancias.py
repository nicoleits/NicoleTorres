import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# Configuración del estilo
plt.style.use('default')

# Crear directorio de resultados si no existe
os.makedirs('resultados', exist_ok=True)

# Cargar los datos usando Polars
def cargar_datos(archivo):
    # Leer el archivo CSV, saltando las primeras 4 líneas que contienen metadatos
    return pl.read_csv(archivo, skip_rows=4)

# Cargar los datos de cada país
datos_chile = cargar_datos('/home/nicole/proyecto/NicoleTorres/Prueba1/datos_Chile.csv')
datos_china = cargar_datos('/home/nicole/proyecto/NicoleTorres/Prueba1/datos_China.csv')
datos_sudafrica = cargar_datos('/home/nicole/proyecto/NicoleTorres/Prueba1/datos_Sudafrica.csv')

# Convertir las columnas de fecha y hora a datetime
def procesar_fecha_hora(df):
    return df.with_columns([
        pl.col('Year').cast(pl.Int64),
        pl.col('Month').cast(pl.Int64),
        pl.col('Day').cast(pl.Int64),
        pl.col('Hour').cast(pl.Int64),
        pl.col('Minute').cast(pl.Int64)
    ]).with_columns([
        pl.datetime(
            'Year', 'Month', 'Day', 'Hour', 'Minute'
        ).alias('datetime')
    ])

# Procesar las fechas para cada dataset
datos_chile = procesar_fecha_hora(datos_chile)
datos_china = procesar_fecha_hora(datos_china)
datos_sudafrica = procesar_fecha_hora(datos_sudafrica)

# Calcular promedios e irradiación diarios
def calcular_promedios_diarios(df):
    # Factor de conversión: (W/m² * minuto) a (kWh/m²)
    # 1 kWh/m² = 1000 W/m² * 1 hora
    # Como tenemos datos cada minuto, multiplicamos por (1/60) para convertir a horas
    # y por (1/1000) para convertir a kWh
    factor_conversion = 1 / (60 * 1000)
    
    return df.group_by_dynamic(
        'datetime',
        every='1d',
        period='1d'
    ).agg([
        pl.col('GHI').mean().alias('GHI_promedio'),
        pl.col('DHI').mean().alias('DHI_promedio'),
        pl.col('DNI').mean().alias('DNI_promedio'),
        (pl.col('GHI').sum() * factor_conversion).alias('GHI_irradiacion'),
        (pl.col('DHI').sum() * factor_conversion).alias('DHI_irradiacion'),
        (pl.col('DNI').sum() * factor_conversion).alias('DNI_irradiacion')
    ])

# Calcular promedios diarios para cada país
promedios_chile = calcular_promedios_diarios(datos_chile)
promedios_china = calcular_promedios_diarios(datos_china)
promedios_sudafrica = calcular_promedios_diarios(datos_sudafrica)

# Crear gráficas
def crear_graficas_irradiancia():
    plt.figure(figsize=(15, 10))

    # Graficar GHI
    plt.subplot(3, 1, 1)
    plt.plot(promedios_chile['datetime'], promedios_chile['GHI_promedio'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['GHI_promedio'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['GHI_promedio'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiancia Global Horizontal (GHI)')
    plt.ylabel('GHI (W/m²)')
    plt.legend()
    plt.grid(True)

    # Graficar DHI
    plt.subplot(3, 1, 2)
    plt.plot(promedios_chile['datetime'], promedios_chile['DHI_promedio'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['DHI_promedio'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DHI_promedio'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiancia Difusa Horizontal (DHI)')
    plt.ylabel('DHI (W/m²)')
    plt.legend()
    plt.grid(True)

    # Graficar DNI
    plt.subplot(3, 1, 3)
    plt.plot(promedios_chile['datetime'], promedios_chile['DNI_promedio'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['DNI_promedio'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DNI_promedio'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiancia Directa Normal (DNI)')
    plt.xlabel('Fecha')
    plt.ylabel('DNI (W/m²)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('resultados/comparacion_irradiancias.png', dpi=300, bbox_inches='tight')
    plt.close()

def crear_graficas_irradiacion():
    plt.figure(figsize=(15, 10))

    # Graficar GHI
    plt.subplot(3, 1, 1)
    plt.plot(promedios_chile['datetime'], promedios_chile['GHI_irradiacion'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['GHI_irradiacion'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['GHI_irradiacion'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiación Global Horizontal (GHI)')
    plt.ylabel('GHI (kWh/m²/día)')
    plt.legend()
    plt.grid(True)

    # Graficar DHI
    plt.subplot(3, 1, 2)
    plt.plot(promedios_chile['datetime'], promedios_chile['DHI_irradiacion'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['DHI_irradiacion'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DHI_irradiacion'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiación Difusa Horizontal (DHI)')
    plt.ylabel('DHI (kWh/m²/día)')
    plt.legend()
    plt.grid(True)

    # Graficar DNI
    plt.subplot(3, 1, 3)
    plt.plot(promedios_chile['datetime'], promedios_chile['DNI_irradiacion'], label='Chile', linewidth=2)
    plt.plot(promedios_china['datetime'], promedios_china['DNI_irradiacion'], label='China', linewidth=2)
    plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DNI_irradiacion'], label='Sudáfrica', linewidth=2)
    plt.title('Comparación de Irradiación Directa Normal (DNI)')
    plt.xlabel('Fecha')
    plt.ylabel('DNI (kWh/m²/día)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('resultados/comparacion_irradiaciones.png', dpi=300, bbox_inches='tight')
    plt.close()

# Crear las gráficas
crear_graficas_irradiancia()
crear_graficas_irradiacion()

# Calcular y mostrar estadísticas
def calcular_estadisticas(df, pais):
    stats = df.select([
        pl.col('GHI').mean().alias('GHI_mean'),
        pl.col('GHI').max().alias('GHI_max'),
        pl.col('DHI').mean().alias('DHI_mean'),
        pl.col('DHI').max().alias('DHI_max'),
        pl.col('DNI').mean().alias('DNI_mean'),
        pl.col('DNI').max().alias('DNI_max')
    ])
    print(f"\nEstadísticas para {pais}:")
    print(stats)
    
    # Calcular estadísticas de irradiación
    irradiacion_stats = calcular_promedios_diarios(df).select([
        pl.col('GHI_irradiacion').mean().alias('GHI_irradiacion_media'),
        pl.col('GHI_irradiacion').max().alias('GHI_irradiacion_max'),
        pl.col('DHI_irradiacion').mean().alias('DHI_irradiacion_media'),
        pl.col('DHI_irradiacion').max().alias('DHI_irradiacion_max'),
        pl.col('DNI_irradiacion').mean().alias('DNI_irradiacion_media'),
        pl.col('DNI_irradiacion').max().alias('DNI_irradiacion_max')
    ])
    print(f"\nEstadísticas de irradiación diaria para {pais} (kWh/m²/día):")
    print(irradiacion_stats)

calcular_estadisticas(datos_chile, "Chile")
calcular_estadisticas(datos_china, "China")
calcular_estadisticas(datos_sudafrica, "Sudáfrica")

# Crear gráfica de barras para máximos
maximos = pl.DataFrame({
    'País': ['Chile', 'China', 'Sudáfrica'],
    'GHI': [
        datos_chile['GHI'].max(),
        datos_china['GHI'].max(),
        datos_sudafrica['GHI'].max()
    ],
    'DHI': [
        datos_chile['DHI'].max(),
        datos_china['DHI'].max(),
        datos_sudafrica['DHI'].max()
    ],
    'DNI': [
        datos_chile['DNI'].max(),
        datos_china['DNI'].max(),
        datos_sudafrica['DNI'].max()
    ]
})

plt.figure(figsize=(12, 6))
x = range(len(maximos['País']))
width = 0.25

plt.bar([i - width for i in x], maximos['GHI'], width, label='GHI')
plt.bar(x, maximos['DHI'], width, label='DHI')
plt.bar([i + width for i in x], maximos['DNI'], width, label='DNI')

plt.xlabel('País')
plt.ylabel('Irradiancia Máxima (W/m²)')
plt.title('Comparación de Máximos de Irradiancia por País')
plt.xticks(x, maximos['País'])
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('resultados/comparacion_maximos.png', dpi=300, bbox_inches='tight')
plt.close() 