from funcionarios import titulo

MAX_TENTATIVAS = 3


# ---------- Leitura de dados (reaproveitada no cadastro e na edição) ----------

def ler_usuario_novo(admins, atual=None):
    """Pede um usuário que não pode ficar vazio nem repetir o de outro administrador.
    'atual' é o administrador que está sendo editado: ele pode manter o próprio nome."""
    while True:
        usuario = input("Usuário: ").strip()
        if usuario == "":
            print("O usuário não pode ficar vazio. Tente novamente.")
            continue

        existente = buscar_admin(admins, usuario)
        if existente and existente is not atual:
            print("Esse usuário já existe. Escolha outro.")
            continue

        return usuario


def ler_senha_nova():
    """Pede uma senha de no mínimo 4 caracteres e a confirmação."""
    senha = input("Senha (mínimo 4 caracteres): ")
    while len(senha) < 4:
        print("Senha muito curta. Tente novamente.")
        senha = input("Senha (mínimo 4 caracteres): ")

    confirmacao = input("Confirme a senha: ")
    while confirmacao != senha:
        print("As senhas não conferem. Tente novamente.")
        confirmacao = input("Confirme a senha: ")

    return senha


# ---------- Cadastro, busca exata e login ----------

def cadastrar_admin(admins):
    usuario = ler_usuario_novo(admins)
    senha = ler_senha_nova()

    admin = {
        "usuario": usuario,
        "senha": senha,
    }

    return admin


def buscar_admin(admins, usuario):
    """Busca EXATA (usada para impedir usuários repetidos e no login)."""
    for admin in admins:
        if admin["usuario"].lower() == usuario.lower():
            return admin
    return None


def login_admin(admins):
    if not admins:

        print("Nenhum administrador cadastrado. Cadastre um primeiro.")
        print("")
        return None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        usuario = input("Usuário: ").strip()
        senha = input("Senha: ")

        admin = buscar_admin(admins, usuario)
        if admin and admin["senha"] == senha:
            print(f"Login realizado! Bem-vindo, {admin['usuario']}.")
            return admin

        restantes = MAX_TENTATIVAS - tentativa
        if restantes > 0:
            print(f"Usuário ou senha incorretos. Tentativas restantes: {restantes}")

    print("Número máximo de tentativas atingido.")
    return None


# ---------- Listar, pesquisar, editar e excluir ----------

def listar_admins(admins):
    """Mostra só os usuários. A senha nunca aparece na tela."""
    if not admins:
        print("\nNenhum administrador cadastrado no sistema!")
        return

    titulo(f"ADMINISTRADORES ({len(admins)})")
    for numero, admin in enumerate(admins, start=1):
        print(f"  {numero} - {admin['usuario']}")


def pesquisar_admins(admins, texto):
    """Busca PARCIAL, sem diferenciar maiúsculas. Devolve uma lista (pode ser vazia)."""
    texto = texto.lower().strip()
    if not texto:
        return []
    return [a for a in admins if texto in a["usuario"].lower()]


def escolher_admin(encontrados):
    """Se houver mais de um resultado, o usuário escolhe qual deles usar.
    Retorna o administrador escolhido ou None se a escolha for inválida."""
    if len(encontrados) == 1:
        return encontrados[0]

    print("\nVários administradores encontrados:")
    for numero, admin in enumerate(encontrados, start=1):
        print(f"  {numero} - {admin['usuario']}")
    escolha = input("Digite o número do administrador: ").strip()

    if escolha.isdigit() and 1 <= int(escolha) <= len(encontrados):
        return encontrados[int(escolha) - 1]

    print("Opção inválida! Voltando ao menu...")
    return None


def editar_admin(admins):
    titulo("EDITAR ADMINISTRADOR")

    texto = input("Qual administrador deseja editar? ")
    encontrados = pesquisar_admins(admins, texto)

    if not encontrados:
        print("\nEsse administrador não está cadastrado no sistema!")
        return

    admin = escolher_admin(encontrados)
    if admin is None:
        return

    print(f"\nAdministrador selecionado: {admin['usuario']}")
    print("Qual dado deseja editar?")
    print("  [1] Usuário")
    print("  [2] Senha")
    print("  [0] Cancelar")
    opcao = input("Escolha uma opção: ").strip()

    # "admin" é o mesmo dicionário que está dentro da lista "admins",
    # então alterar aqui já altera o dado no sistema.
    if opcao == "1":
        admin["usuario"] = ler_usuario_novo(admins, atual=admin)
        print(f"✔ Usuário atualizado para: {admin['usuario']}")

    elif opcao == "2":
        admin["senha"] = ler_senha_nova()
        print("✔ Senha atualizada com sucesso!")

    elif opcao == "0":
        print("Edição cancelada.")

    else:
        print("Opção inválida!")


def excluir_admin(admins, admin_logado):
    titulo("EXCLUIR ADMINISTRADOR")

    texto = input("Qual administrador deseja excluir? ")
    encontrados = pesquisar_admins(admins, texto)

    if not encontrados:
        print("\nEsse administrador não está cadastrado no sistema!")
        return

    admin = escolher_admin(encontrados)
    if admin is None:
        return

    # Evita apagar a própria conta enquanto está logado (e ficar sem acesso)
    if admin is admin_logado:
        print("\nVocê não pode excluir o administrador que está logado.")
        return

    print(f"\nAdministrador selecionado: {admin['usuario']}")
    while True:
        resposta = input(f"Tem certeza que deseja excluir \"{admin['usuario']}\"? [S]im ou [N]ão: ").strip().lower()
        if resposta in ("s", "sim"):
            admins.remove(admin)
            print(f"\n✔ Administrador \"{admin['usuario']}\" excluído com sucesso!")
            return
        elif resposta in ("n", "não", "nao"):
            print("\nExclusão cancelada.")
            return
        print("Resposta inválida! Digite S para sim ou N para não.")