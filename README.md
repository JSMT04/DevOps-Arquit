# Pipeline de Ventas - DevOps para Arquitecturas de Datos

Este repositorio implementa el ejercicio práctico del taller **DevOps para Arquitecturas de Datos**, aplicando principios de DataOps: control de versiones, pruebas de calidad automatizadas, idempotencia e Integración Continua (CI) mediante GitHub Actions.

## Estructura del Proyecto

```text
├── .github/
│   └── workflows/
│       └── ci.yml          # Workflow de GitHub Actions (CI)
├── data/
│   └── ventas.csv         # Datos crudos de ventas (duplicados, nulos, valores negativos)
├── tests/
│   └── test_etl.py        # Pruebas unitarias de calidad con pytest
├── etl.py                 # Pipeline ETL (extraer, transformar, cargar)
├── requirements.txt       # Dependencias del proyecto
├── .gitignore             # Exclusión de artefactos compilados y bases de datos locales
└── README.md              # Documentación técnica
```

## Reglas de Calidad y Transformación

El pipeline (`etl.py`) procesa el archivo crudo `data/ventas.csv` aplicando:
1. **Eliminación de valores nulos:** Se descartan registros sin `id_venta` o `monto`.
2. **Deduplicación:** Se eliminan registros duplicados basados en `id_venta`.
3. **Casting de tipos:** La columna `fecha` se convierte a `datetime` y `monto` a `float`.
4. **Filtro de negocio:** Se conservan únicamente registros con `monto > 0`.
5. **Carga Idempotente:** Guarda los datos en una base de datos SQLite (`ventas.db`) sobrescribiendo la tabla (`if_exists="replace"`) sin generar inconsistencias por reejecución.

## Instalación y Ejecución Local

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar pruebas unitarias:**
   ```bash
   python -m pytest -v
   ```

3. **Ejecutar el pipeline ETL:**
   ```bash
   python etl.py
   ```

## Integración Continua (CI)

El archivo `.github/workflows/ci.yml` automatiza:
- Configuración de un entorno limpio con Python 3.12 en `ubuntu-latest`.
- Instalación de las dependencias (`pandas`, `pytest`).
- Ejecución de pruebas con `python -m pytest -v`.
- Ejecución completa del pipeline `python etl.py`.

