from funcionarios import titulo
from funcionarios import ler_texto
from funcionarios import ler_float
from funcionarios import ler_carga
from funcionarios import limpar_tela
from funcionarios import pausar
from funcionarios import dar_tempo
from menu_adm import cadastrar_admin, login_admin
from menu_adm import listar_admins, pesquisar_admins, editar_admin, excluir_admin

admins = []


def ler_opcao(texto):
    try:
        return int(input(texto))
    except ValueError:
        return None


def desenhar_menu_adm(admin_logado):
    print('╔' + '═' * 44 + '╗')
    print('║' + '★  OPERIUM  ★'.center(44) + '║')
    print('║' + f'(admin: {admin_logado["usuario"]})'.center(44) + '║')
    print('║' + 'LOGUIN ADMINISTRADOR'.center(44) + '║')
    print('╠' + '═' * 44 + '╣')
    print('║' + ' ' * 44 + '║')
    print('║' + '   [1]  Cadastrar Administrador'.ljust(44) + '║')
    print('║' + '   [2]  Listar Administrador'.ljust(44) + '║')
    print('║' + '   [3]  Buscar Administrador'.ljust(44) + '║')
    print('║' + '   [4]  Editar Administrador'.ljust(44) + '║')
    print('║' + '   [5]  Excluir Administrador'.ljust(44) + '║')
    print('║' + '   [6]  Sair (logout)'.ljust(44) + '║')
    print('║' + ' ' * 44 + '║')
    print('╚' + '═' * 44 + '╝')


def mostrar_menu_adm(admin_logado):
    """Menu do administrador logado. Quando escolhe [6], a função termina
    e volta para quem a chamou (a tela de login do administrador)."""
    while True:
        limpar_tela()
        desenhar_menu_adm(admin_logado)
        opcao = ler_opcao("Escolha uma opção: ")

        if opcao == 1:
            limpar_tela()
            titulo(" NOVO ADMINISTRADOR ")
            novo_admin = cadastrar_admin(admins)
            admins.append(novo_admin)
            print(f"\n✔ Administrador '{novo_admin['usuario']}' cadastrado com sucesso!")
            pausar()

        elif opcao == 2:
            limpar_tela()
            listar_admins(admins)
            pausar()

        elif opcao == 3:
            limpar_tela()
            titulo("BUSCAR ADMINISTRADOR")
            texto = input("Qual administrador deseja buscar? ")
            encontrados = pesquisar_admins(admins, texto)

            if encontrados:
                print(f"\n{len(encontrados)} administrador(es) encontrado(s):")
                for admin in encontrados:
                    print(f"  - {admin['usuario']}")
            else:
                print("\nEsse administrador não está cadastrado no sistema!")
            pausar()

        elif opcao == 4:
            limpar_tela()
            editar_admin(admins)
            pausar()

        elif opcao == 5:
            limpar_tela()
            excluir_admin(admins, admin_logado)
            pausar()

        elif opcao == 6:
            print("Sessão encerrada.")
            dar_tempo()
            break

        else:
            print("Opção inválida!")
            pausar()


def cadastro_adm():
    titulo('CADASTRO DE ADMINISTRADOR')

    nome_adm = ler_texto('Nome: ')
    area_adm = ler_texto('Área: ')
    salario_adm = ler_float('Salário: R$ ')
    carga_adm = ler_carga('Carga semanal (até 44h): ')

    admins = {
        "nome": nome_adm,
        "Área": area_adm,
        "salario": salario_adm,
        "carga": carga_adm,
    }
    
    limpar_tela()
    print(f'\n✔ Administrador "{nome_adm}" cadastrado com sucesso!')
    return admins


def menu_autenticacao():
    """
    Menu de autenticação do sistema Operium ( ADM ).
    Quando o usuário escolhe Sair, a função termina e volta ao menu principal.
    """
    while True:
        limpar_tela()
        print('╔' + '═' * 44 + '╗')
        print('║' + '★  OPERIUM  ★'.center(44) + '║')
        print('║' + ' ' * 44 + '║')
        print('║' + 'LOGUIN ADMINISTRADOR'.center(44) + '║')
        print('║' + ' ' * 44 + '║')
        print('╚' + '═' * 44 + '╝')

        if not admins:
            print("")
            print("Nenhum administrador cadastrado.")
            print("")
            print("1 - Cadastrar Primeiro Administrador")
            print("2 - Sair")
            print("")
            opcao = ler_opcao("Escolha uma opção: ")

            if opcao == 1:
                primeiro_admin = cadastrar_admin(admins)
                admins.append(primeiro_admin)
                limpar_tela()
                print("Primeiro administrador cadastrado! Faça login para continuar.")
                pausar()

            elif opcao == 2:
                limpar_tela()
                print("Voltando ao menu principal...")
                break

            else:
                print("Opção inválida!")
                pausar()

        else:
            print("1 - Login")
            print("2 - Sair")
            opcao = ler_opcao("Escolha uma opção: ")

            if opcao == 1:
                admin_logado = login_admin(admins)
                if admin_logado:
                    pausar()
                    mostrar_menu_adm(admin_logado)
                else:
                    pausar()
            elif opcao == 2:
                print("Voltando ao menu principal...")
                break
            else:
                print("Opção inválida!")
                pausar()