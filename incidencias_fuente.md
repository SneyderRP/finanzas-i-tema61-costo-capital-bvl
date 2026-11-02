# Incidencias de fuente

Registro de limitaciones técnicas de las fuentes consultadas y de las
decisiones adoptadas (numeral 2.4.3).

Todas las comprobaciones se hicieron con script propio, con User-Agent
identificable y pausa de 1,5 segundos entre solicitudes (numeral 2.4.8). El
detalle con fecha, hora, URL y código de respuesta está en
`log_ejecucion.txt`.

---

## 1. Sondeo inicial de fuentes (2026-10-25)

Se sondearon nueve portales institucionales antes de elegir las vías.

| Fuente | HTTP | robots.txt | Resultado |
|---|---|---|---|
| BCRPData | 200 | PERMITE | Respondía correctamente en esa fecha |
| www.bvl.com.pe | 200 | PERMITE | Aplicación de página única: 9 030 bytes de HTML y cero tablas |
| SMV | 200 | PERMITE | Redirige a gob.pe/smv, ficha institucional |
| SBS | 200 | **PROHIBE** | El robots.txt prohíbe la ruta. Descartada |
| MEF | 200 | PERMITE | Devuelve 212 bytes, sin contenido útil |
| INEI | --- | no se pudo leer | Error de certificado SSL |

---

## 2. El portal de la BVL no entrega su contenido a un cliente automatizado

**Comprobación del 2026-10-25.** Tres rutas distintas devolvieron
exactamente el mismo archivo de 9 030 bytes con `Content-Type: text/html`:
`/`, `/mercado/movimientos-diarios` y `/mercado/indices`.

Tampoco entrega sus propios recursos de JavaScript:
`main.51eaa9480eef072e76bb.js` devolvió los mismos 9 030 bytes de HTML, y una
ruta inventada (`esto-no-existe-98765.js`) devolvió también 9 030 bytes con
HTTP 200 en lugar de 404.

Se repitió la solicitud agregando las cabeceras `Accept`, `Referer` y
`Sec-Fetch-Dest` que envía un navegador, conservando el User-Agent
identificable. Resultado idéntico.

**Conclusión.** El servidor responde el cascarón de la aplicación a cualquier
ruta. El contenido se carga por JavaScript y no es rastreable desde el HTML.

---

## 3. Localización del backend de la BVL

Mediante inspección del tráfico del portal (herramientas de desarrollo,
pestaña Red, filtro Fetch/XHR) se identificó que la aplicación consume otro
dominio:

```
https://dataondemand.bvl.com.pe
```

Es un API Gateway de AWS (cabecera `x-amz-apigw-id`) que responde JSON, con
`access-control-allow-origin: *` y **sin exigir clave**: las cabeceras que
envía el navegador no incluyen `Authorization` ni `X-Api-Key`.

La inspección del tráfico no es descarga manual: no se guardó ningún archivo
desde el navegador. La descarga la realiza íntegramente `02_scraping_web.py`.

| Endpoint | Método | Entrega |
|---|---|---|
| `/v1/sector` | GET | Los nueve sectores oficiales de la BVL |
| `/v1/stock-quote/market` | POST | Instrumentos con precio, sector y moneda |
| `/v1/traded-amount/daily` | GET | Monto negociado de un día |
| `/v1/indices` | GET | Cuatro índices generales |

Cuerpo del POST:
`{"sector": "", "today": true, "companyCode": "", "inputCompany": ""}`.
El campo `sector` acepta los códigos de `/v1/sector`.

---

## 4. La BVL no publica series históricas ni índices sectoriales

**Comprobación del 2026-10-25.**

Ocho rutas plausibles de histórico devolvieron 404:
`/v1/stock-quote/history`, `/v1/stock-quote/historical`, `/v1/quote/history`,
`/v1/indices/history`, `/v1/index/history`, `/v1/chart`,
`/v1/stock-quote/chart` y `/v1/traded-amount/monthly`.

Se intentó pedir un rango de fechas al endpoint `market` en dos formatos
(`startDate`/`endDate` y `dateFrom`/`dateTo`). **El backend ignora los
parámetros de fecha**: ambas peticiones devolvieron respuestas idénticas de
14 877 bytes, y las fechas presentes correspondían a la última negociación de
cada acción, no a una serie temporal.

`/v1/indices` devuelve solo cuatro índices, todos generales (MSCI NUAM Perú
General, Select Capped 15 %, Select y USD). **No existen índices
sectoriales.** Sus valores diarios son ticks de un solo día, cada 15 segundos.

