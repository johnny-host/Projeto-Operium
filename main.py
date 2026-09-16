from funcionarios import cadastro_funcionario
from funcionarios import mostrar_funcionario
from funcionarios import listar_funcionarios
from funcionarios import buscar_funcionario

funcionarios = []

while True:
    print('==== OPERIUM MENU ====')
    print('1 - Cadastrar Fúncionário')
    print('2 - Listar Funcionários')
    print('3 - Buscar Funcionários')
    print('4 - Sair')


continuar = "sim"

print("=== CADASTRO FUNCIONÁRIO ===")

while continuar == "sim":

    funcionario = cadastro_funcionario()

    funcionarios.append(funcionario)

    print("=== FUNCIONÁRIO CADASTRADO ===")
    mostrar_funcionario(funcionario)
    
    continuar = input("Deseja cadastrar um novo funcionário? (sim/não)").lower()

print("=== FUNCIONÁRIOS CADASTRADOS ===")
listar_funcionarios(funcionarios)

nome_busca = input("Qual fumcionário deseja buscar? ").lower()

funcionario_encontrado = buscar_funcionario(funcionarios, nome_busca)
if funcionario_encontrado:
    print("Funcionário encontrado!" , funcionario_encontrado)
else:
    print("Funcionário não encontrado!")
