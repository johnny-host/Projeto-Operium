"""Ponto eletrônico (Fase 4): marcações, apuração diária e ocorrências.

Escopo: registrar marcações e apurar o que foi realizado. Este módulo NÃO altera
cadastro, escalas, regras, folha de pagamento nem banco de horas; apenas lê esses dados.

Marcação (dict) — fica em funcionario["marcacoes"], como "jornadas" fica em
funcionario["jornadas"]:
    {
        "data": "27/10/2026",        # DD/MM/AAAA, mesmo formato do projeto
        "hora": "08:02",             # HH:MM
        "tipo": "entrada" | "saida_intervalo" | "volta_intervalo" | "saida",
        "origem": "ponto" | "manual",  # ponto = hora do sistema; manual = lançada pelo admin
        "observacao": "",            # motivo, obrigatório quando manual
    }

Turno: sequência entrada -> [saida_intervalo -> volta_intervalo] -> saida. Pode virar a
meia-noite e é atribuído à data da entrada (como nas escalas). Um turno aberto há 24h
ou mais é considerado esquecido e uma nova entrada é aceita.

Apuração do dia (dict devolvido por apurar_dia):
    data, turnos, previsto_min, trabalhado_min, intervalo_min, diferenca_min (ou None),
    extra_min, debito_min, ocorrencias (list[str]), incompleto (bool)

A diferença diária é só informativa: não é acumulada nem vira saldo de banco de horas.
"""
from datetime import datetime, time, timedelta

from escalas import planejar_dia
from funcionarios import obter_data_admissao, selecionar_funcionario
from jornada import (
    DIAS_SEMANA, converter_data, duracao_turno, formatar_minutos, ler_periodo,
    minutos_horario, minutos_trabalhados, validar_horario,
)
from regras import regra_vigente
from validacoes import confirmar, ler_validado, validar_data, validar_nome

TIPOS = ("entrada", "saida_intervalo", "volta_intervalo", "saida")
ROTULOS = {
    "entrada": "Entrada",
    "saida_intervalo": "Saída para intervalo",
    "volta_intervalo": "Volta do intervalo",
    "saida": "Saída",
}
ORIGENS = ("ponto", "manual")

# Tipos aceitos depois de cada marcação (None = ainda não há marcações).
SEGUINTES = {
    None: ("entrada",),
    "entrada": ("saida_intervalo", "saida"),
    "saida_intervalo": ("volta_intervalo",),
    "volta_intervalo": ("saida",),
    "saida": ("entrada",),
}
LIMITE_TURNO = timedelta(hours=24)
TOLERANCIA_MIN = 5  # diferença até este valor não gera extra/débito nem atraso


# ---------- Marcações ----------


def momento(marcacao):
    return datetime.strptime(f"{marcacao['data']} {marcacao['hora']}", "%d/%m/%Y %H:%M")


def marcacoes_ordenadas(funcionario):
    return sorted(funcionario.get("marcacoes", []), key=momento)


def criar_marcacao(tipo, data, hora, origem="ponto", observacao=""):
    if tipo not in TIPOS:
        raise ValueError("Tipo de marcação inválido.")
    if origem not in ORIGENS:
        raise ValueError("Origem de marcação inválida.")
    return {"data": validar_data(data), "hora": validar_horario(hora),
            "tipo": tipo, "origem": origem, "observacao": observacao.strip()}


def tipos_seguintes(anterior, instante):
    """Tipos aceitos depois da marcação `anterior` (ou None), no `instante` dado."""
    if anterior is None:
        return SEGUINTES[None]
    if anterior["tipo"] != "saida" and instante - momento(anterior) >= LIMITE_TURNO:
        return ("entrada",)  # o turno anterior ficou aberto e não bloqueia o novo
    return SEGUINTES[anterior["tipo"]]


def tipos_permitidos(funcionario, agora=None):
    agora = agora or datetime.now()
    passadas = [m for m in marcacoes_ordenadas(funcionario) if momento(m) <= agora]
    return tipos_seguintes(passadas[-1] if passadas else None, agora)


