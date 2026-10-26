from funcionarios import titulo
from menu_funcionario import mostrar_menu_funcionario
from funcionarios import limpar_tela
from funcionarios import dar_tempo
from administradores import menu_autenticacao


def Mostrar_menu_principal():

    titulo(" BEM-VINDO AO SISTEMA!! ")

    while True:
        
        limpar_tela()
        
        print('╔' + '═' * 44 + '╗')
        print('║' + '★  OPERIUM  ★'.center(44) + '║')
        print('║' + ' ' * 44 + '║')
        print('║' + 'LOGUIN'.center(44) + '║')
        print('║' + ' ' * 44 + '║')
        print('╚' + '═' * 44 + '╝')

        print("-- Escolha uma opção para efetuar o Loguin --")
        print("")
        print("(1) Administrador ")
        print("")
        print("(2) Funcionário ")
        print("")

        Escolha_principal = input("Digite 1 ou 2 para escolher seu Usuário e prosseguir: ").strip()

        if Escolha_principal == "1":
            limpar_tela()
            menu_autenticacao()

        elif Escolha_principal == "2":
            limpar_tela()
            mostrar_menu_funcionario()

        else:
            limpar_tela()
            print("Digite apenas uma das opções válidas.")
            dar_tempo()
            


# Só roda o menu quando ESTE arquivo é executado diretamente.
# Se outro arquivo importar o menu_principal, nada roda sozinho.
if __name__ == "__main__":
    Mostrar_menu_principal()