# Base de datos y código - Unidad II

**Estudiante:** ROJAS POMA, MEGLINHO SNEYDER
**Código de matrícula:** 2024200522B
**Curso:** Finanzas I (055D) · Escuela Profesional de Economía · UNCP · 2026-II
**Tema del temario:** N.º 61: Costo de capital por sector en la BVL (minería, banca, consumo y construcción)
**Docente:** Dr. Ciro Iván Machacuay Meza

## 1. Objetivo

Estimar el costo de capital de cuatro sectores de la Bolsa de Valores de Lima
a partir de las betas sectoriales estimadas con datos diarios.

Las betas no se suponen: se estiman con una regresión por sector sobre el
retorno del mercado. De ellas se obtiene el costo de capital mediante el
modelo de valoración de activos de capital (CAPM).

| Campo | Valor |
|---|---|
| Estructura | Panel balanceado, 4 sectores por 918 días |
| Observaciones | 3 672 |
| Dependiente | Retorno diario de la cartera sectorial, en porcentaje |
| Explicativas | Retorno del mercado, tasa libre de riesgo y tipo de cambio |
| Acciones | 20 de la BVL (16 en carteras, 4 solo para el índice de mercado) |

## 2. Fuentes y vías de extracción

La Unidad II exige dos vías (numeral 2.4.1): al menos una API y al menos un
scraping o descarga programática.

| Vía | Fuente | Endpoint | Aporta |
|---|---|---|---|
| **Scraping** | Backend de la Bolsa de Valores de Lima | `https://dataondemand.bvl.com.pe/v1/sector` y `/v1/stock-quote/market` | Clasificación sectorial oficial y moneda de cotización de 80 instrumentos |
| **API** | Yahoo Finance | `https://query1.finance.yahoo.com/v8/finance/chart/{símbolo}` | Precio diario de 20 acciones, Tesoro EE.UU. 10 años y tipo de cambio |

**Llave común:** `fecha` para unir precios con las series de mercado,
`nemonico` para unir precios con la clasificación de la BVL. El panel final
queda indexado por `fecha` más `sector`.

**Ninguna vía es decorativa** (numeral 2.4.6, Bloque B). La BVL no aporta una
serie temporal, aporta dos cosas sin las cuales la variable dependiente no
existe: qué acciones componen cada cartera y en qué moneda cotiza cada una.
Yahoo devuelve el campo de moneda vacío en 18 de las 19 acciones de Lima, de
modo que sin la BVL se promediarían soles con dólares en 6 de las 16 acciones
del modelo. La clasificación sectorial, además, es la dimensión del panel:
aparece en todas las tablas y figuras del artículo.

### Cómo se localizó el backend de la BVL

El portal `www.bvl.com.pe` es una aplicación Angular de página única: su HTML
pesa 9 030 bytes y no contiene ninguna tabla. Al inspeccionar el tráfico de la
página se identificó que los datos provienen de `dataondemand.bvl.com.pe`, un
API Gateway que responde JSON sin exigir clave. No es una API documentada: se
localizó rastreando el portal, y por eso cuenta como vía de scraping.

El detalle completo, con códigos de respuesta y fechas, está en
`incidencias_fuente.md`.

## 3. Ventana congelada (numeral 2.4.5)

| Parámetro | Valor |
|---|---|
| `FECHA_INICIO` | 2021-11-01 |
| `FECHA_CORTE` | 2026-10-31 |
| `YF_PERIOD1` | 1635724800 |
| `YF_PERIOD2` | 1793404800 |

Declarados como constantes en `codigo/00_config.py`. Yahoo admite el
parámetro `range=5y`, que es una ventana **móvil**: cambia cada día y
equivale a `datetime.today()`. No se usa. Se emplean `period1` y `period2`
con las fechas fijas convertidas a epoch, de modo que la reejecución produce
el mismo archivo.

## 4. Orden de ejecución

