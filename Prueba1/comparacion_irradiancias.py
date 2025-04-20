import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configurar el estilo de las gráficas
plt.style.use('default')  # Usar estilo por defecto en lugar de seaborn
sns.set_theme()  # Configurar tema de seaborn

# Cargar los datos
resultados_dir = Path("Prueba1/resultados")
chile_data = pd.read_csv(resultados_dir / "datos_Chile.csv")
indonesia_data = pd.read_csv(resultados_dir / "datos_Indonesia.csv")
sudafrica_data = pd.read_csv(resultados_dir / "datos_Sudáfrica.csv")

# Función para calcular promedios diarios
def calcular_promedios_diarios(df):
    df['Fecha'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
    return df.groupby('Fecha').agg({
        'GHI': 'mean',
        'DHI': 'mean',
        'DNI': 'mean'
    }).reset_index()

# Calcular promedios diarios para cada país
chile_daily = calcular_promedios_diarios(chile_data)
indonesia_daily = calcular_promedios_diarios(indonesia_data)
sudafrica_daily = calcular_promedios_diarios(sudafrica_data)

# Crear gráficas
fig, axes = plt.subplots(3, 1, figsize=(12, 15))
fig.suptitle('Comparación de Irradiancia Solar entre Países', fontsize=16)

# GHI
axes[0].plot(chile_daily['Fecha'], chile_daily['GHI'], label='Chile', alpha=0.7)
axes[0].plot(indonesia_daily['Fecha'], indonesia_daily['GHI'], label='Indonesia', alpha=0.7)
axes[0].plot(sudafrica_daily['Fecha'], sudafrica_daily['GHI'], label='Sudáfrica', alpha=0.7)
axes[0].set_title('Irradiancia Global Horizontal (GHI)')
axes[0].set_xlabel('Fecha')
axes[0].set_ylabel('GHI (W/m²)')
axes[0].legend()
axes[0].grid(True)

# DHI
axes[1].plot(chile_daily['Fecha'], chile_daily['DHI'], label='Chile', alpha=0.7)
axes[1].plot(indonesia_daily['Fecha'], indonesia_daily['DHI'], label='Indonesia', alpha=0.7)
axes[1].plot(sudafrica_daily['Fecha'], sudafrica_daily['DHI'], label='Sudáfrica', alpha=0.7)
axes[1].set_title('Irradiancia Difusa Horizontal (DHI)')
axes[1].set_xlabel('Fecha')
axes[1].set_ylabel('DHI (W/m²)')
axes[1].legend()
axes[1].grid(True)

# DNI
axes[2].plot(chile_daily['Fecha'], chile_daily['DNI'], label='Chile', alpha=0.7)
axes[2].plot(indonesia_daily['Fecha'], indonesia_daily['DNI'], label='Indonesia', alpha=0.7)
axes[2].plot(sudafrica_daily['Fecha'], sudafrica_daily['DNI'], label='Sudáfrica', alpha=0.7)
axes[2].set_title('Irradiancia Directa Normal (DNI)')
axes[2].set_xlabel('Fecha')
axes[2].set_ylabel('DNI (W/m²)')
axes[2].legend()
axes[2].grid(True)

plt.tight_layout()
plt.savefig('Prueba1/resultados/comparacion_irradiancias.png', dpi=300, bbox_inches='tight')

# Calcular estadísticas básicas
def calcular_estadisticas(df, pais):
    return {
        'País': pais,
        'GHI Promedio': df['GHI'].mean(),
        'DHI Promedio': df['DHI'].mean(),
        'DNI Promedio': df['DNI'].mean(),
        'GHI Máximo': df['GHI'].max(),
        'DHI Máximo': df['DHI'].max(),
        'DNI Máximo': df['DNI'].max()
    }

estadisticas = pd.DataFrame([
    calcular_estadisticas(chile_daily, 'Chile'),
    calcular_estadisticas(indonesia_daily, 'Indonesia'),
    calcular_estadisticas(sudafrica_daily, 'Sudáfrica')
])

print("\nEstadísticas de Irradiancia por País:")
print(estadisticas.round(2))

# Crear gráfica de barras para comparar máximos
plt.figure(figsize=(12, 6))
x = range(len(estadisticas['País']))
width = 0.25

plt.bar([i - width for i in x], estadisticas['GHI Máximo'], width, label='GHI Máximo', color='#1f77b4', alpha=0.7)
plt.bar(x, estadisticas['DHI Máximo'], width, label='DHI Máximo', color='#ff7f0e', alpha=0.7)
plt.bar([i + width for i in x], estadisticas['DNI Máximo'], width, label='DNI Máximo', color='#2ca02c', alpha=0.7)

plt.xlabel('País')
plt.ylabel('Irradiancia Máxima (W/m²)')
plt.title('Comparación de Valores Máximos de Irradiancia por País')
plt.xticks(x, estadisticas['País'])
plt.legend()
plt.grid(True, alpha=0.3)

# Añadir valores sobre las barras
for i in x:
    plt.text(i - width, estadisticas['GHI Máximo'].iloc[i], f'{estadisticas["GHI Máximo"].iloc[i]:.1f}', 
             ha='center', va='bottom')
    plt.text(i, estadisticas['DHI Máximo'].iloc[i], f'{estadisticas["DHI Máximo"].iloc[i]:.1f}', 
             ha='center', va='bottom')
    plt.text(i + width, estadisticas['DNI Máximo'].iloc[i], f'{estadisticas["DNI Máximo"].iloc[i]:.1f}', 
             ha='center', va='bottom')

plt.tight_layout()
plt.savefig('Prueba1/resultados/comparacion_maximos.png', dpi=300, bbox_inches='tight') 