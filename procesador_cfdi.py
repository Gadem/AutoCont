import xml.etree.ElementTree as ET
import sys
import os
import json 
import csv 

# --- CONFIGURACIÓN DE NAMESPACES ---
NAMESPACES = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
}

def extraer_datos_factura(ruta_archivo):
    """
    Función para analizar el XML y extraer los datos clave (incluyendo Impuestos).
    """
    print(f"-> Procesando: {os.path.basename(ruta_archivo)}")
    
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        comprobante = root
        
        # Preparar el diccionario de datos con campos para SubTotal e impuestos
        datos = {
            'UUID': 'N/A', 
            'Fecha': comprobante.get('Fecha'),
            'SubTotal': comprobante.get('SubTotal'), # <-- Agregado SubTotal
            'Total': comprobante.get('Total'),
            'Moneda': comprobante.get('Moneda'),
            'TipoDeComprobante': comprobante.get('TipoDeComprobante'),
            
            # Campos de Impuestos
            'TotalImpuestosTrasladados': '0.00', 
            'IVA_Tasa16': '0.00', 
            
            'Conceptos': []
        }
        
        # --- 1. Extracción de Emisor y Receptor ---
        emisor = comprobante.find('cfdi:Emisor', NAMESPACES)
        if emisor is not None:
            datos['Emisor_RFC'] = emisor.get('Rfc')
            datos['Emisor_Nombre'] = emisor.get('Nombre')

        receptor = comprobante.find('cfdi:Receptor', NAMESPACES)
        if receptor is not None:
            datos['Receptor_RFC'] = receptor.get('Rfc')
            datos['UsoCFDI'] = receptor.get('UsoCFDI')

        # --- 2. Extracción de Impuestos a nivel de Comprobante ---
        impuestos_nodo = comprobante.find('cfdi:Impuestos', NAMESPACES)
        if impuestos_nodo is not None:
            total_traslados = impuestos_nodo.get('TotalImpuestosTrasladados')
            if total_traslados is not None:
                 datos['TotalImpuestosTrasladados'] = total_traslados

            traslados_generales = impuestos_nodo.find('cfdi:Traslados', NAMESPACES)
            if traslados_generales is not None:
                for traslado in traslados_generales.findall('cfdi:Traslado', NAMESPACES):
                    impuesto_tipo = traslado.get('Impuesto') 
                    tasa_o_cuota = traslado.get('TasaOCuota')
                    importe_impuesto = traslado.get('Importe')

                    if impuesto_tipo == '002' and tasa_o_cuota == '0.160000':
                        datos['IVA_Tasa16'] = str(float(datos['IVA_Tasa16']) + float(importe_impuesto))
                        
        # --- 3. Extracción de Conceptos ---
        conceptos_nodo = comprobante.find('cfdi:Conceptos', NAMESPACES)
        if conceptos_nodo is not None:
            for concepto in conceptos_nodo.findall('cfdi:Concepto', NAMESPACES):
                datos['Conceptos'].append({
                    'ClaveProdServ': concepto.get('ClaveProdServ'),
                    'Cantidad': concepto.get('Cantidad'),
                    'Descripcion': concepto.get('Descripcion'),
                    'ValorUnitario': concepto.get('ValorUnitario'),
                    'Importe': concepto.get('Importe')
                })
        
        # --- 4. Extracción del UUID ---
        complemento = comprobante.find('cfdi:Complemento', NAMESPACES)
        if complemento is not None:
            tfd = complemento.find('tfd:TimbreFiscalDigital', NAMESPACES)
            if tfd is not None:
                datos['UUID'] = tfd.get('UUID')
        
        return datos

    except Exception as e:
        print(f"ERROR al procesar el archivo: {e}")
        return None


def guardar_en_csv(datos_facturas, nombre_archivo='datos_facturas.csv'):
    
    print(f"\n-> Guardando {len(datos_facturas)} facturas en {nombre_archivo}...")
    
    # --- CORRECCIÓN FINAL: Lista de encabezados en una sola línea para evitar SyntaxError ---
    fieldnames = ['UUID', 'Fecha', 'SubTotal', 'Total', 'Moneda', 'TotalImpuestosTrasladados', 'IVA_Tasa16', 'TipoDeComprobante', 'Emisor_RFC', 'Emisor_Nombre', 'Receptor_RFC', 'UsoCFDI', 'ClaveProdServ', 'Descripcion', 'Cantidad', 'ValorUnitario', 'Importe_Concepto']
    # ------------------------------------------------------------------------------------------
    
    filas_csv = []
    for factura in datos_facturas:
        datos_principales = {k: v for k, v in factura.items() if k not in ['Conceptos']}
        
        if factura['Conceptos']:
            for concepto in factura['Conceptos']:
                fila = datos_principales.copy()
                fila.update({
                    'ClaveProdServ': concepto.get('ClaveProdServ'),
                    'Descripcion': concepto.get('Descripcion'),
                    'Cantidad': concepto.get('Cantidad'),
                    'ValorUnitario': concepto.get('ValorUnitario'),
                    'Importe_Concepto': concepto.get('Importe') 
                })
                filas_csv.append(fila)
        else:
             filas_csv.append(datos_principales)

    try:
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() 
            writer.writerows(filas_csv)

        print(f"✅ ¡Guardado completado!")
    except Exception as e:
        print(f"❌ ERROR al guardar el archivo CSV: {e}")


def main(archivos_xml):
    
    print(f"DEBUG: Argumentos recibidos: {archivos_xml}")
    
    if not archivos_xml:
        print("Uso: python procesador_cfdi.py <archivo1.xml> [archivo2.xml...]")
        return

    resultados_colectados = [] 
    
    for archivo in archivos_xml:
        datos_extraidos = extraer_datos_factura(archivo)
        
        if datos_extraidos:
            resultados_colectados.append(datos_extraidos)

    print("\n--- RESUMEN ---")
    print(f"Facturas procesadas correctamente: {len(resultados_colectados)}")

    if resultados_colectados:
        print("\n--- DATOS EXTRAÍDOS (JSON) ---")
        print(json.dumps(resultados_colectados, indent=2))

    guardar_en_csv(resultados_colectados)


if __name__ == '__main__':
    main(sys.argv[1:])