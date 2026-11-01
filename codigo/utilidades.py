# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
Funciones compartidas: registro en el log, hash SHA-256, parseo de fechas
del BCRP y registro de incidencias de fuente.

El log_ejecucion.txt es entregable obligatorio (numeral 2.4.2): debe mostrar
fecha y hora de cada extraccion, numero de filas descargadas y codigo de
respuesta HTTP.
"""

import hashlib
import importlib.util
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Carga 00_config.py. El nombre empieza por digito, asi que no se puede
# importar con 'import 00_config': hay que cargarlo por ruta.
_ruta = Path(__file__).resolve().parent / "00_config.py"
_spec = importlib.util.spec_from_file_location("config", _ruta)
cfg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cfg)

MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "set": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


def registrar(mensaje, http=None, filas=None):
    """Escribe una linea en log_ejecucion.txt y la imprime."""
    partes = [f"[{datetime.now():%Y-%m-%d %H:%M:%S}]", mensaje]
    if http is not None:
        partes.append(f"| HTTP {http}")
    if filas is not None:
        partes.append(f"| filas={filas}")
    linea = " ".join(partes)
    with open(cfg.LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")
    print(linea)


def abortar(mensaje):
    """Detiene la ejecucion dejando constancia. Mejor parar que seguir
    con datos incompletos."""
    registrar(f"ABORTADO: {mensaje}")
    sys.exit(1)


def hash_sha256(ruta):
    """Huella digital del archivo. Un solo caracter distinto cambia el hash
    por completo (numeral 2.4.6, verificacion 3)."""
    digest = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            digest.update(bloque)
    return digest.hexdigest()


def a_fecha(texto):
    """
    Convierte el periodo que devuelve el BCRP en Timestamp.

    El formato varia entre series: el anio llega con dos o con cuatro digitos
    y el separador cambia. Por eso se separa por cualquier delimitador y se
    identifica cada parte por su CONTENIDO, no por su posicion.
    """
    partes = [p for p in re.split(r"[.\s\-/]+", texto.strip()) if p]
    dia = mes = anio = None
    for p in partes:
        clave = p.lower()[:3]
        if clave in MESES:
            mes = MESES[clave]
        elif p.isdigit():
            if len(p) == 4:
                anio = int(p)
            elif dia is None:
                dia = int(p)
            else:
                anio = 2000 + int(p)
    if anio is not None and anio < 100:
        anio += 2000
    if mes is None or anio is None:
        raise ValueError(f"No se pudo interpretar el periodo '{texto}'")
    return pd.Timestamp(year=anio, month=mes, day=dia or 1)


def registrar_incidencia(url, http, detalle):
    """
    Deja constancia escrita de un bloqueo de la fuente en
    incidencias_fuente.md (numeral 2.4.3).

    Con ese registro se solicita la sustitucion de fuente al docente, con un
    minimo de 5 dias calendario de anticipacion al EXANTE.
    """
    existe = cfg.INCIDENCIAS.exists()
    with open(cfg.INCIDENCIAS, "a", encoding="utf-8") as f:
        if not existe:
            f.write("# Incidencias de fuente\n\n"
                    "Registro de limitaciones tecnicas de las fuentes "
                    "consultadas (numeral 2.4.3).\n")
        f.write(f"\n## {datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
                f"- **URL:** {url}\n"
                f"- **Respuesta HTTP:** {http}\n"
                f"- **Detalle:** {detalle}\n")
    registrar(f"Incidencia registrada: {url} (HTTP {http})")
