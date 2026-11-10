-- Dados principais são relacionais. Configurações variáveis usam JSON.
CREATE TABLE IF NOT EXISTS administradores (
    usuario TEXT PRIMARY KEY COLLATE NOCASE,
    senha TEXT NOT NULL CHECK(json_valid(senha))
);
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY CHECK(id > 0),
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    data_nascimento TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ativo', 'inativo')),
    senha TEXT CHECK(senha IS NULL OR json_valid(senha))
);
CREATE TABLE IF NOT EXISTS contratos (
    funcionario_id INTEGER PRIMARY KEY REFERENCES funcionarios(id) ON DELETE CASCADE,
    cargo TEXT NOT NULL,
    salario REAL NOT NULL CHECK(salario > 0),
    carga REAL NOT NULL CHECK(carga > 0),
    regime TEXT NOT NULL,
    jornada TEXT NOT NULL,
    data_admissao TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS escalas (
    id INTEGER PRIMARY KEY,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    tipo TEXT NOT NULL,
    empresa TEXT NOT NULL,
    categoria TEXT NOT NULL,
    carga_semanal REAL NOT NULL,
    configuracao TEXT NOT NULL CHECK(json_valid(configuracao))
);
CREATE TABLE IF NOT EXISTS ajustes_escala (
    id INTEGER PRIMARY KEY,
    escala_id INTEGER NOT NULL REFERENCES escalas(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    turno TEXT NOT NULL CHECK(json_valid(turno)),
    motivo TEXT NOT NULL,
    registrado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jornadas (
    id INTEGER PRIMARY KEY,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    status TEXT NOT NULL,
    entrada TEXT NOT NULL,
    saida TEXT NOT NULL,
    intervalo INTEGER NOT NULL CHECK(intervalo >= 0),
    saida_intervalo TEXT NOT NULL,
    volta_intervalo TEXT NOT NULL,
    observacao TEXT NOT NULL,
    UNIQUE(funcionario_id, data)
);
CREATE TABLE IF NOT EXISTS regras (
    versao INTEGER PRIMARY KEY,
    empresa TEXT NOT NULL,
    categoria TEXT NOT NULL,
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    fonte TEXT NOT NULL,
    parametros TEXT NOT NULL CHECK(json_valid(parametros))
);
CREATE INDEX IF NOT EXISTS escalas_funcionario ON escalas(funcionario_id);
CREATE INDEX IF NOT EXISTS regras_grupo ON regras(empresa, categoria);
PRAGMA user_version = 1;
