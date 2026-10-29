from datetime import datetime
from getpass import getpass
from senhas import solicitar_senha, verificar_senha
from jornada import validar_jornada
from validacoes import (
    confirmar, ler_validado, validar_carga, validar_cpf, validar_data,
    validar_nascimento, validar_nome, validar_regime, validar_salario,
)


def buscar_funcionario(funcionarios, id_busca):
    for funcionario in funcionarios:
        if str(funcionario["id"]) == str(id_busca).strip():
            return funcionario
    return None


def cpf_ja_cadastrado(funcionarios, cpf, id_atual=None):
    for funcionario in funcionarios:
        if funcionario["cpf"] == cpf and funcionario["id"] != id_atual:
            return True
    return False


def ler_cpf(funcionarios, id_atual=None):
    while True:
        cpf = ler_validado("CPF: ", validar_cpf)
        if not cpf_ja_cadastrado(funcionarios, cpf, id_atual):
            return cpf
        print("Este CPF já está cadastrado.")


def datas_validas(nascimento, admissao):
    nascimento = datetime.strptime(nascimento, "%d/%m/%Y")
    admissao = datetime.strptime(admissao, "%d/%m/%Y")
    return admissao >= nascimento


def cadastro_funcionario(funcionarios):
    # Como não apagamos funcionários, o próximo ID fica após o maior ID.
    novo_id = 1
    for funcionario in funcionarios:
        if funcionario["id"] >= novo_id:
            novo_id = funcionario["id"] + 1

    nome = ler_validado("Nome: ", validar_nome)
    cpf = ler_cpf(funcionarios)
    nascimento = ler_validado("Nascimento (DD/MM/AAAA): ", validar_nascimento)
    while True:
        admissao = ler_validado("Admissão (DD/MM/AAAA): ", validar_data)
        if datas_validas(nascimento, admissao):
            break
        print("A admissão não pode ser anterior ao nascimento.")

    cargo = ler_validado("Cargo: ", validar_nome)
    salario = ler_validado("Salário: ", validar_salario)
    carga = ler_validado("Carga semanal: ", validar_carga)
    regime = ler_validado("Regime (clt, pj, estagio, aprendiz, temporario, outro): ", validar_regime)
    jornada = ler_validado("Jornada (5x2, 6x1, 12x36, horista): ", validar_jornada)
    print("Defina a senha inicial de acesso do funcionário.")
    senha = solicitar_senha()

    funcionario = {
        "id": novo_id,
        "nome": nome,
        "cpf": cpf,
        "data_nascimento": nascimento,
        "status": "ativo",
        "senha": senha,
        # Um dicionário interno agrupa os dados do contrato.
        "contrato": {
            "cargo": cargo,
            "salario": salario,
            "carga": carga,
            "regime": regime,
            "jornada": jornada,
            "data_admissao": admissao,
        },
    }
    print(f"Funcionário cadastrado! ID: {novo_id}")
    return funcionario


def obter_data_admissao(funcionario):
    """Data-base do vínculo, disponível para os futuros cálculos de direitos."""
    return datetime.strptime(funcionario["contrato"]["data_admissao"], "%d/%m/%Y").date()


def login_funcionario(funcionarios):
    for tentativa in range(3):
        identificador = input("ID do funcionário: ")
        senha = getpass("Senha: ")
        funcionario = buscar_funcionario(funcionarios, identificador)
        # Cadastros antigos não têm senha: o administrador deve defini-la.
        if (funcionario and funcionario["status"] == "ativo"
                and funcionario.get("senha")
                and verificar_senha(senha, funcionario["senha"])):
            print(f"Bem-vindo, {funcionario['nome']}!")
            return funcionario
        print("Acesso não autorizado. Confira ID e senha ou procure o administrador.")
    print("Número máximo de tentativas atingido.")
    return None