def validar_marcacao(funcionario, marcacao, agora=None):
    agora = agora or datetime.now()
    if funcionario["status"] != "ativo":
        raise ValueError("Reative o funcionário antes de registrar ponto.")
    if marcacao["origem"] == "manual" and not marcacao["observacao"]:
        raise ValueError("Informe o motivo da marcação manual.")
    instante = momento(marcacao)
    if instante > agora:
        raise ValueError("Não é possível registrar uma marcação no futuro.")
    if instante.date() < obter_data_admissao(funcionario):
        raise ValueError("A marcação não pode ser anterior à admissão.")

    ordenadas = marcacoes_ordenadas(funcionario)
    if any(momento(m) == instante for m in ordenadas):
        raise ValueError("Já existe uma marcação neste mesmo minuto.")
    anteriores = [m for m in ordenadas if momento(m) < instante]
    posteriores = [m for m in ordenadas if momento(m) > instante]

    anterior = anteriores[-1] if anteriores else None
    aceitos = tipos_seguintes(anterior, instante)
    if marcacao["tipo"] not in aceitos:
        raise ValueError("Neste ponto da sequência só é possível registrar: "
                         + ", ".join(ROTULOS[t] for t in aceitos) + ".")
    if posteriores:
        proxima = posteriores[0]
        # Intervalo esquecido é lançado em dois passos: a saída para intervalo pode ser
        # inserida antes da volta e o dia fica sinalizado até o segundo lançamento.
        em_dois_passos = marcacao["tipo"] == "saida_intervalo" and proxima["tipo"] == "saida"
        if not em_dois_passos and proxima["tipo"] not in tipos_seguintes(marcacao, momento(proxima)):
            raise ValueError("Esta marcação deixaria inconsistente a sequência já registrada depois dela.")


def registrar_marcacao(funcionario, marcacao, agora=None):
    validar_marcacao(funcionario, marcacao, agora)
    funcionario.setdefault("marcacoes", []).append(marcacao)
    return marcacao


# ---------- Turnos e horas realizadas ----------


