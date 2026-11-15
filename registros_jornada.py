"""Lançamento manual de jornadas realizadas pelo administrador."""
from datetime import datetime, timedelta
from funcionarios import selecionar_funcionario, obter_data_admissao
from jornada import (converter_data, validar_horario, minutos_horario, duracao_turno,
                     criar_turno, minutos_trabalhados, formatar_minutos, ler_periodo)
from validacoes import confirmar, ler_validado, validar_data


def criar_registro(data, entrada, saida, saida_intervalo="", volta_intervalo="", observacao=""):
    data = validar_data(data)
    duracao = duracao_turno(entrada, saida)
    intervalo = 0
    if bool(saida_intervalo) != bool(volta_intervalo):
        raise ValueError("Informe os dois horários do intervalo, ou deixe ambos vazios.")
    if saida_intervalo:
        # Distâncias desde a entrada permitem tratar a virada da meia-noite.
        inicio_pausa = (minutos_horario(saida_intervalo) - minutos_horario(entrada)) % 1440
        fim_pausa = (minutos_horario(volta_intervalo) - minutos_horario(entrada)) % 1440
        if not 0 < inicio_pausa < fim_pausa < duracao:
            raise ValueError("O intervalo deve ocorrer dentro do turno, com retorno após a saída para pausa.")
        intervalo = fim_pausa - inicio_pausa
    turno = criar_turno(entrada, saida, intervalo)
    turno.update({"data": data, "saida_intervalo": saida_intervalo,
                  "volta_intervalo": volta_intervalo, "observacao": observacao.strip()})
    return turno


def limites_registro(registro):
    inicio = datetime.combine(converter_data(registro["data"]), datetime.min.time())
    inicio += timedelta(minutes=minutos_horario(registro["entrada"]))
    return inicio, inicio + timedelta(minutes=duracao_turno(registro["entrada"], registro["saida"]))


def validar_registro(funcionario, registro):
    if funcionario["status"] != "ativo":
        raise ValueError("Reative o funcionário antes de lançar uma jornada.")
    if converter_data(registro["data"]) < obter_data_admissao(funcionario):
        raise ValueError("A jornada não pode ser anterior à admissão.")
    inicio, fim = limites_registro(registro)
    if fim > datetime.now():
        raise ValueError("Só é possível lançar jornadas já encerradas.")
    for anterior in funcionario.get("jornadas", []):
        # A mesma data será corrigida mediante confirmação, não duplicada.
        if anterior["data"] == registro["data"]:
            continue
        outro_inicio, outro_fim = limites_registro(anterior)
        if inicio < outro_fim and outro_inicio < fim:
            raise ValueError("Este turno se sobrepõe a outra jornada registrada.")


def registrar_jornada(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return False
    if funcionario["status"] != "ativo":
        print("Reative o funcionário antes de lançar uma jornada.")
        return False
    data = ler_validado("Data de entrada (DD/MM/AAAA): ", validar_data)
    anterior = next((r for r in funcionario.get("jornadas", []) if r["data"] == data), None)
    if anterior:
        print("Já existe uma jornada nesta data:")
        mostrar_registro(anterior)
        if not confirmar("Deseja corrigir este lançamento?"):
            return False
    print("Turnos devem durar menos de 24h. Saída menor que entrada significa dia seguinte.")
    while True:
        entrada = ler_validado("Horário de entrada: ", validar_horario)
        saida = ler_validado("Horário de saída: ", validar_horario)
        saida_intervalo = volta_intervalo = ""
        if confirmar("Houve intervalo?"):
            saida_intervalo = ler_validado("Saída para intervalo: ", validar_horario)
            volta_intervalo = ler_validado("Volta do intervalo: ", validar_horario)
        try:
            registro = criar_registro(data, entrada, saida, saida_intervalo, volta_intervalo)
            validar_registro(funcionario, registro)
            break
        except ValueError as erro:
            print(erro)
            if not confirmar("Tentar novamente os horários desta data?"):
                return False
    registro["observacao"] = input("Observação (opcional): ").strip()
    mostrar_registro(registro)
    if not confirmar("Confirmar lançamento?"):
        return False
    registros = funcionario.setdefault("jornadas", [])
    if anterior:
        registros[registros.index(anterior)] = registro
    else:
        registros.append(registro)
    print("Jornada registrada.")
    return True


def mostrar_registro(registro):
    print(f"{registro['data']} | {registro['entrada']}-{registro['saida']} | "
          f"intervalo: {registro['intervalo']} min | realizado: {formatar_minutos(minutos_trabalhados(registro))}")
    if registro.get("observacao"):
        print("Observação:", registro["observacao"])


def mostrar_jornadas(funcionario):
    inicio, fim = ler_periodo()
    registros = [r for r in funcionario.get("jornadas", [])
                 if converter_data(inicio) <= converter_data(r["data"]) <= converter_data(fim)]
    if not registros:
        print("Nenhuma jornada realizada registrada neste período.")
        return
    total = 0
    for registro in sorted(registros, key=lambda r: converter_data(r["data"])):
        mostrar_registro(registro)
        total += minutos_trabalhados(registro)
    print("Total realizado:", formatar_minutos(total))
    print("Datas sem lançamento não são consideradas faltas. Este total não é saldo de banco de horas.")


def consultar_jornadas(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is not None:
        mostrar_jornadas(funcionario)
