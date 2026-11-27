# -*- coding: utf-8 -*-
"""Acolhe: motor do chatbot de primeiro acolhimento em saúde mental.

Este arquivo contém exatamente a lógica do notebook (segurança, temas, questionários
e a classe Acolhe), sem nada que dependa do Colab/Jupyter. O servidor web está em app.py.
"""

import re
import random
import unicodedata


def normalizar(texto):
    """Minúsculas, sem acentos e sem pontuação, para facilitar a comparação."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


PADROES_CRISE = [
    r"\bquer(o|ia) morrer\b(?! de (rir|vergonha|sono|fome|saudade|medo|calor|frio))",
    r"\b(vontade|desejo|pensando|penso|pensei|pensamentos?) (de|em) (morrer|me matar|suicidio)",
    r"\bme (matar|suicidar|mate)\b",
    r"\bsuicid\w*",
    r"\b(tirar|acabar com|por fim a|dar fim a) (a )?(minha )?(propria )?vida\b",
    r"\bnao (quero|aguento|consigo) mais viver\b",
    r"\bnao quero mais (estar aqui|existir|acordar)\b",
    r"\b(melhor|seria melhor) sem mim\b",
    r"\bninguem (sentiria|sentiu) (a )?minha falta\b",
    r"\bme (machucar|cortar|ferir)\b",
    r"\bauto ?mutila\w*",
    r"\b(quero|queria|vou|penso em|pensando em) acabar com tudo\b",
    r"\bdesaparecer (pra|para) sempre\b",
]
_CRISE_RX = [re.compile(p) for p in PADROES_CRISE]


def detectar_crise(texto_normalizado):
    return any(rx.search(texto_normalizado) for rx in _CRISE_RX)


RESPOSTA_CRISE = """Sinto muito que você esteja passando por isso, e obrigado por ter me contado. Fico preocupado com você.

Eu sou um programa de computador e não consigo te acompanhar como uma pessoa consegue. Por isso, quero que você fale com alguém agora:

• **CVV: ligue 188** (24 horas, gratuito e sigiloso). Também há chat e e-mail em cvv.org.br.
• **Risco imediato** (se você já se machucou ou sente que pode se machucar agora): ligue **192 (SAMU)** ou vá à UPA / pronto-socorro mais próximo.
• Se possível, **não fique sozinho(a)**: chame alguém de confiança para ficar com você neste momento.

Você não precisa dar conta disso sozinho(a). Pedir ajuda é um passo importante."""

LEMBRETE_CRISE = "💛 Lembrete: CVV **188** (24h, gratuito) • SAMU **192** em risco imediato."


MSG_BOAS_VINDAS = """Oi! Eu sou o **Acolhe**, um chatbot de apoio emocional criado para um trabalho acadêmico sobre saúde mental e esgotamento profissional.

Posso te ouvir, sugerir exercícios simples (como respiração), aplicar pequenos questionários de triagem e indicar onde buscar ajuda.

**Importante:** eu sou um programa de computador. Não faço diagnóstico, não substituo psicólogo, psiquiatra ou médico, e suas mensagens não ficam salvas.

Se você estiver em sofrimento intenso, ligue para o CVV no **188** (24h, gratuito). Em risco imediato, ligue **192** (SAMU).

Como você está se sentindo hoje? Digite **menu** para ver as opções."""

MSG_MENU = """O que você gostaria de fazer?

**1** - Desabafar / conversar
**2** - Questionário de humor (2 perguntas)
**3** - Questionário de ansiedade (2 perguntas)
**4** - Questionário de esgotamento profissional/acadêmico (6 perguntas)
**5** - Exercício de respiração
**6** - Onde buscar ajuda
**7** - Dados e fontes (OPAS)

Digite o número ou escreva livremente o que está sentindo."""

MSG_RESPIRACAO = """**Respiração guiada (cerca de 2 minutos)**

Sente-se de forma confortável e, se quiser, feche os olhos.

1. Inspire pelo nariz, contando devagar: 1, 2, 3, 4.
2. Solte o ar pela boca, bem devagar: 1, 2, 3, 4, 5, 6.
3. Repita de 5 a 8 vezes, deixando os ombros soltos.

Se sentir tontura, volte a respirar normalmente. Como você se sente depois?"""

MSG_RECURSOS = """**Onde buscar ajuda no Brasil**

• **CVV: 188**: apoio emocional gratuito e sigiloso, 24h por dia. Também por chat e e-mail em cvv.org.br.
• **SAMU: 192**: emergências, inclusive risco imediato à vida.
• **UBS** (posto de saúde) e **CAPS**: atendimento gratuito pelo SUS. A UBS pode encaminhar para acompanhamento em saúde mental.
• **UPA / pronto-socorro**: em situações agudas.
• **Serviços da sua faculdade, hospital ou empresa**: muitos têm apoio psicológico, psicopedagógico ou saúde ocupacional.