def _minutos(inicio, fim):
    return int((fim - inicio).total_seconds() // 60)


def _novo_turno(instante=None):
    return {"data": None if instante is None else instante.date(), "entrada": instante,
            "saida": None, "pausa_inicio": None, "pausa_fim": None,
            "marcacoes": [], "ocorrencias": [], "abandonado": False}


def montar_turnos(marcacoes, agora=None):
    """Agrupa as marcações em turnos. Sequências incoerentes viram ocorrências."""
    agora = agora or datetime.now()
    turnos, atual = [], None
    for marcacao in sorted(marcacoes, key=momento):
        instante, tipo = momento(marcacao), marcacao["tipo"]
        if (atual and atual["entrada"] and atual["saida"] is None
                and instante - atual["entrada"] >= LIMITE_TURNO):
            atual["abandonado"] = True
            turnos.append(atual)
            atual = None
        if tipo == "entrada":
            if atual:
                atual["abandonado"] = True
                turnos.append(atual)
            atual = _novo_turno(instante)
        elif atual is None:
            atual = _novo_turno()
            atual["data"] = instante.date()
            atual["ocorrencias"].append(f"{ROTULOS[tipo]} sem entrada correspondente")
        atual["marcacoes"].append(marcacao)
        if tipo == "saida_intervalo" and atual["pausa_inicio"] is None:
            atual["pausa_inicio"] = instante
        elif tipo == "volta_intervalo" and atual["pausa_inicio"] and atual["pausa_fim"] is None:
            atual["pausa_fim"] = instante
        elif tipo == "saida":
            atual["saida"] = instante
            turnos.append(atual)
            atual = None
    if atual:
        turnos.append(atual)
    for turno in turnos:
        _avaliar_turno(turno, agora)
    return turnos


def _avaliar_turno(turno, agora):
    if turno["saida"] is None and turno["entrada"] is not None:
        if turno["abandonado"] or agora - turno["entrada"] >= LIMITE_TURNO:
            turno["ocorrencias"].append("Turno sem saída registrada")
        else:
            turno["ocorrencias"].append("Turno em andamento (saída ainda não marcada)")
    fechado = turno["saida"] is not None or turno["abandonado"]
    if fechado and turno["pausa_inicio"] and turno["pausa_fim"] is None:
        turno["ocorrencias"].append("Intervalo iniciado sem retorno registrado")


def turno_completo(turno):
    return (turno["entrada"] is not None and turno["saida"] is not None
            and (turno["pausa_inicio"] is None) == (turno["pausa_fim"] is None))


def minutos_intervalo(turno):
    if turno["pausa_inicio"] and turno["pausa_fim"]:
        return _minutos(turno["pausa_inicio"], turno["pausa_fim"])
    return 0


def minutos_realizados(turno):
    """Minutos líquidos (sem o intervalo); 0 se o turno estiver incompleto."""
    if not turno_completo(turno):
        return 0
    return max(_minutos(turno["entrada"], turno["saida"]) - minutos_intervalo(turno), 0)


# ---------- Apuração ----------


def comparar_horarios(dia, planejado, completos, ocorrencias, tolerancia):
    previsto_entrada = datetime.combine(dia, time()) + timedelta(minutes=minutos_horario(planejado["entrada"]))
    previsto_saida = previsto_entrada + timedelta(minutes=duracao_turno(planejado["entrada"], planejado["saida"]))
    diferenca = _minutos(previsto_entrada, completos[0]["entrada"])
    if diferenca > tolerancia:
        ocorrencias.append(f"Atraso de {diferenca} min na entrada")
    elif diferenca < -tolerancia:
        ocorrencias.append(f"Entrada {-diferenca} min antes do previsto")
    diferenca = _minutos(previsto_saida, completos[-1]["saida"])
    if diferenca < -tolerancia:
        ocorrencias.append(f"Saída antecipada de {-diferenca} min")
    elif diferenca > tolerancia:
        ocorrencias.append(f"Saída {diferenca} min após o previsto")


def conferir_regra(escala, regras, dia, turnos, todos, trabalhado, ocorrencias):
    regra = regra_vigente(regras, escala["empresa"], escala["categoria"], dia)
    if regra is None:
        ocorrencias.append("Sem regra vigente; limites não avaliados.")
        return
    horas = trabalhado / 60
    if horas > regra["limite_diario"]:
        ocorrencias.append(f"Jornada acima do limite diário da versão {regra['versao']}")
    if horas > regra["limite_diario"] + regra["limite_extra"]:
        ocorrencias.append("Excedente diário acima do limite de horas extras configurado")
    for turno in turnos:
        if not turno_completo(turno):
            continue
        pausa = minutos_intervalo(turno)
        if minutos_realizados(turno) / 60 > regra["intervalo_acima"] and pausa < regra["intervalo_minimo"]:
            ocorrencias.append(f"Intervalo de {pausa} min, menor que o configurado ({regra['intervalo_minimo']:g} min)")
        anterior = next((t for t in reversed(todos[:todos.index(turno)]) if t["saida"]), None)
        if anterior:
            descanso = _minutos(anterior["saida"], turno["entrada"]) / 60
            if descanso < regra["descanso_minimo"]:
                ocorrencias.append(f"Descanso de {descanso:.1f} h entre jornadas, menor que o configurado")


def apurar_dia(funcionario, dia, regras, agora=None, tolerancia=TOLERANCIA_MIN):
    """Apura um dia (date) comparando as marcações com a escala planejada."""
    agora = agora or datetime.now()
    todos = montar_turnos(funcionario.get("marcacoes", []), agora)
    turnos = [t for t in todos if t["data"] == dia]
    planejado, escala = planejar_dia(funcionario, dia)
    previsto = minutos_trabalhados(planejado)
    trabalhado = sum(minutos_realizados(t) for t in turnos)
    ocorrencias = [o for t in turnos for o in t["ocorrencias"]]
    incompleto = any(not turno_completo(t) for t in turnos)
    diferenca = None

    if not turnos:
        if (planejado["status"] == "trabalho" and dia < agora.date()
                and dia >= obter_data_admissao(funcionario)):
            ocorrencias.append("Sem marcação em dia de trabalho previsto (falta ou lançamento pendente)")
            incompleto = True
            diferenca = -previsto
    else:
        completos = [t for t in turnos if turno_completo(t)]
        if planejado["status"] != "trabalho":
            ocorrencias.append(f"Marcação em dia sem trabalho previsto ({planejado['status']})")
        elif completos:
            comparar_horarios(dia, planejado, completos, ocorrencias, tolerancia)
        if escala is not None:
            conferir_regra(escala, regras, dia, turnos, todos, trabalhado, ocorrencias)
        if not incompleto:
            diferenca = trabalhado - previsto

    extra = debito = 0
    if diferenca is not None and abs(diferenca) > tolerancia:
        extra, debito = max(diferenca, 0), max(-diferenca, 0)
    return {
        "data": dia, "turnos": turnos, "previsto_min": previsto, "trabalhado_min": trabalhado,
        "intervalo_min": sum(minutos_intervalo(t) for t in turnos if turno_completo(t)),
        "diferenca_min": diferenca, "extra_min": extra, "debito_min": debito,
        "ocorrencias": ocorrencias, "incompleto": incompleto,
    }


def apurar_periodo(funcionario, inicio, fim, regras, agora=None, tolerancia=TOLERANCIA_MIN):
    dia, ultimo = converter_data(inicio), converter_data(fim)
    if ultimo < dia or (ultimo - dia).days > 365:
        raise ValueError("Consulte de 1 a 366 dias.")
    dias = []
    while dia <= ultimo:
        dias.append(apurar_dia(funcionario, dia, regras, agora, tolerancia))
        dia += timedelta(days=1)
    apurados = [d for d in dias if d["diferenca_min"] is not None]
    return {
        "dias": dias,
        "trabalhado_min": sum(d["trabalhado_min"] for d in dias),
        "previsto_min": sum(d["previsto_min"] for d in apurados),
        "extra_min": sum(d["extra_min"] for d in dias),
        "debito_min": sum(d["debito_min"] for d in dias),
        "ocorrencias": sum(len(d["ocorrencias"]) for d in dias),
        "dias_apurados": len(apurados),
    }


# ---------- Exibição ----------


def formatar_marcacoes(apuracao):
    texto_dia = apuracao["data"].strftime("%d/%m/%Y")
    partes = []
    for turno in apuracao["turnos"]:
        for m in turno["marcacoes"]:
            outro_dia = "" if m["data"] == texto_dia else f" ({m['data'][:5]})"
            origem = " [manual]" if m["origem"] == "manual" else ""
            partes.append(f"{m['hora']} {ROTULOS[m['tipo']]}{outro_dia}{origem}")
    return "; ".join(partes)


def mostrar_apuracao_dia(apuracao):
    dia = apuracao["data"]
    linha = (f"\n{dia:%d/%m/%Y} {DIAS_SEMANA[dia.weekday()]} | previsto {formatar_minutos(apuracao['previsto_min'])}"
             f" | realizado {formatar_minutos(apuracao['trabalhado_min'])}")
    if apuracao["diferenca_min"] is not None:
        linha += f" | diferença {formatar_minutos(apuracao['diferenca_min'])}"
        if apuracao["extra_min"]:
            linha += f" (extra {formatar_minutos(apuracao['extra_min'])})"
        if apuracao["debito_min"]:
            linha += f" (débito {formatar_minutos(apuracao['debito_min'])})"
    print(linha)
    if apuracao["turnos"]:
        print("  Marcações:", formatar_marcacoes(apuracao))
    for ocorrencia in apuracao["ocorrencias"]:
        print("  Ocorrência:", ocorrencia)


def mostrar_ponto(funcionario, regras, agora=None):
    """Consulta apenas o funcionário recebido (usada no menu admin e no do funcionário)."""
    inicio, fim = ler_periodo()
    try:
        resumo = apurar_periodo(funcionario, inicio, fim, regras, agora)
    except ValueError as erro:
        print(erro)
        return
    print("\nPONTO — apuração das marcações realizadas; não é folha nem banco de horas.")
    mostrados = [d for d in resumo["dias"] if d["turnos"] or d["ocorrencias"]]
    for apuracao in mostrados:
        mostrar_apuracao_dia(apuracao)
    if not mostrados:
        print("Nenhuma marcação ou ocorrência neste período.")
    print("\nTotal realizado:", formatar_minutos(resumo["trabalhado_min"]))
    print(f"Dias apurados: {resumo['dias_apurados']} | previsto neles: {formatar_minutos(resumo['previsto_min'])}")
    print(f"Extras do período: {formatar_minutos(resumo['extra_min'])} | débitos: {formatar_minutos(resumo['debito_min'])}"
          f" (tolerância de {TOLERANCIA_MIN} min por dia)")
    print(f"Ocorrências: {resumo['ocorrencias']}")
    print("Diferenças e ocorrências auxiliam a conferência; não são saldo de banco de horas nem certificam conformidade trabalhista.")


# ---------- Menus ----------


def mostrar_ultimas(funcionario, quantidade=4):
    ultimas = marcacoes_ordenadas(funcionario)[-quantidade:]
    if not ultimas:
        print("Nenhuma marcação registrada ainda.")
        return
    print("Últimas marcações:")
    for m in ultimas:
        print(f"  {m['data']} {m['hora']} - {ROTULOS[m['tipo']]}")


def escolher_tipo(opcoes):
    if len(opcoes) == 1:
        return opcoes[0]
    for numero, tipo in enumerate(opcoes, start=1):
        print(f"{numero} - {ROTULOS[tipo]}")
    while True:
        escolha = input("Tipo de marcação: ").strip()
        if escolha.isascii() and escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        print("Opção inválida.")


def bater_ponto(funcionario, agora=None):
    """Registra a marcação do próprio funcionário usando a hora do sistema."""
    agora = (agora or datetime.now()).replace(second=0, microsecond=0)
    print(f"Agora: {agora:%d/%m/%Y %H:%M}")
    mostrar_ultimas(funcionario)
    tipo = escolher_tipo(tipos_permitidos(funcionario, agora))
    if not confirmar(f"Registrar {ROTULOS[tipo]} às {agora:%H:%M}?"):
        print("Marcação cancelada.")
        return False
    try:
        marcacao = criar_marcacao(tipo, agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M"))
        registrar_marcacao(funcionario, marcacao, agora)
    except ValueError as erro:
        print(erro)
        return False
    print(f"Marcação registrada: {ROTULOS[tipo]} às {marcacao['hora']}.")
    return True


def registrar_marcacao_manual(funcionarios, agora=None):
    """Lançamento do administrador para esquecimentos/correções, com motivo obrigatório."""
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return False
    if funcionario["status"] != "ativo":
        print("Reative o funcionário antes de registrar ponto.")
        return False
    mostrar_ultimas(funcionario)
    data = ler_validado("Data da marcação (DD/MM/AAAA): ", validar_data)
    hora = ler_validado("Hora da marcação (HH:MM): ", validar_horario)
    tipo = escolher_tipo(TIPOS)
    motivo = ler_validado("Motivo da marcação manual: ", validar_nome)
    try:
        marcacao = criar_marcacao(tipo, data, hora, "manual", motivo)
        validar_marcacao(funcionario, marcacao, agora)
    except ValueError as erro:
        print(erro)
        return False
    if not confirmar(f"Registrar {ROTULOS[tipo]} em {data} às {hora} para {funcionario['nome']}?"):
        print("Marcação cancelada.")
        return False
    registrar_marcacao(funcionario, marcacao, agora)
    print("Marcação manual registrada.")
    return True


def consultar_ponto(funcionarios, regras):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is not None:
        mostrar_ponto(funcionario, regras)
