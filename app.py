# -*- coding: utf-8 -*-
"""Servidor web do Acolhe (Flask). Rodar com:  python app.py  e abrir http://127.0.0.1:5000

Privacidade: as conversas existem só na memória do servidor, por sessão, e
nada é gravado em arquivo ou banco de dados. Sessões inativas são descartadas.
"""
import time
import uuid
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory

from acolhe_bot import Acolhe, criar_llm
from conhecimento import carregar_base

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Cliente da Groq, criado uma única vez (None se faltar GROQ_API_KEY ou a biblioteca).
LLM = criar_llm()
# Base de conhecimento: arquivos da pasta conhecimento/ (PDF, TXT, MD, CSV).
BASE = carregar_base()
print(f"Base de conhecimento: {len(BASE.trechos)} trechos de {BASE.arquivos}" if BASE
      else "Base de conhecimento vazia (coloque arquivos na pasta conhecimento/).")
print("Groq ativa." if LLM else "AVISO: Groq NÃO configurada (GROQ_API_KEY ausente). Rodando só com regras.")

TEMPO_MAX_INATIVO = 60 * 60   # descarta sessões paradas há 1 hora
MAX_SESSOES = 500             # proteção simples contra excesso de memória
MAX_CARACTERES = 1000         # tamanho máximo de cada mensagem

_sessoes = {}                 # id -> {"bot": Acolhe, "ultimo": timestamp}
_trava = Lock()


def _limpar():
    agora = time.time()
    velhas = [k for k, v in _sessoes.items() if agora - v["ultimo"] > TEMPO_MAX_INATIVO]
    for k in velhas:
        del _sessoes[k]
    # se ainda estiver cheio, remove as mais antigas
    while len(_sessoes) >= MAX_SESSOES:
        mais_antiga = min(_sessoes, key=lambda k: _sessoes[k]["ultimo"])
        del _sessoes[mais_antiga]


def _obter_sessao(sid):
    """Devolve (sid, bot, nova). Cria uma sessão nova se o id não existir."""
    with _trava:
        _limpar()
        nova = sid not in _sessoes
        if nova:
            sid = uuid.uuid4().hex
            _sessoes[sid] = {"bot": Acolhe(llm=LLM, base=BASE), "ultimo": time.time()}
        _sessoes[sid]["ultimo"] = time.time()
        return sid, _sessoes[sid]["bot"], nova


@app.get("/")
def pagina():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/api/iniciar")
def iniciar():
    """Cria (ou reinicia) uma conversa e devolve a mensagem de boas-vindas."""
    dados = request.get_json(silent=True) or {}
    sid = dados.get("sessao")
    with _trava:
        _sessoes.pop(sid, None)          # "nova conversa" sempre começa do zero
    sid, bot, _ = _obter_sessao(None)
    return jsonify({"sessao": sid, "resposta": bot.inicio()})


@app.post("/api/mensagem")
def mensagem():
    dados = request.get_json(silent=True) or {}
    texto = str(dados.get("mensagem", ""))[:MAX_CARACTERES]
    sid, bot, nova = _obter_sessao(dados.get("sessao"))
    resposta = bot.responder(texto)
    return jsonify({"sessao": sid, "resposta": resposta, "sessao_nova": nova})


if __name__ == "__main__":
    # debug=False: não deixe o modo debug ligado em produção
    app.run(host="127.0.0.1", port=5000, debug=False)
