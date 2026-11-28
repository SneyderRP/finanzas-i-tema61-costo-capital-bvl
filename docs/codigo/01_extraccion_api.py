# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: 2026-11-01

"""
VIA 1 - API. Yahoo Finance, fuente sugerida en el numeral 2.4.1.

    https://query1.finance.yahoo.com/v8/finance/chart/[simbolo]
        ?period1=[epoch]&period2=[epoch]&interval=1d

Sin clave de acceso.

QUE SE DESCARGA
  1. El precio diario de 24 acciones de la BVL. Diecinueve componen las
     cuatro carteras sectoriales; las otras cinco solo amplian el indice de
     mercado cuando hay que construirlo.
  2. El rendimiento del Tesoro de EE.UU. a 10 anos (^TNX): la tasa libre
     de riesgo del CAPM.
  3. El tipo de cambio soles por dolar (USDPEN=X): convierte a soles las
     acciones que cotizan en dolares.
  4. El indice S&P/BVL Peru General, si Yahoo lo publica. Si no responde,
     03_limpieza_datos.py construye el indice con las 24 acciones.

POR QUE NO SE USA BCRPData
  Desde el 2026-10-31 su cortafuegos responde HTTP 200 con una pagina
  antibot en lugar de JSON, a cualquier serie. Se comprobo desde Google
  Colab y desde una computadora personal, con cuatro configuraciones de
  cabeceras, incluido un agente de navegador completo. El navegador accede
  al catalogo, pero el acceso por script esta filtrado. Toda la evidencia,
  con fecha, hora, URL y codigo de respuesta, esta en incidencias_fuente.md.
  Es el supuesto del numeral 2.4.3.

VALIDACION DE LA FUENTE
  Los precios de Yahoo se cotejaron contra el backend de la BVL el
  2026-10-31: diez acciones de cuatro sectores, coincidencia al centimo en
  las diez. Es el paso 1 de la verificacion del numeral 2.4.6.

VENTANA CONGELADA (numeral 2.4.5)
  Se usan period1 y period2 con fechas fijas en epoch. El parametro range=5y
  seria una ventana movil, equivalente a datetime.today(), y rompe el hash.

TOLERANCIA A FALLOS
  Cada descarga se guarda en su propio archivo. La reejecucion no vuelve a
  pedir lo que ya esta en disco. Para forzar una descarga limpia, borra
  /datos_crudos/api.
"""

import json
import time
from urllib.parse import quote

import pandas as pd
import requests

from utilidades import cfg, registrar, registrar_incidencia, abortar

CABECERAS = {"User-Agent": cfg.USER_AGENT,
             "Accept": "application/json, text/plain, */*"}


class FuenteBloqueada(Exception):
    """La fuente respondio, pero no con los datos pedidos."""


def pedir_json(url, fuente):
    """
    GET que exige JSON de verdad.

    Un cortafuegos puede responder HTTP 200 con una pagina HTML, asi que
    comprobar el codigo de estado no basta: hay que mirar el contenido.
    """
    for intento in range(1, cfg.REINTENTOS + 1):
        r = requests.get(url, headers=CABECERAS, timeout=cfg.TIMEOUT)
        es_json = r.text.lstrip()[:1] in ("{", "[")
        registrar(f"GET {url[:88]}",
                  http=f"{r.status_code} {'JSON' if es_json else 'NO-JSON'}")
        if r.status_code == 200 and es_json:
            return r.json()
        if "Pardon Our Interruption" in r.text or "Request unsuccessful" in r.text:
            registrar_incidencia(
                url=url, http=f"{r.status_code} (pagina antibot)",
                detalle=f"{fuente} devolvio una pagina de interrupcion "
                        f"en lugar de JSON.")
            raise FuenteBloqueada(fuente)
        time.sleep(cfg.PAUSA_SEGUNDOS * intento * 2)
    raise FuenteBloqueada(f"{fuente}: sin JSON tras {cfg.REINTENTOS} intentos")


def simbolo_yahoo(ticker):
    """Las acciones de Lima llevan el sufijo .LM; las de fuera, no."""
    return ticker if ticker in cfg.SIN_SUFIJO else f"{ticker}.LM"


def descargar(simbolo, nombre_archivo):
    """Descarga una serie diaria y la deja en /datos_crudos/api."""
    destino = cfg.DIR_API / f"{nombre_archivo}.json"
    if destino.exists():
        registrar(f"{destino.name} ya estaba descargado")
        return json.loads(destino.read_text(encoding="utf-8"))

    url = (f"{cfg.YAHOO_API}/{quote(simbolo, safe='')}"
           f"?period1={cfg.YF_PERIOD1}&period2={cfg.YF_PERIOD2}&interval=1d")
    bruto = pedir_json(url, "Yahoo Finance")
    destino.write_text(json.dumps(bruto, ensure_ascii=False), encoding="utf-8")
    time.sleep(cfg.PAUSA_SEGUNDOS)
    return bruto


