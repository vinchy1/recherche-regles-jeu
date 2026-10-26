"""Met en PDF les règles affichées sur une ou plusieurs pages web, sans rien couper.

    python -I -X utf8 page_pdf.py sortie.pdf URL [URL ...] --fidele [--largeur 1280] [--titre "Nom"]
    python -I -X utf8 page_pdf.py sortie.pdf URL [URL ...] --xpath "//article" [--titre "Nom"]
    python -I -X utf8 page_pdf.py sortie.pdf URL --complet

--fidele : la page entière avec sa mise en page (en-tête, pied de page, couleurs et images de fond, polices),
           sur des pages de --largeur pixels (mise en page « ordinateur » du site), proportions A4. Les images
           sont téléchargées à part : certains sites (Google Sites) interdisent de les afficher ailleurs.
--xpath : bloc(s) de chaque page qui contiennent les règles, dans une mise en page simple (noir sur blanc).
--complet : la page entière, telle que le navigateur l'imprime.
Dans tous les cas : aucun lien cliquable dans le PDF (sommaire compris) et pas de ligne « Source » ajoutée
(le lien de la page est noté dans la note du jeu).
Le navigateur (Chrome, sinon Edge) tourne en arrière-plan avec un profil temporaire : il ne touche pas à
celui de l'utilisateur. À la fin, bilan caractères / images de la source et du PDF.
"""
import argparse, base64, json, mimetypes, os, re, shutil, socket, subprocess, sys, tempfile, time
import urllib.parse, urllib.request
from pathlib import Path

import lxml.html
import pymupdf

NAVIGATEURS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
               r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
               "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
RETIRER = "//script | //noscript | //style | //link | //iframe | //form | //button"
CSS = """
body { font-family: "Segoe UI", "Yu Gothic", "Meiryo", "Microsoft YaHei", "Malgun Gothic", sans-serif;
       font-size: 11pt; line-height: 1.45; color: #000; margin: 0; }
img, svg, video { max-width: 100%; height: auto; }
table { border-collapse: collapse; max-width: 100%; margin: .5em 0; }
td, th { border: 1px solid #888; padding: 3px 6px; vertical-align: top; }
pre, code { white-space: pre-wrap; }
h1, h2, h3, h4 { break-after: avoid; }
img, table, figure { break-inside: avoid; }
.page + .page { break-before: page; }
@page { size: A4; margin: 15mm 14mm; }
"""
# fonds imprimés (couleur, images de fond) ; pages sans marge blanche, à la largeur de la page web ;
# paragraphes, images et titres jamais coupés (une section entière insécable laisserait des pages à moitié
# vides) ; fond du site jusqu'en bas des pages
FIDELE_CSS = """
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
p, figure, img, table, tr, li, blockquote, pre { break-inside: avoid; }
h1, h2, h3, h4 { break-after: avoid; break-inside: avoid; }
%(fond)s
@page { size: %(l)dpx %(h)dpx; margin: 0; }
"""
PX = 0.75  # points PDF par pixel CSS
URL_CSS = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")
IMAGE_CSS = re.compile(r"\.(png|jpe?g|gif|webp|avif|svg)\b|googleusercontent|sitesv-images", re.I)


def navigateur():
    for p in NAVIGATEURS:
        if os.path.exists(p):
            return p
    for nom in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge"):
        if shutil.which(nom):
            return shutil.which(nom)
    sys.exit("ERREUR : ni Chrome ni Edge trouvé.")


def dossier_travail():
    """Dossier temporaire aux droits ordinaires. Sous Windows, tempfile.mkdtemp le réserve au seul utilisateur
    (Python 3.12.4 et suivants) : les processus protégés du navigateur ne peuvent alors ni y lire la page à
    imprimer ni y garder leur profil (PDF jamais écrit, page vide)."""
    while True:
        d = Path(tempfile.gettempdir()) / f"page_pdf_{os.urandom(4).hex()}"
        try:
            d.mkdir()
            return d
        except FileExistsError:
            continue


