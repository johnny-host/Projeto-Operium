MAX_TENTATIVAS = 3


def cadastrar_admin(admins):

    usuario = input("Usuário: ").strip()
    while usuario == "" or buscar_admin(admins, usuario):
        if usuario == "":
            print("O usuário não pode ficar vazio. Tente novamente.")
        else:
            print("Esse usuário já existe. Escolha outro.")
        usuario = input("Usuário: ").strip()

    senha = input("Senha (mínimo 4 caracteres): ")
    while len(senha) < 4:
        print("Senha muito curta. Tente novamente.")
        senha = input("Senha (mínimo 4 caracteres): ")

    confirmacao = input("Confirme a senha: ")
    while confirmacao != senha:
        print("As senhas não conferem. Tente novamente.")
        confirmacao = input("Confirme a senha: ")

    admin = {
        "usuario": usuario,
        "senha": senha,
    }

    return admin


def buscar_admin(admins, usuario):
    for admin in admins:
        if admin["usuario"].lower() == usuario.lower():
            return admin
    return None


def login_admin(admins):
    if not admins:
        print("Nenhum administrador cadastrado. Cadastre um primeiro.")
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

MAX_TENTATIVAS = 3


def cadastrar_admin(admins):

    usuario = input("Usuário: ").strip()
    while usuario == "" or buscar_admin(admins, usuario):
        if usuario == "":
            print("O usuário não pode ficar vazio. Tente novamente.")
        else:
            print("Esse usuário já existe. Escolha outro.")
        usuario = input("Usuário: ").strip()

    senha = input("Senha (mínimo 4 caracteres): ")
    while len(senha) < 4:
        print("Senha muito curta. Tente novamente.")
        senha = input("Senha (mínimo 4 caracteres): ")

    confirmacao = input("Confirme a senha: ")
    while confirmacao != senha:
        print("As senhas não conferem. Tente novamente.")
        confirmacao = input("Confirme a senha: ")

    admin = {
        "usuario": usuario,
        "senha": senha,
    }

    return admin


def buscar_admin(admins, usuario):
    for admin in admins:
        if admin["usuario"].lower() == usuario.lower():
            return admin
    return None


def login_admin(admins):
    if not admins:
        print("Nenhum administrador cadastrado. Cadastre um primeiro.")
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