def a_tabla(bruto, etiqueta):
    """Pasa la respuesta de Yahoo a filas fecha-valor. No rellena huecos."""
    resultado = (bruto.get("chart") or {}).get("result")
    if not resultado:
        return None, None
    g = resultado[0]
    meta = g.get("meta", {})
    marcas = g.get("timestamp") or []
    cierres = ((g.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    filas = [
        {"fecha": pd.Timestamp(t, unit="s", tz="UTC").tz_localize(None).normalize(),
         etiqueta: float(c)}
        for t, c in zip(marcas, cierres) if c is not None
    ]
    return (pd.DataFrame(filas).drop_duplicates("fecha").sort_values("fecha"),
            meta.get("currency"))


def main():
    registrar(f"Ventana congelada: {cfg.FECHA_INICIO} a {cfg.FECHA_CORTE} "
              f"(epoch {cfg.YF_PERIOD1} a {cfg.YF_PERIOD2})")

    # ------------------------------------------------------------------ 1
    print("=" * 78)
    print(f"1. PRECIOS DE {len(cfg.TICKERS)} ACCIONES DE LA BVL")
    print("=" * 78)
    filas = []
    for ticker in cfg.TICKERS:
        bruto = descargar(simbolo_yahoo(ticker), f"yahoo_{ticker}")
        t, mon = a_tabla(bruto, "cierre")
        if t is None or t.empty:
            registrar(f"AVISO: {ticker} sin datos en Yahoo")
            continue
        t["nemonico"] = ticker
        t["moneda_yahoo"] = mon
        t["en_cartera"] = ticker in cfg.TICKERS_CARTERAS
        filas.append(t)
        registrar(f"{ticker}", filas=len(t))

    if not filas:
        abortar("Yahoo no devolvio ningun precio.")
    precios = (pd.concat(filas, ignore_index=True)
               .sort_values(["nemonico", "fecha"]))
    ruta = cfg.DIR_CRUDOS / f"datos_crudos_precios_{cfg.CODIGO_MATRICULA}.csv"
    precios.to_csv(ruta, index=False, encoding="utf-8")
    registrar(f"Guardado {ruta.name}", filas=len(precios))

    # ------------------------------------------------------------------ 2
    print("\n" + "=" * 78)
    print("2. SERIES DE MERCADO Y MACROECONOMICAS")
    print("=" * 78)
    macro = None
    for nombre, simbolo in cfg.SERIES_YAHOO.items():
        bruto = descargar(simbolo, f"yahoo_{nombre}")
        t, mon = a_tabla(bruto, nombre)
        if t is None:
            abortar(f"{simbolo} no devolvio datos. Es imprescindible.")
        registrar(f"{nombre} <- {simbolo} ({mon})", filas=len(t))
        # LLAVE COMUN: la columna fecha alinea las series dia contra dia.
        macro = t if macro is None else macro.merge(t, on="fecha", how="outer")

    # ------------------------------------------------------------------ 3
    print("\n" + "=" * 78)
    print("3. INDICE DE MERCADO OFICIAL (si Yahoo lo publica)")
    print("=" * 78)
    try:
        bruto = descargar(cfg.INDICE_MERCADO, "yahoo_indice_mercado")
        t, mon = a_tabla(bruto, "indice_mercado")
        if t is not None and len(t) > 500:
            macro = macro.merge(t, on="fecha", how="outer")
            registrar(f"Indice oficial {cfg.INDICE_MERCADO} disponible",
                      filas=len(t))
            print(f"   DISPONIBLE: {len(t)} dias. Se usara el indice oficial.")
        else:
            registrar(f"El indice {cfg.INDICE_MERCADO} no trae suficiente "
                      f"historico. Se construira con las acciones.")
            print("   NO DISPONIBLE. 03_limpieza_datos.py construira el indice")
            print("   de mercado promediando las acciones de la BVL.")
    except Exception as e:
        registrar(f"Indice oficial no disponible: {type(e).__name__}. "
                  f"Se construira con las acciones.")
        print("   NO DISPONIBLE. 03_limpieza_datos.py construira el indice")
        print("   de mercado promediando las acciones de la BVL.")

    macro = macro.sort_values("fecha")
    ruta_m = cfg.DIR_CRUDOS / f"datos_crudos_macro_{cfg.CODIGO_MATRICULA}.csv"
    macro.to_csv(ruta_m, index=False, encoding="utf-8")
    registrar(f"Guardado {ruta_m.name}", filas=len(macro))

    # ------------------------------------------------------------------ 4
    print("\n" + "=" * 78)
    print("RESUMEN")
    print("=" * 78)
    print(f"Acciones : {precios.nemonico.nunique()} "
          f"({len(cfg.TICKERS_CARTERAS)} en carteras, "
          f"{len(cfg.TICKERS_EXTRA)} solo para el mercado)")
    print(f"Precios  : {len(precios):,} filas")
    print(f"Periodo  : {precios.fecha.min().date()} a {precios.fecha.max().date()}")
    print(f"Macro    : {len(macro):,} fechas · "
          f"{len(macro.columns) - 1} series -> {list(macro.columns[1:])}")
    print()
    print(macro.notna().sum().to_string())


if __name__ == "__main__":
    main()