Procurar ajuda cedo costuma facilitar o cuidado. Você não precisa estar "no limite" para isso."""

MSG_DADOS = """**Alguns dados da OPAS/OMS sobre saúde mental**

• Na América Latina e Caribe, a lacuna mediana de tratamento para transtornos afetivos, de ansiedade e por uso de substâncias (graves e moderados, em adultos) é de cerca de **77,9%**. Para depressão, é de **73,9%**.
• O gasto público médio com saúde mental na Região das Américas é de apenas **2,0%** do orçamento da saúde, e mais de **60%** desse valor vai para hospitais psiquiátricos.
• A OPAS aponta o estigma, a exclusão social e a discriminação como fatores que agravam a falta de tratamento.

Para o público da saúde, a OPAS tem materiais específicos (como um folheto sobre cuidados com a saúde mental do pessoal de saúde) e, em 15/10/2026, convidou profissionais de enfermagem e medicina de 17 países a participar de um estudo regional sobre saúde mental e condições de trabalho.

**Fontes:** OPAS/OMS (paho.org/pt/topicos/saude-mental). Para boletins e manuais, veja também o portal do Ministério da Saúde (gov.br/saude)."""


# Cada tema tem: palavras-chave (o "*" no final aceita qualquer terminação) e respostas.
INTENCOES = [
    {"nome": "panico",
     "chaves": ["panico", "crise de ansiedade", "falta de ar", "aperto no peito", "taquicardia",
                "coracao acelerado", "vou morrer", "vou desmaiar", "mao* suando"],
     "respostas": ["""Sinto muito que esteja passando por isso. Crises de pânico ou de ansiedade intensa são assustadoras, mas costumam passar em alguns minutos.

Vamos tentar com calma:
1. Se puder, sente-se e apoie os pés no chão.
2. Inspire pelo nariz contando 4 e solte devagar pela boca contando 6. Repita por alguns minutos.
3. Olhe ao redor e nomeie **5** coisas que você vê, **4** que consegue tocar, **3** que ouve, **2** que cheira e **1** que sente o gosto.

⚠️ Se houver dor forte no peito, falta de ar que não melhora, desmaio, ou se for a primeira vez que você sente isso, procure atendimento médico (UPA ou SAMU **192**), porque esses sintomas também podem ter causas físicas."""]},

    {"nome": "burnout",
     "chaves": ["burnout", "burn out", "esgotad*", "esgotamento", "exaust*", "sem energia", "estafa*",
                "sobrecarreg*", "nao aguento mais", "carga horaria", "cansaco extremo", "sem forcas"],
     "respostas": ["""O que você descreve lembra sinais de esgotamento. A OMS (CID-11) trata o burnout como um **fenômeno ocupacional**, ligado ao estresse crônico no trabalho que não foi bem manejado. Os sinais mais comuns são exaustão, distanciamento ou cinismo e sensação de pouca eficácia.

O que costuma ajudar:
• Reduzir o que for possível: o que dá para delegar, adiar ou recusar?
• Proteger pausas e pelo menos um momento do dia sem trabalho/estudo.
• Conversar com colegas, chefia ou coordenação sobre carga e prazos. Muita gente acha que está sozinha nisso e não está.
• Procurar a saúde ocupacional do seu local, a UBS ou um psicólogo.

Quer fazer o questionário de esgotamento? Digite **teste burnout**. Ele não é diagnóstico, mas ajuda a organizar o que você sente.""",
                    """Estar esgotado(a) não é falta de força de vontade. Muitas vezes é o resultado de um período longo de sobrecarga sem descanso suficiente.

Pequenos passos que podem ajudar:
• Anote o que mais drena sua energia durante a semana e o que recarrega.
• Negocie o que puder: prazos, escalas, divisão de tarefas.
• Garanta sono e pausas, mesmo que curtas.
• Se o cansaço vem junto com desânimo, irritação ou sensação de que nada do que você faz importa, converse com um profissional.

Posso aplicar um questionário rápido de esgotamento se você quiser. Digite **teste burnout**."""]},

    {"nome": "ansiedade",
     "chaves": ["ansied*", "ansios*", "nervos*", "preocupa*", "agonia", "aflit*", "tenso", "tensa",
                "pensamentos acelerados", "cabeca nao desliga", "medo de errar"],
     "respostas": ["""A ansiedade pode ser muito desgastante, principalmente quando a cabeça não desliga. É mais comum do que parece, e existem coisas que ajudam.

Algumas ideias para agora:
• Respire devagar: inspire pelo nariz contando até 4 e solte pela boca contando até 6, por uns 5 ciclos.
• Escreva o que está te preocupando e separe o que depende de você do que não depende.
• Escolha só a próxima tarefa pequena, em vez de tentar resolver tudo de uma vez.

