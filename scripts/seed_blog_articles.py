"""Seed idempotente dos 40 artigos do blog/notícias do Portal ACCTA.

spec-blog-artigos. O conteúdo é fundamentado na **base de conhecimento curada**
da área pública — `frontend/src/content/cta/` (profissao, licenciamento,
formacao, estruturaAts, legislacao, faq, contactosUteis), derivada de
`memory/deep-research-report.md` e reconciliada por `tasks/spec-base-conhecimento.md`
(PT-PT, ACCTA tratada como associação constituída, base legal citada em cada
requisito, dados "não especificados" nunca inventados). Cada artigo alinha com
os mesmos factos e a mesma terminologia desse módulo — nome canónico
"Associação Cabo-verdiana dos Controladores de Tráfego Aéreo (ACCTA)".

Mecânica (decisão do dono): script dedicado, versionado, **não destrutivo** —
nunca apaga; para cada artigo faz upsert por `id` determinístico (uuid5 do slug),
preservando `created_at`/`published_at` em atualizações. Correr N vezes não
duplica nem reescreve a cronologia.

Uso:
    python scripts/seed_blog_articles.py            # valida (offline) + faz seed
    python scripts/seed_blog_articles.py --validate # só guarda editorial offline
"""

import asyncio
import re
import sys
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Datas determinísticas: o artigo de índice 0 fica mais recente; cada seguinte
# recua 3 dias (mais recentes primeiro). BASE_DATE alinhada com a entrega.
BASE_DATE = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
SLUG_BASE_URL = "https://controlador.cv/noticias/"

# Termos proibidos (regras editoriais herdadas de spec-base-conhecimento §2 e
# critérios de aceitação §7). Scan offline sobre título+excerpt+conteúdo+tags.
FORBIDDEN = [
    "inadimpl",
    "adimplência",
    "adimplencia",
    "autoridade de aviação",
    "fir de sal",
    "fir sal",
    "60 profissionais",
    "500 voos",
    "40-50 milhas",
    "40–50 milhas",
]


def slugify(text: str) -> str:
    """kebab-case sem acentos (NFKD); [^a-z0-9]+ -> '-', trim de '-'."""
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "artigo"


# --------------------------------------------------------------------------- #
# Catálogo dos 40 artigos (spec §5). Conteúdo em texto simples; parágrafos
# separados por linha em branco (render futuro `whitespace-pre-wrap`).
# --------------------------------------------------------------------------- #

