from funcionarios import cadastro_funcionario
from funcionarios import mostrar_funcionario
from funcionarios import listar_funcionarios
from funcionarios import buscar_funcionario
from funcionarios import editar_funcionario
from funcionarios import oferecer_cadastro
from funcionarios import limpar_tela
from funcionarios import pausar
from funcionarios import dar_tempo
from funcionarios import excluir_funcionario

# A lista fica fora da função para os cadastros não se perderem
# quando o usuário sai do menu e volta depois.
funcionarios = []


def desenhar_menu_funcionario():
    print()
    print('╔' + '═' * 44 + '╗')
    print('║' + '★  OPERIUM  ★'.center(44) + '║')
    print('║' + 'Gestão de Funcionários'.center(44) + '║')
    print('╠' + '═' * 44 + '╣')
    print('║' + ' ' * 44 + '║')
    print('║' + '   [1]  Cadastrar Funcionário'.ljust(44) + '║')
    print('║' + '   [2]  Listar Funcionários'.ljust(44) + '║')
    print('║' + '   [3]  Buscar Funcionário'.ljust(44) + '║')
    print('║' + '   [4]  Editar Funcionário'.ljust(44) + '║')
    print('║' + '   [5]  Excluir Funcionário'.ljust(44) + '║')
    print('║' + '   [6]  Voltar Ao Menu Principal'.ljust(44) + '║')
    print('║' + ' ' * 44 + '║')
    print('╚' + '═' * 44 + '╝')


def mostrar_menu_funcionario():
    """Roda o menu de funcionários. Quando o usuário escolhe [6], a função
    termina e o programa volta para quem a chamou (o menu principal)."""
    while True:
        limpar_tela()
        desenhar_menu_funcionario()
        menu_opcao = input('Escolha uma opção: ').strip()

        if menu_opcao == "1":
            limpar_tela()
            funcionario = cadastro_funcionario()
            funcionarios.append(funcionario)
            pausar()

        elif menu_opcao == "2":
            limpar_tela()
            listar_funcionarios(funcionarios)
            pausar()

        elif menu_opcao == "3":
            limpar_tela()
            nome_busca = input('Qual funcionário deseja buscar? ')
            encontrados = buscar_funcionario(funcionarios, nome_busca)
            dar_tempo()

            if encontrados:
                print(f'\n{len(encontrados)} funcionário(s) encontrado(s):')
                for funcionario_encontrado in encontrados:
                    mostrar_funcionario(funcionario_encontrado)
            else:
                oferecer_cadastro(funcionarios)
            pausar()

        elif menu_opcao == "4":
            limpar_tela()
            editar_funcionario(funcionarios)
            pausar()

        elif menu_opcao == "5":
            limpar_tela()
            excluir_funcionario(funcionarios)
            pausar()

        elif menu_opcao == "6":
            limpar_tela()
            break   # sai do while e volta para o menu principal

        else:
            limpar_tela()
            print('\nOpção inválida! Escolha um número de 1 a 6.')
            pausar()