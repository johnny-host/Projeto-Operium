def cadastro_funcionario():
    nome = input("Nome: ")
    cargo = input("Cargo: ")

    salario = float(input("Salário: "))
    while salario <= 0:
        print('Valor Inválido! Tente novamente.')
        salario = float(input("Cadastre um valor válido!"))
        
    carga = int(input("Carga semanal: "))
    while carga <= 0 or carga > 44:
        print('Valor inválido ou não permitido. Tente novamante.')
        carga = int(input("Digite a carga semanal: "))

    regime = input("Regime: ").lower()
    while regime not in ("6x1", "5x2", "12x36", "horista"):
        print('Regime inválido! Tente novamente.')
        regime = input("Regime (horista, 6x1, 5x2 ou 12x36):").lower()

    funcionario = {
        "nome": nome,
        "cargo": cargo,
        "salario": salario,
        "carga": carga,
        "regime": regime 
    }

    return funcionario

def mostrar_funcionario(funcionario):

    print("Nome: ", funcionario ["nome"])
    print("Cargo: ", funcionario ["cargo"])
    print(f'Salário: R$ {funcionario["salario"]:.2f}')
    print("Carga: ", funcionario ["carga"])
    print("Regime: ", funcionario ["regime"])

def listar_funcionarios(funcionarios):
    for funcionario in funcionarios:
        mostrar_funcionario(funcionario)

def buscar_funcionario(funcionarios, nome_busca):
    for funcionario in funcionarios:
        if funcionario["nome"].lower() == nome_busca:
            return funcionario
        

def editar_funcionario(funcionarios):
    listar_funcionarios(funcionarios)
    nome_busca = input('Qual funcionário deseja editar? ').lower()
    funcionario_encontrado = buscar_funcionario(funcionarios, nome_busca)
    if funcionario_encontrado:
        mostrar_funcionario(funcionario_encontrado)
        print('== Qual dado deseja editar? ==')
        print('1 - Cargo')
        editar_dado = int(input('Escolha uma opção? '))

        if editar_dado == 1:
            print('Cargo atual:', funcionario_encontrado["cargo"])
            novo_cargo = input('Digite o novo cargo: ').lower()
            funcionario_encontrado["cargo"] = novo_cargo
            print('Cargo atualizado com sucesso!')
            print('Novo cargo:', funcionario_encontrado["cargo"])
            #próximas tarefas: - adicionar a edição dos itens restantes
            