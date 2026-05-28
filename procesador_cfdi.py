from __future__ import annotations

import argparse
from pathlib import Path
import sys
import glob
import os

import pandas as pd

from cfdi_processor import iter_rows, parse_cfdi_file


def expand_inputs(inputs: list[str], *, recursive: bool) -> list[str]:
    files: list[str] = []
    for entry in inputs:
        if os.path.isdir(entry):
            pattern = "**/*.xml" if recursive else "*.xml"
            files.extend(str(p) for p in Path(entry).glob(pattern))
        elif any(ch in entry for ch in "*?[]"):
            files.extend(glob.glob(entry))
        else:
            files.append(entry)
    return sorted(set(files))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Procesador CFDI (XML) → CSV/Excel")
    parser.add_argument("entradas", nargs="+", help="Archivos, carpetas o patrones (*.xml)")
    parser.add_argument("--recursive", action="store_true", help="Buscar XML en subcarpetas")
    parser.add_argument(
        "--granularity",
        choices=["concept", "invoice"],
        default="concept",
        help="Salida por concepto o por factura",
    )
    parser.add_argument("--dedupe", action="store_true", help="Eliminar duplicados (por UUID + llaves básicas)")
    parser.add_argument("--strict", action="store_true", help="Fallar si hay errores al parsear XML")
    parser.add_argument("--excel", type=str, help="Exportar a Excel (ruta .xlsx)")
    parser.add_argument("--csv", type=str, help="Exportar a CSV (ruta .csv)")
    parser.add_argument("-orden", type=str, help="Campo para ordenar")
    parser.add_argument("-desc", action="store_true", help="Orden descendente")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    archivos = expand_inputs(args.entradas, recursive=args.recursive)
    print(f"📂 Archivos encontrados: {len(archivos)}")
    if not archivos:
        print("⚠️ No se encontraron XML")
        return 2

    rows: list[dict] = []
    errors: list[str] = []
    for archivo in archivos:
        try:
            parsed = parse_cfdi_file(archivo)
            rows.extend(iter_rows(parsed, granularity=args.granularity))
        except Exception as exc:  # noqa: BLE001
            msg = f"❌ Error en {archivo}: {exc}"
            if args.strict:
                raise
            errors.append(msg)

    if errors:
        print("\n".join(errors))

    if not rows:
        print("⚠️ No hay datos")
        return 3

    df = pd.DataFrame(rows)

    # Normaliza fecha (si existe)
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

    # Dedupe (más seguro)
    if args.dedupe and "UUID" in df.columns:
        dedupe_cols = [c for c in ["UUID", "ClaveProdServ", "Descripcion", "Importe", "Cantidad"] if c in df.columns]
        df = df.drop_duplicates(subset=dedupe_cols)

    # Orden
    if args.orden and args.orden in df.columns:
        df = df.sort_values(by=args.orden, ascending=not args.desc)

    out_csv = args.csv or ("reporte.csv" if not args.excel else None)
    out_xlsx = args.excel

    if out_xlsx:
        df.to_excel(out_xlsx, index=False)
        print(f"✅ Excel generado: {out_xlsx}")

    if out_csv:
        df.to_csv(out_csv, index=False)
        print(f"✅ CSV generado: {out_csv}")

    print(f"📊 Total registros: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