**Conclusión.** El backend de la BVL expone exclusivamente información del día
en curso. No permite construir la serie histórica que el modelo requiere. Por
eso la vía de scraping se destina a la clasificación sectorial y la moneda, y
los precios se obtienen por la vía API.

---

## 5. BCRPData deja de atender solicitudes automatizadas

Esta es la incidencia principal del trabajo.

**Qué ocurrió.** El 2026-10-31, a las 20:00 aproximadamente, BCRPData
respondía con normalidad desde Google Colab. Veinte minutos después, y de
forma sostenida desde entonces, empezó a devolver **HTTP 200 con una página
de interrupción antibot** de 5 996 a 6 183 bytes en lugar de JSON, para
cualquier serie consultada.

**Pruebas realizadas.**

| Fecha | Desde | Configuración | Resultado |
|---|---|---|---|
| 2026-10-31 | Google Colab | User-Agent institucional | HTML, 6 183 bytes |
| 2026-10-31 | Google Colab | Entorno reiniciado, dirección IP nueva | HTML, 6 183 bytes |
| 2026-10-31 | Google Colab | Con `Accept` y `Referer` añadidos | HTML, 6 183 bytes |
| 2026-11-01 | Computadora personal | User-Agent institucional | HTML, 5 996 bytes |
| 2026-11-01 | Computadora personal | Institucional más `Accept` y `Referer` | HTML, 5 996 bytes |
| 2026-11-01 | Computadora personal | Formato `Mozilla/5.0 (compatible; ...)`, identificable | HTML, 5 996 bytes |
| 2026-11-01 | Computadora personal | Agente de navegador completo, solo para diagnóstico | HTML, 5 996 bytes |

El navegador sí accede al catálogo desde la misma máquina y la misma
conexión. Ninguna variante del User-Agent cambia el resultado, de modo que el
filtro no mira el agente: exige resolver un desafío de JavaScript que un
script no puede completar.

**Series afectadas.** Todas. Se comprobó con `PD38026MD` (Índice General
Bursátil BVL), `PD04638PD` y `PD04637PD` (tipo de cambio interbancario) y las
cinco series de la Unidad I: `PD31893DD`, `PD12301MD`, `PD04719XD`,
`PD04709XD` y `PD04692MD`. Esas cinco respondieron 187 veces en septiembre de
2026 para la Unidad I, de modo que el cambio es del portal y no del código.

**Decisión adoptada.** Las series del BCRP se sustituyen por equivalentes de
Yahoo Finance, que el numeral 2.4.1 nombra expresamente como fuente API
sugerida:

| Serie del BCRP | Sustituto | Equivalencia |
|---|---|---|
| Treasury EE.UU. 10 años (`PD04719XD`) | Yahoo `^TNX` | Es la misma tasa. El BCRP solo la reexporta |
| Tipo de cambio venta (`PD04638PD`) | Yahoo `USDPEN=X` | Equivalente para convertir a soles |
| Índice General Bursátil BVL (`PD38026MD`) | Índice construido con 20 acciones de la BVL | Se intentó `^SPBLPGPT` en Yahoo: HTTP 404 |
| EMBIG Perú (`PD04709XD`) | **Sin sustituto** | El riesgo país peruano no tiene equivalente en Yahoo. El modelo pasa al CAPM clásico |

La pérdida del EMBIG es la única consecuencia sustantiva: el costo de capital
se estima como `Ke = Rf + beta × (Rm − Rf)`, sin el término de prima país
propio de los mercados emergentes. Se declara en Discusión.

**Efecto sobre la Unidad I.** La base entregada en la Unidad I sigue siendo
auténtica y verificable: su hash cuadra y los datos crudos están en la
carpeta. Lo que no es posible hoy es reejecutar su descarga. Eso corresponde
al Bloque B del numeral 2.4.6, indisponibilidad sobrevenida de la fuente, y
no al Bloque A.

---

## 6. Validación de Yahoo Finance contra la BVL

Yahoo identifica las acciones de Lima con la bolsa `YHD` y sin moneda
declarada, lo que obligó a comprobar si sus precios son realmente los de la
BVL antes de adoptar la fuente.

**Primer cotejo, 2026-10-31.** Diez acciones de cuatro sectores, cierre del
30 de octubre de Yahoo contra el último precio publicado por el backend de la
BVL para esa misma fecha.