```bash
cd codigo
pip install -r ../requirements.txt

python 02_scraping_web.py     # vía scraping: BVL   -> /datos_crudos/web
python 01_extraccion_api.py   # vía API: Yahoo      -> /datos_crudos/api
python 03_limpieza_datos.py   # unión y limpieza    -> /datos_procesados
python 04_analisis.py         # tablas y figuras    -> /salidas
```

Los scripts guardan cada descarga por separado y no repiten lo que ya está en
disco. Para forzar una descarga limpia, se borra `/datos_crudos/api`.

## 5. Versiones

Ver `requirements.txt`, generado en la máquina donde se construyó la base.

## 6. Integridad del archivo procesado

| Campo | Valor |
|---|---|
| Archivo | `datos_procesados/datos_procesados_2024200522B.csv` |
| SHA-256 | `d5e5ea080f282ccf3c743665ffefe45fb8bec10ea6777ef499ffdffd429a7ba7` |
| Filas | 3 672 |
| Columnas | 9 |
| Periodo | 2021-11-02 a 2026-10-30 |
| Faltantes | 0 |

El hash se coteja contra el archivo entregado, nunca contra una reejecución
posterior (numeral 2.4.5).

## 7. Tratamiento de datos faltantes

**No se rellenó ningún hueco.**

De los 1 255 días posibles de la ventana se conservan **918**. Se descartan
los días en que falta cualquiera de las tres piezas, porque las tres fuentes
siguen calendarios distintos: las acciones de Lima, el Tesoro de EE.UU. y el
tipo de cambio no cierran los mismos feriados. Cada feriado de cualquiera de
los tres elimina el día.

Además se descartaron 870 filas de acciones en dólares en días sin tipo de
cambio publicado: sin él no se pueden convertir a soles y rellenarlos
produciría celdas sin respaldo en la fuente.

El panel resultante es **balanceado**: cuatro filas por fecha, una por
cartera, sin excepción.

### Filtro de liquidez

Se midió, para cada acción, en qué porcentaje de los días el precio
efectivamente **cambió**. Un precio repetido no es una cotización nueva: es
el último valor conocido arrastrado hacia adelante, y produce retornos cero
que sesgan la beta hacia abajo.

Seis acciones se mueven menos del 30 % de los días. BUENAVI1 estuvo **341
días seguidos** con el mismo precio. La tabla completa está en
`incidencias_fuente.md`.

La regla adoptada, igual en los cuatro sectores, es: un instrumento por grupo
económico, el de mayor liquidez, y fuera lo que se mueva menos del 30 % de
los días.

## 8. Claves de API

Ninguna fuente usada exige clave. El backend de la BVL y Yahoo Finance son de
acceso libre. Se entrega `.env.example` conforme al numeral 2.4.2, por si se
incorporara una fuente con token.

## 9. Repositorio

| Campo | Valor |
|---|---|
| URL | https://github.com/SneyderRP/finanzas-i-tema61-costo-capital-bvl |

## 10. Composición de las carteras

| Cartera | Acciones | N |
|---|---|---|
| Minería | SCCO, BVN, CVERDEC1, VOLCABC1, MINSURI1, NEXAPEC1 | 6 |
| Banca | BAP, IFS, BBVAC1 | 3 |
| Consumo | ALICORC1, BACKUSI1, INRETC1 | 3 |
| Construcción | CPACASC1, UNACEMC1, CORAREI1, SIDERC1 | 4 |

Solo para ampliar el índice de mercado, sin formar parte de ninguna cartera:
CREDITC1, FERREYC1, LUSURC1 y ENGIEC1.

El retorno de cada cartera es el promedio de ponderación igual de los
retornos de sus acciones. La BVL no publica capitalización bursátil en su
backend, de modo que no es posible ponderar por tamaño: se declara como
limitación.

## 11. Trazabilidad de tablas y figuras

Todas se regeneran con `04_analisis.py` (Criterio 4).

