from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from acesso import login_geral
from senhas import proteger_senha
from test_fase3 import funcionario_exemplo
import main as app


class LoginGeralTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = {'usuario': 'gestor', 'senha': proteger_senha('admin1234')}
        cls.funcionario = funcionario_exemplo()
        cls.funcionario['senha'] = proteger_senha('pessoa1234')

    def entrar(self, admins, funcionarios, entradas, senha):
        with patch('builtins.input', side_effect=entradas), patch('acesso.getpass', return_value=senha), redirect_stdout(StringIO()):
            return login_geral(admins, funcionarios)

    def test_perfil_identificado_pelas_credenciais(self):
        acesso = self.entrar([self.admin], [self.funcionario], [' GESTOR '], 'admin1234')
        self.assertEqual(acesso['perfil'], 'administrador')
        acesso = self.entrar([self.admin], [self.funcionario], ['1'], 'pessoa1234')
        self.assertEqual(acesso['perfil'], 'funcionario')

    def test_nao_entra_com_senha_errada_inativo_ou_sem_senha(self):
        self.assertIsNone(self.entrar([self.admin], [self.funcionario], ['gestor'] * 3, 'errada'))
        inativo = dict(self.funcionario, status='inativo')
        self.assertIsNone(self.entrar([self.admin], [inativo], ['1'] * 3, 'pessoa1234'))
        antigo = funcionario_exemplo()
        self.assertIsNone(self.entrar([self.admin], [antigo], ['1'] * 3, 'pessoa1234'))

    def test_usuario_numerico_nao_concede_perfil_errado(self):
        admin = dict(self.admin, usuario='1')
        acesso = self.entrar([admin], [self.funcionario], ['1'], 'pessoa1234')
        self.assertEqual(acesso['perfil'], 'funcionario')
        acesso = self.entrar([admin], [self.funcionario], ['1'], 'admin1234')
        self.assertEqual(acesso['perfil'], 'administrador')
        admin['senha'] = self.funcionario['senha']
        acesso = self.entrar([admin], [self.funcionario], ['1', '2'], 'pessoa1234')
        self.assertEqual(acesso['perfil'], 'funcionario')
        self.assertIsNone(self.entrar([admin], [self.funcionario], ['1', '0'], 'pessoa1234'))

    def test_logout_retorna_ao_login_sem_reutilizar_perfil(self):
        with patch.object(app, 'admins', [self.admin]), patch.object(app, 'funcionarios', [self.funcionario]), \
             patch('builtins.input', side_effect=['1', 'gestor', '1', '1', '2']), \
             patch('acesso.getpass', side_effect=['admin1234', 'pessoa1234']), \
             patch.object(app, 'menu_sistema') as admin_menu, \
             patch.object(app, 'menu_funcionario') as funcionario_menu, redirect_stdout(StringIO()):
            app.menu_autenticacao()
        admin_menu.assert_called_once_with(self.admin)
        funcionario_menu.assert_called_once_with(self.funcionario)
