from funcionarios import cadastro_funcionario
from funcionarios import mostrar_funcionario
from funcionarios import listar_funcionarios
from funcionarios import buscar_funcionario
from funcionarios import editar_funcionario

funcionarios = []

while True:
    print('==== OPERIUM MENU ====')
    print('1 - Cadastrar Fúncionário')
    print('2 - Listar Funcionários')
    print('3 - Buscar Funcionário')
    print('4 - Editar Fúncionário')
    print('5 - Sair')
    menu_opcao = int(input('Escolha uma opção: '))

    if menu_opcao == 1:
        funcionario = cadastro_funcionario()
        funcionarios.append(funcionario)

    elif menu_opcao == 2:
        listar_funcionarios(funcionarios)

    elif menu_opcao == 3:
        nome_busca = input('Qual funcionário deseja buscar? ').lower()
        funcionario_encontrado = buscar_funcionario(funcionarios, nome_busca)

        if funcionario_encontrado:
            mostrar_funcionario(funcionario_encontrado)
        else:
            print("Funcionário não encontrado!")
            
    elif menu_opcao == 4:
        editar_funcionario(funcionarios)


    elif menu_opcao == 5:
        break

    else:
        print('Opção inválida!')