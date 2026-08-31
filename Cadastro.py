funcionarios = []

continuar = "sim"

print("=== CADASTRO FUNCIONÁRIO ===")

while continuar == "sim":
    nome = input("Nome: ").lower()
    cargo = input("Cargo: ").lower()

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

    funcionarios.append(funcionario)

    print("=== FÚNCINÁRIO CADASTRADO ===")
    print(funcionario ["nome"])
    print(funcionario ["cargo"])
    print(f'R$ {funcionario["salario"]:.2f}')
    print(funcionario ["carga"])
    print(funcionario ["regime"])

    continuar = input("Deseja cadastrar um novo funcionário? (sim/não)").lower()

for funcionario in funcionarios:
    print("\n=== FUNCIONÁRIOS ===")
    print(funcionario["nome"])
    print(funcionario ["cargo"])
    print(f'R$ {funcionario["salario"]:.2f}')
    print(funcionario ["carga"])
    print(funcionario ["regime"])