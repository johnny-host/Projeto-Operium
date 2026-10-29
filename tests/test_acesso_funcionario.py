from contextlib import redirect_stdout
from copy import deepcopy
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import main as app
from armazenamento import carregar_dados, dados_vazios, salvar_dados
from funcionarios import (login_funcionario, definir_senha_funcionario,
                          trocar_senha_funcionario, editar_funcionario, obter_data_admissao)
from senhas import proteger_senha, solicitar_senha, verificar_senha
from test_fase3 import funcionario_exemplo, escala_exemplo


class AcessoFuncionarioTest(TestCase):
    def setUp(self):
        self.funcionario = funcionario_exemplo()
        self.funcionario['senha'] = proteger_senha('senha1234')
        self.saida = StringIO()

    def entrar(self, id_busca='1', senha='senha1234'):
        with patch('builtins.input', return_value=id_busca), patch('funcionarios.getpass', return_value=senha), redirect_stdout(self.saida):
            return login_funcionario([self.funcionario])

    def test_login_por_id_e_negacao_por_nome(self):
        self.assertIs(self.entrar(' 1 '), self.funcionario)
        self.assertIsNone(self.entrar('Teste'))
        self.assertIsNone(self.entrar('999'))
        self.assertIsNone(self.entrar(senha='errada'))

    def test_inativo_e_cadastro_antigo_sem_senha(self):
        self.funcionario['status'] = 'inativo'
        self.assertIsNone(self.entrar())
        self.funcionario['status'] = 'ativo'
        del self.funcionario['senha']
        self.assertIsNone(self.entrar())

    def test_definir_senha_de_cadastro_antigo_e_cancelar(self):
        del self.funcionario['senha']
        with patch('builtins.input', side_effect=['1', 'n']), redirect_stdout(self.saida):
            definir_senha_funcionario([self.funcionario])
        self.assertNotIn('senha', self.funcionario)
        with patch('builtins.input', side_effect=['1', 's']), patch('senhas.getpass', side_effect=['nova12345', 'nova12345']), redirect_stdout(self.saida):
            definir_senha_funcionario([self.funcionario])
        self.assertIs(self.entrar(senha='nova12345'), self.funcionario)

    def test_senha_curta_vazia_e_confirmacao(self):
        with patch('senhas.getpass', side_effect=['', '123', '        ', 'senha1234', 'diferente', 'valida1234', 'valida1234']), redirect_stdout(self.saida):
            senha = solicitar_senha()
        self.assertTrue(verificar_senha('valida1234', senha))

    def test_troca_exige_atual_e_confirmacao(self):
        antes = deepcopy(self.funcionario)
        with patch('funcionarios.getpass', return_value='errada'), redirect_stdout(self.saida):
            self.assertFalse(trocar_senha_funcionario(self.funcionario))
        for resposta in ['n', 's']:
            with patch('funcionarios.getpass', return_value='senha1234'), patch('senhas.getpass', side_effect=['nova12345', 'nova12345']), patch('builtins.input', return_value=resposta), redirect_stdout(self.saida):
                resultado = trocar_senha_funcionario(self.funcionario)
            if resposta == 'n':
                self.assertFalse(resultado)
                self.assertEqual(self.funcionario, antes)
            else:
                self.assertTrue(resultado)
                self.assertFalse(verificar_senha('senha1234', self.funcionario['senha']))
                self.assertTrue(verificar_senha('nova12345', self.funcionario['senha']))

    def test_menu_isolado_do_administrador_e_de_outros_funcionarios(self):
        with patch('builtins.input', side_effect=['13', '1', '2', '4']), patch.object(app, 'mostrar_funcionario') as mostrar, patch.object(app, 'mostrar_planejamento') as escala, patch.object(app, 'menu_sistema') as admin, redirect_stdout(self.saida):
            app.menu_funcionario(self.funcionario)
        mostrar.assert_called_once_with(self.funcionario)
        escala.assert_called_once_with(self.funcionario, app.dados['regras'])
        admin.assert_not_called()

    def test_login_e_troca_persistidos_apos_reabrir(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'teste.pkl'
            dados = dados_vazios()
            dados['admins'] = [{'usuario': 'admin', 'senha': proteger_senha('admin1234')}]
            dados['funcionarios'] = [self.funcionario]
            salvar_dados(dados, arquivo)
            with patch.object(app, 'carregar_dados', side_effect=lambda: carregar_dados(arquivo)), patch.object(app, 'salvar_dados', side_effect=lambda d: salvar_dados(d, arquivo)), redirect_stdout(self.saida):
                with patch('builtins.input', side_effect=['1', '1', '3', 's', '4', '2']), patch('acesso.getpass', return_value='senha1234'), patch('funcionarios.getpass', return_value='senha1234'), patch('senhas.getpass', side_effect=['nova12345', 'nova12345']):
                    app.iniciar()
                with patch('builtins.input', side_effect=['1', '1', '4', '2']), patch('acesso.getpass', return_value='nova12345'):
                    app.iniciar()
            recuperado = carregar_dados(arquivo)['funcionarios'][0]
            self.assertTrue(verificar_senha('nova12345', recuperado['senha']))
            self.assertEqual(obter_data_admissao(recuperado), date(2026, 1, 1))
            self.assertNotIn(b'nova12345', arquivo.read_bytes())

    def test_admissao_valida_sem_conflitar_com_escalas(self):
        self.funcionario['escalas'] = [escala_exemplo()]
        entradas = ['1', '7', '31/02/2026', '01/01/1999', '01/11/2026', '01/02/2026', 's']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(self.saida):
            editar_funcionario([self.funcionario])
        self.assertEqual(obter_data_admissao(self.funcionario), date(2026, 2, 1))
        with patch('builtins.input', side_effect=['1', '7', '01/03/2026', 'n']), redirect_stdout(self.saida):
            editar_funcionario([self.funcionario])
        self.assertEqual(obter_data_admissao(self.funcionario), date(2026, 2, 1))
