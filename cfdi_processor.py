from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"


def _detect_cfdi_namespace(root: ET.Element) -> str | None:
    if root.tag.startswith("{") and "}" in root.tag:
        return root.tag.split("}", 1)[0][1:]
    return None


def _ns(root: ET.Element) -> dict[str, str]:
    cfdi_ns = _detect_cfdi_namespace(root) or "http://www.sat.gob.mx/cfd/4"
    return {"cfdi": cfdi_ns, "tfd": TFD_NS}


def _d(value: str | None) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _text_attr(elem: ET.Element | None, attr: str) -> str | None:
    if elem is None:
        return None
    return elem.attrib.get(attr)


@dataclass(frozen=True)
class TaxTotals:
    trasladados: Decimal = Decimal("0")
    retenidos: Decimal = Decimal("0")
    iva_16: Decimal = Decimal("0")


def _parse_impuestos(impuestos: ET.Element | None, ns: dict[str, str]) -> TaxTotals:
    if impuestos is None:
        return TaxTotals()

    iva_16 = Decimal("0")
    trasladados = _d(impuestos.attrib.get("TotalImpuestosTrasladados"))
    retenidos = _d(impuestos.attrib.get("TotalImpuestosRetenidos"))

    traslados = impuestos.find("cfdi:Traslados", ns)
    if traslados is not None:
        for t in traslados.findall("cfdi:Traslado", ns):
            impuesto = t.attrib.get("Impuesto")
            tasa = t.attrib.get("TasaOCuota")
            importe = _d(t.attrib.get("Importe"))
            if impuesto == "002" and tasa in {"0.160000", "0.16"}:
                iva_16 += importe

    return TaxTotals(trasladados=trasladados, retenidos=retenidos, iva_16=iva_16)


def extract_uuid(root: ET.Element) -> str | None:
    ns = _ns(root)
    complemento = root.find("cfdi:Complemento", ns)
    if complemento is None:
        return None
    tfd = complemento.find("tfd:TimbreFiscalDigital", ns)
    if tfd is None:
        return None
    return tfd.attrib.get("UUID")


def parse_cfdi_file(path: str | Path) -> dict[str, Any]:
    xml_path = Path(path)
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = _ns(root)

    emisor = root.find("cfdi:Emisor", ns)
    receptor = root.find("cfdi:Receptor", ns)
    impuestos_comprobante = root.find("cfdi:Impuestos", ns)

    taxes = _parse_impuestos(impuestos_comprobante, ns)

    base: dict[str, Any] = {
        "Archivo": xml_path.name,
        "UUID": extract_uuid(root),
        "Fecha": root.attrib.get("Fecha"),
        "Moneda": root.attrib.get("Moneda"),
        "TipoCambio": root.attrib.get("TipoCambio"),
        "TipoDeComprobante": root.attrib.get("TipoDeComprobante"),
        "SubTotal": _d(root.attrib.get("SubTotal")),
        "Total": _d(root.attrib.get("Total")),
        "Emisor_RFC": _text_attr(emisor, "Rfc"),
        "Emisor_Nombre": _text_attr(emisor, "Nombre"),
        "Receptor_RFC": _text_attr(receptor, "Rfc"),
        "Receptor_Nombre": _text_attr(receptor, "Nombre"),
        "UsoCFDI": _text_attr(receptor, "UsoCFDI"),
        "TotalImpuestosTrasladados": taxes.trasladados,
        "TotalImpuestosRetenidos": taxes.retenidos,
        "IVA_Tasa16": taxes.iva_16,
    }

    conceptos_rows: list[dict[str, Any]] = []
    conceptos = root.findall("cfdi:Conceptos/cfdi:Concepto", ns)
    for c in conceptos:
        impuestos_concepto = c.find("cfdi:Impuestos", ns)
        concept_taxes = _parse_impuestos(impuestos_concepto, ns)
        conceptos_rows.append(
            {
                "ClaveProdServ": c.attrib.get("ClaveProdServ"),
                "Descripcion": c.attrib.get("Descripcion"),
                "Cantidad": _d(c.attrib.get("Cantidad")),
                "ValorUnitario": _d(c.attrib.get("ValorUnitario")),
                "Importe": _d(c.attrib.get("Importe")),
                "IVA_Concepto_16": concept_taxes.iva_16,
            }
        )

    return {"base": base, "conceptos": conceptos_rows}


def iter_rows(
    parsed: dict[str, Any],
    *,
    granularity: str = "concept",
) -> Iterable[dict[str, Any]]:
    base: dict[str, Any] = parsed["base"]
    conceptos: list[dict[str, Any]] = parsed["conceptos"]

    if granularity == "invoice":
        row = dict(base)
        row["Conceptos_Count"] = len(conceptos)
        yield row
        return

    for concepto in conceptos or [{}]:
        row = dict(base)
        row.update(concepto)
        yield row

