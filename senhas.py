"""Funções de senha compartilhadas pelos dois tipos de acesso."""
from getpass import getpass
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_hex


def proteger_senha(senha):
    # O salt faz senhas iguais gerarem resultados diferentes no arquivo.
    salt = token_hex(16)
    resumo = pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), 600_000)
    return {"salt": salt, "resumo": resumo.hex(), "iteracoes": 600_000}


def verificar_senha(senha, registro):
    resumo = pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(registro["salt"]), registro["iteracoes"])
    return compare_digest(resumo.hex(), registro["resumo"])


def solicitar_senha():
    while True:
        senha = getpass("Nova senha (mínimo 8 caracteres): ")
        if len(senha) < 8 or not senha.strip():
            print("Use pelo menos 8 caracteres; a senha não pode conter apenas espaços.")
            continue
        if senha != getpass("Confirme a senha: "):
            print("As senhas não conferem.")
            continue
        return proteger_senha(senha)
