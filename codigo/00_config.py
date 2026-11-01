# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
Parametros compartidos por todos los scripts del proyecto.

Numeral 2.4.5: la consulta se CONGELA. Las fechas se declaran aqui como
constantes y se convierten a epoch para Yahoo. Nunca se usa el parametro
range=5y, que es una ventana movil equivalente a datetime.today().

Numeral 2.4.4: rutas relativas, nunca rutas absolutas del computador.
"""

from datetime import datetime, timezone
from pathlib import Path

CODIGO_MATRICULA = "2024200522B"
NOMBRE_COMPLETO = "ROJAS POMA MEGLINHO SNEYDER"
TEMA = ("61 - Costo de capital por sector en la BVL: "
        "mineria, banca, consumo y construccion")
SEMILLA = 522   # cuatro ultimos digitos del codigo (numeral 2.4.4)

# --------------------------------------------------------------------------
# VENTANA CONGELADA
# --------------------------------------------------------------------------
FECHA_INICIO = "2021-11-01"
FECHA_CORTE = "2026-10-31"

BCRP_INICIO = "2021-11-1"
BCRP_FIN = "2026-10-31"


def a_epoch(fecha_iso):
    """Convierte AAAA-MM-DD en segundos epoch UTC, que es lo que pide Yahoo."""
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


YF_PERIOD1 = a_epoch(FECHA_INICIO)
YF_PERIOD2 = a_epoch(FECHA_CORTE)

# --------------------------------------------------------------------------
# LAS CUATRO CARTERAS SECTORIALES
# --------------------------------------------------------------------------
# Construidas a partir de la clasificacion oficial de la BVL (/v1/sector) y
# de la actividad economica de cada emisor. Se excluyen duplicados: una
# empresa no puede entrar dos veces por tener ADR o dos clases de accion.
#
# Excluidos y por que:
#   BVN       ADR de BUENAVI1 en Nueva York
#   CPACASI1  segunda clase de accion de Cementos Pacasmayo
#   BAP       holding de CREDITC1
#   IFS       holding de INTERBC1
#   BACKUBC1  segunda clase de accion de Backus
CARTERAS = {
    "mineria": ["BUENAVI1", "ATACOBC1", "CVERDEC1", "MINSURI1",
                "NEXAPEC1", "VOLCABC1", "SCCO"],
    "banca": ["BBVAC1", "CREDITC1", "INTERBC1", "SCOTIAC1"],
    "consumo": ["ALICORC1", "BACKUSI1", "GLORIAI1", "INRETC1"],
    "construccion": ["CPACASC1", "UNACEMC1", "CORAREI1", "SIDERC1"],
}

ETIQUETAS = {"mineria": "Mineria", "banca": "Banca",
             "consumo": "Consumo", "construccion": "Construccion"}

TICKERS = sorted({t for lista in CARTERAS.values() for t in lista})

# --------------------------------------------------------------------------
# SERIES DEL BCRP
# --------------------------------------------------------------------------
# CONFIRMADAS: verificadas contra el catalogo oficial.
SERIES_BCRP = {
    "igbvl":        "PD38026MD",   # Indice General Bursatil BVL (indice)
    "isbvl":        "PD38027MD",   # Indice Selectivo Bursatil BVL (indice)
    "embig":        "PD04709XD",   # Spread EMBIG Peru (pbs)
    "treasury_10a": "PD04719XD",   # Bonos del Tesoro EE.UU. 10 anos (%)
}

# POR VERIFICAR: buscar en el catalogo y pegar el codigo. El script avisa
# de los que sigan vacios y continua; no inventa ninguno.
SERIES_POR_VERIFICAR = {
    # Confirmadas en el catalogo el 2026-10-31.
    # Se descargan las dos puntas del tipo de cambio: se convierte con la de
    # venta y la de compra queda como prueba de robustez. El diferencial es
    # casi constante, de modo que al trabajar con retornos la eleccion entre
    # una y otra no altera los resultados.
    "tc_venta":    "PD04638PD",   # Tipo de cambio Interbancario - Venta
    "tc_compra":   "PD04637PD",   # Tipo de cambio Interbancario - Compra
    # Pendientes de buscar en el catalogo. El script avisa y continua.
    "cobre":       "",   # cotizacion del cobre, diaria
    "oro":         "",   # cotizacion del oro, diaria
    "zinc":        "",   # cotizacion del zinc, diaria
    "tasa_activa": "",   # tasa activa en soles (TAMN)
}

# --------------------------------------------------------------------------
# RUTAS RELATIVAS (numeral 2.4.4)
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
# CORTESIA EN EL RASTREO (numeral 2.4.8)
# --------------------------------------------------------------------------
USER_AGENT = ("UNCP-FacultadEconomia-FinanzasI/1.0 (trabajo academico; "
              "contacto: e_2024200522B@uncp.edu.pe)")
PAUSA_SEGUNDOS = 1.5
TIMEOUT = 90
REINTENTOS = 3

BVL_API = "https://dataondemand.bvl.com.pe"
BCRP_API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
YAHOO_API = "https://query1.finance.yahoo.com/v8/finance/chart"
