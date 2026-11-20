# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
VIA 2 - SCRAPING. Backend de la Bolsa de Valores de Lima.

Como se llego a esta fuente (y esto es lo que se explica en la disertacion):
el portal www.bvl.com.pe es una aplicacion Angular de pagina unica. Su HTML
pesa 9 030 bytes y no contiene ni una tabla: todo lo dibuja JavaScript. Al
inspeccionar el trafico de la pagina (F12, pestana Red) se identifico que los
datos provienen de otro dominio, dataondemand.bvl.com.pe, un API Gateway que
responde JSON sin exigir clave.

No es una API documentada ni publicada: se localizo rastreando el portal. Por
eso cuenta como via de scraping y no como via API (numeral 2.4.1).

QUE APORTA ESTA VIA AL MODELO
  - La clasificacion sectorial oficial de la BVL (sectorCode), que define
    a que cartera pertenece cada accion. Es la dimension 'sector' del panel.
  - La moneda de cotizacion de cada accion, imprescindible porque hay
    acciones en soles y en dolares y no se pueden promediar sin convertir.
Ninguna de las dos la publica el BCRP, asi que esta via no es decorativa
(numeral 2.4.6, Bloque B).

ETICA Y LEGALIDAD (numeral 2.4.8)
  - robots.txt de www.bvl.com.pe consultado el 2026-10-25: PERMITE la ruta.
  - User-Agent identificable, con institucion y correo de contacto.
  - Pausa de 1.5 s entre solicitudes; el minimo exigido es 1 s.
  - Solo informacion publica de mercado. Ningun dato personal.

Los archivos crudos se guardan TAL COMO LLEGAN, sin editar (numeral 2.4.5).
"""

import json
import time

import pandas as pd
import requests

from utilidades import cfg, registrar, registrar_incidencia, abortar

# Los nueve sectores que devuelve /v1/sector. Se consultan todos y no solo
# los cuatro del modelo, para dejar constancia del universo completo.
SECTORES_BVL = ["CM", "CB", "CI", "CD", "CP", "CG", "CS", "CA", "FI"]

CABECERAS = {
    "User-Agent": cfg.USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-PE,es;q=0.9",
    "Origin": "https://www.bvl.com.pe",
    "Referer": "https://www.bvl.com.pe/",
}


def pedir(metodo, ruta, cuerpo=None):
    """Solicitud cortes con reintentos. Registra el codigo HTTP de cada intento."""
    url = cfg.BVL_API + ruta
    for intento in range(1, cfg.REINTENTOS + 1):
        time.sleep(cfg.PAUSA_SEGUNDOS)
        if metodo == "GET":
            r = requests.get(url, headers=CABECERAS, timeout=cfg.TIMEOUT)
        else:
            r = requests.post(url, headers=CABECERAS, json=cuerpo,
                              timeout=cfg.TIMEOUT)
        registrar(f"{metodo} {ruta}" + (f" {json.dumps(cuerpo)}" if cuerpo else ""),
                  http=r.status_code)
        if r.status_code == 200:
            return r
        if r.status_code in (403, 418, 429):
            registrar_incidencia(
                url=url, http=r.status_code,
                detalle=("El backend rechaza solicitudes automatizadas. "
                         "Aplicar el procedimiento de sustitucion de fuente "
                         "del numeral 2.4.3."))
            abortar(f"La BVL respondio HTTP {r.status_code}. Incidencia registrada.")
        time.sleep(cfg.PAUSA_SEGUNDOS * intento * 2)
    abortar(f"Sin respuesta 200 de {url} tras {cfg.REINTENTOS} intentos.")


def guardar_crudo(objeto, nombre):
    """Deja el JSON tal como llego. Es la evidencia primaria y no se edita."""
    ruta = cfg.DIR_WEB / nombre
    ruta.write_text(json.dumps(objeto, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return ruta


def main():
    # ---------------------------------------------------------------- 1
    # Catalogo oficial de sectores
    r = pedir("GET", "/v1/sector")
    sectores = r.json()
    guardar_crudo(sectores, "bvl_sectores.json")
    registrar("Catalogo de sectores guardado", filas=len(sectores))

    mapa_sector = {s["sectorCode"]: s["description"] for s in sectores}

    # ---------------------------------------------------------------- 2
    # Un POST por sector. Asi cada registro llega ya con su sectorCode.
    filas = []
    for codigo in SECTORES_BVL:
        cuerpo = {"sector": codigo, "today": True,
                  "companyCode": "", "inputCompany": ""}
        r = pedir("POST", "/v1/stock-quote/market", cuerpo)
        datos = r.json()
        guardar_crudo(datos, f"bvl_market_{codigo}.json")

        contenido = datos.get("content", [])
        registrar(f"Sector {codigo} ({mapa_sector.get(codigo, '?')})",
                  filas=len(contenido))

        for x in contenido:
            filas.append({
                "nemonico": x.get("nemonico"),
                "codigo_empresa": x.get("companyCode"),
                "empresa": x.get("companyName"),
                "empresa_corto": x.get("shortName"),
                "sector_codigo": x.get("sectorCode") or codigo,
                "sector_bvl": x.get("sectorDescription") or mapa_sector.get(codigo),
                "moneda": x.get("currency"),
                "ultimo_precio": x.get("last"),
                "fecha_ultimo": x.get("lastDate"),
                "operaciones": x.get("operationsNumber"),
                "monto_negociado": x.get("negotiatedAmount"),
                "segmento": x.get("segment"),
            })

    if not filas:
        abortar("El backend respondio, pero no devolvio ningun instrumento.")

    tabla = pd.DataFrame(filas).drop_duplicates(subset=["nemonico"])
    tabla = tabla.sort_values(["sector_codigo", "nemonico"])
    tabla.to_csv(cfg.ARCHIVO_CRUDO_WEB, index=False, encoding="utf-8")
    registrar(f"Guardado {cfg.ARCHIVO_CRUDO_WEB.name}", filas=len(tabla))

    # ---------------------------------------------------------------- 3
    # Comprobacion: los 19 tickers de las cuatro carteras deben estar aqui.
    # Si falta alguno, el panel saldria incompleto y hay que saberlo ahora.
    presentes = set(tabla["nemonico"])
    faltan = [t for t in cfg.TICKERS if t not in presentes]
    if faltan:
        registrar(f"AVISO: no aparecen en la BVL: {', '.join(faltan)}")
    else:
        registrar(f"Los {len(cfg.TICKERS)} tickers de las carteras estan presentes")

    # ---------------------------------------------------------------- 4
    # Monedas de las acciones del modelo: decide la conversion de 03.
    print("\n" + "=" * 78)
    print("MONEDA DE CADA ACCION DE LAS CARTERAS")
    print("=" * 78)
    for cartera, tickers in cfg.CARTERAS.items():
        print(f"\n{cfg.ETIQUETAS[cartera]}")
        for t in tickers:
            fila = tabla[tabla.nemonico == t]
            if fila.empty:
                print(f"   {t:<11} NO APARECE")
            else:
                f = fila.iloc[0]
                print(f"   {t:<11} {str(f.moneda):<5} "
                      f"{str(f.sector_bvl)[:28]:<29} {f.empresa_corto}")

    print(f"\nInstrumentos en el universo: {len(tabla)}")
    print(f"Archivo: {cfg.ARCHIVO_CRUDO_WEB.name}")


if __name__ == "__main__":
    main()
