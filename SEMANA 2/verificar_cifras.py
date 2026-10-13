"""Verifica que cada cifra decimal del informe (docx o pdf->txt) aparezca en las salidas del notebook o en su JSON.

Uso: python3 -I verificar_cifras.py informe.docx notebook.ipynb resultados.json [--salida reporte.txt]
Una cifra del informe se considera respaldada si algún número del notebook/JSON, redondeado al mismo
número de decimales, es igual a ella (acepta coma o punto decimal y también porcentajes: 0,87 <-> 87,0).
"""
import json, re, sys
import docx


def numeros_notebook(nb_path, js_path):
    nb = json.load(open(nb_path, encoding="utf8"))
    txt = ""
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            for o in c.get("outputs", []):
                if "text" in o:
                    txt += "".join(o["text"]) + "\n"
                for k in ("text/plain", "text/html"):
                    if k in o.get("data", {}):
                        txt += "".join(o["data"][k]) + "\n"
    nums = [float(x) for x in re.findall(r"-?\d+\.\d+|-?\d+", txt)]

    def recorre(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from recorre(v)
        elif isinstance(o, list):
            for v in o:
                yield from recorre(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            yield float(o)
    nums += list(recorre(json.load(open(js_path, encoding="utf8"))))
    return nums


def texto_docx(path):
    d = docx.Document(path)
    partes = [p.text for p in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                partes.append(c.text)
    return "\n".join(partes)


def main():
    doc, nb, js = sys.argv[1:4]
    base = numeros_notebook(nb, js)
    txt = texto_docx(doc).replace("\xa0", " ")
    txt = re.sub(r"https?://\S+", " ", txt)          # URLs y DOI no son cifras del estudio
    txt = re.sub(r"\(\d{4}\)|\b(19|20)\d{2}\b", " ", txt)   # años
    citadas = sorted(set(re.findall(r"\d+[,.]\d+", txt)))
    sin = []
    for c in citadas:
        v = float(c.replace(",", "."))
        d = len(c.replace(",", ".").split(".")[1])
        ok = any(round(x, d) == round(v, d) or round(x * 100, d) == round(v, d) or round(x / 100, d) == round(v, d) for x in base)
        if not ok:
            sin.append(c)
    print(f"Cifras decimales distintas en el informe: {len(citadas)}")
    print(f"Sin respaldo en el notebook/JSON: {len(sin)} -> {sin}")
    return sin


if __name__ == "__main__":
    main()
