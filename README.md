# Projeto-Operium
Projeto relacionado a cadeira de Algoritmos e Programação II - Onde recebemos a tarefa de criar um projeto que resolve um problema para o mercado atual.

A proposta do projeto é desenvolver um sistema para gestão de colaboradores e automatização de cálculos relacionados à jornada de trabalho, banco de horas, remuneração e encargos trabalhistas.

O sistema busca facilitar o trabalho de pequenos gestores e administradores que ainda realizam esse controle manualmente por planilhas, reduzindo cálculos repetitivos e possíveis erros. O administrador poderá cadastrar colaboradores com informações como nome, cargo, salário-base, data de admissão, carga horária e regime de trabalho, como 5x2, 6x1 ou 12x36.

Nesta primeira versão, o sistema não funcionará como ponto eletrônico. Horas extras, horas debitadas e movimentações do banco de horas serão informadas manualmente pelo gestor, e o programa realizará os cálculos automaticamente.

Entre as funções previstas estão cadastro de colaboradores, cálculo do valor da hora, horas extras, horas debitadas, banco de horas, remuneração simplificada, INSS, FGTS e geração de relatórios mensais.

O projeto será desenvolvido inicialmente em Python, aplicando conteúdos da disciplina de Algoritmos e Programação, como variáveis, condicionais, repetições, funções, listas e dicionários.

Como evolução, pretendemos adicionar interface gráfica ou web, banco de dados e sistema de login ainda durante o semestre. Futuramente, poderão ser incluídos ponto eletrônico, férias, 13º salário, rescisões, dashboards, relatórios avançados e integração com outros sistemas de gestão.

## Versão atual — funcionários, jornada e persistência

Execute `python main.py` com Python 3. Não há dependências externas. Mantivemos funções, listas e dicionários para facilitar o estudo.

O módulo de funcionários inclui ID sequencial, CPF validado e único, nascimento, admissão, edição confirmada e inativação. Nomes iguais são permitidos. Regime contratual e tipo de jornada são campos separados.

### Dados salvos com pickle

`armazenamento.py` grava administradores, funcionários, escalas e regras em `dados/operium.pkl`. A pasta é criada na primeira gravação. O caminho independe da pasta de onde você executa o programa. Os IDs continuam a partir dos cadastros existentes após reabrir.

Cada operação de alteração concluída dispara o salvamento. Antes de substituir o arquivo, o programa escreve um temporário e mantém a versão anterior em `dados/operium.bak`. Operações canceladas também podem gerar uma gravação sem alterações. Se o arquivo não puder ser lido, o programa encerra sem substituí-lo por uma base vazia. Em falha de gravação, informa o erro e encerra; a alteração mais recente pode não ter sido salva.

O backup contém apenas a gravação anterior, não todo o histórico. Para recuperar: feche o Operium, guarde uma cópia do arquivo problemático e copie o backup confiável para `operium.pkl`. Um backup sem arquivo principal bloqueia a criação automática de uma base vazia. Não abra duas instâncias ao mesmo tempo: esta versão não tem controle de concorrência.

