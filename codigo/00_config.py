# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: 2026-11-01

"""
Parametros compartidos por todos los scripts.

Numeral 2.4.5: la consulta se CONGELA. Las fechas se declaran aqui como
constantes y se convierten a epoch. Nunca se usa el parametro range=5y de
Yahoo, que es una ventana movil equivalente a datetime.today().

Numeral 2.4.4: rutas relativas, nunca rutas absolutas del computador.
"""

from datetime import datetime, timezone
from pathlib import Path

CODIGO_MATRICULA = "2024200522B"
NOMBRE_COMPLETO = "ROJAS POMA MEGLINHO SNEYDER"
TEMA = ("61 - Costo de capital por sector en la BVL: "
        "mineria, banca, consumo y construccion")
SEMILLA = 522          # cuatro ultimos digitos del codigo (numeral 2.4.4)

# --------------------------------------------------------------------------
# 1. VENTANA CONGELADA
# --------------------------------------------------------------------------
FECHA_INICIO = "2021-11-01"
FECHA_CORTE = "2026-10-31"


def a_epoch(fecha_iso):
    """AAAA-MM-DD a segundos epoch UTC, que es lo que pide Yahoo."""
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


YF_PERIOD1 = a_epoch(FECHA_INICIO)
YF_PERIOD2 = a_epoch(FECHA_CORTE)

# --------------------------------------------------------------------------
# 2. LAS CUATRO CARTERAS SECTORIALES
# --------------------------------------------------------------------------
# La BVL no reconoce consumo ni construccion como sector, y su categoria
# DIVERSAS mezcla un holding bancario, un retail y una cementera. Las
# carteras se arman con la clasificacion oficial (/v1/sector) y la actividad
# economica del emisor, y la agrupacion se declara en Materiales y metodos.
#
# FILTRO DE LIQUIDEZ
# Se midio, para cada accion, en que porcentaje de los dias el precio
# efectivamente CAMBIO. Un precio repetido no es una cotizacion nueva: es el
# ultimo valor conocido arrastrado hacia adelante, y produce retornos cero
# que sesgan la beta hacia abajo. Seis acciones se mueven menos del 30 % de
# los dias; BUENAVI1 llego a estar 341 dias seguidos con el mismo precio.
#
# REGLA APLICADA, la misma en los cuatro sectores:
#   1. Un instrumento por grupo economico, el de mayor liquidez.
#   2. Fuera lo que se mueva menos del 30 % de los dias.
#
# Sustituciones por grupo:
#   BUENAVI1 ( 4.1 %) -> BVN      (98.3 %)   Buenaventura
#   INTERBC1 (11.9 %) -> IFS      (98.9 %)   Intercorp
#   CREDITC1 (67.5 %) -> BAP      (99.4 %)   Credicorp
#   ATACOBC1 (26.6 %) -> NEXAPEC1 (43.2 %)   Nexa, mismo grupo
# Exclusiones sin reemplazo, por no tener vehiculo listado liquido:
#   SCOTIAC1 (12.5 %), GLORIAI1 (10.1 %)
#
# Hallazgo que se discute en el articulo: las empresas peruanas grandes se
# negocian con regularidad en Nueva York y no en Lima. Buenaventura se mueve
# el 4.1 % de los dias en la BVL y el 98.3 % como ADR.
CARTERAS = {
    "mineria": ["SCCO", "BVN", "CVERDEC1", "VOLCABC1", "MINSURI1", "NEXAPEC1"],
    "banca": ["BAP", "IFS", "BBVAC1"],
    "consumo": ["ALICORC1", "BACKUSI1", "INRETC1"],
    "construccion": ["CPACASC1", "UNACEMC1", "CORAREI1", "SIDERC1"],
}

ETIQUETAS = {"mineria": "Mineria", "banca": "Banca",
             "consumo": "Consumo", "construccion": "Construccion"}

TICKERS_CARTERAS = sorted({t for v in CARTERAS.values() for t in v})

# Acciones liquidas que no entran en ninguna cartera. Solo amplian el indice
# de mercado, lo que reduce la correlacion mecanica entre cada cartera y el
# mercado. Se excluyen las que no pasan el filtro de liquidez.
TICKERS_EXTRA = ["CREDITC1", "FERREYC1", "LUSURC1", "ENGIEC1"]

TICKERS = sorted(set(TICKERS_CARTERAS) | set(TICKERS_EXTRA))

# Cotizan fuera de Lima: su simbolo en Yahoo no lleva el sufijo .LM
SIN_SUFIJO = ("SCCO", "BVN", "BAP", "IFS", "TEF")

# --------------------------------------------------------------------------
# 3. SERIES DE MERCADO Y MACROECONOMICAS
# --------------------------------------------------------------------------
# BCRPData quedo inaccesible por via automatizada desde el 2026-10-31: su
# cortafuegos responde HTTP 200 con una pagina antibot en lugar de JSON, a
# cualquier serie, desde Colab y desde una conexion domestica, con cuatro
# configuraciones distintas de cabeceras, incluido un agente de navegador
# completo. Documentado en incidencias_fuente.md.
#
# Los sustitutos se toman de Yahoo Finance, fuente API sugerida en el
# numeral 2.4.1.
SERIES_YAHOO = {
    "treasury_10a": "^TNX",       # Rf: rendimiento del Tesoro EE.UU. 10 anos
    "tipo_cambio":  "USDPEN=X",   # soles por dolar
}

# Indice de mercado. Se intenta el oficial de la BVL; Yahoo respondio 404 el
# 2026-11-01, de modo que 03_limpieza_datos.py lo construye promediando las
# 20 acciones. El script vuelve a intentarlo en cada ejecucion.
INDICE_MERCADO = "^SPBLPGPT"      # S&P/BVL Peru General

# --------------------------------------------------------------------------
# 4. RUTAS RELATIVAS (numeral 2.4.4)
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_CRUDOS = RAIZ / "datos_crudos"
DIR_API = DIR_CRUDOS / "api"
DIR_WEB = DIR_CRUDOS / "web"
DIR_PROCESADOS = RAIZ / "datos_procesados"
DIR_SALIDAS = RAIZ / "salidas"
LOG = RAIZ / "log_ejecucion.txt"
INCIDENCIAS = RAIZ / "incidencias_fuente.md"

for _c in (DIR_CRUDOS, DIR_API, DIR_WEB, DIR_PROCESADOS, DIR_SALIDAS):
    _c.mkdir(parents=True, exist_ok=True)

ARCHIVO_CRUDO_API = DIR_CRUDOS / f"datos_crudos_api_{CODIGO_MATRICULA}.csv"
ARCHIVO_CRUDO_WEB = DIR_CRUDOS / f"datos_crudos_web_{CODIGO_MATRICULA}.csv"
ARCHIVO_PROCESADO = DIR_PROCESADOS / f"datos_procesados_{CODIGO_MATRICULA}.csv"

# --------------------------------------------------------------------------
# 5. CORTESIA EN EL RASTREO (numeral 2.4.8)
# --------------------------------------------------------------------------
USER_AGENT = ("UNCP-FacultadEconomia-FinanzasI/1.0 (trabajo academico; "
              "contacto: e_2024200522B@uncp.edu.pe)")
PAUSA_SEGUNDOS = 1.5
TIMEOUT = 90
REINTENTOS = 3

BVL_API = "https://dataondemand.bvl.com.pe"
YAHOO_API = "https://query1.finance.yahoo.com/v8/finance/chart"
