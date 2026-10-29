"""Parâmetros informados pelo gestor, separados por vigência."""
from math import isfinite
from jornada import converter_data, ler_periodo, periodos_sobrepostos
from validacoes import confirmar, ler_validado, validar_nome

# Não são valores legais predefinidos: cada versão recebe os seus parâmetros.
PARAMETROS = {
    "limite_diario": "Limite de horas trabalhadas por dia",
    "limite_semanal": "Limite de horas trabalhadas por semana",
    "intervalo_minimo": "Intervalo mínimo em minutos",
    "intervalo_acima": "Exigir intervalo quando horas trabalhadas excederem",
    "descanso_minimo": "Descanso mínimo entre turnos em horas",
    "dsr_minimo": "Descanso contínuo mínimo para DSR em horas",
    "percentual_extra": "Adicional de hora extra em % (50 significa 50%)",
    "limite_extra": "Limite diário de horas extras",
    "adicional_noturno": "Adicional noturno em %",
    "divisor": "Divisor mensal para cálculo do valor da hora",
}


def validar_parametro(valor):
    try:
        numero = float(valor.replace(",", "."))
    except ValueError:
        raise ValueError("Informe um número válido.")
    if not isfinite(numero) or numero < 0:
        raise ValueError("Informe um número finito, maior ou igual a zero.")
    return numero


def validar_regra(regras, regra):
    if converter_data(regra["fim"]) < converter_data(regra["inicio"]):
        raise ValueError("Vigência final anterior à inicial.")
    for campo in PARAMETROS:
        valor = validar_parametro(str(regra[campo]))
        if campo in ("limite_diario", "limite_semanal", "divisor") and valor == 0:
            raise ValueError(f"{PARAMETROS[campo]} deve ser maior que zero.")
    for outra in regras:
        mesmo_grupo = (outra["empresa"] == regra["empresa"] and outra["categoria"] == regra["categoria"])
        if mesmo_grupo and periodos_sobrepostos(regra["inicio"], regra["fim"], outra["inicio"], outra["fim"]):
            raise ValueError("Já existe uma regra para esta empresa/categoria nessa vigência.")


def cadastrar_regra(regras):
    print("\nInforme parâmetros da empresa/categoria. Consulte o acordo aplicável.")
    empresa = ler_validado("Empresa: ", validar_nome).casefold()
    categoria = ler_validado("Categoria: ", validar_nome).casefold()
    inicio, fim = ler_periodo()
    regra = {"empresa": empresa, "categoria": categoria, "inicio": inicio, "fim": fim}
    for campo, descricao in PARAMETROS.items():
        while True:
            valor = ler_validado(descricao + ": ", validar_parametro)
            if campo in ("limite_diario", "limite_semanal", "divisor") and valor == 0:
                print("Este parâmetro deve ser maior que zero.")
            else:
                regra[campo] = valor
                break
    regra["fonte"] = ler_validado("Referência do acordo/convenção ou observação: ", validar_nome)
    regra["versao"] = len(regras) + 1
    try:
        validar_regra(regras, regra)
    except ValueError as erro:
        print(erro)
        return
    mostrar_regra(regra)
    if confirmar("Salvar esta versão?"):
        regras.append(regra)
        print("Versão cadastrada. Versões anteriores foram preservadas.")


def regra_vigente(regras, empresa, categoria, dia):
    for regra in regras:
        if (regra["empresa"] == empresa.casefold() and regra["categoria"] == categoria.casefold()
                and converter_data(regra["inicio"]) <= dia <= converter_data(regra["fim"])):
            return regra
    return None


def mostrar_regra(regra):
    print(f"\nVersão {regra['versao']} | {regra['empresa']} / {regra['categoria']} | {regra['inicio']} a {regra['fim']}")
    for campo, descricao in PARAMETROS.items():
        print(f"{descricao}: {regra[campo]}")
    print("Referência:", regra["fonte"])


def listar_regras(regras):
    if not regras:
        print("Nenhuma regra cadastrada.")
    for regra in regras:
        mostrar_regra(regra)
