# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: 2026-11-01

"""
ANALISIS. Genera TODAS las tablas y figuras del articulo.

Criterio 4 de la rubrica: cada tabla y cada figura del articulo debe
regenerarse con este archivo. Una que no se regenere se anula.

MODELO
    El CAPM dice que el retorno de una cartera se explica por el del
    mercado, y que la sensibilidad a ese movimiento es la beta:

        R(s,t) = alfa(s) + beta(s) * Rm(t) + controles + error

    Se estima UNA REGRESION POR SECTOR, sobre la submuestra de esa cartera.
    Es la forma en que se calculan las betas en la practica y es la mas
    facil de explicar: cuatro regresiones, cuatro betas. El coeficiente
    del retorno del mercado en cada una es la beta de ese sector.

    Con las betas estimadas:

        Ke(s) = Rf + beta(s) * (Rm - Rf)

    Rf es el rendimiento promedio del Tesoro de EE.UU. a 10 anos en la
    ventana, y Rm el retorno anualizado del mercado peruano.

ERRORES ESTANDAR
    Newey-West con 5 rezagos (una semana de negociacion). Con datos
    financieros diarios hay heterocedasticidad y autocorrelacion casi
    garantizadas: sin corregir, los p-valores salen artificialmente
    pequenos y se encuentra significancia donde no la hay.

ROBUSTEZ
    Las cuatro carteras son subconjuntos del indice de mercado cuando este
    se construye con las acciones, lo que introduce correlacion mecanica.
    Por eso se estima tambien contra el mercado que excluye a cada sector
    (X1b) y se reportan las dos tablas.
"""

import matplotlib
matplotlib.use("Agg")   # sin ventana: funciona en Colab y en cualquier maquina

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import jarque_bera
from statsmodels.tsa.stattools import adfuller

from utilidades import cfg, registrar, abortar

np.random.seed(cfg.SEMILLA)       # numeral 2.4.4

DIAS_ANIO = 252                   # dias de negociacion al ano
ETQ = cfg.ETIQUETAS


def guardar_tabla(t, nombre, titulo):
    """Deja la tabla en /salidas como .csv y como .tex para LaTeX."""
    t.to_csv(cfg.DIR_SALIDAS / f"{nombre}.csv", encoding="utf-8")
    (cfg.DIR_SALIDAS / f"{nombre}.tex").write_text(
        t.to_latex(caption=titulo, label=f"tab:{nombre}", float_format="%.4f"),
        encoding="utf-8")
    registrar(f"Salida generada: {nombre}")


def guardar_figura(nombre):
    plt.tight_layout()
    plt.savefig(cfg.DIR_SALIDAS / f"{nombre}.png", dpi=300)
    plt.close()
    registrar(f"Salida generada: {nombre}.png")


def estimar_por_sector(d, var_mercado):
    """
    Una regresion por cartera, sobre su propia submuestra.

        R(s,t) = alfa(s) + beta(s)*Rm(t) + c1*Treasury + c2*TipoCambio + e

    El coeficiente de Rm es la beta de ese sector. Devuelve el diccionario
    de modelos y la tabla de betas con su error estandar y su p-valor.
    """
    modelos, filas = {}, []
    formula = (f"Y_retorno_sector ~ {var_mercado} "
               f"+ X2_treasury_10a + X3_tipo_cambio")

    for sector in cfg.CARTERAS:
        sub = d[d["sector"] == sector].dropna(
            subset=["Y_retorno_sector", var_mercado,
                    "X2_treasury_10a", "X3_tipo_cambio"])
        if len(sub) < 100:
            registrar(f"AVISO: {sector} tiene solo {len(sub)} observaciones")
            continue

        mod = smf.ols(formula, data=sub).fit(cov_type="HAC",
                                             cov_kwds={"maxlags": 5})
        modelos[sector] = mod
        inf, sup = mod.conf_int().loc[var_mercado]
        filas.append({
            "Sector": ETQ[sector],
            "Beta": mod.params[var_mercado],
            "Error estandar": mod.bse[var_mercado],
            "z": mod.tvalues[var_mercado],
            "p-valor": mod.pvalues[var_mercado],
            "IC 95% inferior": inf,
            "IC 95% superior": sup,
            "R2": mod.rsquared,
            "N": int(mod.nobs),
        })
        registrar(f"Beta de {ETQ[sector]} = {mod.params[var_mercado]:.4f} "
                  f"(p={mod.pvalues[var_mercado]:.4f}, N={int(mod.nobs)})")

    if not filas:
        abortar("No se pudo estimar ninguna beta.")
    return modelos, pd.DataFrame(filas).set_index("Sector")