Se a ansiedade aparece quase todos os dias, atrapalha o sono ou o trabalho/estudo, vale conversar com um profissional. Digite **respiração** para um exercício guiado ou **teste ansiedade** para um questionário rápido.""",
                    """Obrigado por contar. Quando a ansiedade aperta, o corpo e a mente entram em alerta, mesmo sem perigo real.

O que pode ajudar:
• Ancorar no presente: nomeie 3 coisas que você vê e 3 sons que você escuta agora.
• Reduzir a cafeína nesses dias.
• Dividir o que te preocupa em partes pequenas e resolver uma de cada vez.
• Lembrar que pensamento não é fato: "e se der tudo errado?" é uma possibilidade, não uma previsão.

Quer tentar uma respiração guiada? Digite **respiração**."""]},

    {"nome": "tristeza",
     "chaves": ["triste*", "tristeza", "deprimid*", "depressao", "desanimad*", "sem vontade", "vazio",
                "chorando", "choro", "sem esperanca", "sem animo", "sem prazer", "desmotivad*"],
     "respostas": ["""Sinto muito que você esteja se sentindo assim. Tristeza, desânimo e sensação de vazio pesam bastante, e é importante levar isso a sério.

Algumas coisas que podem ajudar, mesmo em pequenas doses:
• Manter o básico: dormir em horários parecidos, se alimentar, pegar um pouco de sol.
• Fazer uma coisa pequena que antes te fazia bem, sem cobrar o mesmo resultado de antes.
• Falar com alguém de confiança. Não precisa ter as palavras certas.

Quando esse sentimento dura mais de duas semanas, tira o interesse pelas coisas ou atrapalha a rotina, o ideal é procurar um profissional (UBS, CAPS ou psicólogo). Você pode fazer um questionário rápido de humor: **teste humor**."""]},

    {"nome": "estudos",
     "chaves": ["prova*", "estagio", "faculdade", "tcc", "residencia", "reprov*", "prazo*", "estudar",
                "estudo*", "vestibular", "semestre", "trabalho da faculdade", "seminario"],
     "respostas": ["""Pressão com provas, prazos e estágios é uma das principais fontes de estresse entre estudantes, especialmente na área da saúde, onde a carga é grande.

Ideias práticas:
• Divida o conteúdo em blocos pequenos e use ciclos de foco (por exemplo, 25 minutos de estudo e 5 de pausa).
• Priorize o que tem mais peso na nota ou o prazo mais próximo.
• Mantenha sono e alimentação: estudar sem dormir costuma render menos.
• Estude em grupo quando ajudar e peça apoio a professores ou à coordenação se a carga estiver inviável.

Se você sente que a pressão está virando esgotamento, posso aplicar o questionário: digite **teste burnout**."""]},

    {"nome": "profissional_saude",
     "chaves": ["paciente*", "plantao", "plantoes", "enfermeir*", "enfermagem", "medico", "medica",
                "hospital", "uti", "pronto socorro", "tecnico de enfermagem", "residente"],
     "respostas": ["""Cuidar dos outros exige muito emocionalmente. Profissionais e estudantes da saúde convivem com sofrimento, perdas, plantões longos e muita responsabilidade. Sentir peso com isso não é fraqueza.

Algumas formas de se proteger:
• Conversar com a equipe ou com colegas depois de casos difíceis. Dividir o peso ajuda.
• Respeitar intervalos e descanso sempre que possível.
• Usar os serviços de saúde ocupacional ou de apoio psicológico da instituição, se existirem.
• Ter acompanhamento próprio, como qualquer pessoa. Quem cuida também precisa ser cuidado.

Quer contar mais sobre o que tem pesado?"""]},

    {"nome": "sono",
     "chaves": ["sono", "insonia", "dormir", "dormindo", "acordo cansad*", "acordo de madrugada", "pesadelo*"],
     "respostas": ["""Dormir mal piora tudo: humor, concentração e ansiedade. Algumas medidas que ajudam:
• Horários regulares para deitar e levantar, inclusive nos fins de semana.
• Evitar cafeína no fim da tarde/noite e telas por 30 a 60 minutos antes de dormir.
• Não trabalhar nem estudar na cama.
• Se a cabeça acelerar, anotar as preocupações num papel para "deixar para amanhã".

Se a dificuldade de dormir dura semanas, vale conversar com um médico. Não tome medicamentos por conta própria."""]},

    {"nome": "solidao",
     "chaves": ["sozinh*", "solidao", "isolad*", "ninguem", "sem amigos", "ninguem me entende"],
     "respostas": ["""Sentir-se sozinho(a) dói, e é mais comum do que parece, principalmente em fases de muita cobrança. Uma tentativa pequena pode ajudar: mandar uma mensagem simples para alguém (um colega, familiar ou amigo) só para conversar, sem precisar falar de tudo.

