"""Bobby Bot: ideias -> artes -> postagem no Instagram. Tudo gratuito."""
import os, sys, json, random, time, pathlib, base64, io
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
FILA = ROOT / "fila.json"
POSES = ROOT / "bobby_poses"
REFS = ROOT / "referencias"
CONTEXTOS = ROOT / "contextos.txt"
NEGATIVOS = ROOT / "negativos.txt"
GEMINI_IMG_MODEL = os.getenv("GEMINI_IMG_MODEL", "gemini-3.1-flash-image")
ARTES = ROOT / "artes"
W, H = 1080, 1350
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
MIN_PRONTOS = 7          # mantém sempre X posts prontos na fila
LOTE = 14                # quantos gerar quando a fila baixar


def load():
    return json.loads(FILA.read_text(encoding="utf-8"))


def save(fila):
    FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 1) IDEIAS (Gemini, plano grátis) ----------
def ideias(n=LOTE):
    fila = load()
    recentes = [p["texto"] for p in fila[-60:]]
    prompt = f"""{(ROOT / 'briefing.md').read_text(encoding='utf-8')}

Crie {n} posts NOVOS e originais. Não repita nem pareça com estes já usados:
{json.dumps(recentes, ensure_ascii=False)}

Responda SOMENTE um JSON: lista de objetos com as chaves "texto" e "legenda"."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    r = requests.post(
        url,
        params={"key": os.environ["GEMINI_API_KEY"]},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
        },
        timeout=120,
    )
    r.raise_for_status()
    itens = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    base = int(time.time())
    for i, it in enumerate(itens):
        fila.append({"id": f"p{base}{i:02d}", "texto": it["texto"].strip(),
                     "legenda": it["legenda"].strip(), "status": "pendente"})
    save(fila)
    print(f"{len(itens)} ideias adicionadas")


# ---------- 2) ARTES (Pillow, sem IA de imagem, sem erro de português) ----------
def fonte(tam):
    for p in [ROOT / "fonts" / "fonte.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if pathlib.Path(p).exists():
            return ImageFont.truetype(str(p), tam)
    return ImageFont.load_default()


def quebra(draw, texto, f, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=f) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    linhas.append(atual)
    return linhas

def gerar_cena(contexto):
    """Gera uma cena nova do Bobby a partir de referencias + contexto, via Gemini."""
    refs = [p for p in REFS.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not refs:
        return None
    escolhidas = random.sample(refs, k=min(3, len(refs)))
    partes = []
    negativo = NEGATIVOS.read_text(encoding="utf-8").strip() if NEGATIVOS.exists() else ""
    prompt = f"""Use as imagens anexadas como referencia EXATA do personagem Bobby Capivara:
mesmo rosto, monoculo dourado com corrente, gravata com simbolo do Bitcoin, estilo de arte
(line art preto e branco e dourado, ou fotografia dramatica em preto e branco, dependendo da referencia).

Gere uma cena NOVA, mantendo o personagem identico, no seguinte contexto:
{contexto}

Formato vertical 1080x1350 (proporcao 4:5), estilo para post de Instagram, alta qualidade,
composicao com espaco livre na parte de cima ou de baixo para inserir texto depois.

EVITE: {negativo}"""
    partes.append({"text": prompt})
    for ref in escolhidas:
        b64 = base64.b64encode(ref.read_bytes()).decode()
        mime = "image/png" if ref.suffix.lower() == ".png" else "image/jpeg"
        partes.append({"inline_data": {"mime_type": mime, "data": b64}})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_IMG_MODEL}:generateContent"
    r = requests.post(url, params={"key": os.environ["GEMINI_API_KEY"]},
                       json={"contents": [{"parts": partes}]}, timeout=120)
    if not r.ok:
        print("Erro ao gerar cena:", r.text[:300])
        return None
    data = r.json()
    for parte in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in parte:
            img_bytes = base64.b64decode(parte["inlineData"]["data"])
            return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    return None
def render(post):
    cena = None
    if CONTEXTOS.exists():
        linhas = [l.strip() for l in CONTEXTOS.read_text(encoding="utf-8").splitlines() if l.strip()]
        if linhas:
            contexto = random.choice(linhas)
            cena = gerar_cena(contexto)

    if cena:
        img = cena.resize((W, H)).convert("RGB")
    else:
        img = Image.new("RGB", (W, H), "black")
        poses = [p for p in POSES.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if poses:
            pose = Image.open(random.choice(poses)).convert("RGBA")
            esc = min(W / pose.width, H / pose.height)
            pose = pose.resize((int(pose.width * esc), int(pose.height * esc)))
            img.paste(pose, ((W - pose.width) // 2, H - pose.height), pose)

    d = ImageDraw.Draw(img)
    f = fonte(70)
    linhas_txt = quebra(d, post["texto"].upper(), f, W - 160)
    y = 60
    for l in linhas_txt:
        d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill="white",
               stroke_width=3, stroke_fill="black")
        y += 88
    d.text((W / 2 - 110, H - 40), "@bobbycapivara.astro", font=fonte(26), fill="#F5C518")
    caminho = ARTES / f"{post['id']}.jpg"
    img.save(caminho, quality=95)
    return caminho


def artes():
    fila = load()
    for p in fila:
        if p["status"] == "pendente":
            render(p)
            p["status"] = "pronto"
    save(fila)
    print("artes geradas")


# ---------- 3) POSTAR (Instagram Graph API, grátis) ----------
def postar():
    fila = load()
    prox = next((p for p in fila if p["status"] == "pronto"), None)
    if not prox:
        print("nada pronto para postar")
        return
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.getenv("GITHUB_REF_NAME", "main")
    img_url = f"https://raw.githubusercontent.com/{repo}/{branch}/artes/{prox['id']}.jpg"
    ig, tok = os.environ["IG_USER_ID"], os.environ["IG_TOKEN"]
    api = "https://graph.facebook.com/v21.0"
    r = requests.post(f"{api}/{ig}/media", data={"image_url": img_url,
                      "caption": prox["legenda"], "access_token": tok}, timeout=60)
    if not r.ok:
        raise SystemExit(f"Erro ao criar mídia: {r.text}")
    time.sleep(15)
    r = requests.post(f"{api}/{ig}/media_publish", data={"creation_id": r.json()["id"],
                      "access_token": tok}, timeout=60)
    if not r.ok:
        raise SystemExit(f"Erro ao publicar: {r.text}")
    prox["status"] = "postado"
    save(fila)
    print("postado:", prox["texto"])


# ---------- 4) MANTER (automático: repõe a fila sozinho) ----------
def manter():
    prontos = sum(1 for p in load() if p["status"] == "pronto")
    if prontos < MIN_PRONTOS:
        ideias(LOTE)
        artes()
    else:
        print(f"{prontos} prontos, nada a fazer")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "manter"
    if cmd == "ideias":
        ideias(int(sys.argv[2]) if len(sys.argv) > 2 else LOTE)
    else:
        {"artes": artes, "postar": postar, "manter": manter}[cmd]()
