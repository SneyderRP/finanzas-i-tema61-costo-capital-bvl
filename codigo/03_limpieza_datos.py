# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: COMPLETAR (AAAA-MM-DD, el dia que ejecutes la extraccion)

"""
LIMPIEZA Y CONSTRUCCION DEL PANEL SECTORIAL.

Entra
    datos_crudos_precios_<codigo>.csv  Yahoo: 24 acciones de la BVL
    datos_crudos_macro_<codigo>.csv    Yahoo: Treasury, tipo de cambio e
                                       indice de mercado si estuvo disponible
    datos_crudos_web_<codigo>.csv      BVL:   sector y moneda de cada accion

Sale
    intermedio_acciones_<codigo>.csv   retornos por accion, para auditoria
    datos_procesados_<codigo>.csv      panel final: 4 sectores x dias

LLAVE COMUN
    Precios y macro se unen por `fecha`. Precios y BVL, por `nemonico`.
    El panel queda indexado por `fecha` + `sector`.

LAS DOS VIAS PARTICIPAN
    API (Yahoo): los precios, la tasa libre de riesgo y el tipo de cambio.
    Scraping (BVL): a que cartera pertenece cada accion y en que moneda
    cotiza. Yahoo devuelve la moneda vacia en 18 de 19 acciones de Lima, de
    modo que sin la BVL se promediarian soles con dolares y el retorno
    sectorial saldria mal. La via de scraping no es decorativa.

EL INDICE DE MERCADO
    Si Yahoo publico el S&P/BVL Peru General, se usa ese.
    Si no, se construye promediando los retornos de las 24 acciones. Ambos
    casos quedan registrados en el log.

    Reparo: las cuatro carteras son subconjuntos del indice construido, lo
    que introduce correlacion mecanica y eleva algo las betas. Por eso se
    calcula tambien, para cada sector, un mercado que EXCLUYE a ese sector.
    El panel lleva las dos columnas y 04_analisis.py reporta las dos
    estimaciones.

CRITERIO DE FALTANTES
    No se rellena ningun hueco. Se conservan los dias con Treasury, tipo de
    cambio y al menos una accion con precio en cada una de las cuatro
    carteras. El panel resultante es balanceado: cuatro filas por fecha.

DECIMALES
    Un retorno diario es del orden de 0.001, de modo que los 3 decimales de
    la Unidad I lo destruirian. Los retornos se expresan en PORCENTAJE y se
    redondean a 4 decimales: una diezmilesima de punto porcentual.
"""

import numpy as np
import pandas as pd

from utilidades import cfg, registrar, hash_sha256, abortar


def cargar():
    f_precios = cfg.DIR_CRUDOS / f"datos_crudos_precios_{cfg.CODIGO_MATRICULA}.csv"
    f_macro = cfg.DIR_CRUDOS / f"datos_crudos_macro_{cfg.CODIGO_MATRICULA}.csv"
    f_web = cfg.ARCHIVO_CRUDO_WEB
    for f in (f_precios, f_macro, f_web):
        if not f.exists():
            abortar(f"Falta {f.name}. Ejecuta antes 01_extraccion_api.py "
                    f"y 02_scraping_web.py.")
    precios = pd.read_csv(f_precios, parse_dates=["fecha"])
    macro = pd.read_csv(f_macro, parse_dates=["fecha"])
    web = pd.read_csv(f_web)
    registrar("Cargado crudo de precios", filas=len(precios))
    registrar("Cargado crudo macro", filas=len(macro))
    registrar("Cargado crudo de la BVL", filas=len(web))
    return precios, macro, web


def sector_de(nemonico):
    for cartera, tickers in cfg.CARTERAS.items():
        if nemonico in tickers:
            return cartera
    return None