Se não houver ninguém por perto, grupos de estudo, atividades coletivas e serviços como o CVV (**188**) também são lugares para ser ouvido(a). O que tem feito você se sentir assim?"""]},

    {"nome": "culpa",
     "chaves": ["culpa*", "incapaz", "fracasso", "fracassad*", "impostor*", "nao sou suficiente",
                "nao sou bom", "nao sou boa", "burro", "burra", "inutil", "nao presto"],
     "respostas": ["""Muita gente, principalmente em áreas de alta cobrança como a saúde, sente que nunca faz o suficiente. Pensamentos como "sou um fracasso" ou "não sou bom o bastante" podem parecer verdade quando estamos esgotados, mas são muito influenciados pelo cansaço e pela pressão.

Um exercício: escreva o pensamento e, ao lado, o que você diria a um amigo na mesma situação. Se esse tipo de pensamento é frequente, vale levar o assunto para um psicólogo."""]},

    {"nome": "raiva",
     "chaves": ["irritad*", "irritac*", "raiva", "estressad*", "estresse", "perdendo a paciencia", "explodi*", "sem paciencia"],
     "respostas": ["""Irritação e falta de paciência são sinais comuns de sobrecarga. Quando perceber que está no limite, uma pausa curta (sair do ambiente por alguns minutos, beber água, respirar fundo) ajuda a esfriar antes de reagir.