ARTICLES = [
    # ===================== EDUCATIVO (27 · publico) ===================== #
    {
        "title": "O que faz um controlador de tráfego aéreo",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["CTA", "ATC", "ICAO", "CV-CAR 17"],
        "excerpt": "O controlador de tráfego aéreo é o profissional licenciado pela AAC para garantir voos seguros e ordenados. Veja o que define a profissão segundo o Anexo 11 da ICAO e o CV-CAR 17.",
        "content": (
            "O controlador de tráfego aéreo (CTA) é o profissional licenciado pela Agência de Aviação Civil (AAC) para "
            "exercer, num órgão de serviços de tráfego aéreo específico, os privilégios das qualificações de aeródromo, "
            "aproximação ou área. O exercício depende ainda do averbamento de órgão de controlo e dos requisitos médicos "
            "e linguísticos aplicáveis (CV-CAR 2.3, 2026).\n\n"
            "O quadro internacional que enquadra a profissão é o Anexo 11 da ICAO, que define os serviços de tráfego aéreo "
            "(ATS) e fixa os seus objetivos: prevenir colisões entre aeronaves, prevenir colisões entre aeronaves e "
            "obstáculos na área de manobras, acelerar e manter um fluxo de tráfego ordenado e fornecer informação útil à "
            "condução segura e eficiente dos voos.\n\n"
            "Em Cabo Verde, o CV-CAR 17 reproduz esta lógica e organiza os serviços de tráfego aéreo em três blocos: o "
            "controlo de tráfego aéreo (ATC), o serviço de informação de voo (FIS) e o serviço de alerta. No dia a dia, o "
            "controlador aplica estas normas para separar aeronaves, sequenciar chegadas e partidas e apoiar as tripulações "
            "com informação atualizada."
        ),
    },
    {
        "title": "Como se tornar CTA em Cabo Verde",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["licenciamento", "formação", "CV-CAR 2.3", "carreira"],
        "excerpt": "Cinco etapas, da elegibilidade à manutenção da recência. Um guia fiel ao CV-CAR 2.3 (2026) e ao CV-CAR 2.4 para quem quer seguir a profissão de controlador.",
        "content": (
            "Tornar-se controlador de tráfego aéreo em Cabo Verde segue um caminho-padrão definido pelo CV-CAR 2.3 (2026). "
            "A primeira etapa é a elegibilidade: ter pelo menos 21 anos, deter o Certificado Médico Classe 3 (CV-CAR 2.4) e "
            "demonstrar proficiência em inglês para radiotelefonia, no mínimo ao Nível Operacional 4.\n\n"
            "A segunda etapa é a formação inicial numa organização de formação (ATO) aprovada pela AAC, com formação teórica "
            "nas áreas obrigatórias de conhecimento e aprovação em exame teórico. Segue-se a formação operacional, com a "
            "qualificação pretendida e, sobretudo, pelo menos três meses de serviço satisfatório envolvendo controlo real de "
            "tráfego aéreo sob supervisão de um instrutor em exercício (OJTI).\n\n"
            "A quarta etapa é o ingresso numa unidade, através do curso e do averbamento de órgão de controlo, que autoriza a "
            "operação numa posição específica. A última etapa é a manutenção: revalidar o averbamento — cuja validade é "
            "definida no plano de competências da unidade e nunca é superior a três anos — e preservar a recência, sabendo que "
            "o averbamento se torna inválido após mais de 90 dias sem exercício dos privilégios."
        ),
    },
    {
        "title": "A estrutura de navegação aérea em quatro camadas",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["AAC", "ASA", "aeroportos", "IPIAAM"],
        "excerpt": "Regulação, prestação ATS, gestão aeroportuária e investigação técnica: quatro camadas distintas que sustentam a aviação civil cabo-verdiana e o trabalho do controlador.",
        "content": (
            "A aviação civil de Cabo Verde organiza-se em camadas com papéis distintos. A regulação técnica e económica do "
            "setor cabe à Agência de Aviação Civil (AAC), regida pelos estatutos aprovados pelo Decreto-Lei n.º 47/2019 — o "
            "equivalente funcional de uma autoridade nacional de aviação.\n\n"
            "A prestação dos serviços de tráfego aéreo está, nas fontes oficiais consultadas, associada à ASA — Navegação "
            "Aérea de Cabo Verde, S.A., com sede no Sal. A gestão das infraestruturas aeroportuárias, por seu lado, é "
            "concessionada: a Lei n.º 64/IX/2019 fixou o regime da concessão e o Decreto-Lei n.º 14/2022 atribuiu-a, passando "
            "a Cabo Verde Airports a assumir a gestão dos aeroportos e aeródromos.\n\n"
            "A quarta camada surge em caso de acidente ou incidente grave: a investigação técnica é regida pelo Decreto-Lei "
            "n.º 6/2023, que atribui essa responsabilidade ao IPIAAM. Distinguir estas quatro camadas — regular, prestar, "
            "gerir infraestrutura e investigar — ajuda a compreender onde se insere o trabalho do controlador."
        ),
    },
    {
        "title": "FIR Oceânica do Sal",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["FIR", "ICAO", "legislação", "ATS"],
        "excerpt": "Criada pelo Decreto-Lei n.º 9/80, a FIR Oceânica do Sal define o espaço de responsabilidade ATS de Cabo Verde. O limite exato de UTA/UIR mantém-se não especificado.",
        "content": (
            "A FIR Oceânica do Sal foi estabelecida pelo Decreto-Lei n.º 9/80, de 11 de fevereiro. O mesmo diploma "
            "determinou que os serviços, instalações, equipamentos e pessoal afetos ao seu funcionamento se consideravam "
            "integrados no Aeroporto Internacional Amílcar Cabral, na ilha do Sal.\n\n"
            "Nesse espaço, o decreto assegura apoio à navegação aérea de acordo com a ICAO, incluindo controlo de tráfego "
            "aéreo, telecomunicações aeronáuticas, assistência meteorológica e busca e salvamento. É este o marco "
            "institucional que enquadra a responsabilidade ATS sobre o vasto espaço oceânico associado ao arquipélago.\n\n"
            "Quanto ao limite superior exato de UTA/UIR aplicável, o dado mantém-se não especificado nas fontes oficiais "
            "consolidadas. A formulação correta para consulta é confirmar diretamente na AIP/e-AIP vigente, em vez de supor "
            "limites."
        ),
    },
    {
        "title": "As cinco qualificações do controlador",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["qualificações", "CV-CAR 2.3", "ATC", "averbamento"],
        "excerpt": "ADI, aproximação procedural e por vigilância, área procedural e por vigilância: as cinco qualificações de CTA previstas pelo CV-CAR 2.3 e os privilégios de cada uma.",
        "content": (
            "O CV-CAR 2.3 (2026) prevê cinco qualificações para o controlador de tráfego aéreo, cada uma com privilégios "
            "próprios. A qualificação de controlo de aeródromo (ADI) habilita ao serviço prestado pela torre de controlo.\n\n"
            "Seguem-se as duas qualificações de aproximação: o controlo de aproximação por procedimentos (sem recurso a "
            "sistemas de vigilância) e o controlo de aproximação por vigilância (com esses sistemas). De forma análoga, o "
            "controlo de área divide-se em controlo de área por procedimentos e controlo de área por vigilância.\n\n"
            "Esta taxonomia — ADI, APP procedural, APP por vigilância, ACC procedural e ACC por vigilância — permite "
            "perceber que a licença CTA não é monolítica: o profissional exerce os privilégios das qualificações de que é "
            "titular, sempre em articulação com o averbamento do órgão onde opera."
        ),
    },
    {
        "title": "Certificado Médico Classe 3",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["medicina aeronáutica", "CV-CAR 2.4", "CTA"],
        "excerpt": "O Certificado Médico Classe 3 é exigência de ingresso e de exercício do CTA (CV-CAR 2.4). A periodicidade dos exames é escalonada por idade.",
        "content": (
            "O ingresso e o exercício como controlador de tráfego aéreo exigem o Certificado Médico Classe 3, disciplinado "
            "pelo CV-CAR 2.4. O candidato realiza um exame médico inicial e, depois, revalida-o nos intervalos previstos.\n\n"
            "A tabela oficial de periodicidade publicada pela AAC mostra, para a Classe 3, exigências como o "
            "eletrocardiograma no exame inicial e, em seguida, em períodos até quatro anos antes dos 30 anos, de dois anos "
            "entre os 30 e os 49, e de um ano a partir dos 50.\n\n"
            "A par do exame cardiológico, são previstos exames de otorrinolaringologia com audiograma e exames "
            "oftalmológicos, também em periodicidades escalonadas por idade e condição visual. A aptidão médica é, assim, "
            "acompanhada ao longo de toda a carreira, e não apenas no momento de entrada."
        ),
    },
    {
        "title": "Inglês Nível Operacional 4",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["inglês", "CV-CAR 2.3", "ICAO", "licenciamento"],
        "excerpt": "A proficiência em inglês para radiotelefonia, no mínimo ao Nível Operacional 4 da escala ICAO, é obrigatória para controladores e instruendos (CV-CAR 2.3).",
        "content": (
            "A proficiência linguística é um requisito obrigatório do regime de licenciamento. O CV-CAR 2.3 determina que "
            "controladores e instruendos demonstrem capacidade de falar e compreender a língua inglesa usada nas "
            "comunicações de radiotelefonia, pelo menos ao Nível Operacional 4.\n\n"
            "O Nível 4 corresponde, na escala da ICAO, ao patamar operacional mínimo: assegura comunicação eficaz em "
            "situações de rotina e a capacidade de gerir trocas verbais quando surge uma complicação inesperada.\n\n"
            "A exigência é também transversal à conversão de licença estrangeira: a AAC pede a comprovação de proficiência "
            "na língua usada na radiotelefonia em Cabo Verde e em inglês. Sem este averbamento de proficiência linguística, "
            "não há exercício pleno dos privilégios da licença."
        ),
    },
    {
        "title": "Averbamento de órgão de controlo",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["averbamento", "recência", "CV-CAR 2.3"],
        "excerpt": "O averbamento de órgão de controlo autoriza a operação numa unidade específica. Vale até três anos pelo plano da unidade e invalida-se após mais de 90 dias sem exercício.",
        "content": (
            "Para além das qualificações, o exercício prático depende do averbamento de órgão de controlo, que autoriza o "
            "controlador a prestar serviço numa unidade ou posição operacional concreta. É este o documento mais relevante "
            "para a operação diária.\n\n"
            "A sua validade é definida no plano de competências da unidade, aprovado pela autoridade aeronáutica, e nunca é "
            "superior a três anos (CV-CAR 2.3). Além disso, o averbamento torna-se inválido se o controlador deixar de "
            "exercer os privilégios por período superior a 90 dias.\n\n"
            "A revalidação assenta em horas mínimas de exercício, formação de refrescamento e avaliação de competência, "
            "conforme o plano da unidade. É esta combinação que mantém o controlador apto à posição que ocupa."
        ),
    },
    {
        "title": "ATC, FIS e serviço de alerta",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["ATC", "FIS", "ATS", "CV-CAR 17"],
        "excerpt": "Os serviços de tráfego aéreo dividem-se em três: controlo de tráfego aéreo, serviço de informação de voo e serviço de alerta (Anexo 11 da ICAO e CV-CAR 17).",
        "content": (
            "Os serviços de tráfego aéreo (ATS) não se resumem ao controlo. Segundo o Anexo 11 da ICAO, refletido no CV-CAR "
            "17, os ATS desdobram-se em três serviços complementares.\n\n"
            "O primeiro é o controlo de tráfego aéreo (ATC), que separa aeronaves e ordena o fluxo. O segundo é o serviço de "
            "informação de voo (FIS), que fornece informação e conselhos úteis à condução segura e eficiente dos voos. O "
            "terceiro é o serviço de alerta, que notifica os organismos adequados quando uma aeronave necessita de busca e "
            "salvamento e presta o apoio necessário.\n\n"
            "Compreender esta divisão é importante: nem todos os órgãos prestam todos os serviços. Em Cabo Verde, por "
            "exemplo, existem unidades de controlo e unidades de informação de voo, com responsabilidades distintas."
        ),
    },
    {
        "title": "Condições de trabalho e prevenção da fadiga",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["condições de trabalho", "CV-CAR 17", "segurança"],
        "excerpt": "O CV-CAR 17 fixa salvaguardas de fadiga: pelo menos 5 minutos por mudança de turno, máximo de 6 horas de trabalho contínuo e turnos que não devem exceder 8 horas.",
        "content": (
            "O CV-CAR 17 estabelece mínimos regulatórios objetivos para as condições de trabalho nas posições operacionais "
            "ATS. O prestador deve prever pelo menos cinco minutos para cada mudança de turno e disponibilizar local de "
            "descanso.\n\n"
            "O regulamento determina ainda que o período máximo de trabalho contínuo não pode exceder seis horas sem "
            "intervalo para descanso fora do ambiente ATC, e que a duração de um turno não deve exceder oito horas. São "
            "parâmetros pensados para a prevenção da fadiga, fator crítico de segurança nesta profissão.\n\n"
            "Importa distinguir estes mínimos regulatórios das escalas praticadas localmente: o desenho exato dos turnos em "
            "cada órgão (ACC, APP, TWR ou FIS) não está especificado nas fontes públicas. O que o regulamento garante é o "
            "patamar mínimo que qualquer escala deve respeitar."
        ),
    },
    {
        "title": "Onde formar: ATO aprovadas pela AAC",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["formação", "AAC", "ATO", "licenciamento"],
        "excerpt": "A SENASA (Espanha) e a NAV Portugal constam entre as ATO aprovadas pela AAC com cursos de CTA. As validades dos certificados são pontuais — confirme sempre a lista vigente.",
        "content": (
            "A formação de controladores faz-se em organizações de formação (ATO) aprovadas pela AAC. Na lista mais recente "
            "consultada para esta base de conhecimento, com cursos de CTA identificados, constam pelo menos a SENASA, em "
            "Espanha, e a NAV Portugal.\n\n"
            "Ambas surgem autorizadas para formação básica de controlador, formação de qualificações (aeródromo, "
            "aproximação procedural e por vigilância, área procedural e por vigilância), formação prática de instrutor e "
            "formação de avaliadores; a NAV Portugal aparece ainda com formação de refrescamento e de conversão.\n\n"
            "Os certificados destas ATO têm validades pontuais — conforme a lista da AAC à data desta consulta, a da SENASA "
            "indicava 31/07/2027 e a da NAV Portugal 25/07/2027. Por serem datas que envelhecem, deve confirmar-se sempre a "
            "versão vigente da lista oficial antes de decidir."
        ),
    },
    {
        "title": "Conversão de licença estrangeira",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["licenciamento", "AAC", "conversão", "inglês"],
        "excerpt": "Quem já é CTA noutro país pode converter a licença na AAC: prova de legislação aeronáutica (FS.PEL.09) e, após aprovação, o pedido de conversão (FS.PEL.01), com prova de proficiência.",
        "content": (
            "Para quem já detém licença de controlador noutro país, a AAC publica um fluxo de conversão distinto do caminho "
            "de emissão inicial. O processo começa com o pedido de teste em legislação aeronáutica, através do formulário "
            "FS.PEL.09, com pagamento da taxa de exame teórico de 4.500$00 por prova.\n\n"
            "O requerente apresenta também a licença válida, o Certificado Médico Classe 3, documento de identificação e "
            "fotografia, e tem de fazer prova de proficiência linguística na língua usada na radiotelefonia em Cabo Verde e "
            "em inglês.\n\n"
            "Após aprovação na prova teórica, segue-se o pedido de conversão propriamente dito, através do formulário "
            "FS.PEL.01, com pagamento de 9.000$00. É este o trajeto formal para integrar, em Cabo Verde, uma qualificação "
            "obtida no estrangeiro."
        ),
    },
    {
        "title": "Unidades operacionais: ACC, torres e FIS",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["ASA", "ATC", "FIS", "ATS"],
        "excerpt": "Centro de Controlo no Sal, torres no Sal, Praia, Boa Vista e São Vicente, e serviço de informação de voo em São Filipe, Maio e São Nicolau: a malha ATS descrita pela ASA.",
        "content": (
            "A melhor fotografia oficial da malha de órgãos ATS de Cabo Verde vem das páginas da ASA — Navegação Aérea de "
            "Cabo Verde, S.A. A estrutura descrita inclui um Centro de Controlo de Tráfego Aéreo (ACC) no Sal.\n\n"
            "A nível de torres de controlo, a ASA refere quatro órgãos: Sal, Praia, Boa Vista e São Vicente. São as "
            "posições de controlo de aeródromo associadas aos principais aeroportos do país.\n\n"
            "Existem ainda órgãos de serviço de informação de voo (FIS) em São Filipe, no Maio e em São Nicolau. Esta "
            "distribuição — um centro de controlo, quatro torres e três órgãos FIS — descreve o ambiente operacional onde os "
            "controladores cabo-verdianos prestam serviço."
        ),
    },
    {
        "title": "Recência e revalidação",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["recência", "averbamento", "CV-CAR 2.3"],
        "excerpt": "Manter a recência é continuar apto a operar. O ponto prático é o averbamento de órgão: invalida-se após mais de 90 dias sem exercício e revalida-se por horas, refrescamento e avaliação.",
        "content": (
            "A recência traduz a ideia de que o controlador tem de continuar a praticar para se manter apto. O dado mais "
            "atual sobre o tema não é o texto informativo antigo da AAC, mas o CV-CAR 2.3 (2026).\n\n"
            "O ponto mais prático para a operação diária é o averbamento de órgão de controlo: vale por prazo definido no "
            "plano de competências da unidade, nunca superior a três anos, e torna-se inválido se o controlador deixar de "
            "exercer os privilégios por mais de 90 dias.\n\n"
            "Para revalidar, o profissional cumpre horas mínimas de exercício, formação de refrescamento e avaliação de "
            "competência, conforme o plano da unidade aprovado pela autoridade aeronáutica. É assim que a aptidão se mantém "
            "ao longo do tempo, mesmo sem alterar as qualificações já detidas."
        ),
    },
    {
        "title": "Controlo de área, aproximação e aeródromo",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["ATC", "CV-CAR 17", "ATS"],
        "excerpt": "O controlo de tráfego aéreo organiza-se em três níveis — área, aproximação e aeródromo — prestados, respetivamente, pelo centro de controlo, pelo centro/torres e pela torre (CV-CAR 17).",
        "content": (
            "Segundo o CV-CAR 17, o serviço de controlo de tráfego aéreo desdobra-se em três níveis, conforme a fase do voo "
            "e o espaço em causa: controlo de área, controlo de aproximação e controlo de aeródromo.\n\n"
            "O regulamento indica quem presta cada um. O controlo de área é prestado pelo centro de controlo; o controlo de "
            "aproximação pelo centro de controlo e, quando aplicável, pelas torres; e o controlo de aeródromo pela torre de "
            "controlo.\n\n"
            "Esta arrumação ajuda a perceber a viagem de uma aeronave do ponto de vista do controlo: do espaço de rota "
            "(área) para a transição de chegada e partida (aproximação) e, finalmente, para o movimento no e junto ao "
            "aeródromo."
        ),
    },
    {
        "title": "Os 3 meses sob OJTI",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["formação", "CV-CAR 2.3", "OJTI"],
        "excerpt": "A formação teórica não basta: o CV-CAR 2.3 exige pelo menos três meses de serviço com controlo real de tráfego aéreo sob supervisão de um instrutor em exercício (OJTI).",
        "content": (
            "Há uma diferença essencial entre saber a teoria e estar pronto para operar. O CV-CAR 2.3 (2026) torna essa "
            "diferença explícita ao exigir, para a emissão da licença, experiência prática com tráfego real.\n\n"
            "Em concreto, o candidato deve completar o curso de formação aprovado, demonstrar a competência exigida e "
            "realizar pelo menos três meses de serviço satisfatório envolvendo controlo real de tráfego aéreo sob supervisão "
            "de um instrutor em exercício (OJTI).\n\n"
            "É neste período que o futuro controlador consolida, sob acompanhamento, a tomada de decisão em tempo real. Por "
            "isso, no caminho para a profissão, estes três meses marcam a passagem da formação inicial para a prontidão "
            "operacional."
        ),
    },
    {
        "title": "O quadro legal da aviação civil em Cabo Verde",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["legislação", "CV-CAR 2.3", "AAC"],
        "excerpt": "Do Código Aeronáutico aos CV-CAR: a hierarquia normativa que enquadra o controlador. Em caso de divergência, prevalece o CV-CAR 2.3 (2026).",
        "content": (
            "O sistema de aviação civil de Cabo Verde ancora-se no Código Aeronáutico, aprovado pelo Decreto-Legislativo "
            "n.º 1/2001 e alterado pelo Decreto-Legislativo n.º 4/2009. Os regulamentos técnicos da AAC citam o artigo "
            "173.º deste código como base jurídica para a emissão dos CV-CAR.\n\n"
            "Para efeitos de hierarquia, o Código é a lei de base e os CV-CAR detalham a implementação técnica. Sobre os "
            "controladores incidem, em especial, o CV-CAR 17 (serviços de tráfego aéreo), o CV-CAR 2.3 (licenciamento de "
            "CTA), o CV-CAR 2.4 (medicina aeronáutica) e o CV-CAR 22 (notificação de ocorrências).\n\n"
            "Existe um cuidado editorial importante: páginas informativas antigas da AAC coexistem com o texto normativo "
            "mais recente. Em caso de divergência, prevalece o CV-CAR 2.3 (2026), que atualizou o regime anterior."
        ),
    },
    {
        "title": "As normas ICAO que enquadram o trabalho do CTA",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["ICAO", "legislação", "ATS", "segurança"],
        "excerpt": "Anexos 1, 11 e 19 e os documentos 4444 e 7030 da ICAO formam o padrão internacional que sustenta o licenciamento, os serviços ATS e a gestão da segurança em Cabo Verde.",
        "content": (
            "A regulação cabo-verdiana declara aderência às normas da ICAO, e várias delas são diretamente relevantes para "
            "o trabalho do controlador. O Anexo 1 — Personnel Licensing reúne os padrões mínimos para o licenciamento de "
            "pessoal, incluindo controladores; a introdução do CV-CAR 2.3 (2026) afirma incorporar emendas recentes deste "
            "anexo.\n\n"
            "O Anexo 11 cobre os serviços de tráfego aéreo e o Anexo 19 trata da gestão da segurança. A estes juntam-se "
            "documentos de implementação como o Doc 4444 (PANS-ATM) e o Doc 7030.\n\n"
            "A ligação não é meramente teórica: o próprio CV-CAR 17 manda que a separação entre voos controlados e espaço "
            "aéreo especial ativo observe os Documentos 4444 e 7030 da ICAO. O padrão internacional traduz-se, assim, em "
            "regra nacional aplicável no terreno."
        ),
    },
    {
        "title": "Reentrada após afastamento longo",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["recência", "licenciamento", "CV-CAR 2.3"],
        "excerpt": "A Diretiva n.º 01/PEL/2024 gradua o restabelecimento de privilégios após longos períodos sem exercício. É uma regra de reentrada operacional, não o caminho normal de ingresso.",
        "content": (
            "Quando um controlador se afasta da operação por um período longo, a recuperação dos privilégios obedece a uma "
            "gradação prevista na Diretiva n.º 01/PEL/2024 (com a anterior Instrução n.º 20/DSV/2015 ainda útil como "
            "referência histórica).\n\n"
            "Acima de seis meses e até um ano, exige-se supervisão e verificação de competência. Acima de um e até cinco "
            "anos, acrescenta-se curso de refrescamento, supervisão mais prolongada e verificação. Acima de cinco anos, o "
            "retorno é mais exigente, podendo implicar curso inicial, exames, nova qualificação e supervisão ampliada.\n\n"
            "É importante ler isto pelo que é: uma regra de reentrada operacional para quem já foi controlador, e não o "
            "caminho normal de ingresso na profissão."
        ),
    },
    {
        "title": "Requisitos de elegibilidade: idade, conhecimentos e experiência",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["licenciamento", "CV-CAR 2.3", "formação"],
        "excerpt": "Idade mínima de 21 anos, um conjunto de áreas obrigatórias de conhecimento e experiência prática supervisionada: os requisitos de elegibilidade para a licença CTA (CV-CAR 2.3).",
        "content": (
            "O CV-CAR 2.3 (2026) fixa requisitos de elegibilidade para a emissão da licença de controlador. O primeiro é a "
            "idade: o candidato deve ter pelo menos 21 anos.\n\n"
            "A par disso, exige-se domínio de um conjunto de áreas obrigatórias de conhecimento, entre as quais legislação "
            "aeronáutica, equipamento ATC, conhecimentos gerais de aeronaves, desempenho humano, língua, meteorologia, "
            "navegação e procedimentos operacionais.\n\n"
            "Por fim, há o requisito de experiência: o candidato completa curso aprovado, demonstra a competência exigida e "
            "realiza pelo menos três meses de serviço com controlo real de tráfego aéreo sob supervisão de um OJTI. "
            "Elegibilidade, conhecimento e experiência supervisionada formam, em conjunto, a porta de entrada na profissão."
        ),
    },
    {
        "title": "Caminhos de carreira do CTA",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["carreira", "CV-CAR 2.3", "AAC"],
        "excerpt": "Do instruendo ao avaliador, da supervisão à inspeção: uma leitura dos percursos possíveis na profissão, ancorada nas qualificações do CV-CAR 2.3 e em vagas técnicas da AAC.",
        "content": (
            "Embora as fontes não publiquem um plano de carreira único, as normas e as oportunidades públicas permitem "
            "traçar, com elevada confiança, um percurso típico. Tudo começa no instruendo CTA, que evolui para controlador "
            "recém-licenciado.\n\n"
            "A partir daí, o profissional obtém qualificações em torre, aproximação ou área e o respetivo averbamento de "
            "órgão, tornando-se controlador experiente. Pode depois assumir funções de formação e avaliação — instrutor em "
            "exercício (OJTI), instrutor em simulador (STDI) ou avaliador.\n\n"
            "No topo do percurso surgem funções de supervisão operacional, coordenação ou inspeção, bem como uma trilha "
            "regulatória na AAC. Esta leitura apoia-se nas categorias de qualificação do CV-CAR 2.3, nos requisitos para "
            "OJTI e numa vaga pública da AAC para Inspetor de Navegação Aérea, que pedia formação de CTA e experiência "
            "relevante."
        ),
    },
    {
        "title": "UTA/ISAT: formação académica complementar",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["formação", "carreira", "aviação civil"],
        "excerpt": "O ISAT, da UTA, oferece formação superior em Gestão e Planeamento da Aviação Civil no Sal. É uma via académica complementar — não uma via direta de licença de controlador.",
        "content": (
            "A Universidade Técnica do Atlântico (UTA), através do ISAT no Sal, oferece formação superior em Gestão e "
            "Planeamento da Aviação Civil. É uma base académica que pode ser relevante para quem pretende uma carreira "
            "ligada ao setor.\n\n"
            "Importa, porém, classificar bem este percurso. Nas páginas consultadas, o ISAT não aparece como curso de "
            "licenciamento de controlador de tráfego aéreo.\n\n"
            "O enquadramento correto é, por isso, tratar o ISAT como formação académica complementar ou preparatória, e não "
            "como via direta para a licença de CTA, que se obtém em organizações de formação (ATO) aprovadas pela AAC."
        ),
    },
    {
        "title": "Comunicações e vigilância na FIR do Sal",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["FIR", "ATS", "ICAO"],
        "excerpt": "VHF, HF e CPDLC nas comunicações; cobertura radar de três estações e ADS-C na vigilância. O contexto técnico do controlo de área e rota — com o limite de UTA/UIR não especificado.",
        "content": (
            "A divulgação da AAC caracteriza o ambiente técnico de trabalho na FIR Oceânica do Sal. No plano das "
            "comunicações, a FIR dispõe de VHF, HF e CPDLC (comunicações por enlace de dados entre controlador e piloto).\n\n"
            "No plano da vigilância, há cobertura radar a partir de três estações — Santo Antão, Sal e Santiago — e "
            "vigilância por ADS-C. Estes meios sustentam o trabalho dos controladores que operam em área e rota e nos "
            "principais aeroportos.\n\n"
            "Mantém-se, ainda assim, um dado por confirmar: o limite exato de UTA/UIR aplicável ao espaço cabo-verdiano não "
            "está especificado nas fontes oficiais consolidadas e deve ser verificado diretamente na AIP/e-AIP vigente."
        ),
    },
    {
        "title": "Aeródromo e aeroporto: as definições oficiais",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["aeroportos", "AAC", "legislação"],
        "excerpt": "Aeródromo e aeroporto não são sinónimos. A AAC distingue-os tecnicamente e regista que Cabo Verde tem 7 aeródromos — 4 internacionais e 3 domésticos.",
        "content": (
            "Na linguagem corrente confundem-se, mas tecnicamente aeródromo e aeroporto têm definições distintas. A AAC "
            "define aeródromo como a área delimitada de terra ou água, com edificações, instalações e equipamentos, "
            "destinada total ou parcialmente à chegada, ao movimento e à partida de aeronaves.\n\n"
            "Aeroporto é, mais precisamente, o aeródromo público internacional dotado de serviços como alfândega, sanidade, "
            "imigração e afins. Todo o aeroporto é um aeródromo, mas nem todo o aeródromo é aeroporto.\n\n"
            "A mesma fonte oficial regista que Cabo Verde possui sete aeródromos, sendo quatro internacionais e três "
            "domésticos. Esta distinção é útil para separar a infraestrutura aeroportuária da prestação dos serviços de "
            "tráfego aéreo."
        ),
    },
    {
        "title": "Cultura justa, SMS e sistema de qualidade",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["cultura justa", "segurança", "CV-CAR 17", "CV-CAR 22"],
        "excerpt": "Sistema de qualidade, gestor de qualidade, SMS aprovado e notificação de ocorrências (CV-CAR 17), com reporte orientado para a prevenção e não para a culpa (CV-CAR 22).",
        "content": (
            "A segurança operacional em Cabo Verde tem um desenho jurídico sólido. O CV-CAR 17 obriga o prestador de "
            "serviços de tráfego aéreo a manter um sistema de qualidade, um gestor de qualidade, um sistema de gestão da "
            "segurança (SMS) aprovado pela autoridade aeronáutica e um sistema de notificação de ocorrências.\n\n"
            "Esse sistema de notificação serve para recolher, tratar e analisar dados, identificar tendências adversas e "
            "corrigir deficiências antes que se transformem em acidentes.\n\n"
            "A filosofia subjacente é a da cultura justa, consagrada no CV-CAR 22, que afirma expressamente que a "
            "notificação de ocorrências se destina a prevenir acidentes e incidentes, e não a imputar culpas ou "
            "responsabilidades. É esta combinação — qualidade, SMS e reporte preventivo — que protege quem opera e quem voa."
        ),
    },
    {
        "title": "Da notificação de ocorrências à investigação técnica",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["segurança", "CV-CAR 22", "IPIAAM", "cultura justa"],
        "excerpt": "Da mitigação imediata ao feedback de segurança, o fluxo de notificação de ocorrências (CV-CAR 17 e 22) liga-se, quando há acidente ou incidente grave, à investigação técnica do DL n.º 6/2023.",
        "content": (
            "Quando ocorre algo de anormal num órgão ATS, há um fluxo estruturado a seguir. Primeiro, a mitigação imediata e "
            "a continuidade segura do serviço; depois, o registo interno da ocorrência e a preservação de documentos, "
            "gravações e evidências.\n\n"
            "Segue-se a notificação à AAC, conforme a regulamentação aplicável, e a recolha, tratamento e análise dos "
            "dados, com vista a identificar tendências e deficiências e a desencadear ações corretivas, formação ou revisão "
            "de procedimentos. Este desenho está alinhado com o CV-CAR 17 e com a orientação preventiva do CV-CAR 22.\n\n"
            "Quando se trata de acidente ou incidente grave, aciona-se o regime de investigação técnica previsto no "
            "Decreto-Lei n.º 6/2023, conduzido pelo IPIAAM. A investigação técnica é distinta da regulação e do reporte "
            "interno, e visa aprender com o sucedido para reforçar a segurança."
        ),
    },
    {
        "title": "Dados não especificados: porque publicamos só o oficial",
        "type": "educativo",
        "visibility": "publico",
        "tags": ["transparência", "legislação", "AAC"],
        "excerpt": "Salários de CTA e limites de UTA/UIR mantêm-se não especificados nas fontes oficiais. A política editorial da ACCTA é publicar apenas o que tem origem oficial e nunca inventar números.",
        "content": (
            "Há informação que, por rigor, não publicamos. Os salários de controlador de tráfego aéreo em Cabo Verde não "
            "estão especificados nas publicações públicas examinadas; vagas técnicas mencionam remuneração segundo tabela "
            "vigente, sem expor montantes. Por isso, evitamos divulgar faixas não oficiais.\n\n"
            "O mesmo se aplica ao limite exato de UTA/UIR aplicável à FIR Oceânica do Sal, que se mantém não especificado e "
            "deve ser confirmado por leitura direta da AIP/e-AIP vigente.\n\n"
            "Esta é a nossa política editorial: citar a base legal de cada requisito, fazer prevalecer o CV-CAR 2.3 (2026) "
            "sobre páginas informativas antigas e assinalar com transparência o que está por confirmar, em vez de preencher "
            "lacunas com suposições."
        ),
    },
    # ===================== INSTITUCIONAL (7) ===================== #
    {
        "title": "Missão e objetivos da ACCTA",
        "type": "institucional",
        "visibility": "publico",
        "tags": ["ACCTA", "associação", "segurança"],
        "excerpt": "A ACCTA existe para representar os controladores de tráfego aéreo, valorizar a profissão e promover a segurança operacional e o conhecimento rigoroso sobre o setor em Cabo Verde.",
        "content": (
            "A ACCTA — Associação Cabo-verdiana dos Controladores de Tráfego Aéreo nasce da vontade de dar voz coletiva a "
            "uma profissão essencial para a segurança da aviação. A sua missão é representar os controladores, valorizar a "
            "profissão e contribuir para um setor mais seguro e bem informado.\n\n"
            "Entre os seus objetivos está o de informar com rigor: reunir e divulgar conhecimento fiável sobre a profissão, "
            "a formação, o licenciamento e o quadro regulatório que enquadra o trabalho do controlador em Cabo Verde, "
            "sempre a partir de fontes oficiais.\n\n"
            "A associação assume também um papel educativo perante o público, ajudando a explicar o que fazem os "
            "controladores e por que razão o seu trabalho é determinante para que cada voo decorra em segurança. É este "
            "compromisso com a profissão e com o interesse público que orienta a sua atuação."
        ),
    },
    {
        "title": "Quem é a ACCTA: a voz dos controladores",
        "type": "institucional",
        "visibility": "publico",
        "tags": ["ACCTA", "associação", "condições de trabalho", "segurança"],
        "excerpt": "Identidade e compromissos da ACCTA: a segurança operacional, a valorização da profissão e a defesa de condições de trabalho dignas para os controladores de tráfego aéreo.",
        "content": (
            "A ACCTA assume-se como a voz coletiva dos controladores de tráfego aéreo de Cabo Verde. A sua identidade "
            "constrói-se em torno de três compromissos que orientam tudo o que faz.\n\n"
            "O primeiro é a segurança operacional: defender uma cultura de segurança robusta e o reporte responsável de "
            "ocorrências. O segundo é a valorização da profissão: dar a conhecer o papel do controlador e promover "
            "conhecimento rigoroso sobre formação, licenciamento e carreira.\n\n"
            "O terceiro é a defesa de condições de trabalho dignas e seguras, com base nas salvaguardas que o próprio quadro "
            "regulatório consagra. Estes três compromissos — segurança, valorização e condições de trabalho — definem o "
            "lugar que a ACCTA pretende ocupar junto dos seus membros e da comunidade aeronáutica."
        ),
    },
    {
        "title": "O compromisso com a segurança e a cultura justa",
        "type": "institucional",
        "visibility": "publico",
        "tags": ["segurança", "cultura justa", "CV-CAR 22", "ACCTA"],
        "excerpt": "A ACCTA defende a cultura justa de segurança: um ambiente em que reportar ocorrências serve para prevenir e aprender, não para punir, em linha com o CV-CAR 22 e o CV-CAR 17.",
        "content": (
            "Para a ACCTA, a segurança operacional não é um slogan, mas o eixo da profissão. Por isso, a associação assume "
            "como princípio a cultura justa: um ambiente em que reportar ocorrências serve para aprender e prevenir, e não "
            "para atribuir culpas.\n\n"
            "Este princípio tem base regulatória clara. O CV-CAR 22 afirma que a notificação de ocorrências se destina a "
            "prevenir acidentes e incidentes, e não a imputar responsabilidades; e o CV-CAR 17 obriga o prestador ATS a "
            "manter um sistema de gestão da segurança aprovado e um sistema de notificação de ocorrências.\n\n"
            "A ACCTA defende que estas garantias sejam plenamente vividas no terreno, porque um profissional que confia no "
            "sistema reporta mais e melhor — e é desse reporte que nasce a melhoria contínua da segurança de todos."
        ),
    },
    {
        "title": "Defesa de condições de trabalho dignas e seguras",
        "type": "institucional",
        "visibility": "socios",
        "tags": ["condições de trabalho", "CV-CAR 17", "ACCTA"],
        "excerpt": "As salvaguardas de fadiga do CV-CAR 17 — pausas por mudança de turno, limite de trabalho contínuo e duração máxima de turno — são a base regulatória da pauta da ACCTA por condições dignas.",
        "content": (
            "A defesa de condições de trabalho dignas e seguras é uma das prioridades da ACCTA junto dos seus membros. Esta "
            "pauta não parte de meras reivindicações: assenta em salvaguardas que o próprio CV-CAR 17 consagra.\n\n"
            "O regulamento fixa mínimos objetivos de prevenção da fadiga: pelo menos cinco minutos por mudança de turno nas "
            "posições operacionais, um limite de seis horas de trabalho contínuo antes de intervalo fora do ambiente ATC e "
            "uma duração de turno que não deve exceder oito horas, além de local de descanso.\n\n"
            "A ACCTA toma estes mínimos regulatórios como ponto de partida para acompanhar as escalas praticadas localmente "
            "e para dialogar, em nome dos controladores, sobre condições de trabalho que protejam a saúde dos profissionais "
            "e, com ela, a segurança das operações."
        ),
    },
    {
        "title": "Código de conduta da ACCTA",
        "type": "institucional",
        "visibility": "socios",
        "tags": ["ACCTA", "associação", "ética"],
        "excerpt": "Princípios, deveres dos membros, condutas vedadas, comissão de ética e sanções: as linhas do código de conduta que orienta a vida associativa da ACCTA.",
        "content": (
            "O código de conduta da ACCTA define a forma como os membros se relacionam entre si e com a comunidade "
            "aeronáutica. Os seus princípios orientadores são a segurança operacional, a ética, a legalidade, a "
            "independência técnica, a solidariedade profissional e a defesa do interesse público.\n\n"
            "Entre os deveres dos membros estão respeitar a legislação aeronáutica e as normas da AAC, atuar com "
            "profissionalismo e integridade, preservar a confidencialidade de informação sensível, promover a cultura justa "
            "de segurança, evitar conflitos de interesse e tratar com respeito colegas, pilotos, técnicos, passageiros e "
            "autoridades.\n\n"
            "O código identifica ainda condutas vedadas — como divulgar dados operacionais sensíveis sem autorização, "
            "representar a associação sem mandato, assediar ou discriminar, usar indevidamente os recursos da associação ou "
            "disseminar informação falsa em seu nome. Uma comissão de ética recebe denúncias, apura os factos com "
            "contraditório e recomenda medidas; as sanções vão da advertência à exclusão, conforme a gravidade e os "
            "estatutos."
        ),
    },
    {
        "title": "Transparência, prestação de contas e política editorial",
        "type": "institucional",
        "visibility": "socios",
        "tags": ["transparência", "ACCTA", "associação"],
        "excerpt": "A ACCTA assume a transparência como princípio de governança e adota uma política editorial estrita: apenas conteúdo de origem oficial, com o CV-CAR 2.3 a prevalecer e o que falta assinalado.",
        "content": (
            "A confiança numa associação constrói-se com transparência e prestação de contas. A ACCTA assume estes valores "
            "como princípios de governança perante os seus membros, comprometendo-se a informar com clareza sobre as suas "
            "decisões e atividades.\n\n"
            "A par da governança, a ACCTA adota uma política editorial estrita para tudo o que publica. A regra é "
            "fundamental: nenhum facto sem origem oficial. Os requisitos são apresentados com a sua base legal, e em caso "
            "de divergência regulatória prevalece o CV-CAR 2.3 (2026).\n\n"
            "Quando um dado não está especificado nas fontes oficiais — como os salários ou o limite de UTA/UIR — a "
            "associação assinala-o como tal e remete para a fonte adequada, em vez de inventar números. Esta disciplina "
            "editorial é, ela própria, uma forma de prestação de contas à comunidade."
        ),
    },
    {
        "title": "Quem pode aderir à ACCTA e categorias de membro",
        "type": "institucional",
        "visibility": "publico",
        "tags": ["ACCTA", "associação", "adesão"],
        "excerpt": "Da situação operacional ao instruendo, do reformado ao inspetor: quem pode aderir à ACCTA e as categorias de membro previstas — efetivo, associado, fundador e honorário.",
        "content": (
            "A adesão à ACCTA está pensada para acolher quem se relaciona com a profissão de controlador de tráfego aéreo. "
            "A ficha de adesão prevê diferentes situações profissionais: controlador operacional, instruendo, controlador "
            "reformado, inspetor ou regulador, entre outras.\n\n"
            "Quanto ao tipo de adesão, o modelo associativo prevê quatro categorias de membro: efetivo, associado, fundador "
            "e honorário. Cada uma reflete a forma de ligação do membro à associação.\n\n"
            "Ao aderir, o membro declara que as informações prestadas são verdadeiras, que conhece e aceita os estatutos e "
            "o código de conduta e que autoriza o tratamento dos seus dados para fins associativos e administrativos. É "
            "através desta adesão informada que a ACCTA reúne a comunidade que representa."
        ),
    },
    # ===================== NOTÍCIA (6 · publico) ===================== #
    {
        "title": "CV-CAR 2.3 (2026): o novo regime de licenciamento",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["CV-CAR 2.3", "licenciamento", "AAC", "ICAO"],
        "excerpt": "O CV-CAR 2.3 (2026) atualizou o licenciamento de controladores: eliminou a validade da licença em si, concentrou a disciplina nas qualificações e averbamentos e incorporou o Anexo 1 da ICAO.",
        "content": (
            "O CV-CAR 2.3, na sua versão de 2026, marca uma mudança importante no regime de licenciamento de controladores "
            "de tráfego aéreo em Cabo Verde. A própria introdução do regulamento informa que a revisão eliminou a validade "
            "da licença em si.\n\n"
            "Em vez de uma validade fixa para a licença, a disciplina passou a concentrar-se na emissão, revalidação e "
            "renovação de qualificações, averbamentos e designações. Na prática, o que importa acompanhar passou a ser, "
            "sobretudo, a validade do averbamento de órgão de controlo e das qualificações.\n\n"
            "A revisão incorpora ainda emendas recentes do Anexo 1 da ICAO, que reúne os padrões mínimos para o "
            "licenciamento de pessoal aeronáutico. Para efeitos de informação ao público, este é o texto que prevalece "
            "sobre páginas antigas que ainda referiam validades já ultrapassadas."
        ),
    },
    {
        "title": "Cabo Verde Airports assume a gestão dos aeroportos (desde julho 2023)",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["aeroportos", "legislação", "ASA"],
        "excerpt": "Com o contrato de concessão em vigor desde julho de 2023, a Cabo Verde Airports passou a gerir os aeroportos e aeródromos do país. A ASA mantém a prestação dos serviços de tráfego aéreo.",
        "content": (
            "A gestão das infraestruturas aeroportuárias de Cabo Verde está concessionada. A Lei n.º 64/IX/2019 estabeleceu "
            "o regime jurídico da concessão do serviço público aeroportuário, e o Decreto-Lei n.º 14/2022 atribuiu a "
            "concessão à VINCI Airports.\n\n"
            "Com a entrada em vigor do contrato, em julho de 2023, a Cabo Verde Airports passou a assumir a gestão dos "
            "aeroportos e aeródromos do país. Trata-se de uma alteração relevante na arquitetura institucional do setor.\n\n"
            "É importante, no entanto, separar os papéis: a concessão diz respeito à infraestrutura aeroportuária. A "
            "prestação dos serviços de tráfego aéreo continua, nas fontes oficiais consultadas, associada à ASA — Navegação "
            "Aérea de Cabo Verde, S.A. — que é o operador mais diretamente ligado ao trabalho dos controladores."
        ),
    },
    {
        "title": "FPEF e SENASA abrem curso inicial de controlo de tráfego aéreo",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["formação", "carreira", "ATO"],
        "excerpt": "Registo oficial de um curso inicial de CTA patrocinado: 24 vagas, em Madrid, com 16 semanas de duração e seleção em três fases. Um exemplo de ingresso por via patrocinada na profissão.",
        "content": (
            "Para além do trajeto geral através de ATO aprovadas, há registo oficial de um caminho de ingresso por via "
            "patrocinada. O FPEF, em cooperação com a SENASA, abriu concurso para um curso inicial de controlo de tráfego "
            "aéreo destinado a torre — formação básica e qualificações de aeródromo (ADI/ADV).\n\n"
            "Segundo a divulgação, o curso oferecia 24 vagas, decorria em Madrid e tinha duração de 16 semanas. A seleção "
            "organizava-se em três fases: teste de inglês, teste psicotécnico e de personalidade e entrevista oral em "
            "inglês.\n\n"
            "Este tipo de programa mostra que, em Cabo Verde, o ingresso na profissão pode ocorrer por um modelo "
            "patrocinado e selecionado, além do percurso geral via organizações de formação. Por se tratar de informação "
            "datada, os interessados devem confirmar sempre a existência de concursos em aberto junto das entidades "
            "competentes."
        ),
    },
    {
        "title": "ASA passa a apresentar-se como Navegação Aérea de Cabo Verde",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["ASA", "ATS", "aviação civil"],
        "excerpt": "A ASA passou a apresentar-se institucionalmente como Navegação Aérea de Cabo Verde, S.A. — um reposicionamento que ajuda a identificar o prestador ligado ao trabalho dos controladores.",
        "content": (
            "A ASA passou a apresentar-se institucionalmente como Navegação Aérea de Cabo Verde, S.A., com sede na ilha do "
            "Sal. O reposicionamento traduz, no nome, a sua função central no sistema aeronáutico nacional.\n\n"
            "Esta clarificação é materialmente relevante. Num contexto em que a gestão aeroportuária passou para uma "
            "concessionária, identificar o prestador dos serviços de tráfego aéreo ajuda a perceber qual é o operador mais "
            "diretamente ligado ao trabalho dos controladores.\n\n"
            "Segundo a documentação oficial, é a ASA que opera o Centro de Controlo no Sal, as torres de controlo e os "
            "órgãos de informação de voo. O reposicionamento institucional reforça, assim, a leitura da estrutura ATS do "
            "país."
        ),
    },
    {
        "title": "IPIAAM e o regime de investigação técnica",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["IPIAAM", "segurança", "legislação"],
        "excerpt": "O Decreto-Lei n.º 6/2023 atribui ao IPIAAM a investigação técnica de acidentes e incidentes graves — uma função distinta da regulação e do reporte interno dos órgãos ATS.",
        "content": (
            "A investigação técnica de acidentes e incidentes graves na aviação civil cabo-verdiana é regida pelo "
            "Decreto-Lei n.º 6/2023, que atribui essa responsabilidade ao IPIAAM.\n\n"
            "Esta função é distinta das demais camadas do sistema. Não se confunde com a regulação, que cabe à AAC, nem com "
            "o reporte interno de ocorrências dos órgãos ATS, orientado para a prevenção segundo o CV-CAR 22.\n\n"
            "A investigação técnica entra em cena perante um acidente ou incidente grave e tem por finalidade apurar causas "
            "e fatores contributivos para que se possa aprender e prevenir. Distinguir investigação, regulação e reporte é "
            "essencial para compreender como o sistema protege a segurança das operações."
        ),
    },
    {
        "title": "AAC mantém SENASA e NAV Portugal entre as ATO aprovadas",
        "type": "noticia",
        "visibility": "publico",
        "tags": ["formação", "AAC", "ATO", "licenciamento"],
        "excerpt": "A lista oficial de ATO aprovadas pela AAC inclui a SENASA e a NAV Portugal com cursos de CTA. As validades dos certificados são pontuais e devem ser confirmadas na versão vigente.",
        "content": (
            "A lista oficial de organizações de formação (ATO) aprovadas pela AAC, na versão consultada para esta base de "
            "conhecimento, mantém a SENASA, em Espanha, e a NAV Portugal entre as entidades com cursos de controlador de "
            "tráfego aéreo.\n\n"
            "O escopo aprovado abrange formação básica de controlador, formação de qualificações (aeródromo, aproximação "
            "procedural e por vigilância, área procedural e por vigilância), formação prática de instrutor e formação de "
            "avaliadores; no caso da NAV Portugal, surgem ainda formação de refrescamento e de conversão.\n\n"
            "Como os certificados destas ATO têm validades pontuais, esta informação envelhece. Por isso, deve confirmar-se "
            "sempre a versão vigente da lista oficial da AAC antes de qualquer decisão de formação."
        ),
    },
]


