# Procesador de Facturas CFDI (XML) → Excel/CSV + Dashboard

Este proyecto procesa archivos XML de facturas CFDI (SAT) y genera un reporte tabular (CSV/Excel). Incluye un dashboard (Streamlit) para explorar el `reporte.xlsx`.

## Requisitos

- Python 3.10+

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para desarrollo (tests/lint):

```bash
pip install -r requirements-dev.txt
```

## Estructura

- `procesador_cfdi.py`: CLI que procesa XML CFDI y genera el reporte.
- `app.py`: dashboard en Streamlit para explorar el Excel.
- `facturas-xml/`: carpeta local (ignorada por git) para tus XML de trabajo.

## Uso rápido

Procesar una carpeta con XML y exportar a Excel:

```bash
python procesador_cfdi.py facturas-xml --excel reporte.xlsx
```

Procesar uno o varios archivos/patrones, ordenar y eliminar duplicados:

```bash
python procesador_cfdi.py facturas-xml/*.xml -orden Fecha -desc --dedupe --excel reporte.xlsx
```

Si no usas `--excel`, el script genera `reporte.csv` en la raíz.

Opciones útiles:

- `--granularity invoice` para una fila por factura (mejor para dashboard).
- `--recursive` para buscar XML en subcarpetas.
- `--csv ruta.csv` y/o `--excel ruta.xlsx` para controlar salidas.

## Dashboard (Streamlit)

El dashboard lee `reporte.xlsx` desde la raíz del proyecto.

```bash
streamlit run app.py
```

## Columnas principales del reporte

El reporte se genera “por concepto” (una fila por concepto) e incluye, entre otras:

- `Archivo`, `UUID`, `Fecha`
- `Emisor_RFC`, `Emisor_Nombre`
- `Receptor_RFC`, `Receptor_Nombre`
- `SubTotal`, `Total`, `Moneda`, `TipoCambio`
- `ClaveProdServ`, `Descripcion`, `Cantidad`, `ValorUnitario`, `Importe`, `IVA`

## Notas

- Actualmente el parser está orientado a CFDI 4.0 (namespace `http://www.sat.gob.mx/cfd/4`).
- `facturas-xml/`, `reporte.xlsx` y otros artefactos locales se ignoran por defecto vía `.gitignore`.

## Licencia

GPL-3.0-or-later. Ver `LICENSE`.
