# Bitácora de decisiones

**Tema N.º 61:** Costo de capital por sector en la BVL (minería, banca,
consumo y construcción)

Por qué el trabajo quedó así y no de otra forma. Este archivo alimenta la
sección de Materiales y métodos del artículo y sirve de guion para la
disertación.

---

## 2026-10-24 · Montaje del proyecto

Se crea la estructura de las tres subcarpetas del numeral 2.5 y se inicia el
repositorio, para que el historial refleje el proceso real de trabajo y no un
volcado final (numerales 2.4.4 y 2.4.7).

## 2026-10-25 · Por qué la endógena es el retorno sectorial

El costo de capital no es un dato observable: hay que estimarlo. La fórmula
del CAPM lo construye a partir de la beta, y la beta se obtiene regresando el
retorno de una cartera contra el del mercado.

Por eso la variable dependiente es el **retorno diario de cada cartera
sectorial**, que sí es un dato observado, y el costo de capital es el
resultado del artículo, no un supuesto de partida.

## 2026-10-25 · Por qué no se usó la clasificación oficial tal cual

La BVL reconoce nueve sectores y entre ellos no están consumo ni
construcción. Su categoría DIVERSAS agrupa un holding bancario (BAP), uno
financiero (IFS), un retail (INRETC1), una empresa de maquinaria (FERREYC1) y
una cementera (UNACEMC1): entidades sin relación económica entre sí.

Usar esa taxonomía habría producido una beta de DIVERSAS que no significa
nada. Las carteras se arman con la clasificación oficial más la actividad
económica del emisor, y la agrupación se declara.

**Criterio discutible y declarado:** Corporación Aceros Arequipa (CORAREI1) y
SIDERPERU (SIDERC1) se asignan a construcción y no a industria, porque
producen acero de construcción y su demanda sigue al ciclo constructor.

## 2026-10-25 · Exclusiones por duplicidad

Una empresa no puede entrar dos veces en la misma cartera. Se excluyen los
instrumentos que representan al mismo emisor:

- CPACASI1, segunda clase de acción de Cementos Pacasmayo
- BACKUBC1, segunda clase de acción de Backus

## 2026-11-01 · Sustitución de BCRPData

BCRPData dejó de atender solicitudes automatizadas. Siete pruebas desde dos
máquinas y cuatro configuraciones de cabeceras devolvieron una página antibot
en lugar de JSON. El detalle está en `incidencias_fuente.md`.

Las series se sustituyeron por equivalentes de Yahoo Finance, fuente API
sugerida en el numeral 2.4.1. La única pérdida sustantiva es el riesgo país
(EMBIG), que no tiene equivalente: el modelo pasa al CAPM clásico y se
declara en Discusión.

## 2026-11-01 · Filtro de liquidez

Un cotejo detectó una discrepancia del 11,3 % en BUENAVI1. Al investigarla
apareció que Yahoo arrastra el último precio conocido en los días sin
negociación, de modo que contar "días con precio" no mide la liquidez.

Se midió, para cada acción, en qué porcentaje de los días el precio
efectivamente cambió. BUENAVI1 estuvo 341 días seguidos con el mismo precio.

**Regla adoptada**, igual en los cuatro sectores:

1. Un instrumento por grupo económico, el de mayor liquidez.
2. Fuera lo que se mueva menos del 30 % de los días.

Eso dejó fuera a BUENAVI1, INTERBC1, SCOTIAC1, GLORIAI1, ATACOBC1 y CPACASI1,
y trajo a BVN, IFS y BAP en su lugar.

## 2026-11-01 · Por qué el índice de mercado se construye

Se intentó el índice oficial S&P/BVL Perú General en Yahoo (`^SPBLPGPT`):
HTTP 404 en los tres intentos. El índice se construye promediando las 20
acciones con ponderación igual.

Como las cuatro carteras son subconjuntos de ese índice, hay correlación
mecánica que eleva las betas. Por eso se calcula también, para cada sector,
un mercado que excluye a ese sector, y se reportan las dos estimaciones. El
ordenamiento de las betas se mantiene en ambas.

## 2026-11-01 · Ponderación igual y no por capitalización

Lo correcto sería ponderar cada cartera por capitalización bursátil, pero el
backend de la BVL no la publica. La ponderación igual es el estándar cuando
no se dispone de ella. Queda declarado como limitación.

## Pendiente de discutir en el artículo

- La prima de mercado realizada en la ventana fue de 15,4 %, alta porque la
  BVL tuvo un ciclo favorable. Usar el retorno pasado como esperado infla el
  costo de capital. Se reportan las dos estimaciones.
- La ventana conserva 918 de 1 255 días por la intersección de tres
  calendarios distintos.
- Las empresas peruanas grandes se negocian con regularidad en Nueva York y
  no en Lima. Es el hallazgo más interesante del trabajo.
