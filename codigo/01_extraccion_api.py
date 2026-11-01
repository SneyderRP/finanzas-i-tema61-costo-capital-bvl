# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
VIA 1 - API. Dos APIs publicas, ninguna exige clave.

A) Yahoo Finance
   https://query1.finance.yahoo.com/v8/finance/chart/[ticker]
   Precio diario de las 19 acciones de las cuatro carteras. El sufijo .LM
   corresponde a la plaza de Lima. Los precios se cotejaron contra el backend
   de la BVL el 2026-10-31: 10 de 10 coincidieron al centimo.

B) BCRPData, Banco Central de Reserva del Peru
   https://estadisticas.bcrp.gob.pe/estadisticas/series/api/
       [codigo]/[formato]/[inicio]/[fin]/[idioma]
   Indice general de la bolsa (el mercado del CAPM), riesgo pais, tasa libre
   de riesgo y tipo de cambio.

VENTANA CONGELADA (numeral 2.4.5)
Yahoo admite range=5y, que es una ventana MOVIL y cambia cada dia. No se usa:
equivale a datetime.today() y rompe la reproducibilidad del hash. Se usa
period1/period2 con las fechas fijas de 00_config.py convertidas a epoch.

TOLERANCIA A FALLOS DE LA FUENTE
Las dos fuentes se descargan por separado y cada archivo crudo se conserva.
Si una fuente deja de responder, lo ya descargado no se pierde y la
reejecucion no vuelve a pedir lo que ya esta en disco. Para forzar una
descarga limpia basta con borrar /datos_crudos/api.