| Nemónico | BVL | Yahoo | Moneda | Resultado |
|---|---|---|---|---|
| ALICORC1 | 13,22 | 13,2200 | S/ | coincide |
| VOLCABC1 | 0,79 | 0,7900 | S/ | coincide |
| BBVAC1 | 2,30 | 2,2980 | S/ | coincide |
| ATACOBC1 | 0,30 | 0,3000 | S/ | coincide |
| CPACASC1 | 8,72 | 8,7200 | S/ | coincide |
| BACKUSI1 | 27,80 | 27,8000 | S/ | coincide |
| INRETC1 | 39,00 | 39,0000 | US$ | coincide |
| UNACEMC1 | 2,40 | 2,4000 | S/ | coincide |
| CVERDEC1 | 68,51 | 68,5100 | US$ | coincide |
| MINSURI1 | 7,37 | 7,3720 | S/ | coincide |

Diez de diez. La comparación usa tolerancia **relativa** del 0,5 %: la BVL
publica el precio redondeado a dos decimales, de modo que una tolerancia
absoluta marcaría como diferencia lo que solo es el redondeo de la fuente
(2,298 frente a 2,30).

Este cotejo es, por sí mismo, el paso 1 de la verificación de autenticidad
del numeral 2.4.6.

---

## 7. Hallazgo: iliquidez del mercado peruano

Un segundo cotejo detectó una discrepancia del 11,3 % en BUENAVI1. Al
investigarla apareció un problema que afectaba a todo el diseño.

**Qué pasaba.** Yahoo arrastra el último precio conocido en los días sin
negociación. Contar "días con precio" no mide la liquidez: un precio repetido
no es una cotización nueva, y produce retornos cero que sesgan la beta hacia
abajo.

**Medición.** Se calculó, para cada acción, en qué porcentaje de los días el
precio efectivamente cambió, y la racha más larga sin moverse.

| Nemónico | Se mueve | Peor racha | Nemónico | Se mueve | Peor racha |
|---|---|---|---|---|---|
| SCCO | 99,7 % | 2 | UNACEMC1 | 59,4 % | 9 |
| BVN | 98,6 % | 2 | SIDERC1 | 57,4 % | 10 |
| VOLCABC1 | 79,6 % | 6 | CORAREI1 | 57,1 % | 15 |
| ALICORC1 | 74,4 % | 6 | NEXAPEC1 | 43,2 % | 27 |
| FERREYC1 | 71,8 % | 11 | ENGIEC1 | 39,5 % | 26 |
| CVERDEC1 | 71,3 % | 13 | LUSURC1 | 36,6 % | 34 |
| MINSURI1 | 70,6 % | 8 | ATACOBC1 | 26,6 % | 65 |
| INRETC1 | 69,5 % | 13 | SCOTIAC1 | 12,5 % | 50 |
| CREDITC1 | 67,5 % | 10 | INTERBC1 | 11,9 % | 56 |
| CPACASC1 | 66,5 % | 9 | GLORIAI1 | 10,1 % | 64 |
| BBVAC1 | 61,8 % | 12 | CPACASI1 | 7,2 % | 121 |
| BACKUSI1 | 60,9 % | 19 | BUENAVI1 | 4,1 % | **341** |

BUENAVI1 estuvo 341 días seguidos con el mismo precio.

**Regla adoptada**, igual en los cuatro sectores:

1. Un instrumento por grupo económico, el de mayor liquidez.
2. Fuera lo que se mueva menos del 30 % de los días.

| Grupo | Sale | Entra | Liquidez |
|---|---|---|---|
| Buenaventura | BUENAVI1 (4,1 %) | BVN | 98,3 % |
| Intercorp | INTERBC1 (11,9 %) | IFS | 98,9 % |
| Credicorp | CREDITC1 (67,5 %) | BAP | 99,4 % |
| Nexa | ATACOBC1 (26,6 %) | NEXAPEC1 | 43,2 % |
| Scotiabank Perú | SCOTIAC1 (12,5 %) | sin reemplazo | no tiene vehículo listado |
| Gloria | GLORIAI1 (10,1 %) | sin reemplazo | bajo el umbral |

**Hallazgo para el artículo.** Las empresas peruanas grandes se negocian con
regularidad en Nueva York y no en Lima. Buenaventura se mueve el 4,1 % de los
días como acción local y el 98,3 % como ADR. Es la misma empresa. Lo mismo
ocurre con Credicorp e Intercorp Financial.

---

## 8. Acciones cotizadas en dólares

Seis de las dieciséis acciones del modelo cotizan en dólares: BAP, BVN,
CVERDEC1, IFS, INRETC1 y SCCO. Sus precios se convierten a soles con el tipo
de cambio diario antes de calcular retornos.

La moneda la declara la BVL. **Yahoo devuelve el campo de moneda vacío en 18
de las 19 acciones de Lima consultadas**, de modo que sin la vía de scraping
no sería posible saber qué acciones hay que convertir.

Se descartaron 870 filas de acciones en dólares en días sin tipo de cambio
publicado. No se rellenaron.
