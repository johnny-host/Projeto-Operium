from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
import pickle
import sqlite3

from armazenamento import carregar_dados, salvar_dados, dados_vazios, conectar
from migracao import migrar_pickle
from test_fase3 import funcionario_exemplo, escala_exemplo, regra_exemplo
from registros_jornada import criar_registro
from senhas import proteger_senha, verificar_senha


class SQLiteTest(TestCase):
    def test_migracao_completa_preserva_original_e_nao_repete(self):
        with TemporaryDirectory() as pasta:
            origem = Path(pasta) / 'operium.pkl'
            destino = Path(pasta) / 'operium.db'
            dados = dados_vazios()
            f = funcionario_exemplo()
            f['senha'] = proteger_senha('senha12345')
            f['escalas'] = [escala_exemplo()]
            f['escalas'][0]['ajustes'] = [{'data':'27/10/2026', 'turno':{'status':'folga','feriado':True}, 'motivo':'Teste', 'registrado_em':'2026-10-26T12:00:00'}]
            f['jornadas'] = [criar_registro('26/10/2026','08:00','17:00','12:00','13:00','Teste')]
            dados['funcionarios'] = [f]
            dados['regras'] = [regra_exemplo()]
            dados['admins'] = [{'usuario':'gestor','senha':proteger_senha('admin1234')}]
            original = pickle.dumps(dados)
            origem.write_bytes(original)
            convertido = carregar_dados(destino)
            self.assertEqual(convertido,dados)
            self.assertEqual(origem.read_bytes(),original)
            self.assertTrue(verificar_senha('senha12345',convertido['funcionarios'][0]['senha']))
            convertido['funcionarios'][0]['nome'] = 'Atualizado'
            salvar_dados(convertido,destino)
            self.assertEqual(carregar_dados(destino)['funcionarios'][0]['nome'],'Atualizado')
            with self.assertRaises(ValueError):
                migrar_pickle(origem,destino)

    def test_migracao_invalida_nao_deixa_banco_parcial(self):
        with TemporaryDirectory() as pasta:
            origem = Path(pasta) / 'operium.pkl'
            destino = Path(pasta) / 'operium.db'
            dados = dados_vazios()
            dados['funcionarios'] = [funcionario_exemplo(), funcionario_exemplo()]
            origem.write_bytes(pickle.dumps(dados))
            with self.assertRaises(sqlite3.IntegrityError):
                carregar_dados(destino)
            self.assertFalse(destino.exists())
            self.assertFalse(destino.with_suffix('.migracao.db').exists())
            self.assertTrue(origem.exists())

    def test_cpf_duplicado_rollback_e_relacionamentos(self):
        with TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'teste.db'
            dados = dados_vazios()
            dados['funcionarios'] = [funcionario_exemplo()]
            salvar_dados(dados,destino)
            duplicado = deepcopy(dados['funcionarios'][0])
            duplicado['id'] = 2
            dados['funcionarios'].append(duplicado)
            with self.assertRaises(sqlite3.IntegrityError):
                salvar_dados(dados,destino)
            self.assertEqual(len(carregar_dados(destino)['funcionarios']),1)
            con = conectar(destino)
            try:
                with self.assertRaises(sqlite3.IntegrityError):
                    con.execute("INSERT INTO contratos VALUES (99,'Teste',2000,40,'clt','5x2','01/01/2026')")
                self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:
                con.close()

    def test_valores_sql_sao_texto_e_nao_comandos(self):
        with TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'teste.db'
            dados = dados_vazios()
            dados['funcionarios'] = [funcionario_exemplo()]
            nome = "Ana'); DROP TABLE funcionarios; --"
            dados['funcionarios'][0]['nome'] = nome
            salvar_dados(dados,destino)
            self.assertEqual(carregar_dados(destino)['funcionarios'][0]['nome'],nome)

    def test_objetos_pickle_nao_permitidos(self):
        with TemporaryDirectory() as pasta:
            origem = Path(pasta) / 'operium.pkl'
            destino = Path(pasta) / 'operium.db'
            origem.write_bytes(pickle.dumps(Path('teste')))
            with self.assertRaises(ValueError):
                migrar_pickle(origem,destino)
            self.assertFalse(destino.exists())
