"""Calcula la exactitud real de la BiGRU y de la distancia de edición con la hoja de etiquetado experto ya llena.
Uso: python evaluar_hoja_experta.py hoja_etiquetado_experto_85_textos.xlsx"""
import sys, pandas as pd
d = pd.read_excel(sys.argv[1] if len(sys.argv) > 1 else "hoja_etiquetado_experto_85_textos.xlsx", sheet_name="Textos")
d = d[d["Cantón correcto (EXPERTO)"].notna()]
if d.empty: sys.exit("La hoja aún no tiene etiquetas del experto.")
es = d["Cantón correcto (EXPERTO)"] != "NO_ES_CANTON"; w = d["registros"]
for m in ("propuesta BiGRU", "propuesta distancia de edición"):
    ok = (d[m] == d["Cantón correcto (EXPERTO)"])
    print(f"{m:32s} | textos que sí son cantón: {ok[es].sum()}/{es.sum()} ({ok[es].mean():.1%}) | ponderado por registros: {(ok[es]*w[es]).sum()/w[es].sum():.1%}")
print(f"Textos que NO son cantón: {(~es).sum()} ({w[~es].sum():,} registros). Ningún método cerrado puede rechazarlos.")
