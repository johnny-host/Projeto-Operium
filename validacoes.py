"""Funções usadas para validar os dados no cadastro e na edição."""
from datetime import datetime, date
from math import isfinite

# Limite físico de uma semana. Limites contratuais ficam nas regras por vigência.
CARGA_MAXIMA = 7 * 24


def validar_nome(valor):
    valor = valor.strip()
    if valor == "":
        raise ValueError("O campo não pode ficar vazio.")
    return valor


def validar_salario(valor):
    try:
        salario = float(valor.replace(",", "."))
    except ValueError:
        raise ValueError("Digite um salário numérico. Exemplo: 1500,50.")
    if not isfinite(salario) or salario <= 0:
        raise ValueError("O salário deve ser maior que zero e finito.")
    return round(salario, 2)


def validar_carga(valor):
    try:
        carga = float(valor.replace(",", "."))
    except ValueError:
        raise ValueError("Digite uma carga numérica. Exemplo: 40.")
    if not isfinite(carga) or carga <= 0 or carga > CARGA_MAXIMA:
        raise ValueError(f"A carga deve ser maior que zero e até {CARGA_MAXIMA} horas.")
    return carga


def validar_regime(valor):
    regime = valor.strip().lower()
    if regime not in ("clt", "pj", "estagio", "aprendiz", "temporario", "outro"):
        raise ValueError("Use: clt, pj, estagio, aprendiz, temporario ou outro.")
    return regime


def validar_data(valor):
    try:
        data = datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("Digite uma data válida no formato DD/MM/AAAA.")
    return data.strftime("%d/%m/%Y")


def validar_nascimento(valor):
    valor = validar_data(valor)
    data = datetime.strptime(valor, "%d/%m/%Y").date()
    if data >= date.today():
        raise ValueError("O nascimento deve ser anterior a hoje.")
    return valor


def validar_cpf(valor):
    cpf = valor.strip().replace(".", "").replace("-", "")
    if len(cpf) != 11 or not cpf.isascii() or not cpf.isdigit():
        raise ValueError("O CPF deve conter 11 números.")
    if cpf == cpf[0] * 11:
        raise ValueError("CPF inválido.")

    # Calcula os dois dígitos verificadores do CPF.
    for tamanho in (9, 10):
        soma = 0
        for indice in range(tamanho):
            soma += int(cpf[indice]) * (tamanho + 1 - indice)
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[tamanho]):
            raise ValueError("CPF inválido. Confira os números.")
    return cpf


def ler_validado(mensagem, funcao_validacao):
    # Recebe uma função para reaproveitar este laço em diferentes campos.
    while True:
        valor = input(mensagem)
        try:
            return funcao_validacao(valor)
        except ValueError as erro:
            print(erro)


def confirmar(mensagem):
    while True:
        resposta = input(mensagem + " (s/n): ").strip().lower()
        if resposta == "s":
            return True
        if resposta == "n":
            return False
        print("Digite s ou n.")
