# -*- coding: utf-8 -*-
"""Base de conhecimento do Acolhe (RAG simples, sem banco vetorial).

Lê os arquivos da pasta `conhecimento/` (.pdf, .txt, .md, .csv), divide em trechos e,
para cada pergunta, devolve os trechos mais parecidos (busca por palavras, estilo BM25).
Só usa Python puro + pypdf (para ler PDF), então instala em qualquer versão do Python.
"""
import math
import os
import re
from collections import Counter

PASTA_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conhecimento")
EXTENSOES = (".pdf", ".txt", ".md", ".csv")
TAMANHO_TRECHO = 900      # caracteres por trecho
SOBREPOSICAO = 150        # repetição entre trechos vizinhos, para não cortar endereços ao meio

_STOP = set("""a o as os um uma uns umas de do da dos das em no na nos nas por para pra com sem sobre ate e ou mas que se
qual quais onde como quando quem eu me meu minha voce vc ele ela eles elas e sao foi ser ter tem ha isso isto esse essa
este esta aquele aquela ao aos ja nao sim mais menos muito muita quero queria preciso gostaria saber pode podem favor""".split())


def _norm(texto):
    import unicodedata
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", texto)


def _tokens(texto):
    out = []
    for p in _norm(texto).split():
        if p in _STOP or len(p) < 2:
            continue
        if len(p) > 3 and p.endswith("s"):     # plural simples: "enderecos" -> "endereco"
            p = p[:-1]
        out.append(p)
    return out


def _ler_arquivo(caminho):
    """Devolve lista de (texto, rótulo_da_fonte)."""
    nome = os.path.basename(caminho)
    if caminho.lower().endswith(".pdf"):
        from pypdf import PdfReader
        paginas = []
        for i, pag in enumerate(PdfReader(caminho).pages, start=1):
            paginas.append(((pag.extract_text() or ""), f"{nome}, p. {i}"))
        return paginas
    with open(caminho, encoding="utf-8", errors="ignore") as f:
        return [(f.read(), nome)]


def _dividir(texto, tamanho=TAMANHO_TRECHO, sobre=SOBREPOSICAO):
    texto = re.sub(r"[ \t]+", " ", texto).strip()
    if len(texto) <= tamanho:
        return [texto] if texto else []
    # Arquivos em blocos separados por linha em branco (ex.: um CAPS por bloco): junta blocos
    # inteiros, sem cortar nenhum ao meio.
    blocos = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    if len(blocos) > 1 and all(len(b) <= tamanho for b in blocos):
        trechos, atual = [], ""
        for b in blocos:
            if atual and len(atual) + 2 + len(b) > tamanho:
                trechos.append(atual)
                atual = b
            else:
                atual = (atual + "\n\n" + b) if atual else b
        if atual:
            trechos.append(atual)
        return trechos
    trechos, ini = [], 0
    while ini < len(texto):
        fim = min(ini + tamanho, len(texto))
        if fim < len(texto):                          # tenta cortar numa quebra de linha/ponto
            corte = max(texto.rfind("\n", ini, fim), texto.rfind(". ", ini, fim))
            if corte > ini + tamanho // 2:
                fim = corte + 1
        trechos.append(texto[ini:fim].strip())
        if fim >= len(texto):
            break
        ini = max(fim - sobre, ini + 1)
    return [t for t in trechos if t]


class BaseConhecimento:
    def __init__(self, pasta=PASTA_PADRAO):
        self.trechos = []        # (texto, fonte)
        self._tf = []
        self._df = Counter()
        self.arquivos = []
        if not os.path.isdir(pasta):
            return
        for nome in sorted(os.listdir(pasta)):
            if nome.lower().startswith("leiame") or not nome.lower().endswith(EXTENSOES):
                continue
            caminho = os.path.join(pasta, nome)
            try:
                for texto, fonte in _ler_arquivo(caminho):
                    for t in _dividir(texto):
                        self.trechos.append((t, fonte))
                self.arquivos.append(nome)
            except Exception as erro:
                print(f"Aviso: não consegui ler {nome}: {erro}")
        for texto, _ in self.trechos:
            c = Counter(_tokens(texto))
            self._tf.append(c)
            self._df.update(c.keys())
        n = max(len(self.trechos), 1)
        self._media = sum(sum(c.values()) for c in self._tf) / n if self.trechos else 1

    def __bool__(self):
        return bool(self.trechos)

    def buscar(self, consulta, k=4, min_termos=1):
        """Devolve até k trechos [(texto, fonte)], só os que realmente têm a ver com a consulta."""
        if not self.trechos:
            return []
        termos = list(dict.fromkeys(_tokens(consulta)))
        if not termos:
            return []
        N = len(self.trechos)
        k1, b = 1.5, 0.75
        pontuados = []
        for i, c in enumerate(self._tf):
            dl = sum(c.values()) or 1
            score, achados = 0.0, 0
            for t in termos:
                f = c.get(t, 0)
                if not f:
                    continue
                achados += 1
                idf = math.log(1 + (N - self._df[t] + 0.5) / (self._df[t] + 0.5))
                score += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / self._media))
            if achados >= min_termos:
                pontuados.append((score, i, achados))
        pontuados.sort(reverse=True)
        if not pontuados:
            return []
        melhor = pontuados[0][0]
        # só mantém trechos próximos do melhor (evita injetar lixo no prompt)
        return [self.trechos[i] for s, i, _ in pontuados[:k] if s >= 0.4 * melhor and s > 0.8]


def carregar_base(pasta=PASTA_PADRAO):
    base = BaseConhecimento(pasta)
    return base if base else None
