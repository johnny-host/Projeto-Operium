REGIMES = ("6x1", "5x2", "12x36", "horista")
LARGURA = 44


# ---------- Funções auxiliares ----------


def limpar_tela():
    """Apaga tudo que está na tela do terminal (funciona no Windows, Linux e Mac)."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar():
    """Espera o usuário apertar ENTER, para dar tempo de ler o que apareceu na tela."""
    input('\nPressione ENTER para continuar...')
    
def dar_tempo():
    "Faz o usuário esperar determinado tempo para completar determinada ação"
    import time
    time.sleep(3)

def ler_float(mensagem):
    """Pede um número decimal positivo até o usuário digitar um valor válido."""
    while True:
        valor = input(mensagem).strip().replace(",", ".")
        try:
            numero = float(valor)
            if numero > 0:
                return numero
        except ValueError:
            pass
        print('Valor inválido! Tente novamente.')

def ler_carga(mensagem):
    """Pede a carga semanal (1 a 44) até o usuário digitar um valor válido."""
    while True:
        valor = input(mensagem).strip()
        if valor.isdigit() and 0 < int(valor) <= 44:
            return int(valor)
        print('Valor inválido ou não permitido (máximo 44h). Tente novamente.')

def ler_regime(mensagem):
    """Pede o regime até o usuário digitar um dos regimes permitidos."""
    while True:
        regime = input(mensagem).strip().lower()
        if regime in REGIMES:
            return regime
        print('Regime inválido! Use: horista, 6x1, 5x2 ou 12x36.')

def ler_texto(mensagem):
    """Pede um texto que não pode ficar vazio."""
    while True:
        texto = input(mensagem).strip()
        if texto:
            return texto
        print('Este campo não pode ficar vazio!')

def titulo(texto):
    print()
    print('╔' + '═' * LARGURA + '╗')
    print('║' + texto.center(LARGURA) + '║')
    print('╚' + '═' * LARGURA + '╝')


# ---------- Funções principais ----------

def cadastro_funcionario():
    titulo('CADASTRO DE FUNCIONÁRIO')

    nome = ler_texto('Nome: ')
    cargo = ler_texto('Cargo: ')
    salario = ler_float('Salário: R$ ')
    carga = ler_carga('Carga semanal (até 44h): ')
    regime = ler_regime('Regime (horista, 6x1, 5x2 ou 12x36): ')

    funcionario = {
        "nome": nome,
        "cargo": cargo,
        "salario": salario,
        "carga": carga,
        "regime": regime,
    }

    print(f'\n✔ Funcionário "{nome}" cadastrado com sucesso!')
    return funcionario

def oferecer_cadastro(funcionarios):
    """Pergunta se o usuário quer cadastrar alguém que não está no sistema."""
    print('\nEsse usuário não está contido no sistema.')
    while True:
        resposta = input('Gostaria de adicioná-lo? [S]im ou [N]ão: ').strip().lower()
        if resposta in ('s', 'sim'):
            limpar_tela()
            funcionarios.append(cadastro_funcionario())
            return
        elif resposta in ('n', 'não', 'nao'):
            print('Ok, voltando ao menu...')
            return
        print('Resposta inválida! Digite S para sim ou N para não.')

def mostrar_funcionario(funcionario):
    print('-' * (LARGURA + 2))
    print(f'  Nome:    {funcionario["nome"]}')
    print(f'  Cargo:   {funcionario["cargo"]}')
    print(f'  Salário: R$ {funcionario["salario"]:.2f}')
    print(f'  Carga:   {funcionario["carga"]}h semanais')
    print(f'  Regime:  {funcionario["regime"]}')
    print('-' * (LARGURA + 2))

def listar_funcionarios(funcionarios):
    if not funcionarios:
        oferecer_cadastro(funcionarios)
        return

    titulo(f'FUNCIONÁRIOS CADASTRADOS ({len(funcionarios)})')
    for funcionario in funcionarios:
        mostrar_funcionario(funcionario)

def escolher_funcionario(encontrados):
    """Se houver mais de um resultado, o usuário escolhe qual deles usar.
    Retorna o funcionário escolhido ou None se a escolha for inválida."""

    # Se tiver apenas 1 resultado, o programa deixa de lado e passa adiante
    if len(encontrados) == 1:
        return encontrados[0]
 
    # Vários resultados: mostra uma lista numerada
    print('\nVários funcionários encontrados:')
    for numero, f in enumerate(encontrados, start=1):
        print(f'  {numero} - {f["nome"]} ({f["cargo"]})')
    escolha = input('Digite o número do funcionário: ').strip()
 
    # Número válido: mostra o funcionário escolhido
    if escolha.isdigit() and 1 <= int(escolha) <= len(encontrados):
        return encontrados[int(escolha) - 1]
 
    # Número inválido: mostra mensagem de inválido
    print('Opção inválida! Voltando ao menu...')
    return None

def buscar_funcionario(funcionarios, nome_busca):
    """Retorna uma lista com os funcionários cujo nome contém o texto buscado."""
    nome_busca = nome_busca.lower().strip()
    if not nome_busca:
        return []
    return [f for f in funcionarios if nome_busca in f["nome"].lower()]

def editar_funcionario(funcionarios):
    titulo('EDITAR FUNCIONÁRIO')

    if not funcionarios:
        oferecer_cadastro(funcionarios)
        return

    nome_busca = input('Qual funcionário deseja editar? ')
    encontrados = buscar_funcionario(funcionarios, nome_busca)

    if not encontrados:
        oferecer_cadastro(funcionarios)
        return

    # Se houver mais de um resultado, o usuário escolhe qual editar
    if len(encontrados) > 1:
            print('\nVários funcionários encontrados:')
            for numero, f in enumerate(encontrados, start=1):
                print(f'  {numero} - {f["nome"]} ({f["cargo"]})')
            escolha = input('Digite o número do funcionário: ').strip()
            if not (escolha.isdigit() and 1 <= int(escolha) <= len(encontrados)):
                print('Opção inválida! Voltando ao menu...')
                return
            funcionario = encontrados[int(escolha) - 1]
    else:
        funcionario = encontrados[0]

    print()
    mostrar_funcionario(funcionario)
    print('Qual dado deseja editar?')
    print('  [1] Nome')
    print('  [2] Cargo')
    print('  [3] Salário')
    print('  [4] Carga semanal')
    print('  [5] Regime')
    print('  [0] Cancelar')
    opcao = input('Escolha uma opção: ').strip()

    if opcao == '1':
        funcionario["nome"] = ler_texto('Novo nome: ')
        print(f'✔ Nome atualizado para: {funcionario["nome"]}')

    elif opcao == '2':
        funcionario["cargo"] = ler_texto('Novo cargo: ')
        print(f'✔ Cargo atualizado para: {funcionario["cargo"]}')

    elif opcao == '3':
        funcionario["salario"] = ler_float('Novo salário: R$ ')
        print(f'✔ Salário atualizado para: R$ {funcionario["salario"]:.2f}')

    elif opcao == '4':
        funcionario["carga"] = ler_carga('Nova carga semanal (até 44h): ')
        print(f'✔ Carga atualizada para: {funcionario["carga"]}h')

    elif opcao == '5':
        funcionario["regime"] = ler_regime('Novo regime (horista, 6x1, 5x2 ou 12x36): ')
        print(f'✔ Regime atualizado para: {funcionario["regime"]}')

    elif opcao == '0':
        print('Edição cancelada.')

    else:
        print('Opção inválida!')

def excluir_funcionario(funcionarios):
    titulo('EXCLUIR FUNCIONÁRIO')
 
    # 1) Não dá para excluir se não há ninguém
    if not funcionarios:
        print('\nNenhum funcionário cadastrado no sistema!')
        return
 
    # 2) Pergunta quem excluir e busca (parcial, sem diferenciar maiúsculas)
    nome_busca = input('Qual funcionário deseja excluir? ')
    encontrados = buscar_funcionario(funcionarios, nome_busca)
 
    # 3) Nenhum resultado: avisa e sai
    if not encontrados:
        print('\nEsse nome não está cadastrado no sistema!')
        return
 
    # 4) Se houver vários, o usuário escolhe qual
    funcionario = escolher_funcionario(encontrados)
    if funcionario is None:      # escolha inválida: não apaga ninguém
        return
 
    # 5) Mostra quem será excluído e pede confirmação
    print()
    mostrar_funcionario(funcionario)
    while True:
        resposta = input(f'Tem certeza que deseja excluir "{funcionario["nome"]}"? [S]im ou [N]ão: ').strip().lower()
        if resposta in ('s', 'sim'):
            funcionarios.remove(funcionario)     # 6) exclui de verdade
            print(f'\n✔ Funcionário "{funcionario["nome"]}" excluído com sucesso!')
            return
        elif resposta in ('n', 'não', 'nao'):
            print('\nExclusão cancelada.')
            return
        print('Resposta inválida! Digite S para sim ou N para não.')