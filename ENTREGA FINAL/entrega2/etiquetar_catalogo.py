"""Etiqueta automática (a confirmar por experto) de los 85 textos de cantón sin resolver del data lake,
usando SOLO reglas sobre los catálogos oficiales del INEC (cantones, provincias y parroquias).
Regla aplicada, en orden:
  M  marcador de dato faltante o no geográfico            -> NO_ES_CANTON
  P  el texto es el nombre de una provincia (sin ser cantón) -> NO_ES_CANTON (provincia)
  C  el texto contiene un nombre de cantón completo como secuencia de palabras (un solo cantón) -> ese cantón
  S  el texto es prefijo o sufijo por palabras de un único nombre de cantón       -> ese cantón
  Q  el texto coincide por palabras con una única parroquia (nombre o nombre entre paréntesis) -> cantón de esa parroquia
  -  sin regla aplicable o ambiguo                          -> sin etiqueta (requiere experto)
"""
import re, sys, unicodedata, pandas as pd

def nrm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()

dpa = pd.read_csv("datos/dpa_cantones.csv", dtype=str)
par = pd.read_csv("datos/dpa_parroquias_completo.csv", dtype=str, encoding="utf-8-sig")
CANT = sorted(set(dpa.canton_norm)); PROV = set(dpa.provincia_norm) - set(CANT)
cod2cant = dict(zip(dpa.cod_canton, dpa.canton_norm))
MARCADORES = {"ND", "S D", "S N", "NAN", "SIN REGISTRAR", "SIN DETERMINAR", "NO DELIMITADA", "NO INDICA", "NO REPORTA",
              "INDISTINTO", "EXPORTACION", "EXTRANJERO", "ES"}

def tok(s): return s.split()
def contiene(txt, nombre):                      # nombre como secuencia contigua de palabras dentro de txt
    a, b = tok(txt), tok(nombre)
    return any(a[i:i + len(b)] == b for i in range(len(a) - len(b) + 1))

# variantes de parroquia: nombre completo y lo que va entre paréntesis
pvar = []
for _, r in par.iterrows():
    nom = str(r.parroquia); c = cod2cant.get(r.cod_canton)
    for v in [nom] + re.findall(r"\(([^)]*)\)", nom) + [re.sub(r"\(.*?\)", "", nom)]:
        v = nrm(v)
        if v: pvar.append((v, c))

def etiquetar(t):
    t = nrm(t) if isinstance(t, str) else "NAN"
    if t in MARCADORES: return "NO_ES_CANTON", "M"
    if t in PROV: return "NO_ES_CANTON", "P"
    cs = {c for c in CANT if contiene(t, c)}
    cs = {c for c in cs if not any(c != d and contiene(d, c) for d in cs)}     # el más específico
    LIBRES = {"CANTON", "CAB", "CANTONAL", "CABECERA"} | {w for p in dpa.provincia_norm for w in p.split()}
    if len(cs) == 1:
        c = next(iter(cs)); resto = set(tok(t)) - set(tok(c))
        if resto <= LIBRES: return c, "C"
    ss = {c for c in CANT if tok(c)[:len(tok(t))] == tok(t) or tok(c)[-len(tok(t)):] == tok(t)}
    if len(ss) == 1 and len(t) >= 4: return ss.pop(), "S"
    return "", "-"

if __name__ == "__main__":
    d = pd.read_csv("predicciones_textos_sin_etiqueta.csv")
    d[["etiqueta_catalogo", "regla"]] = [etiquetar(t) for t in d.vn]
    d.to_csv("textos_sin_etiqueta_con_regla.csv", index=False, encoding="utf-8-sig")
    print(d.regla.value_counts().to_dict()); print(d[["vn", "n", "etiqueta_catalogo", "regla"]].to_string())