def main():
    precios, macro, web = cargar()

    # ------------------------------------------------------------------ 1
    # Moneda de cada accion. La aporta la BVL, no Yahoo.
    moneda = dict(zip(web["nemonico"], web["moneda"]))
    precios["moneda"] = precios["nemonico"].map(moneda)
    faltan = sorted(precios.loc[precios["moneda"].isna(), "nemonico"].unique())
    if faltan:
        registrar(f"AVISO: sin moneda en la BVL, se descartan: {faltan}")
        precios = precios.dropna(subset=["moneda"])

    en_dolares = sorted({n for n, m in moneda.items()
                         if n in set(precios["nemonico"]) and str(m).startswith("US")})
    registrar(f"Acciones en dolares segun la BVL: {', '.join(en_dolares)}")

    # ------------------------------------------------------------------ 2
    # Conversion a soles con el tipo de cambio diario.
    if "tipo_cambio" not in macro.columns:
        abortar("Falta la serie tipo_cambio en el crudo macro.")
    precios = precios.merge(macro[["fecha", "tipo_cambio"]], on="fecha", how="left")
    es_dolar = precios["moneda"].astype(str).str.startswith("US")

    antes = len(precios)
    precios = precios[~(es_dolar & precios["tipo_cambio"].isna())].copy()
    if antes - len(precios):
        registrar(f"Filas en dolares sin tipo de cambio ese dia: "
                  f"{antes - len(precios)}. Se descartan, no se rellenan.")

    es_dolar = precios["moneda"].astype(str).str.startswith("US")
    precios["cierre_soles"] = np.where(es_dolar,
                                       precios["cierre"] * precios["tipo_cambio"],
                                       precios["cierre"])

    # ------------------------------------------------------------------ 3
    # Retorno diario de cada accion, en porcentaje.
    precios = precios.sort_values(["nemonico", "fecha"])
    precios["retorno"] = (precios.groupby("nemonico")["cierre_soles"]
                          .transform(lambda s: 100 * np.log(s / s.shift(1))))
    precios["sector"] = precios["nemonico"].map(sector_de)

    inter = cfg.DIR_PROCESADOS / f"intermedio_acciones_{cfg.CODIGO_MATRICULA}.csv"
    precios.to_csv(inter, index=False, encoding="utf-8")
    registrar(f"Guardado {inter.name}", filas=len(precios))

    con_ret = precios.dropna(subset=["retorno"])

    # ------------------------------------------------------------------ 4
    # Carteras sectoriales: promedio de ponderacion igual.
    # La BVL no publica capitalizacion bursatil, de modo que no se puede
    # ponderar por tamano. Se declara como limitacion del articulo.
    panel = (con_ret.dropna(subset=["sector"])
             .groupby(["fecha", "sector"])
             .agg(Y_retorno_sector=("retorno", "mean"),
                  n_acciones=("retorno", "size"))
             .reset_index())
    registrar("Carteras sectoriales construidas", filas=len(panel))

    # ------------------------------------------------------------------ 5
    # Indice de mercado.
    if "indice_mercado" in macro.columns and macro["indice_mercado"].notna().sum() > 500:
        m = macro.sort_values("fecha").copy()
        m["X1_retorno_mercado"] = 100 * np.log(
            m["indice_mercado"] / m["indice_mercado"].shift(1))
        mercado = m[["fecha", "X1_retorno_mercado"]]
        registrar("Mercado: indice oficial S&P/BVL Peru General")
        origen_mercado = "indice oficial"
    else:
        mercado = (con_ret.groupby("fecha")["retorno"].mean()
                   .rename("X1_retorno_mercado").reset_index())
        registrar(f"Mercado: construido con {con_ret.nemonico.nunique()} "
                  f"acciones de la BVL, ponderacion igual")
        origen_mercado = "construido con las acciones"

    panel = panel.merge(mercado, on="fecha", how="inner")

    # Mercado que excluye al propio sector, para medir la correlacion
    # mecanica que introduce que cada cartera sea parte del indice.
    tot = con_ret.groupby("fecha")["retorno"].agg(suma="sum", n="size")
    sec = (con_ret.dropna(subset=["sector"])
           .groupby(["fecha", "sector"])["retorno"].agg(s_suma="sum", s_n="size")
           .reset_index())
    sec = sec.merge(tot, on="fecha", how="left")
    sec["X1b_mercado_ex_sector"] = np.where(
        sec["n"] > sec["s_n"],
        (sec["suma"] - sec["s_suma"]) / (sec["n"] - sec["s_n"]),
        np.nan)
    panel = panel.merge(sec[["fecha", "sector", "X1b_mercado_ex_sector"]],
                        on=["fecha", "sector"], how="left")

    # ------------------------------------------------------------------ 6
    # Variables macroeconomicas, en variaciones diarias.
    mm = macro.sort_values("fecha").copy()
    mm["X2_treasury_10a"] = mm["treasury_10a"].diff()
    mm["X3_tipo_cambio"] = 100 * np.log(mm["tipo_cambio"] / mm["tipo_cambio"].shift(1))
    EXO = ["X1_retorno_mercado", "X1b_mercado_ex_sector",
           "X2_treasury_10a", "X3_tipo_cambio"]
    panel = panel.merge(mm[["fecha", "X2_treasury_10a", "X3_tipo_cambio"]],
                        on="fecha", how="inner")

    # ------------------------------------------------------------------ 7
    # Sin rellenar, y panel balanceado.
    antes = len(panel)
    panel = panel.dropna(subset=EXO)
    registrar(f"Filas descartadas por faltante en alguna exogena: {antes - len(panel)}")

    completas = panel.groupby("fecha")["sector"].nunique()
    ok = completas[completas == len(cfg.CARTERAS)].index
    antes = len(panel)
    panel = panel[panel["fecha"].isin(ok)]
    registrar(f"Filas descartadas por fecha incompleta: {antes - len(panel)}")

    # ------------------------------------------------------------------ 8
    panel = panel.sort_values(["fecha", "sector"]).reset_index(drop=True)
    panel.insert(0, "id", range(1, len(panel) + 1))
    panel["fecha"] = panel["fecha"].dt.strftime("%Y-%m-%d")
    NUM = ["Y_retorno_sector"] + EXO
    panel[NUM] = panel[NUM].round(4)
    panel = panel[["id", "fecha", "sector", "Y_retorno_sector"] + EXO + ["n_acciones"]]

    panel.to_csv(cfg.ARCHIVO_PROCESADO, index=False, encoding="utf-8")
    firma = hash_sha256(cfg.ARCHIVO_PROCESADO)
    registrar(f"Tabla final | filas={len(panel)} | SHA-256: {firma}")

    print("\n" + "=" * 78)
    print("HASH DE LA TABLA FINAL (va al README)")
    print("=" * 78)
    print(firma)
    print("=" * 78)
    print(f"Filas: {len(panel)} | Columnas: {len(panel.columns)}")
    print(f"Periodo: {panel.fecha.min()} a {panel.fecha.max()}")
    print(f"Faltantes: {int(panel.isna().sum().sum())}")
    print(f"Indice de mercado: {origen_mercado}")
    print()
    print("Observaciones por sector:")
    print(panel.sector.value_counts().to_string())
    print()
    print("Acciones promedio por cartera y dia:")
    print(panel.groupby("sector")["n_acciones"].mean().round(2).to_string())
    print()
    print(panel.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