Depois, vale pensar no que está por trás: cansaço, fome, falta de sono ou excesso de demanda? Se a irritação está virando algo constante, conversar com um profissional pode ajudar."""]},

    {"nome": "ajuda_profissional",
     "chaves": ["psicolog*", "terapia", "psiquiatr*", "procurar ajuda", "caps", "sus", "preciso de ajuda",
                "como conseguir ajuda", "tratamento"],
     "respostas": ["""Procurar ajuda profissional é uma ótima decisão. Opções no Brasil: **UBS** (gratuita, pelo SUS, e que encaminha para saúde mental), **CAPS**, psicólogos particulares, clínicas-escola de cursos de psicologia (costumam ter valor social ou ser gratuitas) e serviços da sua instituição. Digite **recursos** para ver a lista completa."""]},

    {"nome": "autocuidado",
     "chaves": ["autocuidado", "rotina", "dicas", "o que fazer para melhorar", "como melhorar", "me sentir melhor"],
     "respostas": ["""Autocuidado não precisa ser algo grande. O básico ajuda bastante: sono regular, alimentação, movimento (uma caminhada já vale), pausas durante o dia, tempo com pessoas de quem você gosta e limites claros entre trabalho/estudo e descanso. Escolha só um desses para começar esta semana. Qual parece mais viável para você?"""]},

    {"nome": "sobre_bot",
     "chaves": ["quem e voce", "voce e real", "voce e uma pessoa", "o que voce faz", "voce e um robo", "voce e humano"],
     "respostas": ["""Eu sou o Acolhe, um chatbot simples feito para um projeto acadêmico sobre saúde mental. Funciono com regras e mensagens escritas com base em fontes como a OPAS/OMS. Não sou terapeuta, não faço diagnóstico e não substituo atendimento profissional. Se quiser conversar com uma pessoa, o CVV atende no **188**, 24h."""]},

    {"nome": "agradecimento",
     "chaves": ["obrigad*", "brigad*", "valeu", "agradeco"],
     "respostas": ["De nada! Estou por aqui se quiser continuar. Cuide-se. 💛"]},

    {"nome": "despedida",
     "chaves": ["tchau", "ate mais", "ate logo", "sair", "encerrar"],
     "respostas": ["Até mais! Lembre-se: se precisar conversar com uma pessoa, o CVV atende no **188** (24h, gratuito). Cuide-se. 💛"]},

    {"nome": "bem",
     "chaves": ["estou bem", "to bem", "estou melhor", "me sinto bem", "feliz", "tranquil*", "estou otimo", "estou otima"],
     "respostas": ["""Fico feliz em saber. Cuidar da saúde mental também é manter o que está funcionando: rotina, pausas e contato com pessoas. Se quiser, digite **menu** para ver o que posso fazer."""]},

    {"nome": "saudacao",
     "chaves": ["oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "eae", "hello"],
     "respostas": ["Oi! Que bom que você veio conversar. Como você está se sentindo hoje? Digite **menu** se quiser ver as opções."]},
]

FALLBACKS = [
    """Obrigado por compartilhar isso comigo. Quero entender melhor: o que mais tem pesado para você ultimamente? Trabalho ou estudos, ansiedade, tristeza, sono, relacionamentos? Se preferir, digite **menu**.""",
    """Estou ouvindo. Pode me contar com mais detalhes como tem sido isso para você? Se preferir, digite **menu** para ver outras opções.""",
]


def _kw_regex(kw):
    prefixo = kw.endswith("*")
    base = normalizar(kw.rstrip("*"))
    return re.compile(r"\b" + re.escape(base) + (r"\w*" if prefixo else r"\b"))

for _i in INTENCOES:
    _i["_rx"] = [_kw_regex(k) for k in _i["chaves"]]


ESCALA_FREQ = "0 = Nenhum dia  ·  1 = Alguns dias  ·  2 = Mais da metade dos dias  ·  3 = Quase todos os dias"
ESCALA_BURN = "0 = Nunca  ·  1 = Poucas vezes  ·  2 = Frequentemente  ·  3 = Sempre"

AVISO_TRIAGEM = "\n\n*Lembrando: isto é uma triagem, não um diagnóstico. Só um profissional de saúde pode avaliar o seu caso.*"


def _res_humor(p):
    if p >= 3:
        return (f"Sua pontuação foi **{p} de 6**. Esse resultado sugere que vale a pena conversar com um profissional de saúde "
                "(UBS, CAPS ou psicólogo) sobre como você tem se sentido. Procurar ajuda não significa que algo está "
                "'muito errado': é cuidar de você." + AVISO_TRIAGEM)
    return (f"Sua pontuação foi **{p} de 6**, abaixo do ponto de atenção usado nesse tipo de triagem. Isso não significa que "
            "está tudo bem se você sente que algo pesa. Se o desânimo persistir ou aumentar, converse com um profissional." + AVISO_TRIAGEM)


def _res_ansiedade(p):
    if p >= 3:
        return (f"Sua pontuação foi **{p} de 6**. Esse resultado sugere que vale conversar com um profissional de saúde sobre "
                "a ansiedade que você tem sentido. Enquanto isso, exercícios de respiração e pausas ao longo do dia podem "
                "ajudar. Digite **respiração** se quiser tentar." + AVISO_TRIAGEM)
    return (f"Sua pontuação foi **{p} de 6**, abaixo do ponto de atenção desse tipo de triagem. Se a preocupação continuar "
            "atrapalhando seu dia a dia, vale conversar com um profissional." + AVISO_TRIAGEM)


def _res_burnout(p):
    if p <= 5:
        n = (f"Sua pontuação foi **{p} de 18**: poucos sinais de esgotamento neste momento. Continue cuidando de pausas, "
             "sono e limites entre trabalho/estudo e descanso.")
    elif p <= 11:
        n = (f"Sua pontuação foi **{p} de 18**: há **sinais moderados** de desgaste. É um bom momento para agir antes que piore: "
             "rever carga e prazos, proteger pausas e sono, conversar com colegas ou chefia/coordenação.")
    else:
        n = (f"Sua pontuação foi **{p} de 18**: há **muitos sinais** de esgotamento. Recomendo conversar com um profissional "
             "(saúde ocupacional, UBS, CAPS ou psicólogo) e, se possível, com sua chefia ou coordenação sobre ajustes na carga. "
             "Você não precisa passar por isso sozinho(a).")
    return n + AVISO_TRIAGEM


TRIAGENS = {
    "humor": {
        "titulo": "Questionário de humor",
        "intro": "Vou fazer **2 perguntas** sobre as últimas 2 semanas. Responda com um número de 0 a 3. Você pode digitar **cancelar** a qualquer momento.",
        "prefixo": "Nas últimas 2 semanas, com que frequência você foi incomodado(a) por: ",
        "itens": ["pouco interesse ou prazer em fazer as coisas?",
                  "sentir-se para baixo, deprimido(a) ou sem perspectiva?"],
        "escala": ESCALA_FREQ, "resultado": _res_humor},
    "ansiedade": {
        "titulo": "Questionário de ansiedade",
        "intro": "Vou fazer **2 perguntas** sobre as últimas 2 semanas. Responda com um número de 0 a 3. Você pode digitar **cancelar** a qualquer momento.",
        "prefixo": "Nas últimas 2 semanas, com que frequência você foi incomodado(a) por: ",
        "itens": ["sentir-se nervoso(a), ansioso(a) ou muito tenso(a)?",
                  "não conseguir impedir ou controlar as preocupações?"],
        "escala": ESCALA_FREQ, "resultado": _res_ansiedade},
    "burnout": {
        "titulo": "Questionário de esgotamento",
        "intro": "Vou fazer **6 perguntas** sobre como você tem se sentido com o trabalho ou os estudos. Responda com um número de 0 a 3. Você pode digitar **cancelar** a qualquer momento.",
        "prefixo": "Pensando nas últimas semanas, com que frequência isto é verdade para você?\n",
        "itens": ["Ao fim do dia de trabalho/estudo, sinto que não tenho mais energia.",
                  "Acordo já cansado(a) só de pensar no que preciso fazer.",
                  "Tenho me sentido distante, irritado(a) ou indiferente com colegas, pacientes ou tarefas.",
                  "Sinto que, por mais que eu me esforce, o que faço tem pouco valor ou efeito.",
                  "Tenho dificuldade de me desligar do trabalho/estudo nos momentos de descanso.",
                  "Tenho tido dor de cabeça, tensão ou problemas de sono que parecem ligados à minha rotina."],
        "escala": ESCALA_BURN, "resultado": _res_burnout},
}

_PALAVRAS_NOTA = {"nenhum dia": 0, "nunca": 0, "alguns dias": 1, "poucas vezes": 1,
                  "mais da metade dos dias": 2, "mais da metade": 2, "frequentemente": 2,
                  "quase todos os dias": 3, "sempre": 3}


def ler_nota(t):
    if re.fullmatch(r"[0-3]", t):
        return int(t)
    return _PALAVRAS_NOTA.get(t)



# ---------------------------------------------------------------- LLM (Groq)
MODELO_GROQ = "openai/gpt-oss-120b"   # mesmo modelo usado no exercício do edital

PROMPT_SISTEMA = """Você é o Acolhe, um chatbot de PRIMEIRO ACOLHIMENTO em saúde mental para estudantes e profissionais da saúde, em português do Brasil. É um projeto acadêmico.