def main():
    if not cfg.ARCHIVO_PROCESADO.exists():
        abortar(f"Falta {cfg.ARCHIVO_PROCESADO.name}. "
                f"Ejecuta antes 03_limpieza_datos.py.")
    d = pd.read_csv(cfg.ARCHIVO_PROCESADO, parse_dates=["fecha"])
    registrar("Analisis: panel cargado", filas=len(d))

    # Nivel de la tasa libre de riesgo: el panel guarda su variacion, pero
    # la formula del costo de capital necesita el nivel.
    f_macro = cfg.DIR_CRUDOS / f"datos_crudos_macro_{cfg.CODIGO_MATRICULA}.csv"
    rf_anual = float(pd.read_csv(f_macro)["treasury_10a"].mean())
    registrar(f"Tasa libre de riesgo promedio de la ventana: {rf_anual:.3f} %")

    # ---------------------------------------------------------------- T1
    t1 = (d.groupby("sector")["Y_retorno_sector"]
          .agg(N="size", Media="mean", Desv="std", Minimo="min",
               Mediana="median", Maximo="max"))
    t1.index = [ETQ[i] for i in t1.index]
    t1["Volatilidad anual"] = t1["Desv"] * np.sqrt(DIAS_ANIO)
    t1["Retorno anual"] = t1["Media"] * DIAS_ANIO
    guardar_tabla(t1, "tabla1_descriptiva",
                  "Estadistica descriptiva de los retornos sectoriales diarios")

    # ---------------------------------------------------------------- T2
    filas = []
    for v in ["Y_retorno_sector", "X1_retorno_mercado",
              "X2_treasury_10a", "X3_tipo_cambio"]:
        p = adfuller(d[v].dropna(), autolag="AIC")[1]
        filas.append({"Variable": v, "p-valor ADF": round(p, 4),
                      "Orden": "I(0)" if p < 0.05 else "I(1)"})
    guardar_tabla(pd.DataFrame(filas).set_index("Variable"), "tabla2_adf",
                  "Prueba de raiz unitaria de Dickey-Fuller aumentada")

    # ---------------------------------------------------------------- T3
    piv = d.pivot_table(index="fecha", columns="sector",
                        values="Y_retorno_sector")
    piv.columns = [ETQ[c] for c in piv.columns]
    guardar_tabla(piv.corr().round(4), "tabla3_correlaciones",
                  "Correlaciones entre los retornos sectoriales")

    # ---------------------------------------------------------------- T4
    mods1, b1 = estimar_por_sector(d, "X1_retorno_mercado")
    guardar_tabla(b1, "tabla4_betas",
                  "Betas sectoriales estimadas frente al mercado")
    (cfg.DIR_SALIDAS / "tabla4_salida_completa.txt").write_text(
        "\n\n".join(f"===== {ETQ[s]} =====\n{m.summary()}"
                    for s, m in mods1.items()), encoding="utf-8")

    # ---------------------------------------------------------------- T5
    rm_anual = d.groupby("fecha")["X1_retorno_mercado"].first().mean() * DIAS_ANIO
    prima = rm_anual - rf_anual
    registrar(f"Retorno anualizado del mercado: {rm_anual:.3f} % | "
              f"prima de mercado realizada: {prima:.3f} %")

    # La prima se calcula con el retorno REALIZADO de la ventana. Si el
    # mercado peruano rindio menos que el Tesoro en estos cinco anos, la
    # prima sale negativa y el costo de capital queda por debajo de la tasa
    # libre de riesgo, lo que no tiene sentido economico: nadie exige menos
    # por un activo con riesgo. No es un error de calculo, es una limitacion
    # conocida de usar retornos realizados como aproximacion de los
    # esperados en ventanas cortas. Si ocurre, se reporta igual y se declara
    # en Discusion, y se anade una estimacion con una prima de referencia.
    if prima <= 0:
        registrar("AVISO: la prima de mercado realizada es negativa. "
                  "Se reporta tambien el costo de capital con una prima "
                  "de referencia para mercados emergentes.")

    t5 = b1[["Beta"]].copy()
    t5["Rf (%)"] = rf_anual
    t5["Prima de mercado (%)"] = prima
    t5["Costo de capital Ke (%)"] = rf_anual + t5["Beta"] * prima

    # Segunda columna con una prima de referencia, para contrastar. El valor
    # se declara aqui como constante y se cita su fuente en el articulo.
    PRIMA_REFERENCIA = 7.5   # prima de riesgo de mercado, referencia habitual
    t5["Ke con prima de referencia (%)"] = rf_anual + t5["Beta"] * PRIMA_REFERENCIA
    guardar_tabla(t5.round(4), "tabla5_costo_capital",
                  "Costo de capital por sector segun el CAPM")

    # ---------------------------------------------------------------- T6
    mods2, b2 = estimar_por_sector(d, "X1b_mercado_ex_sector")
    guardar_tabla(b2, "tabla6_betas_robustez",
                  "Robustez: betas frente al mercado que excluye al propio sector")

    # ---------------------------------------------------------------- T7
    diag = []
    for s, mod in mods1.items():
        jb, jbp, sesgo, curt = jarque_bera(mod.resid)
        diag.append({"Especificacion": ETQ[s],
                     "R2": round(mod.rsquared, 4),
                     "Durbin-Watson": round(sm.stats.durbin_watson(mod.resid), 4),
                     "Jarque-Bera": round(jb, 2),
                     "p-valor JB": round(jbp, 4),
                     "Asimetria": round(sesgo, 4),
                     "Curtosis": round(curt, 3),
                     "N": int(mod.nobs)})
    guardar_tabla(pd.DataFrame(diag).set_index("Especificacion"),
                  "tabla7_diagnostico",
                  "Diagnostico de los residuos")

    # ---------------------------------------------------------------- F1
    plt.figure(figsize=(11, 5))
    for s in cfg.CARTERAS:
        sub = d[d.sector == s].sort_values("fecha")
        plt.plot(sub.fecha, sub.Y_retorno_sector.cumsum(), label=ETQ[s], lw=1)
    plt.xlabel("Fecha"); plt.ylabel("Retorno acumulado (%)")
    plt.title("Evolución acumulada de las cuatro carteras sectoriales, 2021-2026")
    plt.legend(); plt.grid(alpha=.3)
    guardar_figura("figura1_evolucion_sectorial")

    # ---------------------------------------------------------------- F2
    fig, ejes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for eje, s in zip(ejes.ravel(), cfg.CARTERAS):
        sub = d[d.sector == s].sort_values("fecha")
        eje.plot(sub.fecha, sub.Y_retorno_sector, lw=.5)
        eje.set_title(ETQ[s]); eje.grid(alpha=.3)
        eje.set_ylabel("Variación diaria (%)")
    plt.suptitle("Retornos diarios por sector")
    guardar_figura("figura2_retornos_diarios")

    # ------------------------------------------------------------- F3-F6
    for i, s in enumerate(cfg.CARTERAS, start=3):
        sub = d[d.sector == s]
        plt.figure(figsize=(6.5, 5))
        plt.scatter(sub.X1_retorno_mercado, sub.Y_retorno_sector, s=6, alpha=.35)
        pend, corte = np.polyfit(sub.X1_retorno_mercado, sub.Y_retorno_sector, 1)
        eje_x = np.linspace(sub.X1_retorno_mercado.min(),
                            sub.X1_retorno_mercado.max(), 100)
        plt.plot(eje_x, corte + pend * eje_x, lw=2, color="firebrick")
        plt.xlabel("Retorno del mercado (%)")
        plt.ylabel(f"Retorno de {ETQ[s]} (%)")
        plt.title(f"{ETQ[s]} frente al mercado · beta = {pend:.3f}")
        plt.grid(alpha=.3)
        guardar_figura(f"figura{i}_{s}_vs_mercado")

    # ---------------------------------------------------------------- F7
    plt.figure(figsize=(7, 5))
    orden = b1.sort_values("Beta")
    plt.barh(orden.index, orden["Beta"], color="steelblue")
    plt.axvline(1, color="firebrick", ls="--", lw=1)
    plt.xlabel("Beta estimada")
    plt.title("Beta por sector. La línea marca la beta del mercado")
    plt.grid(axis="x", alpha=.3)
    guardar_figura("figura7_betas")

    # ---------------------------------------------------------------- F8
    plt.figure(figsize=(7, 5))
    col = ("Costo de capital Ke (%)" if prima > 0
           else "Ke con prima de referencia (%)")
    orden = t5.sort_values(col)
    plt.barh(orden.index, orden[col], color="darkseagreen")
    plt.axvline(rf_anual, color="firebrick", ls="--", lw=1)
    plt.xlabel("Costo de capital anual (%)")
    plt.title("Costo de capital por sector. La línea marca la tasa libre de riesgo")
    plt.grid(axis="x", alpha=.3)
    guardar_figura("figura8_costo_capital")

    registrar("Analisis terminado.")
    print("\n" + "=" * 78)
    print("BETAS SECTORIALES")
    print("=" * 78)
    print(b1.round(4).to_string())
    print("\n" + "=" * 78)
    print("COSTO DE CAPITAL POR SECTOR")
    print("=" * 78)
    print(t5.round(3).to_string())
    print("\n" + "=" * 78)
    print("ROBUSTEZ: mercado que excluye al propio sector")
    print("=" * 78)
    print(b2[["Beta", "p-valor", "R2"]].round(4).to_string())


if __name__ == "__main__":
    main()