`pickle` é persistência em arquivo, não um banco relacional. Carregue apenas o arquivo criado localmente pelo Operium: arquivos pickle adulterados podem executar código. Não importe arquivos recebidos de terceiros. A pasta `dados/` foi excluída do Git. Os demais dados não são criptografados; senhas de administrador são armazenadas como hash com salt, sem o texto original. Referência: [documentação do pickle](https://docs.python.org/3/library/pickle.html).

### Como usar a Fase 3

1. Cadastre o administrador, entre e cadastre os funcionários.
2. Na opção **10**, cadastre regras para uma empresa/categoria, com início e fim de vigência. Os valores são informados pelo gestor, sem perfil legal automático.
3. Na opção **8**, selecione o funcionário pelo ID e cadastre sua escala para um período. Informe a mesma empresa/categoria das regras.
4. Na opção **9**, consulte o planejamento diário e os totais semanais.
5. Na opção **12**, ajuste uma data específica, como uma troca de folga, horário diferente ou feriado local. O padrão semanal permanece intacto e os ajustes anteriores ficam registrados.
6. A opção **11** mostra os parâmetros e as versões cadastradas.

**5x2 e 6x1:** escolha os dias de trabalho, folga e DSR. Cada dia trabalhado recebe entrada, saída e intervalo próprios. O cadastro confere a quantidade de dias e exige identificação de DSR.

**12x36:** a data inicial é a data de entrada do primeiro plantão. Os próximos começam a cada 48 horas, inclusive atravessando meses. O período entre entrada e saída deve ser de 12 horas. O intervalo informado é descontado das horas trabalhadas: um turno de 12 horas com 60 minutos de intervalo aparece com 11 horas líquidas. Não há cálculo de indenização do intervalo.

**Horista:** configure os dias e horários individualmente no padrão semanal, com ao menos um dia trabalhado e um DSR identificado. A escala pode receber ajustes por data. O campo de salário continua sendo remuneração mensal; pagamento por hora ainda não é calculado.

**Turno noturno:** saída menor que entrada significa saída no dia seguinte. Horas são contadas em minutos e atribuídas à data de entrada do turno. Não há distribuição por meia-noite para fins de folha, hora noturna reduzida ou cálculo financeiro de adicional nesta etapa.

Escalas têm períodos de até 366 dias, não podem se sobrepor nem começar antes da admissão. As antigas ficam preservadas. Alterar jornada ou carga do contrato não altera escalas já cadastradas; cadastre um período novo para aplicar a mudança. Ajustes diários permitem corrigir o planejamento existente. Funcionários inativos continuam consultáveis, mas não recebem novas escalas ou ajustes.

### Regras configuráveis e limites do relatório

As regras guardam empresa, categoria, versão, vigência, referência do acordo e os seguintes parâmetros:

- Limites diário e semanal, intervalo mínimo e quantidade de horas acima da qual ele é exigido.
- Descanso entre turnos, descanso contínuo para o DSR e limite diário de horas extras.
- Percentual de hora extra, adicional noturno e divisor mensal, reservados para os cálculos financeiros futuros.

Não se permite sobreposição de vigências para a mesma empresa/categoria. Uma versão nova não sobrescreve a anterior. Os relatórios selecionam a regra aplicável pela data de entrada de cada turno; quando falta uma regra, mostram essa ausência. Nesta etapa as versões são somente adicionadas; não há tela de correção de versão já cadastrada.

Os alertas verificam duração diária, excedente diário, intervalos e descanso entre turnos, além do descanso contínuo associado a um DSR identificado. Procuram o turno anterior em até sete dias antes do início da consulta. Sem esse contexto, não afirmam ter verificado o descanso inicial. O descanso posterior ao último turno consultado só pode ser avaliado em uma consulta que inclua o próximo turno. A avaliação de DSR é básica e não cobre todas as sequências móveis ou exigências legais.

Totais semanais usam segunda a domingo. Semanas incompletas ou com datas sem escala são identificadas como parciais e não recebem avaliação de limite semanal. Em semanas com mudança de regra, o total é comparado com cada versão encontrada, emitindo alertas para conferência, sem rateio ou conclusão automática sobre compensação. Em 12x36, o total pode variar entre semanas; uma diferença em relação à carga contratual é apenas um alerta.

O limite fixo de 44 horas foi retirado do cadastro. Ele agora aceita uma carga positiva até o limite físico de 168 horas na semana, e o planejamento é comparado com os limites configurados. Isso não autoriza jornadas de qualquer duração.

O sistema trabalha com **jornada planejada**, não com ponto realizado. Faltam lançamento de horas efetivas, banco de horas, cálculo financeiro, critérios específicos para domingos/feriados, hora noturna reduzida e múltiplas faixas de intervalo. Feriados são informados manualmente, sem calendário automático. O histórico salarial foi retirado do escopo por decisão do projeto. Os cálculos de 13º e férias serão implementados posteriormente.

A referência de estudo é a [CLT no Portal Planalto](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm), especialmente os arts. 58, 59, 59-A, 66, 67, 71 e 73. A aplicação depende do regime e dos instrumentos coletivos; os alertas do programa não certificam conformidade trabalhista.

### Roteiro de leitura e testes

- `validacoes.py`: entrada de dados, funções de validação e `try/except`.
- `armazenamento.py`: leitura e gravação com `pickle`, `with` e arquivos.
- `jornada.py`: datas, horários e duração em minutos.
- `regras.py`: cadastro e seleção das regras pela vigência.
- `escalas.py`: padrão semanal, ciclo 12x36, ajustes e relatório.
- `main.py`: integração das funções no menu e salvamento.

Execute `python -B -m unittest discover -s tests -v` para verificar persistência, backup, login após reabrir, cadastro integrado, escalas, feriados, virada de dia/mês, cancelamentos, alertas e vigências. Os testes usam arquivos temporários e não modificam os dados reais.

### Login do funcionário e data de admissão

Na tela inicial, use **1 — Entrar**. O administrador informa seu usuário; o funcionário informa seu ID. Após validar a senha, o sistema identifica o perfil e abre o menu correspondente. Não é necessário escolher o tipo de acesso antes de entrar. Se um usuário de administrador coincidir com um ID e a senha for válida para ambos, o sistema pede qual dos dois acessos deseja usar, sem escolher automaticamente o administrador. O cadastro de novos funcionários agora pede uma senha inicial com pelo menos 8 caracteres e confirmação. A digitação fica oculta no terminal. São permitidas três tentativas por chamada de login; não há bloqueio permanente entre chamadas.

Para funcionários já cadastrados, o administrador deve usar **13 — Definir / redefinir senha do funcionário**. Não existe senha padrão e não é necessário apagar ou recadastrar os registros antigos. Funcionários inativos não podem entrar. Senhas são salvas como hash com salt, usando as mesmas funções do administrador.

O funcionário pode consultar apenas seus dados e sua escala, trocar a própria senha informando a atual e encerrar a sessão. Não pode cadastrar, editar dados contratuais ou acessar o menu administrativo. O administrador pode redefinir uma senha esquecida pela opção 13.

A data de admissão já é obrigatória no cadastro e fica em `contrato["data_admissao"]`, no formato DD/MM/AAAA. Pode ser corrigida pelo administrador na edição (opção 7), com validação e confirmação. Não pode anteceder o nascimento nem ficar depois de uma escala existente. A função `obter_data_admissao()` devolve um objeto `date` para os futuros cálculos. Ela não calcula direitos: regras e valores de 13º, férias e outros benefícios ainda serão implementados. Não criamos uma segunda data de início para representar o mesmo vínculo.

O armazenamento continua em pickle nesta etapa; a escolha e a migração para um banco de dados serão discutidas depois.