# --------------------------------------------------------------------------- #
# Construção do documento + validação offline + seed
# --------------------------------------------------------------------------- #


def build_post_doc(article: dict, index: int) -> dict:
    """Documento `posts` determinístico (idempotência por uuid5 do slug)."""
    slug = slugify(article["title"])
    post_id = str(uuid.uuid5(uuid.NAMESPACE_URL, SLUG_BASE_URL + slug))
    when = (BASE_DATE - timedelta(days=index * 3)).isoformat()
    return {
        "id": post_id,
        "title": article["title"],
        "slug": slug,
        "excerpt": article["excerpt"],
        "content": article["content"],
        "type": article["type"],
        "visibility": article["visibility"],
        "status": "publicado",
        "tags": article["tags"],
        "author_id": None,
        "author_name": "ACCTA",
        "created_at": when,
        "updated_at": None,
        "published_at": when,
    }


def validate_articles() -> None:
    """Guarda editorial offline (corre sem BD). Levanta AssertionError se falhar."""
    assert len(ARTICLES) == 40, f"Esperados 40 artigos, encontrados {len(ARTICLES)}"

    docs = [build_post_doc(a, i) for i, a in enumerate(ARTICLES)]

    slugs = [d["slug"] for d in docs]
    ids = [d["id"] for d in docs]
    assert len(set(slugs)) == 40, "Slugs duplicados ou em falta"
    assert len(set(ids)) == 40, "IDs (uuid5) duplicados ou em falta"

    types = {d["type"] for d in docs}
    assert types == {"noticia", "institucional", "educativo"}, f"Categorias inesperadas: {types}"

    visibilities = {d["visibility"] for d in docs}
    assert visibilities <= {"publico", "socios"}, f"Visibilidades inesperadas: {visibilities}"

    for d in docs:
        assert 0 < len(d["excerpt"]) <= 320, f"Excerpt inválido em '{d['title']}' ({len(d['excerpt'])})"
        assert 3 <= len(d["tags"]) <= 5, f"Nº de tags fora de 3-5 em '{d['title']}'"
        haystack = " ".join([d["title"], d["excerpt"], d["content"], " ".join(d["tags"])]).lower()
        for term in FORBIDDEN:
            assert term not in haystack, f"Termo proibido '{term}' em '{d['title']}'"

    # Distribuição esperada (spec §5): educativo 27 · institucional 7 · noticia 6.
    counts = {t: sum(1 for d in docs if d["type"] == t) for t in ("educativo", "institucional", "noticia")}
    assert counts == {"educativo": 27, "institucional": 7, "noticia": 6}, f"Distribuição inesperada: {counts}"


async def seed() -> None:
    from database import db, ensure_schema, close_pool

    await ensure_schema()
    inserted = updated = 0
    try:
        for i, article in enumerate(ARTICLES):
            doc = build_post_doc(article, i)
            existing = await db.posts.find_one({"id": doc["id"]}, {"_id": 0})
            if existing:
                # Preserva a cronologia já gravada (não reescreve datas).
                doc["created_at"] = existing.get("created_at", doc["created_at"])
                doc["published_at"] = existing.get("published_at", doc["published_at"])
                await db.posts.update_one({"id": doc["id"]}, {"$set": doc})
                updated += 1
            else:
                await db.posts.insert_one(doc)
                inserted += 1
        print(f"OK: {inserted} inseridos, {updated} atualizados (total {len(ARTICLES)} artigos).")
    finally:
        await close_pool()


if __name__ == "__main__":
    validate_articles()
    print("Guarda editorial offline: OK (40 artigos, 3 categorias, sem termos proibidos).")
    if "--validate" in sys.argv:
        sys.exit(0)
    asyncio.run(seed())