def lancer(nav, profil, args, timeout=120):
    cmd = [nav, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
           "--disable-extensions", f"--user-data-dir={profil}", "--virtual-time-budget=15000", *args]
    pdf = next((Path(a.split("=", 1)[1]) for a in args if a.startswith("--print-to-pdf=")), None)
    if pdf:
        pdf.unlink(missing_ok=True)
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    # Chrome / Edge peuvent rendre la main tout de suite et finir en arrière-plan (constaté en 2026 sous
    # Windows) : la page n'arrive plus sur la sortie (--dump-dom) et le PDF est écrit après coup.
    if "--dump-dom" in args and not r.stdout.strip():
        return dom_devtools(nav, profil, args[-1], timeout)
    if pdf:
        attendre_fichier(pdf, timeout)
    return r.stdout.decode("utf-8", "replace")


def attendre_fichier(f, timeout):
    """Attend que le fichier existe et que sa taille ne bouge plus (écriture terminée)."""
    taille, debut = -1, time.time()
    while time.time() - debut < timeout:
        t = f.stat().st_size if f.exists() else -1
        if t > 0 and t == taille:
            return
        taille = t
        time.sleep(0.5)


class _WebSocket:
    """Client WebSocket minimal (bibliothèque standard) pour le protocole DevTools du navigateur."""

    def __init__(self, url):
        u = urllib.parse.urlparse(url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=60)
        cle = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(f"GET {u.path} HTTP/1.1\r\nHost: {u.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                       f"Sec-WebSocket-Key: {cle}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
        rep = b""
        while b"\r\n\r\n" not in rep:
            bloc = self.s.recv(4096)
            if not bloc:
                raise OSError("DevTools : connexion refusée")
            rep += bloc
        if b" 101 " not in rep.split(b"\r\n", 1)[0]:
            raise OSError("DevTools : " + rep.split(b"\r\n", 1)[0].decode("latin-1"))
        self.buf, self.n = rep.split(b"\r\n\r\n", 1)[1], 0

    def _lire(self, n):
        while len(self.buf) < n:
            bloc = self.s.recv(65536)
            if not bloc:
                raise OSError("DevTools : connexion fermée")
            self.buf += bloc
        d, self.buf = self.buf[:n], self.buf[n:]
        return d

    def _envoyer(self, texte):
        data, masque = texte.encode(), os.urandom(4)
        n = len(data)
        if n < 126:
            tete = bytes([0x81, 0x80 | n])
        elif n < 65536:
            tete = bytes([0x81, 0x80 | 126]) + n.to_bytes(2, "big")
        else:
            tete = bytes([0x81, 0x80 | 127]) + n.to_bytes(8, "big")
        self.s.sendall(tete + masque + bytes(b ^ masque[i % 4] for i, b in enumerate(data)))

    def _message(self):
        morceaux = []
        while True:
            b0, b1 = self._lire(2)
            n = b1 & 0x7F
            if n == 126:
                n = int.from_bytes(self._lire(2), "big")
            elif n == 127:
                n = int.from_bytes(self._lire(8), "big")
            data, op = self._lire(n), b0 & 0x0F
            if op == 8:
                raise OSError("DevTools : connexion fermée")
            if op in (9, 10):  # ping / pong
                continue
            morceaux.append(data)
            if b0 & 0x80:
                return b"".join(morceaux).decode("utf-8", "replace")

    def appel(self, methode, **params):
        self.n += 1
        self._envoyer(json.dumps({"id": self.n, "method": methode, "params": params}))
        while True:
            m = json.loads(self._message())
            if m.get("id") == self.n:
                if "error" in m:
                    raise OSError(f"DevTools {methode} : {m['error'].get('message')}")
                return m.get("result", {})


def dom_devtools(nav, profil, url, timeout=120):
    """DOM de la page lu par le protocole DevTools (quand --dump-dom ne renvoie rien) ; "" en cas d'échec."""
    # profil à part : le navigateur lancé par --dump-dom tourne peut-être encore sur le profil habituel, et un
    # second navigateur sur le même profil lui confierait la page puis s'arrêterait aussitôt
    profil = f"{profil}_devtools"
    fichier = Path(profil) / "DevToolsActivePort"
    fichier.unlink(missing_ok=True)
    # Windows : processus détaché, sinon le navigateur s'arrête avant d'ouvrir le port DevTools
    detache = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    subprocess.Popen([nav, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                      "--disable-extensions", f"--user-data-dir={profil}", "--remote-debugging-port=0",
                      "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=detache)
    debut = time.time()
    while not (fichier.exists() and len(fichier.read_text().split()) >= 2):
        if time.time() - debut > 30:
            return ""
        time.sleep(0.2)
    port, chemin = fichier.read_text().split()[:2]
    navig = None
    try:
        navig = _WebSocket(f"ws://127.0.0.1:{port}{chemin}")
        cible = navig.appel("Target.createTarget", url=url)["targetId"]
        onglet = _WebSocket(f"ws://127.0.0.1:{port}/devtools/page/{cible}")
        # l'onglet commence sur une page vide déjà « complete » : attendre la page demandée, chargée
        while time.time() - debut < timeout:
            etat = onglet.appel("Runtime.evaluate", returnByValue=True,
                                expression="location.href != 'about:blank' && document.readyState == 'complete'")
            if etat.get("result", {}).get("value") is True:
                break
            time.sleep(0.5)
        time.sleep(3)  # scripts lancés après le chargement (comme --virtual-time-budget)
        html = onglet.appel("Runtime.evaluate", expression="document.documentElement.outerHTML",
                            returnByValue=True)["result"].get("value", "")
        return "<!DOCTYPE html>\n" + html if html else ""
    except (OSError, KeyError, ValueError):
        return ""
    finally:
        if navig:
            try:
                navig.appel("Browser.close")
            except OSError:
                pass
        time.sleep(1)  # le temps que le navigateur libère son profil


def compter(texte):
    return len(re.sub(r"\s+", "", texte))


def sans_liens(el):
    """Liens gardés comme texte, avec leur style, mais plus cliquables dans le PDF."""
    for a in el.iter("a"):
        a.attrib.pop("href", None)


class Images:
    """Télécharge chaque image une seule fois dans le dossier de travail et donne son adresse locale."""

    def __init__(self, dossier):
        self.dossier, self.vues, self.echecs = dossier, {}, []
        dossier.mkdir(parents=True, exist_ok=True)

    def locale(self, url):
        if not url.startswith(("http://", "https://")):
            return url
        if url not in self.vues:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data, typ = r.read(), r.headers.get_content_type()
                if not typ.startswith("image/"):
                    raise ValueError(f"reçu {typ} au lieu d'une image")
                f = self.dossier / f"image_{len(self.vues) + 1}{mimetypes.guess_extension(typ) or '.img'}"
                f.write_bytes(data)
                self.vues[url] = f.as_uri()
            except Exception as e:  # laissée à son adresse d'origine, et signalée dans le bilan
                self.vues[url] = url
                self.echecs.append(f"{url[:100]} ({e})")
        return self.vues[url]

    def css(self, texte):
        return URL_CSS.sub(lambda m: f'url("{self.locale(m.group(2))}")' if IMAGE_CSS.search(m.group(2))
                           else m.group(0), texte)


def plus_grande(srcset):
    """Adresse la plus large d'un srcset (« a.jpg 480w, b.jpg 1280w »)."""
    best, taille = None, -1.0
    for part in srcset.split(","):
        bits = part.split()
        if not bits:
            continue
        n = float(re.sub(r"[^\d.]", "", bits[1]) or 0) if len(bits) > 1 else 1.0
        if n > taille:
            best, taille = bits[0], n
    return best


def epingles(doc):
    """Sélecteurs CSS des éléments épinglés (position fixed / sticky) de la page, styles liés compris.
    À l'impression, un élément épinglé est répété sur chaque page (barre de menu, bannière de cookies)."""
    textes = [st.text or "" for st in doc.xpath("//style")]
    for href in doc.xpath("//link[@rel='stylesheet']/@href"):
        try:
            req = urllib.request.Request(href, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                textes.append(r.read().decode("utf-8", "replace"))
        except Exception:
            pass
    regles = {"fixed": set(), "sticky": set()}
    for t in textes:
        t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        for m in re.finditer(r"([^{}@;]+)\{[^{}]*?position\s*:\s*(fixed|sticky)", t):
            regles[m.group(2)].add(m.group(1).strip())
    return regles


def fidele(nav, profil, url, travail, images, largeur):
    """Page entière avec sa mise en page, enregistrée en HTML local ; renvoie (fichier, caractères, images)."""
    dom = lancer(nav, profil, ["--dump-dom", url])
    if not dom.strip():
        sys.exit(f"ERREUR : page vide ou inaccessible : {url}")
    doc = lxml.html.fromstring(dom, base_url=url)
    for x in doc.xpath("//script | //noscript | //iframe | //base | //link[@rel='preload' or @rel='prefetch']"):
        x.drop_tree()
    doc.make_links_absolute(url)
    # boutons d'interface sans texte (« copier le lien du titre » de Google Sites…) : icônes géantes sinon
    for x in doc.xpath("//*[@role='button'][not(normalize-space())][.//*[local-name()='svg']]"):
        x.drop_tree()
    for x in doc.xpath("//picture/source"):
        x.drop_tree()
    # éléments épinglés : bannières de cookies retirées, le reste (barre de menu…) laissé en haut de la page
    regles = epingles(doc)
    fixes = {s[1:] for s in regles["fixed"] if re.fullmatch(r"\.[\w-]+", s)}
    for el in doc.xpath("//*[contains(translate(text(),'COKIE','cokie'),'cookie')]"):
        for anc in el.iterancestors():
            if fixes & set((anc.get("class") or "").split()) or "fixed" in (anc.get("style") or ""):
                if anc.getparent() is not None:  # bannière déjà retirée (plusieurs textes « cookie » dedans)
                    anc.drop_tree()
                break
    for el in doc.xpath("//*[contains(@style,'fixed') or contains(@style,'sticky')]"):
        el.set("style", re.sub(r"position\s*:\s*(fixed|sticky)", "position: absolute", el.get("style")))
    deplier = "".join(f"{s} {{ position: absolute !important; }}\n" for s in regles["fixed"])
    deplier += "".join(f"{s} {{ position: static !important; }}\n" for s in regles["sticky"])
    n_img = 0
    for img in doc.xpath("//img"):
        src = next((img.get(a) for a in ("data-src", "data-lazy-src", "data-original") if img.get(a)), None)
        src = src or (plus_grande(img.get("srcset")) if img.get("srcset") else None) or img.get("src")
        for a in ("srcset", "data-srcset", "sizes", "loading"):
            img.attrib.pop(a, None)
        if src:
            img.set("src", images.locale(src))
            n_img += 1
    for el in doc.xpath("//*[@style]"):
        el.set("style", images.css(el.get("style")))
    for st in doc.xpath("//style"):
        st.text = images.css(st.text or "")
    sans_liens(doc)
    tete = doc.find("head")
    if tete is None:
        tete = lxml.html.Element("head")
        doc.insert(0, tete)
    st = lxml.html.Element("style")
    st.text = deplier + "/*FIDELE*/"  # réglages d'impression, posés par imprimer_fidele()
    tete.append(st)
    corps = doc.find("body")
    n_txt = compter(corps.text_content()) if corps is not None else 0
    page = travail / f"page_{len(list(travail.glob('page_*.html'))) + 1}.html"
    page.write_text("<!doctype html>" + lxml.html.tostring(doc, encoding="unicode"), encoding="utf-8")
    return page, n_txt, n_img


def analyser(pdf):
    """Colonne du contenu (x0, x1 en points) et couleur de fond dominante. Les bandeaux pleine largeur et ce
    qui est posé dessus (nom du site, barre de menu de l'en-tête) ne comptent pas."""
    d = pymupdf.open(pdf)
    larg = d[0].rect.width
    xs, couleurs = [], {}
    for p in d:
        images = [pymupdf.Rect(i["bbox"]) for i in p.get_image_info()]
        bandeaux = [r for r in images if r.width >= 0.9 * larg]
        boites = [pymupdf.Rect(b[:4]) for b in p.get_text("blocks")] + images
        xs += [(b.x0, b.x1) for b in boites
               if b.width < 0.9 * larg and not any(r.contains(b) or r.intersects(b) and b.y1 <= r.y1 for r in bandeaux)]
        pix = p.get_pixmap(dpi=12)
        s, n = pix.samples, pix.n
        for i in range(0, len(s), n):
            c = s[i:i + 3]
            couleurs[c] = couleurs.get(c, 0) + 1
    x0, x1 = (min(a for a, _ in xs), max(b for _, b in xs)) if xs else (0, larg)
    fond = max(couleurs, key=couleurs.get) if couleurs else None
    return x0, x1, larg, (f"#{fond[0]:02x}{fond[1]:02x}{fond[2]:02x}" if fond else None)


def imprimer_fidele(nav, profil, page, sortie, largeur):
    """Deux passages : le premier mesure la colonne du contenu et la couleur de fond, le second imprime des
    pages A4 à la largeur de cette colonne (texte plus grand une fois imprimé), fond du site jusqu'en bas."""
    html = page.read_text(encoding="utf-8")

    def imprimer(hauteur, fond):
        regle = f"html, body {{ background-color: {fond} !important; }}" if fond else ""
        page.write_text(html.replace("/*FIDELE*/", FIDELE_CSS % {"l": largeur, "h": hauteur, "fond": regle}),
                        encoding="utf-8")
        sortie.unlink(missing_ok=True)
        lancer(nav, profil, [f"--print-to-pdf={sortie}", "--no-pdf-header-footer", page.as_uri()])
        if not sortie.exists():
            sys.exit(f"ERREUR : le navigateur n'a pas produit de PDF pour {page}")

    imprimer(round(largeur * 297 / 210), None)
    x0, x1, larg, fond = analyser(sortie)
    marge = max(12.0, 0.05 * (x1 - x0))
    x0, x1 = max(0.0, x0 - marge), min(larg, x1 + marge)
    imprimer(round((x1 - x0) / PX * 297 / 210), fond)
    d = pymupdf.open(sortie)
    for p in d:
        p.set_cropbox(pymupdf.Rect(x0, 0, x1, p.mediabox.height))
    return d


def nettoyer(el):
    for x in el.xpath(RETIRER + " | .//*[@role='button'][not(normalize-space())][.//*[local-name()='svg']]"):
        x.drop_tree()
    sans_liens(el)
    for img in el.xpath(".//img"):
        # images chargées à la demande : la vraie adresse est souvent dans data-src
        for a in ("data-src", "data-lazy-src", "data-original", "data-orig-file"):
            if img.get(a):
                img.set("src", img.get(a))
                break
        for a in ("srcset", "data-srcset", "loading", "sizes"):
            img.attrib.pop(a, None)
    for x in el.iter():
        if isinstance(x.tag, str):
            for a in ("style", "class", "width", "height") if x.tag != "img" else ("style", "class"):
                x.attrib.pop(a, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sortie")
    ap.add_argument("urls", nargs="+")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fidele", action="store_true")
    g.add_argument("--xpath")
    g.add_argument("--complet", action="store_true")
    ap.add_argument("--largeur", type=int, default=1280)
    ap.add_argument("--titre", default="")
    a = ap.parse_args()

    nav = navigateur()
    sortie = Path(a.sortie).resolve()
    travail = dossier_travail()
    profil = travail / "profil"
    images = Images(travail / "images")
    try:
        if a.fidele:
            d, n_txt, n_img = pymupdf.open(), 0, 0
            for i, url in enumerate(a.urls):
                page, t, im = fidele(nav, profil, url, travail, images, a.largeur)
                n_txt, n_img = n_txt + t, n_img + im
                d.insert_pdf(imprimer_fidele(nav, profil, page, travail / f"partie_{i + 1}.pdf", a.largeur))
            for p in d:  # numéro de page discret, en bas au centre
                r, n, taille = p.rect, str(p.number + 1), 0.014 * p.rect.width
                x = (r.width - pymupdf.get_text_length(n, fontsize=taille)) / 2
                p.insert_text((x, r.y1 - 0.012 * r.width), n, fontsize=taille, color=(0.35, 0.35, 0.35))
            if a.titre:
                d.set_metadata({**d.metadata, "title": a.titre})
            d.save(sortie)
        elif a.complet:
            if len(a.urls) > 1:
                sys.exit("ERREUR : --complet n'accepte qu'une page ; pour plusieurs pages, utiliser --fidele ou --xpath.")
            dom = lancer(nav, profil, ["--dump-dom", a.urls[0]])
            doc = lxml.html.fromstring(dom or "<html></html>")
            for x in doc.xpath(RETIRER):
                x.drop_tree()
            n_txt, n_img = compter(doc.text_content()), len(doc.xpath("//img"))
            lancer(nav, profil, [f"--print-to-pdf={sortie}", "--no-pdf-header-footer", a.urls[0]])
        else:
            blocs, n_txt, n_img = [], 0, 0
            for url in a.urls:
                dom = lancer(nav, profil, ["--dump-dom", url])
                if not dom.strip():
                    sys.exit(f"ERREUR : page vide ou inaccessible : {url}")
                doc = lxml.html.fromstring(dom, base_url=url)
                doc.make_links_absolute(url)
                trouves = doc.xpath(a.xpath)
                if not trouves:
                    sys.exit(f"ERREUR : l'XPath ne trouve rien sur {url}")
                html = []
                for el in trouves:
                    nettoyer(el)
                    for img in el.xpath(".//img[@src]"):
                        img.set("src", images.locale(img.get("src")))
                    n_txt += compter(el.text_content())
                    n_img += len(el.xpath(".//img[@src]"))
                    html.append(lxml.html.tostring(el, encoding="unicode"))
                blocs.append(f'<div class="page">{"".join(html)}</div>')
            titre = f"<title>{a.titre}</title>" if a.titre else ""
            page = travail / "regles.html"
            page.write_text(f'<!doctype html><html><head><meta charset="utf-8">{titre}<style>{CSS}</style>'
                            f'</head><body>{"".join(blocs)}</body></html>', encoding="utf-8")
            lancer(nav, profil, [f"--print-to-pdf={sortie}", "--no-pdf-header-footer", page.as_uri()])

        if not sortie.exists():
            sys.exit("ERREUR : le navigateur n'a pas produit de PDF.")
        d = pymupdf.open(sortie)
        p_txt = compter("".join(p.get_text() for p in d))
        p_img = len({x[0] for p in d for x in p.get_images()})
        liens = sum(len(p.get_links()) for p in d)
        print(f"PDF : {sortie} — {d.page_count} pages")
        print(f"Texte : source {n_txt} caractères, PDF {p_txt}")
        print(f"Images : source {n_img}, PDF {p_img}")
        if liens:
            print(f"ATTENTION : {liens} lien(s) cliquable(s) restent dans le PDF.")
        # --fidele : la source compte aussi menus et textes posés sur le bandeau, hors de la colonne gardée
        if n_txt and p_txt < (0.9 if a.fidele else 0.95) * n_txt:
            print("ALERTE : le PDF contient nettement moins de texte que la source.")
        if p_img < n_img:
            print("ALERTE : des images de la source manquent peut-être dans le PDF.")
        for e in images.echecs:
            print(f"ALERTE : image non téléchargée : {e}")
    finally:
        shutil.rmtree(travail, ignore_errors=True)


if __name__ == "__main__":
    main()
