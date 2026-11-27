# -*- coding: utf-8 -*-
"""Gera a lista de CAPS do estado de São Paulo a partir do CNES/DATASUS (fonte oficial).

Como usar (precisa de internet; leva alguns minutos):
    python gerar_base_caps.py --teste     # confere a leitura em 3 CAPS (rode isto primeiro)
    python gerar_base_caps.py             # gera tudo

Saídas:
    conhecimento/caps_estado_sp.txt   -> o Acolhe lê este arquivo (RAG)
    caps_gerado/caps_estado_sp.csv    -> planilha
    caps_gerado/caps_estado_sp.pdf    -> PDF (só se tiver reportlab: pip install reportlab)

Os dados vêm do CNES (cnes2.datasus.gov.br): a lista de estabelecimentos do tipo
"Centro de Atenção Psicossocial" em SP e, para cada um, a ficha com endereço, telefone e horário.
"""
import argparse
import csv
import datetime
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request
from xml.sax.saxutils import escape

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE_PADRAO = "http://cnes2.datasus.gov.br"
CAMINHO_LISTA = "/Mod_Ind_Unidade_Listar.asp?VTipo=70&VListar=1&VEstado=35&VMun=&VSubUni=&VComp=00"
CAMINHO_FICHA = "/Exibe_Ficha_Estabelecimento.asp?VCo_Unidade={cod}&VListar=1&VEstado=35&VMun="
CACHE = os.path.join(AQUI, ".cache_cnes")

# Cadastros do tipo 70 que não são CAPS propriamente ditos
EXCLUIR = re.compile(r"RESIDENCIA|\bSRT\b|OFICINA|AMBULATORIO|CONVIVENCIA|TERAPEUTICA", re.I)
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
ABREV = {"Segunda": "Seg", "Terça": "Ter", "Quarta": "Qua", "Quinta": "Qui", "Sexta": "Sex",
         "Sábado": "Sáb", "Domingo": "Dom"}


# ----------------------------------------------------------------------------- rede
def baixar(url, nome_cache):
    os.makedirs(CACHE, exist_ok=True)
    caminho = os.path.join(CACHE, nome_cache)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return _decodificar(f.read())
    ultimo = None
    for tentativa in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (acolhe-chatbot, trabalho academico)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                dados = r.read()
            with open(caminho, "wb") as f:
                f.write(dados)
            return _decodificar(dados)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            ultimo = e
            time.sleep(2 * (tentativa + 1))
    raise RuntimeError(f"falha ao baixar {url}: {ultimo}")


