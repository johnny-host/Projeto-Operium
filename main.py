from admin import cadastrar_admin, login_admin
from funcionarios import (
    buscar_funcionario,
    cadastro_funcionario,
    editar_funcionario,
    listar_funcionarios,
    mostrar_funcionario,
)

admins = []
funcionarios = []


def ler_opcao(texto):
    try:
        return int(input(texto))
    except ValueError:
        return None


def menu_sistema(admin_logado):

    while True:
        print(f"\n==== OPERIUM MENU ==== (admin: {admin_logado['usuario']})")
        print("1 - Cadastrar Funcionário")
        print("2 - Listar Funcionários")
        print("3 - Buscar Funcionário")
        print("4 - Editar Funcionário")
        print("5 - Cadastrar Novo Administrador")
        print("6 - Sair (logout)")
        menu_opcao = ler_opcao("Escolha uma opção: ")

        if menu_opcao == 1:
            funcionario = cadastro_funcionario()
            funcionarios.append(funcionario)

        elif menu_opcao == 2:
            listar_funcionarios(funcionarios)

        elif menu_opcao == 3:
            nome_busca = input("Qual funcionário deseja buscar? ")
            funcionario_encontrado = buscar_funcionario(funcionarios, nome_busca)

            if funcionario_encontrado:
                mostrar_funcionario(funcionario_encontrado)
            else:
                print("Funcionário não encontrado!")

        elif menu_opcao == 4:
            editar_funcionario(funcionarios)

        elif menu_opcao == 5:
            #  apenas admins logados cadastrem novos admins
            print("\n-- Novo administrador --")
            novo_admin = cadastrar_admin(admins)
            admins.append(novo_admin)
            print(f"Administrador '{novo_admin['usuario']}' cadastrado com sucesso!")

        elif menu_opcao == 6:
            print("Sessão encerrada.")
            break

        else:
            print("Opção inválida!")


def menu_autenticacao():
    """
    Menu de autenticação do sistema Operium.
    """
    while True:
        print("\n==== OPERIUM - ACESSO ====")

        if not admins:
            print("Nenhum administrador cadastrado.")
            print("1 - Cadastrar Primeiro Administrador")
            print("2 - Sair")
            opcao = ler_opcao("Escolha uma opção: ")

            if opcao == 1:
                primeiro_admin = cadastrar_admin(admins)
                admins.append(primeiro_admin)
                print("Primeiro administrador cadastrado! Faça login para continuar.")
            elif opcao == 2:
                print("Encerrando o Operium. Até logo!")
                break
            else:
                print("Opção inválida!")

        else:
            print("1 - Login")
            print("2 - Sair")
            opcao = ler_opcao("Escolha uma opção: ")

            if opcao == 1:
                admin_logado = login_admin(admins)
                if admin_logado:
                    menu_sistema(admin_logado)  # ao sair, volta para este menu
            elif opcao == 2:
                print("Encerrando o Operium. Até logo!")
                break
            else:
                print("Opção inválida!")


menu_autenticacao()
