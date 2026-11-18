"""
manuali_pdf.py: rifa' i manuali in PDF partendo dai .md.

  1. trasforma MANUALE_WINDOWS.md e MANUALE_MAC.md in pagine HTML, con la grafica di manuali.css;
  2. Chrome (o Chromium) le "stampa" in PDF A4 accanto ai .md.

Uso, dalla cartella del progetto:
    python strumenti/manuali_pdf.py

Serve:  pip install markdown   e Chrome o Chromium installato.
Ciao / Francesco

PS: sta qui, nel progetto, apposta. La prima versione viveva in una cartella di lavoro
    temporanea, ed e' sparita con lei. Lezione imparata.
"""
import shutil, subprocess
import markdown, re, html, sys
from pathlib import Path
QUI = Path(__file__).resolve().parent; css = (QUI/"manuali.css").read_text(encoding="utf-8")
repo = QUI.parent
for n in ["MANUALE_WINDOWS","MANUALE_MAC"]:
    s = (repo/f"{n}.md").read_text(encoding="utf-8")
    # blocchi di codice rientrati dentro gli elenchi: li rendiamo <pre> a mano
    s = re.sub(r"(?ms)^    ```\n(.*?)\n    ```$", lambda m: "    <pre><code>"+html.escape("\n".join(l[4:] for l in m.group(1).split("\n"))).replace("\n","&#10;")+"</code></pre>", s)
    h = markdown.markdown(s, extensions=["tables","fenced_code","sane_lists"])
    i = h.find("<h2>Chi l")
    if i >= 0: h = h[:i]+"<div style='break-inside:avoid'>"+h[i:]+"</div>"
    (QUI/f"{n}.html").write_text(f"<!doctype html><html lang='it'><meta charset='utf-8'><title>{n}</title><style>{css}</style><body>{h}</body></html>", encoding="utf-8")

# Chrome fa da tipografo: HTML dentro, PDF A4 fuori.
chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser",
               "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome") if shutil.which(c) or Path(c).exists()), None)
if not chrome:
    sys.exit("Serve Chrome o Chromium per fare i PDF (le pagine HTML sono pronte in strumenti/).")
for n in ["MANUALE_WINDOWS", "MANUALE_MAC"]:
    subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={repo / (n + '.pdf')}", (QUI / f"{n}.html").as_uri()],
                   check=True, stderr=subprocess.DEVNULL)
    (QUI / f"{n}.html").unlink()
    print(f"[ok] {n}.pdf")
