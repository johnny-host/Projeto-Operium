REGIMES_VALIDOS = ("6x1", "5x2", "12x36", "horista")


def cadastro_funcionario():
    nome = input("Nome: ")
    cargo = input("Cargo: ")

    salario = float(input("Salário: "))
    while salario <= 0:
        print("Valor Inválido! Tente novamente.")
        salario = float(input("Cadastre um valor válido: "))

    carga = int(input("Carga semanal: "))
    while carga <= 0 or carga > 44:
        print("Valor inválido ou não permitido. Tente novamente.")
        carga = int(input("Digite a carga semanal: "))

    regime = input("Regime: ").lower()
    while regime not in REGIMES_VALIDOS:
        print("Regime inválido! Tente novamente.")
        regime = input("Regime (horista, 6x1, 5x2 ou 12x36): ").lower()

    funcionario = {
        "nome": nome,
        "cargo": cargo,
        "salario": salario,
        "carga": carga,
        "regime": regime,
    }

    return funcionario


def mostrar_funcionario(funcionario):

    print("Nome: ", funcionario["nome"])
    print("Cargo: ", funcionario["cargo"])
    print(f"Salário: R$ {funcionario['salario']:.2f}")
    print("Carga: ", funcionario["carga"])
    print("Regime: ", funcionario["regime"])


def listar_funcionarios(funcionarios):
    if not funcionarios:
        print("Nenhum funcionário cadastrado.")
        return
    for funcionario in funcionarios:
        mostrar_funcionario(funcionario)
        print("-" * 20)


def buscar_funcionario(funcionarios, nome_busca):

    nome_busca = nome_busca.strip().lower()
    for funcionario in funcionarios:
        if funcionario["nome"].strip().lower() == nome_busca:
            return funcionario
    return None


def editar_funcionario(funcionarios):
    if not funcionarios:
        print("Nenhum funcionário cadastrado.")
        return

    listar_funcionarios(funcionarios)
    nome_busca = input("Qual funcionário deseja editar? ")
    funcionario_encontrado = buscar_funcionario(funcionarios, nome_busca)

    if not funcionario_encontrado:
        print("Funcionário não encontrado!")
        return

    mostrar_funcionario(funcionario_encontrado)
    print("== Qual dado deseja editar? ==")
    print("1 - Nome")
    print("2 - Cargo")
    print("3 - Salário")
    print("4 - Carga")
    print("5 - Regime")

    try:
        editar_dado = int(input("Escolha uma opção? "))
    except ValueError:
        print("Opção inválida!")
        return

    if editar_dado == 1:
        print("Nome atual: ", funcionario_encontrado["nome"])
        novo_nome = input("Digite o novo nome: ").strip()
        funcionario_encontrado["nome"] = novo_nome
        print("Nome atualizado com sucesso!")
        print("Novo nome: ", funcionario_encontrado["nome"])

    elif editar_dado == 2:
        print("Cargo atual:", funcionario_encontrado["cargo"])
        novo_cargo = input("Digite o novo cargo: ").strip()
        funcionario_encontrado["cargo"] = novo_cargo
        print("Cargo atualizado com sucesso!")
        print("Novo cargo: ", funcionario_encontrado["cargo"])

    elif editar_dado == 3:
        print("Salário atual: ", funcionario_encontrado["salario"])
        novo_salario = float(input("Digite o novo salário: "))
        while novo_salario <= 0:
            print("Valor Inválido! Tente novamente.")
            novo_salario = float(input("Cadastre um valor válido: "))
        funcionario_encontrado["salario"] = novo_salario
        print("Salário atualizado com sucesso!")
        print(f"Novo salário: R$ {funcionario_encontrado['salario']:.2f}")

    elif editar_dado == 4:
        print("Carga horária atual: ", funcionario_encontrado["carga"])
        nova_carga = int(input("Digite nova carga horária: "))
        while nova_carga <= 0 or nova_carga > 44:
            print("Valor inválido ou não permitido. Tente novamente.")
            nova_carga = int(input("Digite a carga semanal: "))
        funcionario_encontrado["carga"] = nova_carga
        print("Carga horária atualizada com sucesso!")
        print("Nova carga horária: ", funcionario_encontrado["carga"])

    elif editar_dado == 5:
        print("Regime atual: ", funcionario_encontrado["regime"])
        novo_regime = input("Digite o novo regime: ").lower()
        while novo_regime not in REGIMES_VALIDOS:
            print("Regime inválido! Tente novamente.")
            novo_regime = input("Regime (horista, 6x1, 5x2 ou 12x36): ").lower()
        funcionario_encontrado["regime"] = novo_regime
        print("Regime atualizado com sucesso!")
        print("Novo regime: ", funcionario_encontrado["regime"])

    else:
        print("Opção inválida!")
