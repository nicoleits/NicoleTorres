import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Configuración del estilo de las gráficas
plt.style.use('seaborn')
sns.set_palette("husl")

# Crear directorio de resultados si no existe
os.makedirs('Prueba1/resultados', exist_ok=True)

# Cargar los datos usando Polars
def cargar_datos(archivo):
    return pl.read_csv(archivo)

# Cargar los datos de cada país
datos_chile = cargar_datos('Prueba1/resultados/datos_Chile.csv')
datos_china = cargar_datos('Prueba1/resultados/datos_China.csv')
datos_sudafrica = cargar_datos('Prueba1/resultados/datos_Sudáfrica.csv')

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

# Calcular promedios diarios
def calcular_promedios_diarios(df):
    return df.groupby_dynamic('datetime', period='1d').agg([
        pl.col('GHI').mean().alias('GHI_mean'),
        pl.col('DHI').mean().alias('DHI_mean'),
        pl.col('DNI').mean().alias('DNI_mean')
    ])

# Calcular promedios diarios para cada país
promedios_chile = calcular_promedios_diarios(datos_chile)
promedios_china = calcular_promedios_diarios(datos_china)
promedios_sudafrica = calcular_promedios_diarios(datos_sudafrica)

# Crear gráfica de comparación
plt.figure(figsize=(15, 10))

# Graficar GHI
plt.subplot(3, 1, 1)
plt.plot(promedios_chile['datetime'], promedios_chile['GHI_mean'], label='Chile', linewidth=2)
plt.plot(promedios_china['datetime'], promedios_china['GHI_mean'], label='China', linewidth=2)
plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['GHI_mean'], label='Sudáfrica', linewidth=2)
plt.title('Comparación de Irradiancia Global Horizontal (GHI)')
plt.ylabel('GHI (W/m²)')
plt.legend()
plt.grid(True)

# Graficar DHI
plt.subplot(3, 1, 2)
plt.plot(promedios_chile['datetime'], promedios_chile['DHI_mean'], label='Chile', linewidth=2)
plt.plot(promedios_china['datetime'], promedios_china['DHI_mean'], label='China', linewidth=2)
plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DHI_mean'], label='Sudáfrica', linewidth=2)
plt.title('Comparación de Irradiancia Difusa Horizontal (DHI)')
plt.ylabel('DHI (W/m²)')
plt.legend()
plt.grid(True)

# Graficar DNI
plt.subplot(3, 1, 3)
plt.plot(promedios_chile['datetime'], promedios_chile['DNI_mean'], label='Chile', linewidth=2)
plt.plot(promedios_china['datetime'], promedios_china['DNI_mean'], label='China', linewidth=2)
plt.plot(promedios_sudafrica['datetime'], promedios_sudafrica['DNI_mean'], label='Sudáfrica', linewidth=2)
plt.title('Comparación de Irradiancia Directa Normal (DNI)')
plt.xlabel('Fecha')
plt.ylabel('DNI (W/m²)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('Prueba1/resultados/comparacion_irradiancias.png', dpi=300, bbox_inches='tight')
plt.close()

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
plt.savefig('Prueba1/resultados/comparacion_maximos.png', dpi=300, bbox_inches='tight')
plt.close() 