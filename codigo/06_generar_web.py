# Meglinho Sneyder Rojas Poma
# Codigo de matricula: 2024200522B
# Tema 61 del temario: Costo de capital por sector en la BVL: mineria, banca, consumo y construccion
# Fecha de extraccion: 2026-11-01

"""
GENERADOR DE LA PAGINA WEB.

Lee las tablas de salidas/ y escribe docs/index.html, una pagina estatica
que GitHub Pages sirve en https://<usuario>.github.io/<repositorio>/

Por que una pagina estatica y no un servidor: una pagina es un archivo, de
modo que carga en un segundo a cualquier hora y no se duerme por inactividad.
Un tablero servido por un plan gratuito se apaga tras unos dias sin visitas,
y quien escanea el codigo QR del poster se encuentra una pantalla de espera.

Los datos quedan incrustados en la pagina, no se leen por red: asi no
dependen de rutas ni de permisos del navegador, y la pagina funciona hasta
abierta desde el disco. Cuando una tabla cambie, se vuelve a ejecutar este
script y la pagina queda al dia.

ENTRADA
    salidas/tabla0_composicion_carteras.csv
    salidas/tabla1_descriptiva.csv
    salidas/tabla3_correlaciones.csv
    salidas/tabla4_betas.csv
    salidas/tabla5_costo_capital.csv
    salidas/tabla8_frontera_carteras.csv
    salidas/tabla9_desempeno_ajustado.csv
    salidas/tabla10_ganancia_diversificacion.csv

SALIDA
    docs/index.html
    docs/datos/*.csv   copia de las tablas, para que el visitante las descargue

Se ejecuta despues de 05_markowitz.py. No toca los datos crudos ni el panel.
"""

import csv
import io
import json
import shutil
import sys
from pathlib import Path


def carpeta_del_codigo():
    """Ubica codigo/ tanto si esto corre como archivo como si se pega en una celda."""
    try:
        return Path(__file__).resolve().parent
    except NameError:
        pass
    cand = []
    if "C3" in globals():
        cand.append(Path(str(globals()["C3"])) / "codigo")
    cand += [Path.cwd(), Path.cwd() / "codigo", Path.cwd().parent / "codigo"]
    for c in cand:
        if (c / "utilidades.py").exists():
            return c.resolve()
    raise SystemExit("No encuentro utilidades.py. Ejecuta esto desde codigo/, "
                     "o define C3 antes de pegar la celda.")


AQUI = carpeta_del_codigo()
RAIZ = AQUI.parent
SALIDAS = RAIZ / "salidas"
DOCS = RAIZ / "docs"

TABLAS = {
    "composicion":     "tabla0_composicion_carteras",
    "descriptiva":     "tabla1_descriptiva",
    "correlaciones":   "tabla3_correlaciones",
    "betas":           "tabla4_betas",
    "costo":           "tabla5_costo_capital",
    "frontera":        "tabla8_frontera_carteras",
    "desempeno":       "tabla9_desempeno_ajustado",
    "diversificacion": "tabla10_ganancia_diversificacion",
}

# Lo que el visitante puede descargar. Solo material propio: los articulos en
# ingles son de sus editoriales y las traducciones son obras derivadas, de modo
# que en la pagina van como enlace al DOI y no como copia.
PRODUCTOS = [
    ("Journal", "El articulo completo, 30 paginas", "productos/journal.pdf"),
    ("Poster del journal", "El poster de la investigacion", "productos/poster.pdf"),
    ("Beamer", "La presentacion de la exposicion", "productos/beamer.pdf"),
]


def leer(nombre):
    ruta = SALIDAS / f"{nombre}.csv"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.relative_to(RAIZ)}. Ejecuta antes "
                         "04_analisis.py y 05_markowitz.py.")
    with io.open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.reader(f))
    cab = [c if c else "Sector" for c in filas[0]]
    return [dict(zip(cab, fila)) for fila in filas[1:]]


def main():
    datos = {k: leer(v) for k, v in TABLAS.items()}

    DOCS.mkdir(exist_ok=True)
    (DOCS / "datos").mkdir(exist_ok=True)
    for v in TABLAS.values():
        shutil.copy2(SALIDAS / f"{v}.csv", DOCS / "datos" / f"{v}.csv")

    plantilla = AQUI / "plantilla_web.html"
    if not plantilla.exists():
        raise SystemExit(f"Falta {plantilla.name} junto a este script.")

    html = io.open(plantilla, encoding="utf-8").read()
    marca = "/*__DATOS__*/"
    if marca not in html:
        raise SystemExit("La plantilla no tiene la marca de los datos.")

    bloque = ("const DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n"
              "const PRODUCTOS = " + json.dumps(PRODUCTOS, ensure_ascii=False) + ";")
    html = html.replace(marca, bloque, 1)

    destino = DOCS / "index.html"
    io.open(destino, "w", encoding="utf-8").write(html)

    print("Pagina generada")
    print(f"  {destino.relative_to(RAIZ)}  ({len(html.encode()) / 1024:.0f} KB)")
    print(f"  {len(TABLAS)} tablas incrustadas, "
          f"{sum(len(v) for v in datos.values())} filas en total")
    print(f"  copia descargable en docs/datos/ ({len(TABLAS)} archivos)")
    print()
    print("Para publicarla:")
    print("  1. git add docs && git commit -m 'Agrega la pagina web' && git push")
    print("  2. En GitHub: Settings, Pages, Source: Deploy from a branch,")
    print("     Branch: main, carpeta /docs, y Save")
    print("  3. En unos minutos queda en https://<usuario>.github.io/<repositorio>/")
    print()
    faltan = [p for _, _, p in PRODUCTOS if not (DOCS / p).exists()]
    if faltan:
        print("Pendiente: copia tus PDF a docs/productos/ con estos nombres:")
        for p in faltan:
            print("  ", p)


if __name__ == "__main__":
    main()
