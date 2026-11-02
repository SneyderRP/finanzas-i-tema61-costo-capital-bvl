# Diccionario de variables

**Tema N.º 61:** Costo de capital por sector en la BVL (minería, banca,
consumo y construcción)
**Archivo descrito:** `datos_procesados/datos_procesados_2024200522B.csv`
**Dimensiones:** 3 672 filas por 9 columnas · 918 fechas por 4 sectores
**Periodo:** 2021-11-02 a 2026-10-30
**Llave del panel:** `fecha` + `sector`

Exigido por el numeral 2.4.2: nombre, definición, unidad de medida,
frecuencia, fuente exacta y URL o endpoint de origen.

---

## Identificadores

| Columna | Definición | Unidad | Frecuencia | Fuente | Endpoint |
|---|---|---|---|---|---|
| `id` | Número correlativo de fila, de 1 a 3 672 | entero | por fila | construida | `03_limpieza_datos.py` |
| `fecha` | Día de negociación | AAAA-MM-DD | diaria | las dos vías | llave común |
| `sector` | Cartera: mineria, banca, consumo o construccion | texto | fija | **BVL (scraping)** | `dataondemand.bvl.com.pe/v1/sector` y `/v1/stock-quote/market` |

## Variable dependiente

| Columna | Definición | Unidad | Frecuencia | Fuente | Endpoint |
|---|---|---|---|---|---|
| `Y_retorno_sector` | Retorno diario de la cartera sectorial: promedio de ponderación igual de los retornos logarítmicos de sus acciones, con los precios convertidos a soles | porcentaje | diaria | Yahoo Finance (precios) y BVL (composición y moneda) | `query1.finance.yahoo.com/v8/finance/chart/{símbolo}` |

## Variables explicativas

| Columna | Definición | Unidad | Frecuencia | Fuente | Endpoint |
|---|---|---|---|---|---|
| `X1_retorno_mercado` | Retorno diario del índice de mercado, construido como promedio de ponderación igual de las 20 acciones | porcentaje | diaria | Yahoo Finance y BVL | ver arriba |
| `X1b_mercado_ex_sector` | Igual que X1 pero excluyendo las acciones del propio sector. Especificación de robustez | porcentaje | diaria | Yahoo Finance y BVL | ver arriba |
| `X2_treasury_10a` | Variación diaria del rendimiento del bono del Tesoro de EE.UU. a 10 años. Tasa libre de riesgo del CAPM | puntos porcentuales | diaria | Yahoo Finance, símbolo `^TNX` | `query1.finance.yahoo.com/v8/finance/chart/%5ETNX` |
| `X3_tipo_cambio` | Variación diaria del tipo de cambio soles por dólar | porcentaje | diaria | Yahoo Finance, símbolo `USDPEN=X` | `query1.finance.yahoo.com/v8/finance/chart/USDPEN%3DX` |

## Control de calidad

| Columna | Definición | Unidad | Frecuencia | Fuente |
|---|---|---|---|---|
| `n_acciones` | Número de acciones con precio ese día en esa cartera | entero | diaria | **BVL (scraping)** |

En el panel final `n_acciones` es constante por sector (minería 6, banca 3,
consumo 3, construcción 4), porque tras el filtro de liquidez todas las
acciones tienen precio todos los días conservados. Se mantiene en la tabla
como constancia de que ningún promedio sectorial se calculó con menos
acciones de las declaradas.

---

## Transformaciones aplicadas

| Paso | Transformación | Motivo |
|---|---|---|
| 1 | Las acciones en dólares (BAP, BVN, CVERDEC1, IFS, INRETC1, SCCO) se multiplican por el tipo de cambio de ese día | Un retorno en dólares y uno en soles no son comparables si el tipo de cambio se movió. La moneda la declara la BVL: Yahoo la devuelve vacía en las acciones de Lima |
| 2 | Retorno logarítmico diario de cada acción: `100 × ln(P_t / P_{t-1})` | El logaritmo es aditivo en el tiempo y simétrico ante subidas y bajadas |
| 3 | Promedio de ponderación igual por cartera y fecha | La BVL no publica capitalización bursátil en su backend, de modo que no es posible ponderar por tamaño. Se declara como limitación |
| 4 | Las series macroeconómicas entran en variaciones, no en niveles | En niveles la regresión sería espuria: las series tienen tendencia común |
| 5 | Redondeo a 4 decimales | Un retorno diario es del orden de 0,001. Tres decimales, como en la Unidad I, lo destruirían. Cuatro conservan una diezmilésima de punto porcentual |

## Composición de las carteras

| Cartera | Acciones | Moneda |
|---|---|---|
| Minería | SCCO (US$), BVN (US$), CVERDEC1 (US$), VOLCABC1 (S/), MINSURI1 (S/), NEXAPEC1 (S/) | mixta |
| Banca | BAP (US$), IFS (US$), BBVAC1 (S/) | mixta |
| Consumo | ALICORC1 (S/), BACKUSI1 (S/), INRETC1 (US$) | mixta |
| Construcción | CPACASC1 (S/), UNACEMC1 (S/), CORAREI1 (S/), SIDERC1 (S/) | soles |

Acciones usadas solo para ampliar el índice de mercado: CREDITC1, FERREYC1,
LUSURC1 y ENGIEC1.

## Notas

- Las variables en porcentaje ya vienen multiplicadas por 100: un valor de
  1,5 significa un movimiento de 1,5 %.
- `X2_treasury_10a` está en puntos porcentuales y no en porcentaje, porque es
  la diferencia de un nivel que ya se expresa en porcentaje.
- Las cuatro acciones que cotizan en Nueva York (SCCO, BVN, BAP, IFS) siguen el
  calendario de esa plaza. La intersección de calendarios es la razón de que
  el panel conserve 918 de los 1 255 días posibles.
