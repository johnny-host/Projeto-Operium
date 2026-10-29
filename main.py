from administrador import cadastrar_admin
from acesso import login_geral
import pickle
from armazenamento import carregar_dados, dados_vazios, salvar_dados
from escalas import ajustar_dia, cadastrar_escala, consultar_planejamento, mostrar_planejamento
from regras import cadastrar_regra, listar_regras
from funcionarios import (
    buscar_funcionario,
    cadastro_funcionario,
    editar_funcionario,
    listar_funcionarios,
    mostrar_funcionario,
    alterar_status,
    definir_senha_funcionario,
    trocar_senha_funcionario,
)

dados = dados_vazios()
admins = dados["admins"]
funcionarios = dados["funcionarios"]


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
        print("7 - Inativar / reativar funcionário")
        print("8 - Cadastrar escala por período")
        print("9 - Consultar jornada e escala planejada")
        print("10 - Cadastrar versão de regras")
        print("11 - Consultar regras")
        print("12 - Ajustar um dia / informar feriado")
        print("13 - Definir / redefinir senha do funcionário")
        menu_opcao = ler_opcao("Escolha uma opção: ")

        if menu_opcao == 1:
            funcionario = cadastro_funcionario(funcionarios)
            funcionarios.append(funcionario)

        elif menu_opcao == 2:
            listar_funcionarios(funcionarios)

        elif menu_opcao == 3:
            id_busca = input("ID do funcionário: ")
            funcionario_encontrado = buscar_funcionario(funcionarios, id_busca)

            if funcionario_encontrado:
                mostrar_funcionario(funcionario_encontrado)
            else:
                print("Funcionário não encontrado!")

        elif menu_opcao == 4:
            editar_funcionario(funcionarios)

        elif menu_opcao == 5:
            print("\n-- Novo administrador --")
            novo_admin = cadastrar_admin(admins)
            admins.append(novo_admin)
            print(f"Administrador '{novo_admin['usuario']}' cadastrado com sucesso!")

        elif menu_opcao == 6:
            print("Sessão encerrada.")
            break

        elif menu_opcao == 7:
            alterar_status(funcionarios)

        elif menu_opcao == 8:
            cadastrar_escala(funcionarios)

        elif menu_opcao == 9:
            consultar_planejamento(funcionarios, dados["regras"])

        elif menu_opcao == 10:
            cadastrar_regra(dados["regras"])

        elif menu_opcao == 11:
            listar_regras(dados["regras"])

        elif menu_opcao == 12:
            ajustar_dia(funcionarios)

        elif menu_opcao == 13:
            definir_senha_funcionario(funcionarios)

        else:
            print("Opção inválida!")

        if menu_opcao in (1, 4, 5, 7, 8, 10, 12, 13):
            salvar_dados(dados)
            print("Dados salvos no arquivo local.")


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
                salvar_dados(dados)
                print("Primeiro administrador cadastrado! Faça login para continuar.")
            elif opcao == 2:
                print("Encerrando o Operium. Até logo!")
                break
            else:
                print("Opção inválida!")

        else:
            print("1 - Entrar")
            print("2 - Sair")
            print("Se ainda não tiver senha, solicite ao administrador.")
            opcao = ler_opcao("Escolha uma opção: ")

            if opcao == 1:
                acesso = login_geral(admins, funcionarios)
                if acesso:
                    if acesso["perfil"] == "administrador":
                        menu_sistema(acesso["usuario"])
                    else:
                        menu_funcionario(acesso["usuario"])
            elif opcao == 2:
                print("Encerrando o Operium. Até logo!")
                break
            else:
                print("Opção inválida!")


def menu_funcionario(funcionario):
    while True:
        print(f"\n==== ÁREA DO FUNCIONÁRIO ==== ID: {funcionario['id']}")
        print("1 - Meus dados")
        print("2 - Minha escala")
        print("3 - Trocar minha senha")
        print("4 - Sair (logout)")
        opcao = ler_opcao("Escolha uma opção: ")
        if opcao == 1:
            mostrar_funcionario(funcionario)
        elif opcao == 2:
            mostrar_planejamento(funcionario, dados["regras"])
        elif opcao == 3:
            if trocar_senha_funcionario(funcionario):
                salvar_dados(dados)
                print("Nova senha salva.")
        elif opcao == 4:
            print("Sessão encerrada.")
            break
        else:
            print("Opção inválida!")


def iniciar():
    global dados, admins, funcionarios
    # Erro de leitura interrompe o início, sem sobrescrever o arquivo existente.
    try:
        dados = carregar_dados()
    except (OSError, ValueError, EOFError, pickle.UnpicklingError, ImportError, AttributeError) as erro:
        print(f"Não foi possível carregar os dados: {erro}")
        print("O arquivo foi preservado. Confira dados/operium.pkl e o backup antes de continuar.")
        return
    admins = dados["admins"]
    funcionarios = dados["funcionarios"]
    try:
        menu_autenticacao()
    except OSError as erro:
        print(f"Falha ao salvar: {erro}")
        print("Sistema encerrado. A última alteração pode não estar salva; a gravação anterior foi preservada.")
    except (EOFError, KeyboardInterrupt):
        print("\nOperium encerrado. Operações já salvas permanecem no arquivo.")


if __name__ == "__main__":
    iniciar()
