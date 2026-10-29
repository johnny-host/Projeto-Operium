"""Execute: python -B -m unittest discover -s tests -v"""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

import armazenamento
import main as aplicativo
from administrador import proteger_senha, verificar_senha
from escalas import (
    ajustar_dia, alertas_planejamento, cadastrar_escala, consultar_planejamento,
    gerar_planejamento, validar_escala,
)
from jornada import criar_turno, converter_data, minutos_trabalhados
from regras import cadastrar_regra, regra_vigente, validar_regra


def funcionario_exemplo():
    return {"id": 1, "nome": "Teste", "cpf": "52998224725", "data_nascimento": "01/01/2000",
            "status": "ativo", "contrato": {"cargo": "Analista", "salario": 2000,
            "data_admissao": "01/01/2026", "jornada": "5x2", "carga": 40, "regime": "clt"}}


def escala_exemplo():
    return {"inicio": "26/10/2026", "fim": "08/11/2026", "tipo": "5x2",
            "empresa": "empresa", "categoria": "equipe", "carga_semanal": 40,
            "dias": [criar_turno("08:00", "17:00", 60) for _ in range(5)]
                    + [{"status": "folga"}, {"status": "dsr"}]}


def regra_exemplo():
    # Números de teste, não um perfil legal recomendado.
    return {"empresa": "empresa", "categoria": "equipe", "inicio": "01/10/2026", "fim": "31/10/2026",
            "versao": 1, "fonte": "Teste", "limite_diario": 8, "limite_semanal": 40,
            "intervalo_minimo": 60, "intervalo_acima": 6, "descanso_minimo": 11,
            "dsr_minimo": 24, "percentual_extra": 50, "limite_extra": 2,
            "adicional_noturno": 20, "divisor": 200}