Un servidor puede responder HTTP 200 y aun asi no entregar lo pedido: es lo
que ocurre cuando un sistema antibot devuelve una pagina de interrupcion. Por
eso no basta con mirar el codigo de estado, hay que comprobar que la
respuesta sea realmente JSON.
"""

import json
import time

import pandas as pd
import requests

from utilidades import cfg, registrar, registrar_incidencia, a_fecha, abortar

CABECERAS = {"User-Agent": cfg.USER_AGENT,
             "Accept": "application/json, text/plain, */*"}


class FuenteBloqueada(Exception):
    """La fuente respondio, pero no con los datos pedidos."""


def pedir_json(url, fuente):
    """
    GET que exige JSON de verdad.

    Comprueba el codigo de estado Y el contenido. Un antibot devuelve HTTP 200
    con HTML, asi que fiarse del 200 no basta.
    """
    for intento in range(1, cfg.REINTENTOS + 1):
        r = requests.get(url, headers=CABECERAS, timeout=cfg.TIMEOUT)
        texto = r.text.lstrip()
        es_json = texto[:1] in ("{", "[")
        registrar(f"GET {url[:92]}", http=f"{r.status_code} "
                                          f"{'JSON' if es_json else 'NO-JSON'}")

        if r.status_code == 200 and es_json:
            return r.json()

        if "Pardon Our Interruption" in r.text or "Request unsuccessful" in r.text:
            registrar_incidencia(
                url=url, http=f"{r.status_code} (pagina antibot)",
                detalle=(f"{fuente} respondio HTTP 200 con una pagina de "
                         "interrupcion antibot en lugar de JSON. Es un bloqueo "
                         "temporal por direccion IP, no un error del codigo. "
                         "Se reintenta mas tarde."))
            raise FuenteBloqueada(fuente)

        time.sleep(cfg.PAUSA_SEGUNDOS * intento * 2)

    raise FuenteBloqueada(f"{fuente}: sin JSON tras {cfg.REINTENTOS} intentos")


# ==========================================================================
# A. Yahoo Finance
# ==========================================================================
# Estas cotizan fuera de Lima y no llevan sufijo de plaza.
SIN_SUFIJO = ("SCCO", "BVN", "BAP", "IFS", "TEF")


def extraer_yahoo():
    filas = []
    for ticker in cfg.TICKERS:
        destino = cfg.DIR_API / f"yahoo_{ticker}.json"

        if destino.exists():
            bruto = json.loads(destino.read_text(encoding="utf-8"))
            registrar(f"yahoo_{ticker}.json ya estaba descargado")
        else:
            simbolo = ticker if ticker in SIN_SUFIJO else f"{ticker}.LM"
            url = (f"{cfg.YAHOO_API}/{simbolo}"
                   f"?period1={cfg.YF_PERIOD1}&period2={cfg.YF_PERIOD2}"
                   f"&interval=1d")
            bruto = pedir_json(url, "Yahoo Finance")
            destino.write_text(json.dumps(bruto, ensure_ascii=False),
                               encoding="utf-8")
            time.sleep(cfg.PAUSA_SEGUNDOS)

        resultado = (bruto.get("chart") or {}).get("result")
        if not resultado:
            registrar(f"AVISO: {ticker} sin datos. "
                      f"{(bruto.get('chart') or {}).get('error')}")
            continue

        g = resultado[0]
        meta = g.get("meta", {})
        marcas = g.get("timestamp") or []
        cierres = ((g.get("indicators") or {}).get("quote")
                   or [{}])[0].get("close") or []

        n = 0
        for marca, cierre in zip(marcas, cierres):
            if cierre is None:
                continue          # dia sin negociacion: no se rellena
            filas.append({
                "fecha": pd.Timestamp(marca, unit="s", tz="UTC")
                           .tz_localize(None).normalize(),
                "nemonico": ticker,
                "cierre": float(cierre),
                "moneda_yahoo": meta.get("currency"),
            })
            n += 1
        registrar(f"{ticker}", filas=n)

    if not filas:
        abortar("Yahoo no devolvio ningun precio.")
    return pd.DataFrame(filas).sort_values(["nemonico", "fecha"])


# ==========================================================================
# B. BCRPData
# ==========================================================================
def extraer_bcrp():
    series = dict(cfg.SERIES_BCRP)
    for nombre, codigo in cfg.SERIES_POR_VERIFICAR.items():
        if codigo:
            series[nombre] = codigo
        else:
            registrar(f"AVISO: la serie '{nombre}' no tiene codigo asignado; "
                      f"se omite. Buscarla en el catalogo de BCRPData.")

    ancho = None
    for nombre, codigo in series.items():
        destino = cfg.DIR_API / f"bcrp_{nombre}__{codigo}.csv"

        if destino.exists():
            t = pd.read_csv(destino, parse_dates=["fecha"])
            registrar(f"bcrp_{nombre} ya estaba descargado", filas=len(t))
        else:
            url = (f"{cfg.BCRP_API}/{codigo}/json/"
                   f"{cfg.BCRP_INICIO}/{cfg.BCRP_FIN}/esp")
            bruto = pedir_json(url, "BCRPData")

            # El bloque config trae el nombre oficial de la serie devuelta:
            # confirma que el codigo trajo lo esperado y no otra cosa.
            registrar(f"{nombre} <- {bruto['config']['series'][0]['name']}")

            t = pd.DataFrame([
                {"fecha": a_fecha(p["name"]),
                 nombre: pd.to_numeric(p["values"][0], errors="coerce")}
                for p in bruto["periods"]
            ]).sort_values("fecha")
            t.to_csv(destino, index=False, encoding="utf-8")
            registrar(f"Guardado {destino.name}", filas=len(t))
            time.sleep(cfg.PAUSA_SEGUNDOS)

        # LLAVE COMUN: la columna fecha alinea las series dia contra dia.
        ancho = t if ancho is None else ancho.merge(t, on="fecha", how="outer")

    return ancho.sort_values("fecha")


def main():
    registrar(f"Ventana congelada: {cfg.FECHA_INICIO} a {cfg.FECHA_CORTE} "
              f"(epoch {cfg.YF_PERIOD1} a {cfg.YF_PERIOD2})")

    # ------------------------------------------------------------------ A
    print("=" * 78)
    print("A. Yahoo Finance: 19 acciones de las cuatro carteras")
    print("=" * 78)
    precios = extraer_yahoo()
    ruta_precios = cfg.DIR_CRUDOS / f"datos_crudos_precios_{cfg.CODIGO_MATRICULA}.csv"
    precios.to_csv(ruta_precios, index=False, encoding="utf-8")
    registrar("Crudo de precios guardado", filas=len(precios))

    print(f"\n{len(precios):,} filas · {precios.nemonico.nunique()} acciones · "
          f"{precios.fecha.min().date()} a {precios.fecha.max().date()}\n")
    print(precios.groupby("nemonico")
          .agg(dias=("cierre", "size"), moneda=("moneda_yahoo", "first"))
          .to_string())

    # ------------------------------------------------------------------ B
    print("\n" + "=" * 78)
    print("B. BCRPData")
    print("=" * 78)
    try:
        macro = extraer_bcrp()
    except FuenteBloqueada as e:
        print()
        registrar(f"BCRPData no disponible: {e}")
        print("=" * 78)
        print("BCRPData no respondio. Lo de Yahoo YA ESTA GUARDADO y no se")
        print("volvera a descargar. Cuando el BCRP vuelva, ejecuta otra vez")
        print("este mismo script: continuara solo por donde se quedo.")
        print("La incidencia quedo registrada en incidencias_fuente.md.")
        print("=" * 78)
        return

    ruta_macro = cfg.DIR_CRUDOS / f"datos_crudos_bcrp_{cfg.CODIGO_MATRICULA}.csv"
    macro.to_csv(ruta_macro, index=False, encoding="utf-8")
    registrar("Crudo BCRP guardado", filas=len(macro))

    print(f"\n{len(macro):,} fechas · {len(macro.columns) - 1} series")
    print(macro.notna().sum().to_string())

    print("\n" + "=" * 78)
    print("EXTRACCION COMPLETA. Sigue 03_limpieza_datos.py")
    print("=" * 78)


if __name__ == "__main__":
    main()