def definir_senha_funcionario(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return
    if confirmar(f"Definir uma nova senha para ID {funcionario['id']} — {funcionario['nome']}?"):
        funcionario["senha"] = solicitar_senha()
        print("Senha definida. O acesso exige que o funcionário esteja ativo.")


def trocar_senha_funcionario(funcionario):
    senha_atual = getpass("Senha atual: ")
    if not verificar_senha(senha_atual, funcionario["senha"]):
        print("Senha atual incorreta.")
        return False
    nova_senha = solicitar_senha()
    if not confirmar("Confirmar troca de senha?"):
        print("Troca cancelada.")
        return False
    funcionario["senha"] = nova_senha
    print("Senha alterada.")
    return True


def mostrar_funcionario(funcionario):
    print("\nID:", funcionario["id"])
    print("Nome:", funcionario["nome"])
    print("CPF:", funcionario["cpf"])
    print("Nascimento:", funcionario["data_nascimento"])
    print("Status:", funcionario["status"])
    contrato = funcionario["contrato"]
    print("Cargo:", contrato["cargo"])
    print(f"Salário: R$ {contrato['salario']:.2f}")
    print("Carga semanal:", contrato["carga"])
    print("Regime:", contrato["regime"])
    print("Jornada:", contrato["jornada"])
    print("Admissão:", contrato["data_admissao"])


def listar_funcionarios(funcionarios):
    if not funcionarios:
        print("Nenhum funcionário cadastrado.")
    for funcionario in funcionarios:
        print(f"ID: {funcionario['id']} | {funcionario['nome']} | {funcionario['status']}")


def selecionar_funcionario(funcionarios):
    listar_funcionarios(funcionarios)
    if not funcionarios:
        return None
    id_busca = input("ID do funcionário: ")
    funcionario = buscar_funcionario(funcionarios, id_busca)
    if funcionario is None:
        print("Funcionário não encontrado!")
    return funcionario


def editar_funcionario(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return

    # Cada opção informa: a chave do dicionário e a função de validação.
    campos = {
        "1": ("nome", validar_nome),
        "2": ("cargo", validar_nome),
        "3": ("salario", validar_salario),
        "4": ("carga", validar_carga),
        "5": ("regime", validar_regime),
        "6": ("jornada", validar_jornada),
        "7": ("data_admissao", validar_data),
        "8": ("data_nascimento", validar_nascimento),
        "9": ("cpf", validar_cpf),
    }
    print("\n1 - Nome\n2 - Cargo\n3 - Salário\n4 - Carga semanal")
    print("5 - Regime\n6 - Jornada\n7 - Admissão\n8 - Nascimento\n9 - CPF\n0 - Cancelar")
    opcao = input("Qual dado deseja editar? ").strip()
    if opcao == "0":
        return
    if opcao not in campos:
        print("Opção inválida!")
        return

    campo, validador = campos[opcao]
    if campo in ("nome", "cpf", "data_nascimento"):
        dados = funcionario
    else:
        dados = funcionario["contrato"]

    print("Valor atual:", dados[campo])
    while True:
        if campo == "cpf":
            novo_valor = ler_cpf(funcionarios, funcionario["id"])
        else:
            novo_valor = ler_validado("Novo valor: ", validador)

        nascimento = funcionario["data_nascimento"]
        admissao = funcionario["contrato"]["data_admissao"]
        if campo == "data_nascimento":
            nascimento = novo_valor
        elif campo == "data_admissao":
            admissao = novo_valor
            if any(datetime.strptime(escala["inicio"], "%d/%m/%Y") < datetime.strptime(admissao, "%d/%m/%Y")
                   for escala in funcionario.get("escalas", [])):
                print("A admissão não pode ficar depois de uma escala já cadastrada.")
                continue
        if datas_validas(nascimento, admissao):
            break
        print("A admissão não pode ser anterior ao nascimento.")

    print("Novo valor:", novo_valor)
    if confirmar("Confirmar alteração?"):
        dados[campo] = novo_valor
        print("Alteração realizada com sucesso!")
        if campo in ("jornada", "carga") and funcionario.get("escalas"):
            print("As escalas existentes mantêm sua configuração. Cadastre um novo período para aplicar a mudança.")
    else:
        print("Alteração cancelada.")


def alterar_status(funcionarios):
    funcionario = selecionar_funcionario(funcionarios)
    if funcionario is None:
        return
    if funcionario["status"] == "ativo":
        novo_status = "inativo"
    else:
        novo_status = "ativo"
    if confirmar(f"Alterar o status de {funcionario['nome']} para {novo_status}?"):
        funcionario["status"] = novo_status
        print("Status atualizado. O cadastro foi preservado.")
    else:
        print("Operação cancelada.")