| Salida | Archivo | Sección |
|---|---|---|
| Tabla 1 | `salidas/tabla1_descriptiva.tex` | Materiales y métodos |
| Tabla 2 | `salidas/tabla2_adf.tex` | Materiales y métodos |
| Tabla 3 | `salidas/tabla3_correlaciones.tex` | Resultados |
| Tabla 4 | `salidas/tabla4_betas.tex` | Resultados |
| Tabla 5 | `salidas/tabla5_costo_capital.tex` | Resultados |
| Tabla 6 | `salidas/tabla6_betas_robustez.tex` | Resultados |
| Tabla 7 | `salidas/tabla7_diagnostico.tex` | Resultados |
| Figura 1 | `salidas/figura1_evolucion_sectorial.png` | Resultados |
| Figura 2 | `salidas/figura2_retornos_diarios.png` | Resultados |
| Figuras 3 a 6 | `salidas/figura{3,4,5,6}_*_vs_mercado.png` | Resultados |
| Figura 7 | `salidas/figura7_betas.png` | Resultados |
| Figura 8 | `salidas/figura8_costo_capital.png` | Resultados |

## 12. Análisis aplicados

| Tipo | Contenido | Salida |
|---|---|---|
| Descriptivo | Media, desviación, mínimo, mediana y máximo del retorno de cada cartera; volatilidad y retorno anualizados; evolución acumulada | `tabla1`, `figura1`, `figura2` |
| Inferencial | Prueba de raíz unitaria de Dickey-Fuller aumentada; correlaciones entre sectores | `tabla2`, `tabla3` |
| Econométrico | Una regresión por sector con errores robustos de Newey-West (5 rezagos); betas con su intervalo de confianza; costo de capital por CAPM; robustez frente al mercado que excluye al propio sector; residuos revisados con Durbin-Watson y Jarque-Bera | `tabla4`, `tabla5`, `tabla6`, `tabla7`, `figuras 3 a 8` |

## 13. Resultados principales

| Sector | Beta | p-valor | R² | Ke con prima realizada | Ke con prima de referencia |
|---|---|---|---|---|---|
| Minería | 1,616 | 0,000 | 0,766 | 28,7 % | 16,0 % |
| Banca | 1,069 | 0,000 | 0,588 | 20,3 % | 11,9 % |
| Construcción | 0,868 | 0,000 | 0,398 | 17,2 % | 10,4 % |
| Consumo | 0,547 | 0,000 | 0,419 | 12,3 % | 8,0 % |

Tasa libre de riesgo promedio de la ventana: 3,886 %. Retorno anualizado del
mercado: 19,266 %. Prima de mercado realizada: 15,380 %.

El ordenamiento es el que predice la teoría: minería amplifica el movimiento
del mercado (beta superior a 1,6), consumo lo amortigua (0,55), banca se
mueve con el mercado. La prueba de robustez frente al mercado que excluye a
cada sector reduce el nivel de las betas pero **conserva el mismo
ordenamiento**, de modo que el resultado no depende de cómo se construya el
índice de mercado.

## 14. Citación en APA 7 (numeral 2.4.8)

Bolsa de Valores de Lima. (2026). *Cotizaciones y clasificación sectorial de
emisores* [Conjunto de datos]. Consultado el 1 de noviembre de 2026.
https://dataondemand.bvl.com.pe

Yahoo Finance. (2026). *Historical market data* [Conjunto de datos].
Consultado el 1 de noviembre de 2026.
https://query1.finance.yahoo.com

## 15. Declaración sobre el uso de IA

Se usó asistencia de IA para redactar y depurar el código de extracción,
dentro de lo permitido por la consigna. El estudiante verificó la fuente
cotejando diez precios al azar contra el backend de la BVL en vivo, con
coincidencia en los diez dentro del redondeo con que la fuente publica sus
precios, detectó por su cuenta el problema de liquidez que invalidaba seis
acciones y puede explicar cada bloque del código durante la disertación.
