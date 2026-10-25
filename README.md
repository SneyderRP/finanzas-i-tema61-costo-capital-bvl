# Base de datos y codigo - Unidad II

**Estudiante:** ROJAS POMA MEGLINHO SNEYDER
**Codigo de matricula:** 2024200522B
**Curso:** Finanzas I (055D) · Escuela Profesional de Economia · UNCP · 2026-II
**Tema del temario:** N.o 61 - Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
**Docente:** Dr. Ciro Ivan Machacuay Meza

## 1. Objetivo

Estimar el costo de capital por sector en la Bolsa de Valores de Lima
(mineria, banca, consumo y construccion) a partir de las betas sectoriales
estimadas y de la prima por riesgo pais.

**Estructura:** panel diario de 4 sectores.
**Dependiente:** retorno diario del indice sectorial.
**Explicativas:** retorno del mercado, drivers sectoriales y riesgo pais.

## 2. Fuentes y vias de extraccion

La Unidad II exige **dos vias** (numeral 2.4.1): al menos una API y al menos
un scraping o descarga programatica.

| Via | Fuente | Endpoint o URL | Variables que aporta |
|---|---|---|---|
| API | BCRPData, Banco Central de Reserva del Peru | `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{inicio}/{fin}/esp` | COMPLETAR |
| Scraping o descarga programatica | COMPLETAR | COMPLETAR | COMPLETAR |

**Llave comun:** COMPLETAR (previsto: fecha y sector).

## 3. Ventana congelada (numeral 2.4.5)

| Parametro | Valor |
|---|---|
| `FECHA_INICIO` | COMPLETAR |
| `FECHA_CORTE` | COMPLETAR |

Declarados como constantes en los scripts. Ningun script usa la fecha del dia.

## 4. Orden de ejecucion

```bash
cd codigo
pip install -r ../requirements.txt

python 01_extraccion_api.py      # via API      -> /datos_crudos
python 02_scraping_web.py        # via scraping -> /datos_crudos
python 03_limpieza_datos.py      # union y limpieza -> /datos_procesados
python 04_analisis.py            # tablas y figuras -> /salidas
```

## 5. Versiones

| Componente | Version |
|---|---|
| Sistema operativo | COMPLETAR |
| Python | COMPLETAR |
| Librerias | ver `requirements.txt` |

## 6. Integridad del archivo procesado

| Campo | Valor |
|---|---|
| Archivo | `datos_procesados/datos_procesados_2024200522B.csv` |
| SHA-256 | COMPLETAR (se calcula sobre el archivo real, nunca se escribe a mano) |
| Filas | COMPLETAR |
| Columnas | COMPLETAR |

## 7. Tratamiento de datos faltantes

COMPLETAR

## 8. Claves de API

BCRPData es una API publica de acceso libre y no exige clave. Se entrega
`.env.example` conforme al numeral 2.4.2.

## 9. Repositorio

| Campo | Valor |
|---|---|
| URL | https://github.com/SneyderRP/finanzas-i-tema61-costo-capital-bvl |
| Commits | se actualiza antes de la entrega |

## 10. Trazabilidad de tablas y figuras

COMPLETAR. Toda tabla y figura del articulo se regenera con `04_analisis.py`
(Criterio 4).

## 11. Analisis aplicados

| Tipo | Contenido | Salida |
|---|---|---|
| Descriptivo | COMPLETAR | COMPLETAR |
| Inferencial | COMPLETAR | COMPLETAR |
| Econometrico | COMPLETAR | COMPLETAR |

## 12. Citacion en APA 7 (numeral 2.4.8)

COMPLETAR

## 13. Declaracion sobre el uso de IA

COMPLETAR antes de la entrega.
