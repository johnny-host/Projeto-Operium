"""Uma entrada comum, com perfil identificado após validar a senha."""
from getpass import getpass
from administrador import buscar_admin
from funcionarios import buscar_funcionario
from senhas import verificar_senha


def login_geral(admins, funcionarios):
    for tentativa in range(3):
        identificador = input("Usuário do administrador ou ID do funcionário: ").strip()
        senha = getpass("Senha: ")
        acessos = []

        admin = buscar_admin(admins, identificador)
        if admin and verificar_senha(senha, admin["senha"]):
            acessos.append({"perfil": "administrador", "usuario": admin})

        funcionario = buscar_funcionario(funcionarios, identificador)
        if (funcionario and funcionario["status"] == "ativo"
                and funcionario.get("senha")
                and verificar_senha(senha, funcionario["senha"])):
            acessos.append({"perfil": "funcionario", "usuario": funcionario})

        if len(acessos) == 1:
            print("Login realizado! Perfil:", acessos[0]["perfil"])
            return acessos[0]

        if len(acessos) == 2:
            # Um usuário de administrador antigo pode ser igual a um ID.
            # Só oferecemos os dois perfis se a senha foi validada para ambos.
            print("Essas credenciais correspondem a dois acessos.")
            opcao = input("1 - Administrador, 2 - Funcionário, 0 - Cancelar: ").strip()
            if opcao == "0":
                return None
            if opcao in ("1", "2"):
                return acessos[int(opcao) - 1]
            print("Opção inválida.")
        else:
            print("Acesso não autorizado. Confira suas credenciais ou procure o administrador.")
        print("Tentativas restantes:", 2 - tentativa)

    print("Número máximo de tentativas atingido.")
    return None
