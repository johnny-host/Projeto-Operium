"""Persistência local: listas e dicionários salvos com pickle."""
from pathlib import Path
import os
import pickle
import shutil

ARQUIVO = Path(__file__).resolve().parent / "dados" / "operium.pkl"


def dados_vazios():
    return {"versao": 1, "admins": [], "funcionarios": [], "regras": []}


def carregar_dados(caminho=ARQUIVO):
    caminho = Path(caminho)
    if not caminho.exists():
        # Uma cópia antiga pode existir após remoção acidental do original.
        if caminho.with_suffix(".bak").exists():
            raise ValueError("Arquivo principal ausente, mas existe backup. Restaure-o antes de continuar.")
        return dados_vazios()
    # Abra somente arquivos locais criados pelo próprio sistema.
    with caminho.open("rb") as arquivo:
        dados = pickle.load(arquivo)
    if not isinstance(dados, dict) or dados.get("versao") != 1:
        raise ValueError("Formato ou versão do arquivo não reconhecido.")
    for chave in ("admins", "funcionarios", "regras"):
        if not isinstance(dados.get(chave), list):
            raise ValueError(f"Lista inválida no arquivo: {chave}.")
        if any(not isinstance(item, dict) for item in dados[chave]):
            raise ValueError(f"Registro inválido no arquivo: {chave}.")
    return dados


def salvar_dados(dados, caminho=ARQUIVO):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    # Só substituímos o original depois de terminar a escrita.
    try:
        with temporario.open("wb") as arquivo:
            pickle.dump(dados, arquivo, protocol=pickle.HIGHEST_PROTOCOL)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        if caminho.exists():
            shutil.copy2(caminho, caminho.with_suffix(".bak"))
        os.replace(temporario, caminho)
    finally:
        if temporario.exists():
            temporario.unlink()