def _decodificar(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1")


# ----------------------------------------------------------------------------- leitura
def html_para_linhas(h):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    t = re.sub(r"(?i)</(td|th)>", " | ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(tr|li|p|div|h\d|table|ul|ol)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\xa0", " ")
    linhas = [re.sub(r"\s+", " ", l).strip(" |") for l in t.split("\n")]
    return [l.strip() for l in linhas if l.strip(" |")]


def valor_apos(linhas, cond):
    for i, l in enumerate(linhas):
        if cond(l) and i + 1 < len(linhas):
            return linhas[i + 1]
    return ""


def horarios(linhas):
    por_dia = {}
    for l in linhas:
        m = re.match(r"^(Segunda|Ter[cç]a|Quarta|Quinta|Sexta|S[aá]bado|Domingo)\S*\W*(\d{2}:\d{2})\s*[àa]s\s*(\d{2}:\d{2})", l, re.I)
        if m:
            d = m.group(1).capitalize().replace("Terca", "Terça").replace("Sabado", "Sábado")
            por_dia[d] = f"{m.group(2)} às {m.group(3)}"
    grupos, atual = [], None
    for d in DIAS:
        if d in por_dia:
            if atual and atual["h"] == por_dia[d] and atual["fim"] == DIAS[DIAS.index(d) - 1]:
                atual["fim"] = d
            else:
                atual = {"ini": d, "fim": d, "h": por_dia[d]}
                grupos.append(atual)
    partes = []
    for g in grupos:
        dias = ABREV[g["ini"]] if g["ini"] == g["fim"] else f"{ABREV[g['ini']]} a {ABREV[g['fim']]}"
        partes.append(f"{dias} {g['h']}")
    return "; ".join(partes)


def parsear(linhas, cod):
    cnes = cod[-7:]
    v_nome = valor_apos(linhas, lambda l: "Nome:" in l and "CNES" in l)
    nome = re.split(r"[\s|]*\b" + cnes + r"\b", v_nome)[0].strip(" |")

    v_log = valor_apos(linhas, lambda l: "Logradouro" in l).replace("|", " ")
    v_log = re.sub(r"\s+", " ", v_log).strip()
    fone = ""
    m = re.search(r"(\(?\d{2}\)?\s*\d{4,5}\s*-?\s*\d{4})\s*$", v_log)
    if m:
        fone, v_log = m.group(1).strip(), v_log[:m.start()].strip()
    m = re.match(r"^(.*?)[\s,]+(\d+[A-Za-z]?|S/?N)$", v_log, re.I)
    logradouro, numero = (m.group(1).strip(" ,"), m.group(2)) if m else (v_log, "")

    v_bai = valor_apos(linhas, lambda l: "Bairro" in l and "CEP" in l).replace("|", " ")
    v_bai = re.sub(r"\s+", " ", v_bai).strip()
    bairro = cep = municipio = ""
    m = re.search(r"^(.*?)\s*\b(\d{8})\b\s*(.*?)\s*-\s*IBGE", v_bai)
    if m:
        bairro, cep, municipio = m.group(1).strip(), m.group(2), m.group(3).strip()
    return {"cnes": cnes, "nome": nome, "logradouro": logradouro, "numero": numero, "bairro": bairro,
            "cep": cep, "municipio": municipio, "telefone": fone, "horario": horarios(linhas)}


# ----------------------------------------------------------------------------- formatação
_ACENTOS = {"sao": "São", "jose": "José", "joao": "João", "jundiai": "Jundiaí", "ribeirao": "Ribeirão",
            "guaruja": "Guarujá", "maua": "Mauá", "andre": "André", "taboao": "Taboão", "jacarei": "Jacareí",
            "aracatuba": "Araçatuba", "marilia": "Marília", "carapicuiba": "Carapicuíba", "taubate": "Taubaté",
            "sumare": "Sumaré", "hortolandia": "Hortolândia", "paulinia": "Paulínia", "braganca": "Bragança",
            "itarare": "Itararé", "tiete": "Tietê", "mococa": "Mococa", "sertaozinho": "Sertãozinho",
            "araraquara": "Araraquara", "ipua": "Ipuã", "iguape": "Iguape", "penapolis": "Penápolis",
            "olimpia": "Olímpia", "catanduva": "Catanduva", "votuporanga": "Votuporanga", "jau": "Jaú",
            "aguai": "Aguaí", "pontal": "Pontal", "mirassol": "Mirassol", "araras": "Araras",
            "itanhaem": "Itanhaém", "peruibe": "Peruíbe", "mongagua": "Mongaguá", "cubatao": "Cubatão",
            "ibiuna": "Ibiúna", "vicente": "Vicente", "ilhabela": "Ilhabela", "cacapava": "Caçapava",
            "pindamonhangaba": "Pindamonhangaba", "uniao": "União", "conceicao": "Conceição",
            "mae": "Mãe", "irmao": "Irmão", "irma": "Irmã", "centro": "Centro", "vila": "Vila",
            "santa": "Santa", "esperanca": "Esperança", "alvorecer": "Alvorecer", "ate": "até"}
_MIN = {"de", "da", "do", "dos", "das", "e", "d"}
_SIGLAS = {"caps", "ad", "i", "ii", "iii", "iv", "ij", "sp", "uf", "cnes", "cat", "ubs", "pam", "hc"}


def bonito(txt):
    out = []
    for p in re.split(r"(\s+)", txt.lower()):
        if not p.strip():
            out.append(p)
        elif p in _SIGLAS:
            out.append(p.upper())
        elif p in _MIN:
            out.append(p)
        elif p in _ACENTOS:
            out.append(_ACENTOS[p])
        else:
            out.append(p[:1].upper() + p[1:])
    return "".join(out)


def endereco(r):
    rua = bonito(r["logradouro"]) + (f", {r['numero']}" if r["numero"] else "")
    cep = f"{r['cep'][:5]}-{r['cep'][5:]}" if len(r["cep"]) == 8 else r["cep"]
    return " - ".join(x for x in [rua, bonito(r["bairro"]), f"CEP {cep}" if cep else ""] if x)


def bloco_txt(r, data):
    linhas = [f"{r['nome_fmt']} (CNES {r['cnes']})",
              f"Município: {r['municipio_fmt']} - SP",
              f"Endereço: {r['end']}"]
    if r["telefone"]:
        linhas.append(f"Telefone: {r['telefone']}")
    if r["horario"]:
        linhas.append(f"Horário: {r['horario']}")
    linhas.append(f"Fonte: CNES/DATASUS, consulta em {data}")
    return "\n".join(linhas)


# ----------------------------------------------------------------------------- saídas
def gerar_pdf(registros, caminho, data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    est = getSampleStyleSheet()
    pequeno = ParagraphStyle("p", parent=est["BodyText"], fontSize=9, leading=12)
    doc = SimpleDocTemplate(caminho, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm, title="CAPS do Estado de São Paulo")
    h = [Paragraph("Centros de Atenção Psicossocial (CAPS) do Estado de São Paulo", est["Title"]),
         Paragraph(f"Fonte: CNES/DATASUS (cnes2.datasus.gov.br), consulta em {data}. "
                   f"Total: {len(registros)} serviços. Confirme por telefone antes de ir: endereços e horários podem mudar.",
                   pequeno), Spacer(1, 10)]
    atual = None
    for r in sorted(registros, key=lambda x: (x["municipio_fmt"], x["nome_fmt"])):
        if r["municipio_fmt"] != atual:
            atual = r["municipio_fmt"]
            h.append(Paragraph(escape(atual), est["Heading2"]))
        txt = f"<b>{escape(r['nome_fmt'])}</b> (CNES {r['cnes']})<br/>{escape(r['end'])}"
        if r["telefone"]:
            txt += f"<br/>Telefone: {escape(r['telefone'])}"
        if r["horario"]:
            txt += f"<br/>Horário: {escape(r['horario'])}"
        h += [Paragraph(txt, pequeno), Spacer(1, 5)]
    doc.build(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teste", action="store_true", help="lê só 3 CAPS e mostra o resultado")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--pausa", type=float, default=0.4, help="segundos entre pedidos (seja gentil com o servidor)")
    ap.add_argument("--base", default=BASE_PADRAO)
    a = ap.parse_args()

    print("Baixando a lista de CAPS de SP no CNES...")
    lista = baixar(a.base + CAMINHO_LISTA, "lista_sp.html")
    codigos = list(dict.fromkeys(re.findall(r"VCo_Unidade=(\d{13})", lista)))
    if not codigos:
        sys.exit("Não encontrei estabelecimentos na página do CNES (o site pode ter mudado).")
    print(f"{len(codigos)} estabelecimentos do tipo CAPS cadastrados em SP.")
    if a.teste:
        codigos = codigos[:3]
    elif a.limite:
        codigos = codigos[:a.limite]

    registros, falhas, incompletos, excluidos = [], [], [], 0
    for i, cod in enumerate(codigos, 1):
        em_cache = os.path.exists(os.path.join(CACHE, f"ficha_{cod}.html"))
        try:
            h = baixar(a.base + CAMINHO_FICHA.format(cod=cod), f"ficha_{cod}.html")
        except RuntimeError as e:
            falhas.append(cod)
            print("  falhou:", cod, e)
            continue
        linhas = html_para_linhas(h)
        r = parsear(linhas, cod)
        if EXCLUIR.search(r["nome"]):
            excluidos += 1
        else:
            if not (r["nome"] and r["logradouro"] and r["municipio"]):
                incompletos.append(cod)
                with open(os.path.join(CACHE, f"debug_{cod}.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(linhas))
            r["nome_fmt"], r["municipio_fmt"], r["end"] = bonito(r["nome"]), bonito(r["municipio"]), endereco(r)
            registros.append(r)
        if a.teste:
            print("\n", {k: v for k, v in r.items() if k in ("nome", "logradouro", "numero", "bairro", "cep", "municipio", "telefone", "horario")})
        elif i % 25 == 0:
            print(f"  {i}/{len(codigos)}")
        if not em_cache:
            time.sleep(a.pausa)

    if a.teste:
        print("\nSe os campos acima estão certos (nome, rua, número, bairro, CEP, município), rode sem --teste.")
        if incompletos:
            print("ATENÇÃO: leitura incompleta. Veja .cache_cnes/debug_*.txt e me envie o conteúdo.")
        return

    data = datetime.date.today().strftime("%d/%m/%Y")
    os.makedirs(os.path.join(AQUI, "conhecimento"), exist_ok=True)
    os.makedirs(os.path.join(AQUI, "caps_gerado"), exist_ok=True)
    registros.sort(key=lambda r: (r["municipio_fmt"], r["nome_fmt"]))
    with open(os.path.join(AQUI, "conhecimento", "caps_estado_sp.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(bloco_txt(r, data) for r in registros) + "\n")
    with open(os.path.join(AQUI, "caps_gerado", "caps_estado_sp.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["municipio", "nome", "cnes", "endereco", "telefone", "horario"])
        for r in registros:
            w.writerow([r["municipio_fmt"], r["nome_fmt"], r["cnes"], r["end"], r["telefone"], r["horario"]])
    try:
        gerar_pdf(registros, os.path.join(AQUI, "caps_gerado", "caps_estado_sp.pdf"), data)
        pdf = "caps_gerado/caps_estado_sp.pdf"
    except ImportError:
        pdf = "(não gerado: rode  pip install reportlab  e execute de novo)"

    print(f"\nPronto: {len(registros)} CAPS ({excluidos} cadastros que não são CAPS foram ignorados).")
    print("  conhecimento/caps_estado_sp.txt  (o Acolhe já usa este arquivo)")
    print("  caps_gerado/caps_estado_sp.csv")
    print("  PDF:", pdf)
    if falhas:
        print(f"  {len(falhas)} fichas não baixaram; rode de novo para tentar só essas (o que já baixou fica em cache).")
    if incompletos:
        print(f"  ATENÇÃO: {len(incompletos)} fichas com leitura incompleta (veja .cache_cnes/debug_*.txt).")


if __name__ == "__main__":
    main()
