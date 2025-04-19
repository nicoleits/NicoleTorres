# Procesamiento de Datos Solares

Este proyecto procesa datos solares de diferentes ubicaciones para los años 2018 y 2019.

## Ubicaciones

1. ID: 1504375
   - Latitud: -26.11
   - Longitud: 27.50

2. ID: 4046597
   - Latitud: -0.96
   - Longitud: 115.07

3. ID: 5815755
   - Latitud: -23.84
   - Longitud: -69.89

## Requisitos

- Python 3.x
- Polars

## Instalación

```bash
pip install polars
```

## Uso

Para procesar los datos:

```bash
python procesar_datos.py
```

Los resultados se guardarán en el directorio `resultados/` con un archivo CSV por cada ubicación. 