class PersistenciaTest(TestCase):
    def test_arquivo_novo_e_reabertura(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "dados.pkl"
            dados = armazenamento.carregar_dados(arquivo)
            dados["funcionarios"].append(funcionario_exemplo())
            dados["funcionarios"][0]["escalas"] = [escala_exemplo()]
            dados["regras"].append(regra_exemplo())
            dados["admins"].append({"usuario": "teste", "senha": proteger_senha("senha123")})
            armazenamento.salvar_dados(dados, arquivo)
            self.assertEqual(armazenamento.carregar_dados(arquivo), dados)
            self.assertNotIn(b'senha123', arquivo.read_bytes())

    def test_backup_e_falha_na_substituicao(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "dados.pkl"
            dados = armazenamento.dados_vazios()
            armazenamento.salvar_dados(dados, arquivo)
            original = arquivo.read_bytes()
            dados["funcionarios"].append(funcionario_exemplo())
            with patch('armazenamento.os.replace', side_effect=OSError('falha simulada')):
                with self.assertRaises(OSError):
                    armazenamento.salvar_dados(dados, arquivo)
            self.assertEqual(arquivo.read_bytes(), original)
            self.assertEqual(arquivo.with_suffix('.bak').read_bytes(), original)
            self.assertFalse(arquivo.with_suffix('.tmp').exists())

    def test_corrompido_nao_inicia_nem_sobrescreve(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "dados.pkl"
            arquivo.write_bytes(b'arquivo corrompido')
            with patch.object(aplicativo, 'carregar_dados', side_effect=lambda: armazenamento.carregar_dados(arquivo)):
                with patch.object(aplicativo, 'menu_autenticacao') as menu, redirect_stdout(StringIO()):
                    aplicativo.iniciar()
                    menu.assert_not_called()
            self.assertEqual(arquivo.read_bytes(), b'arquivo corrompido')

    def test_backup_sem_original_nao_cria_base_vazia(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'dados.pkl'
            arquivo.with_suffix('.bak').write_bytes(b'backup')
            with self.assertRaises(ValueError):
                armazenamento.carregar_dados(arquivo)

    def test_senha_correta_e_incorreta(self):
        registro = proteger_senha('segredo123')
        self.assertTrue(verificar_senha('segredo123', registro))
        self.assertFalse(verificar_senha('outra', registro))

    @patch('senhas.getpass', side_effect=['funcionario123', 'funcionario123'])
    def test_cadastro_e_escala_salvos_pelo_menu(self, senha_digitada):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'dados.pkl'
            dados = armazenamento.dados_vazios()
            dados['admins'].append({'usuario': 'gestor', 'senha': proteger_senha('senha123')})
            armazenamento.salvar_dados(dados, arquivo)
            entradas = ['1', 'gestor',
                        '1', 'Teste', '52998224725', '01/01/2000', '01/01/2026',
                        'Analista', '2000', '42', 'clt', '12x36',
                        '8', '1', '26/10/2026', '08/11/2026', 'empresa', 'equipe',
                        '19:00', '07:00', '60', 's', '6', '2']
            with patch.object(aplicativo, 'carregar_dados', side_effect=lambda: armazenamento.carregar_dados(arquivo)), \
                 patch.object(aplicativo, 'salvar_dados', side_effect=lambda d: armazenamento.salvar_dados(d, arquivo)), \
                 patch('builtins.input', side_effect=entradas), patch('acesso.getpass', return_value='senha123'), redirect_stdout(StringIO()):
                aplicativo.iniciar()
            funcionario = armazenamento.carregar_dados(arquivo)['funcionarios'][0]
            self.assertEqual(funcionario['id'], 1)
            self.assertEqual(funcionario['escalas'][0]['tipo'], '12x36')

    def test_salva_primeiro_admin_e_reabre_login(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'dados.pkl'
            with patch.object(aplicativo, 'carregar_dados', side_effect=lambda: armazenamento.carregar_dados(arquivo)), \
                 patch.object(aplicativo, 'salvar_dados', side_effect=lambda dados: armazenamento.salvar_dados(dados, arquivo)), \
                 redirect_stdout(StringIO()):
                with patch('builtins.input', side_effect=['1', 'gestor', 'senha123', 'senha123', '2']):
                    aplicativo.iniciar()
                with patch('builtins.input', side_effect=['1', 'gestor', '6', '2']), patch('acesso.getpass', return_value='senha123'):
                    aplicativo.iniciar()
            self.assertEqual(armazenamento.carregar_dados(arquivo)['admins'][0]['usuario'], 'gestor')


class EscalasTest(TestCase):
    def setUp(self):
        self.funcionario = funcionario_exemplo()
        self.escala = escala_exemplo()
        self.funcionario['escalas'] = [self.escala]

    def test_semana_5x2_e_horarios_independentes(self):
        self.escala['dias'][1] = criar_turno('09:00', '18:00', 60)
        linhas = gerar_planejamento(self.funcionario, '26/10/2026', '01/11/2026')
        self.assertEqual(sum(l['minutos'] for l in linhas), 40 * 60)
        self.assertEqual(linhas[1]['turno']['entrada'], '09:00')
        self.assertEqual(linhas[-1]['turno']['status'], 'dsr')

    def test_6x1_e_horista(self):
        self.funcionario['escalas'] = []
        self.escala['tipo'] = '6x1'
        self.escala['dias'][5] = criar_turno('08:00', '12:00', 0)
        validar_escala(self.funcionario, self.escala)
        self.escala['tipo'] = 'horista'
        self.escala['dias'][1] = {'status': 'folga'}
        validar_escala(self.funcionario, self.escala)

    def test_noturno_e_intervalo(self):
        self.assertEqual(minutos_trabalhados(criar_turno('22:00', '06:00', 60)), 420)
        for entrada, saida, intervalo in [('08:00', '08:00', 0), ('08:00', '09:00', 60), ('25:00', '09:00', 0)]:
            with self.assertRaises(ValueError):
                criar_turno(entrada, saida, intervalo)

    def test_12x36_continua_mes_seguinte(self):
        self.escala['tipo'] = '12x36'
        self.escala['inicio'] = '31/10/2026'
        self.escala['turno'] = criar_turno('19:00', '07:00', 60)
        linhas = gerar_planejamento(self.funcionario, '31/10/2026', '04/11/2026')
        self.assertEqual([l['minutos'] for l in linhas], [660, 0, 660, 0, 660])
        self.assertEqual(len(alertas_planejamento(self.funcionario, linhas, [])), 5)

    def test_ajuste_de_feriado_e_novo_ajuste_preservam_padrao(self):
        for opcao, motivo in [('2', 'Feriado local'), ('3', 'DSR transferido')]:
            entradas = ['1', '27/10/2026', opcao, 's', motivo, 's']
            with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
                ajustar_dia([self.funcionario])
        linhas = gerar_planejamento(self.funcionario, '26/10/2026', '28/10/2026')
        self.assertEqual(linhas[1]['turno']['status'], 'dsr')
        self.assertTrue(linhas[1]['turno']['feriado'])
        self.assertEqual(linhas[2]['minutos'], 480)
        self.assertEqual(self.escala['dias'][1]['status'], 'trabalho')
        self.assertEqual(len(self.escala['ajustes']), 2)

    def test_sobreposicao_inativo_e_antes_admissao(self):
        with self.assertRaises(ValueError):
            validar_escala(self.funcionario, self.escala)
        self.funcionario['escalas'] = []
        self.funcionario['status'] = 'inativo'
        with self.assertRaises(ValueError):
            validar_escala(self.funcionario, self.escala)
        self.funcionario['status'] = 'ativo'
        self.escala['inicio'] = '01/01/2025'
        with self.assertRaises(ValueError):
            validar_escala(self.funcionario, self.escala)

    def test_quantidade_de_dias_e_dsr(self):
        self.funcionario['escalas'] = []
        self.escala['dias'][0] = {'status': 'folga'}
        with self.assertRaises(ValueError):
            validar_escala(self.funcionario, self.escala)
        self.escala = escala_exemplo()
        self.escala['dias'][6] = {'status': 'folga'}
        with self.assertRaises(ValueError):
            validar_escala(self.funcionario, self.escala)

    def test_limites_de_consulta_e_sem_escala(self):
        with self.assertRaises(ValueError):
            gerar_planejamento(self.funcionario, '02/11/2026', '01/11/2026')
        linhas = gerar_planejamento(self.funcionario, '09/11/2026', '09/11/2026')
        self.assertEqual(linhas[0]['turno']['status'], 'sem escala')

    def test_cancelamento_preserva_escalas(self):
        antes = deepcopy(self.funcionario)
        self.funcionario['contrato']['jornada'] = '12x36'
        entradas = ['1', '09/11/2026', '30/11/2026', 'empresa', 'equipe', '19:00', '07:00', '60', 'n']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            cadastrar_escala([self.funcionario])
        self.assertEqual(self.funcionario['escalas'], antes['escalas'])

    def test_relatorio_completo_e_parcial(self):
        for fim in ('01/11/2026', '28/10/2026'):
            saida = StringIO()
            with patch('builtins.input', side_effect=['1', '26/10/2026', fim]), redirect_stdout(saida):
                consultar_planejamento([self.funcionario], [regra_exemplo()])
            self.assertIn('Total previsto:', saida.getvalue())

    def test_descanso_na_borda_e_intervalo_insuficiente(self):
        self.escala['dias'][0] = criar_turno('16:00', '23:00', 0)
        self.escala['dias'][1] = criar_turno('06:00', '17:00', 0)
        linhas = gerar_planejamento(self.funcionario, '27/10/2026', '27/10/2026')
        alertas = ' '.join(alertas_planejamento(self.funcionario, linhas, [regra_exemplo()]))
        self.assertIn('descanso entre jornadas', alertas)
        self.assertIn('intervalo menor', alertas)
        self.assertIn('excedente diário', alertas)


class RegrasTest(TestCase):
    def test_cadastro_regra_por_menu(self):
        regras = []
        entradas = ['Empresa', 'Equipe', '01/10/2026', '31/10/2026',
                    '8', '40', '60', '6', '11', '24', '50', '2', '20', '0', '200', 'Exemplo de teste', 's']
        with patch('builtins.input', side_effect=entradas), redirect_stdout(StringIO()):
            cadastrar_regra(regras)
        self.assertEqual(len(regras), 1)
        self.assertEqual(regras[0]['divisor'], 200)

    def test_versoes_vigencia_e_grupo(self):
        antiga = regra_exemplo()
        nova = dict(antiga, inicio='01/11/2026', fim='30/11/2026', versao=2)
        validar_regra([antiga], nova)
        regras = [antiga, nova]
        self.assertEqual(regra_vigente(regras, 'EMPRESA', 'equipe', converter_data('31/10/2026'))['versao'], 1)
        self.assertEqual(regra_vigente(regras, 'empresa', 'equipe', converter_data('01/11/2026'))['versao'], 2)
        self.assertIsNone(regra_vigente(regras, 'outra', 'equipe', converter_data('01/11/2026')))
        self.assertIsNone(regra_vigente(regras, 'empresa', 'equipe', converter_data('01/12/2026')))

    def test_sobreposicao_divisor_e_nao_finitos(self):
        regra = regra_exemplo()
        with self.assertRaises(ValueError):
            validar_regra([regra], dict(regra, inicio='31/10/2026', fim='30/11/2026'))
        for valor in (0, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                validar_regra([], dict(regra, divisor=valor))


if __name__ == '__main__':
    main()
