import xml.etree.ElementTree as ET
import sys
import os
import json # Usado solo para imprimir el resultado final

# --- CONFIGURACIÓN DE NAMESPACES ---
# Confirmado para CFDI 4.0
NAMESPACES = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
}

def extraer_datos_factura(ruta_archivo):
    """
    Función para analizar el XML y extraer los datos clave (UUID, Totales, Conceptos).
    """
    print(f"-> Procesando: {os.path.basename(ruta_archivo)}")
    
    try:
        tree = ET.parse(ruta_archivo)
        root = tree.getroot()
        
        # El nodo raíz (root) es el Comprobante (Corrección de búsqueda)
        comprobante = root
        
        datos = {
            'UUID': 'N/A', 
            'Fecha': comprobante.get('Fecha'),
            'Total': comprobante.get('Total'),
            'Moneda': comprobante.get('Moneda'),
            'TipoDeComprobante': comprobante.get('TipoDeComprobante'),
            'Conceptos': []
        }
        
        # --- Extracción de Emisor y Receptor ---
        emisor = comprobante.find('cfdi:Emisor', NAMESPACES)
        if emisor is not None:
            datos['Emisor_RFC'] = emisor.get('Rfc')
            datos['Emisor_Nombre'] = emisor.get('Nombre')

        receptor = comprobante.find('cfdi:Receptor', NAMESPACES)
        if receptor is not None:
            datos['Receptor_RFC'] = receptor.get('Rfc')
            datos['UsoCFDI'] = receptor.get('UsoCFDI')

        # --- Extracción de Conceptos ---
        conceptos_nodo = comprobante.find('cfdi:Conceptos', NAMESPACES)
        if conceptos_nodo is not None:
            for concepto in conceptos_nodo.findall('cfdi:Concepto', NAMESPACES):
                datos['Conceptos'].append({
                    'Descripcion': concepto.get('Descripcion'),
                    'Importe': concepto.get('Importe')
                })
        
        # --- Extracción del UUID (Timbre Fiscal Digital) ---
        complemento = comprobante.find('cfdi:Complemento', NAMESPACES)
        if complemento is not None:
            tfd = complemento.find('tfd:TimbreFiscalDigital', NAMESPACES)
            if tfd is not None:
                datos['UUID'] = tfd.get('UUID')
        
        return datos

    except FileNotFoundError:
        print(f"ERROR: Archivo no encontrado en {ruta_archivo}")
        return None
    except ET.ParseError as e:
        print(f"ERROR: Fallo al analizar el XML. Detalle: {e}")
        return None
    except Exception as e:
        print(f"ERROR DESCONOCIDO al procesar el archivo: {e}")
        return None


def main(archivos_xml):
    """
    Función principal del script que maneja la lógica de ejecución.
    """
    # -----------------------------------------------------
    # DEPURACIÓN: Asegúrate de que los argumentos se reciben.
    # Si ves esta línea, el script está ejecutándose.
    print(f"DEBUG: Argumentos recibidos: {archivos_xml}")
    # -----------------------------------------------------

    if not archivos_xml:
        print("Uso: python procesador_cfdi.py <archivo1.xml> [archivo2.xml...]")
        return

    # Inicialización necesaria (solución al NameError)
    resultados_colectados = [] 
    
    for archivo in archivos_xml:
        datos_extraidos = extraer_datos_factura(archivo)
        
        if datos_extraidos:
            resultados_colectados.append(datos_extraidos)

    print("\n--- RESUMEN ---")
    print(f"Facturas procesadas correctamente: {len(resultados_colectados)}")

    if resultados_colectados:
        print("\n--- DATOS EXTRAÍDOS (JSON) ---")
        # Imprime el JSON completo para confirmar la extracción exitosa
        print(json.dumps(resultados_colectados, indent=2))

    # NOTA: En esta versión, no se guarda el CSV.
    # El script termina aquí.


# --- Punto de Entrada del Script ---
if __name__ == '__main__':
    main(sys.argv[1:])