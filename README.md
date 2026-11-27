# Acolhe (versão web)

## Como rodar
1. `pip install -r requirements.txt`
2. `python app.py`
3. Abra http://127.0.0.1:5000

## Arquivos
- `acolhe_bot.py`: motor do chatbot (o mesmo do notebook, sem Colab). Teste no terminal: `python acolhe_bot.py`
- `app.py`: servidor Flask (rotas `/api/iniciar` e `/api/mensagem`)
- `static/index.html`: interface do chat (HTML + CSS + JS)

## Deixar no ar (hospedagem Python)
Comando de inicialização (Render, Railway etc.):

    gunicorn app:app --workers 1 --threads 4 --bind 0.0.0.0:$PORT

Use sempre **1 worker**: as conversas ficam na memória do processo. Com vários workers,
cada um teria sua própria memória e a pessoa perderia o questionário no meio.
Build command: `pip install -r requirements.txt`

## API da Groq
1. Crie uma chave em console.groq.com.
2. Copie `.env.example` para `.env` e coloque sua chave (o `.env` NÃO vai para o GitHub).
3. Na hospedagem, crie a variável de ambiente `GROQ_API_KEY` no painel do serviço.
A integração usa a API da Groq direto (biblioteca padrão do Python), sem langchain.
Sem a chave, o Acolhe funciona só com regras. A crise é sempre detectada por regras, antes do LLM.

## Base de CAPS do estado de São Paulo (CNES/DATASUS)
Com internet, na pasta do projeto:

    python gerar_base_caps.py --teste     # confere a leitura em 3 CAPS (rode primeiro)
    python gerar_base_caps.py             # gera tudo (alguns minutos)

Gera `conhecimento/caps_estado_sp.txt` (o Acolhe já usa), `caps_gerado/caps_estado_sp.csv`
e `caps_gerado/caps_estado_sp.pdf` (precisa de `pip install reportlab`). Reinicie o `app.py` depois.
