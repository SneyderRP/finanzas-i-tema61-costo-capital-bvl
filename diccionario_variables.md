# Diccionario de variables

Tema N.o 61: Costo de capital por sector en la BVL (mineria, banca, consumo
y construccion).

Exigido por el numeral 2.4.2: nombre, definicion, unidad de medida,
frecuencia, fuente exacta y URL o endpoint de origen.

**Llave comun del panel:** `fecha` + `sector`.

---

## Identificadores

| Columna | Definicion | Tipo |
|---|---|---|
| `id` | Numero correlativo de fila | entero |
| `fecha` | Dia de negociacion | AAAA-MM-DD |
| `sector` | mineria, banca, consumo o construccion | texto |

## Variable dependiente

| Columna | Definicion | Unidad | Frecuencia | Fuente | Via | Endpoint o URL |
|---|---|---|---|---|---|---|
| `Y_retorno_sector` | Variacion diaria del indice sectorial | % | diaria | COMPLETAR | scraping | COMPLETAR |

## Variables explicativas

| Columna | Definicion | Unidad | Frecuencia | Fuente | Via | Endpoint o URL |
|---|---|---|---|---|---|---|
| `X1_retorno_mercado` | Variacion diaria del indice general de la BVL | % | diaria | COMPLETAR | scraping | COMPLETAR |
| `X2_COMPLETAR` | Driver sectorial (metales) | COMPLETAR | diaria | BCRPData | API | COMPLETAR |
| `X3_COMPLETAR` | Driver sectorial (tipo de cambio) | COMPLETAR | diaria | BCRPData | API | COMPLETAR |
| `X4_COMPLETAR` | Driver sectorial (tasas) | COMPLETAR | diaria | BCRPData | API | COMPLETAR |
| `X5_riesgo_pais` | Spread EMBIG Peru dividido entre 100 | % | diaria | BCRPData | API | `PD04709XD` |

## Transformaciones aplicadas

| Variable | Transformacion | Motivo |
|---|---|---|
| COMPLETAR | COMPLETAR | COMPLETAR |

## Notas

- El EMBIG se publica en puntos basicos; se divide entre 100 para expresarlo
  en porcentaje, igual que las demas tasas.
- Las variables con prefijo `d_` son variaciones diarias y las calcula
  `04_analisis.py` a partir de los niveles de la tabla final.
