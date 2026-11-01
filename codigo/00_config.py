# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
Parametros compartidos por todos los scripts del proyecto.

Numeral 2.4.5: la consulta se CONGELA. Las fechas se declaran aqui como
constantes. Nunca se usa datetime.today() para el corte, porque las fuentes
se actualizan a diario y el hash dejaria de cuadrar.

Numeral 2.4.4: rutas relativas, nunca rutas absolutas del computador.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# 1. Identificacion del estudiante
# --------------------------------------------------------------------------
CODIGO_MATRICULA = "2024200522B"
NOMBRE_COMPLETO = "ROJAS POMA MEGLINHO SNEYDER"
TEMA = ("61 - Costo de capital por sector en la BVL: "
        "mineria, banca, consumo y construccion")

# Numeral 2.4.4: si el tema exige aleatoriedad, la semilla son los cuatro
# ultimos digitos del codigo de matricula (2024200522B -> 0522).
SEMILLA = 522

# --------------------------------------------------------------------------
# 2. Ventana de extraccion CONGELADA (numeral 2.4.5)
# --------------------------------------------------------------------------
# PROVISIONAL. El inicio definitivo no puede ser anterior al primer dato de
# la serie sectorial mas corta. Se fija cuando el sondeo de fuentes diga
# desde cuando publica la BVL cada indice.
FECHA_INICIO = "2020-01-01"   # COMPLETAR tras el sondeo
FECHA_CORTE = "2025-12-31"

# Formato de periodo que usa la API del BCRP en la URL.
# Series diarias: AAAA-M-D   ·   Series mensuales: AAAA-M
BCRP_INICIO = "2020-1-1"      # COMPLETAR, debe coincidir con FECHA_INICIO
BCRP_FIN = "2025-12-31"

# --------------------------------------------------------------------------
# 3. Los cuatro sectores del tema
# --------------------------------------------------------------------------
# La clave es la etiqueta que va en la columna 'sector' del panel.
# El valor es el nombre que se usa en las tablas y figuras del articulo.
SECTORES = {
    "mineria":      "Mineria",
    "banca":        "Banca",
    "consumo":      "Consumo",
    "construccion": "Construccion",
}

# --------------------------------------------------------------------------
# 4. Rutas relativas (numeral 2.4.4)
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_CRUDOS = RAIZ / "datos_crudos"
DIR_API = DIR_CRUDOS / "api"            # un CSV por serie del BCRP
DIR_WEB = DIR_CRUDOS / "web"            # HTML o archivos tal como llegan
DIR_PROCESADOS = RAIZ / "datos_procesados"
DIR_SALIDAS = RAIZ / "salidas"
LOG = RAIZ / "log_ejecucion.txt"
INCIDENCIAS = RAIZ / "incidencias_fuente.md"

for _c in (DIR_CRUDOS, DIR_API, DIR_WEB, DIR_PROCESADOS, DIR_SALIDAS):
    _c.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 5. Nombres de archivo exigidos por el numeral 2.4.2
# --------------------------------------------------------------------------
ARCHIVO_CRUDO_API = DIR_CRUDOS / f"datos_crudos_api_{CODIGO_MATRICULA}.csv"
ARCHIVO_CRUDO_WEB = DIR_CRUDOS / f"datos_crudos_web_{CODIGO_MATRICULA}.csv"
ARCHIVO_PROCESADO = DIR_PROCESADOS / f"datos_procesados_{CODIGO_MATRICULA}.csv"

# --------------------------------------------------------------------------
# 6. Cortesia en el rastreo (numeral 2.4.8)
# --------------------------------------------------------------------------
# User-Agent identificable: institucion, curso y correo de contacto.
USER_AGENT = (
    "UNCP-FacultadEconomia-FinanzasI/1.0 (trabajo academico; "
    "contacto: e_2024200522B@uncp.edu.pe)"
)
PAUSA_SEGUNDOS = 1.5   # minimo exigido: 1 segundo
TIMEOUT = 60
REINTENTOS = 3
