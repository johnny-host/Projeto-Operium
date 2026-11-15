"""Importação única do pickle local, preservando o arquivo original."""
from copy import deepcopy
from pathlib import Path
import os
import pickle


class LeitorDadosSimples(pickle.Unpickler):
    def find_class(self, modulo, nome):
        # O Operium antigo só gravava dicionários, listas e valores simples.
        raise ValueError('O arquivo contém objetos que não são dados simples do Operium.')


def normalizar(dados):
    dados = deepcopy(dados)
    for funcionario in dados['funcionarios']:
        for escala in funcionario.get('escalas', []):
            if escala.get('ajustes') == []:
                del escala['ajustes']
        for chave in ('escalas', 'jornadas'):
            if funcionario.get(chave) == []:
                del funcionario[chave]
    return dados


def migrar_pickle(origem, destino):
    from armazenamento import salvar_dados, carregar_dados
    origem, destino = Path(origem), Path(destino)
    if destino.exists():
        raise ValueError('O banco de destino já existe; não será sobrescrito pela migração.')
    with origem.open('rb') as arquivo:
        dados = LeitorDadosSimples(arquivo).load()
    if not isinstance(dados, dict) or dados.get('versao') != 1:
        raise ValueError('Formato do arquivo antigo não reconhecido.')
    for chave in ('admins', 'funcionarios', 'regras'):
        if not isinstance(dados.get(chave), list):
            raise ValueError(f'Lista inválida no arquivo antigo: {chave}.')
    temporario = destino.with_suffix('.migracao.db')
    if temporario.exists():
        raise ValueError('Existe uma migração incompleta. Preserve e confira o arquivo .migracao.db.')
    try:
        salvar_dados(dados, temporario)
        if normalizar(carregar_dados(temporario)) != normalizar(dados):
            raise ValueError('A conferência encontrou diferença nos dados; migração cancelada.')
        os.replace(temporario, destino)
    finally:
        if temporario.exists():
            temporario.unlink()
