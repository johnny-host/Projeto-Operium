from datetime import datetime
from validacoes import ler_validado, validar_data

TIPOS_JORNADA = ("5x2", "6x1", "12x36", "horista")
DIAS_SEMANA = ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")


def validar_jornada(valor):
    valor = valor.strip().lower()
    if valor not in TIPOS_JORNADA:
        raise ValueError("Use: " + ", ".join(TIPOS_JORNADA))
    return valor


def converter_data(valor):
    return datetime.strptime(valor, "%d/%m/%Y").date()


def ler_periodo():
    inicio = ler_validado("Início (DD/MM/AAAA): ", validar_data)
    while True:
        fim = ler_validado("Fim (DD/MM/AAAA): ", validar_data)
        if 0 <= (converter_data(fim) - converter_data(inicio)).days <= 365:
            return inicio, fim
        print("Informe um período de 1 a 366 dias, com fim igual ou posterior ao início.")


def periodos_sobrepostos(inicio, fim, outro_inicio, outro_fim):
    return converter_data(inicio) <= converter_data(outro_fim) and converter_data(outro_inicio) <= converter_data(fim)


def validar_horario(valor):
    try:
        return datetime.strptime(valor.strip(), "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ValueError("Informe um horário válido, como 08:00.")


def minutos_horario(horario):
    horas, minutos = validar_horario(horario).split(":")
    return int(horas) * 60 + int(minutos)


def validar_minutos(valor):
    try:
        minutos = int(valor)
    except ValueError:
        raise ValueError("Informe minutos inteiros.")
    if minutos < 0:
        raise ValueError("Os minutos não podem ser negativos.")
    return minutos


def duracao_turno(entrada, saida):
    duracao = (minutos_horario(saida) - minutos_horario(entrada)) % 1440
    if duracao == 0:
        raise ValueError("Entrada e saída iguais não são permitidas.")
    return duracao


def criar_turno(entrada, saida, intervalo):
    entrada = validar_horario(entrada)
    saida = validar_horario(saida)
    intervalo = validar_minutos(str(intervalo))
    if intervalo >= duracao_turno(entrada, saida):
        raise ValueError("O intervalo deve ser menor que o turno.")
    return {"status": "trabalho", "entrada": entrada, "saida": saida, "intervalo": intervalo}


def ler_turno(tipo):
    while True:
        entrada = ler_validado("Entrada (HH:MM): ", validar_horario)
        saida = ler_validado("Saída (HH:MM; menor = dia seguinte): ", validar_horario)
        intervalo = ler_validado("Intervalo não trabalhado em minutos: ", validar_minutos)
        try:
            turno = criar_turno(entrada, saida, intervalo)
            if tipo == "12x36" and duracao_turno(entrada, saida) != 720:
                raise ValueError("O período entre entrada e saída do modelo 12x36 deve ser de 12 horas.")
            return turno
        except ValueError as erro:
            print(erro)


def minutos_trabalhados(turno):
    if turno["status"] != "trabalho":
        return 0
    return duracao_turno(turno["entrada"], turno["saida"]) - turno["intervalo"]


def formatar_minutos(minutos):
    sinal = "-" if minutos < 0 else ""
    minutos = abs(minutos)
    return f"{sinal}{minutos // 60:02d}h{minutos % 60:02d}"