Regras obrigatórias:
- Seja acolhedor, simples e direto. Respostas curtas (no máximo 120 palavras), sem listas longas.
- Você NÃO faz diagnóstico, NÃO prescreve nem comenta doses de medicamentos e NÃO substitui psicólogo, psiquiatra ou médico.
- Nunca afirme que a pessoa "tem" depressão, ansiedade, burnout ou qualquer transtorno. Fale em "sinais" e sugira avaliação profissional quando fizer sentido (UBS, CAPS, psicólogo, saúde ocupacional).
- Se houver QUALQUER sinal de desesperança, ideia de morte, suicídio ou autolesão, priorize a segurança: oriente a ligar para o CVV (188, 24h, gratuito) e, em risco imediato, SAMU (192), e incentive a pessoa a não ficar sozinha.
- Pode sugerir exercícios simples (respiração, aterramento) e dicas de autocuidado. Para exercícios e questionários, lembre que a pessoa pode digitar: menu, respiração, teste humor, teste ansiedade, teste burnout, recursos.
- Use apenas o material de referência abaixo e conhecimento geral seguro. Não invente estatísticas, fontes, endereços, telefones, horários ou serviços.
- Se a pergunta fugir de saúde mental e bem-estar, explique gentilmente que seu foco é acolhimento e ofereça o menu.
- Use **negrito** só para destacar o essencial. Não use títulos nem tabelas.
- Termine, quando fizer sentido, com uma pergunta aberta curta para a pessoa continuar."""

# Temas curtos e previsíveis continuam respondidos só por regras (sem gastar chamada ao LLM).
TEMAS_SO_REGRAS = {"saudacao", "agradecimento", "despedida", "sobre_bot"}


class ClienteGroq:
    """Cliente mínimo da API da Groq (compatível com a API da OpenAI), usando só a
    biblioteca padrão. Tem o mesmo método .invoke(mensagens) -> objeto com .content."""

    def __init__(self, chave, modelo=MODELO_GROQ,
                 url="https://api.groq.com/openai/v1/chat/completions"):
        self.chave, self.modelo, self.url = chave, modelo, url

    def _chamar(self, mensagens, extras):
        import json
        import urllib.request
        corpo = {"model": self.modelo, "temperature": 0.4,
                 "max_completion_tokens": 1500, "messages": mensagens}
        corpo.update(extras)
        req = urllib.request.Request(
            self.url, data=json.dumps(corpo).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.chave,
                     "User-Agent": "acolhe-chatbot/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)

    def invoke(self, mensagens):
        import urllib.error
        papeis = {"human": "user", "assistant": "assistant", "system": "system"}
        msgs = [{"role": papeis.get(r, r), "content": c} for r, c in mensagens]
        try:
            dados = self._chamar(msgs, {"reasoning_effort": "low"})
        except urllib.error.HTTPError as e:
            detalhe = e.read().decode("utf-8", "ignore")[:300]
            if e.code != 400:
                raise RuntimeError(f"Groq respondeu HTTP {e.code}: {detalhe}")
            # 400: tenta de novo sem o parâmetro opcional de raciocínio
            try:
                dados = self._chamar(msgs, {})
            except urllib.error.HTTPError as e2:
                raise RuntimeError(f"Groq respondeu HTTP {e2.code}: {e2.read().decode('utf-8', 'ignore')[:300]}")

        class _Resposta:
            pass
        r = _Resposta()
        r.content = (dados["choices"][0]["message"].get("content") or "")
        return r


def criar_llm():
    """Cria o cliente da Groq. Devolve None se não houver chave, e nesse caso o
    Acolhe funciona só com regras."""
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    chave = (os.getenv("GROQ_API_KEY") or "").strip()
    if not chave:
        return None
    return ClienteGroq(chave, os.getenv("GROQ_MODEL", MODELO_GROQ))


class Acolhe:
    """Chatbot de primeiro acolhimento. Guarda apenas o estado da conversa em memória."""

    def __init__(self, llm=None, base=None):
        self.llm = llm                # cliente da Groq (ou None = só regras)
        self.base = base              # base de conhecimento (PDFs/textos) ou None
        self.reiniciar()

    def reiniciar(self):
        self.modo = "conversa"        # "conversa" ou "triagem"
        self.triagem = None
        self.idx = 0
        self.notas = []
        self.crise_ativa = False
        self.aguarda_menu = False
        self._ultima_resposta = None
        self.historico = []           # últimas mensagens, enviadas ao LLM como contexto
        self._texto_original = ""

    # ---------------------------------------------------------- entrada principal
    def inicio(self):
        return MSG_BOAS_VINDAS

    def responder(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return "Pode escrever o que quiser. Se preferir, digite **menu**."
        t = normalizar(texto)
        self._texto_original = texto

        # 1) Segurança primeiro, sempre (regras, nunca depende do LLM).
        if detectar_crise(t):
            self.crise_ativa = True
            self.modo, self.triagem, self.aguarda_menu = "conversa", None, False
            self._guardar(texto, RESPOSTA_CRISE)
            return RESPOSTA_CRISE

        # 2) Questionário em andamento.
        if self.modo == "triagem":
            resp = self._passo_triagem(t)
        else:
            resp = self._conversa(t)

        if self.crise_ativa:
            resp += "\n\n" + LEMBRETE_CRISE
        self._guardar(texto, resp)
        return resp

    def _guardar(self, pergunta, resposta):
        """Mantém só as últimas 8 trocas, apenas em memória."""
        self.historico.append(("human", pergunta))
        self.historico.append(("assistant", resposta))
        self.historico = self.historico[-16:]

    # ---------------------------------------------------------- conversa livre
    def _conversa(self, t):
        if self.aguarda_menu and re.fullmatch(r"[1-7]", t):
            self.aguarda_menu = False
            return self._opcao_menu(int(t))
        self.aguarda_menu = False

        if t in ("menu", "ajuda", "opcoes", "help", "inicio"):
            self.aguarda_menu = True
            return MSG_MENU
        if re.search(r"\b(teste|triagem|questionario)\b.*\b(humor|depress\w*|tristeza)\b", t):
            return self._iniciar_triagem("humor")
        if re.search(r"\b(teste|triagem|questionario)\b.*\b(ansiedade|ansios\w*)\b", t):
            return self._iniciar_triagem("ansiedade")
        if re.search(r"\b(teste|triagem|questionario)\b.*\b(burnout|esgotamento|estafa)\b", t):
            return self._iniciar_triagem("burnout")
        if re.fullmatch(r"(quero )?(uma |a |o )?(exercicio de )?(respiracao|respirar)( guiada)?", t):
            return MSG_RESPIRACAO
        if re.search(r"\b(recursos|telefones?|cvv|onde (buscar|procurar|encontrar) ajuda)\b", t):
            return MSG_RECURSOS
        if re.search(r"\b(dados|fontes|estatisticas?|opas)\b", t):
            return MSG_DADOS

        return self._por_tema(t)

    def _opcao_menu(self, n):
        if n == 1:
            return "Estou aqui para ouvir. Pode escrever com calma o que está sentindo."
        if n == 2:
            return self._iniciar_triagem("humor")
        if n == 3:
            return self._iniciar_triagem("ansiedade")
        if n == 4:
            return self._iniciar_triagem("burnout")
        if n == 5:
            return MSG_RESPIRACAO
        if n == 6:
            return MSG_RECURSOS
        return MSG_DADOS

    def _por_tema(self, t):
        melhor, pontos = None, 0
        for tema in INTENCOES:                       # a ordem da lista define o desempate
            p = sum(1 for rx in tema["_rx"] if rx.search(t))
            if p > pontos:
                melhor, pontos = tema, p

        # Conversa livre: tenta o LLM (Groq), usando o tema encontrado como referência.
        if self.llm is not None and not (melhor and melhor["nome"] in TEMAS_SO_REGRAS):
            resp = self._por_llm(melhor)
            if resp:
                self._ultima_resposta = resp
                return resp
        if melhor is None:
            opcoes = [f for f in FALLBACKS if f != self._ultima_resposta] or FALLBACKS
            resp = random.choice(opcoes)
        else:
            opcoes = [r for r in melhor["respostas"] if r != self._ultima_resposta] or melhor["respostas"]
            resp = random.choice(opcoes)
        self._ultima_resposta = resp
        return resp

    def _por_llm(self, tema):
        """Gera a resposta com a Groq. Em qualquer falha devolve None (e usa as regras)."""
        try:
            sistema = PROMPT_SISTEMA
            if tema:
                sistema += ("\n\nMATERIAL DE REFERÊNCIA (tema: " + tema["nome"] + "). "
                            "Use como base, reescrevendo com suas palavras e adaptando ao que a pessoa disse:\n"
                            + "\n\n".join(tema["respostas"]))
            sistema += self._contexto_documentos()
            if self.crise_ativa:
                sistema += ("\n\nATENÇÃO: nesta conversa a pessoa já demonstrou sinais de crise. "
                            "Mantenha tom cuidadoso e reforce o CVV 188 e a importância de falar com alguém.")
            mensagens = [("system", sistema)] + self.historico[-10:] + [("human", self._texto_original)]
            texto = self.llm.invoke(mensagens).content
            texto = (texto or "").strip()
            return texto or None
        except Exception as erro:
            print("Aviso: falha na Groq, usando respostas por regras ->", erro)
            return None

    def _contexto_documentos(self):
        """Busca nos arquivos da pasta conhecimento/ e monta o trecho extra do prompt."""
        if not self.base:
            return ""
        consulta = self._texto_original
        if len(consulta.split()) < 6:      # pergunta curta ("e o telefone?"): junta a mensagem anterior
            anteriores = [c for r, c in self.historico if r == "human"]
            if anteriores:
                consulta = anteriores[-1] + " " + consulta
        achados = self.base.buscar(consulta, k=4)
        if not achados:
            return ("\n\nDOCUMENTOS DE APOIO: nenhum trecho dos documentos correspondeu a esta mensagem. "
                    "Se a pessoa pedir endereço, telefone, horário ou lista de serviços, diga com sinceridade que "
                    "não tem essa informação e sugira ligar para 136 (Disque Saúde) ou procurar a UBS da região.")
        blocos = "\n\n".join(f"[Fonte: {fonte}]\n{texto}" for texto, fonte in achados)
        return ("\n\nDOCUMENTOS DE APOIO (trechos encontrados). Para endereços, telefones, horários e serviços, "
                "responda SOMENTE com base nestes trechos, citando a fonte (nome do arquivo). "
                "Se o que a pessoa pediu não estiver nos trechos, diga que não encontrou:\n\n" + blocos)

    # ---------------------------------------------------------- questionários
    def _iniciar_triagem(self, chave):
        self.modo, self.triagem, self.idx, self.notas = "triagem", chave, 0, []
        tr = TRIAGENS[chave]
        return f"**{tr['titulo']}**\n{tr['intro']}\n\n" + self._pergunta()

    def _pergunta(self):
        tr = TRIAGENS[self.triagem]
        n = len(tr["itens"])
        return (f"**Pergunta {self.idx + 1} de {n}**\n{tr['prefixo']}{tr['itens'][self.idx]}\n{tr['escala']}")

    def _passo_triagem(self, t):
        if t in ("cancelar", "parar", "sair", "menu"):
            self.modo, self.triagem = "conversa", None
            return "Tudo bem, cancelei o questionário. Digite **menu** para ver outras opções ou conte como você está."
        nota = ler_nota(t)
        if nota is None:
            return "Não entendi. Responda com um número de **0 a 3** (ou digite **cancelar**).\n\n" + self._pergunta()
        self.notas.append(nota)
        self.idx += 1
        tr = TRIAGENS[self.triagem]
        if self.idx < len(tr["itens"]):
            return self._pergunta()
        resultado = tr["resultado"](sum(self.notas))
        self.modo, self.triagem = "conversa", None
        return resultado + "\n\nDigite **menu** para ver outras opções ou, se quiser, conte mais sobre como você está."


def conversar_no_terminal():
    """Teste rápido no terminal: python acolhe_bot.py"""
    bot = Acolhe()
    print(bot.inicio().replace("**", ""))
    while True:
        msg = input("\nVocê: ")
        if normalizar(msg) in ("sair", "tchau", "encerrar"):
            print("\nAcolhe:", bot.responder("tchau").replace("**", ""))
            break
        print("\nAcolhe:", bot.responder(msg).replace("**", ""))


if __name__ == "__main__":
    conversar_no_terminal()
