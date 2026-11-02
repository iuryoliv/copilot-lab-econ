PRAGMA foreign_keys = ON;
CREATE TABLE fontes (
  id_fonte INTEGER PRIMARY KEY,
  nome TEXT NOT NULL UNIQUE,
  url TEXT NOT NULL,
  condicoes TEXT NOT NULL
);
CREATE TABLE series (
  codigo_serie TEXT PRIMARY KEY,
  id_fonte INTEGER NOT NULL REFERENCES fontes,
  nome TEXT NOT NULL,
  unidade TEXT NOT NULL,
  frequencia TEXT NOT NULL CHECK (frequencia = 'M'),
  tema TEXT NOT NULL
);
CREATE TABLE cargas (
  id_carga INTEGER PRIMARY KEY,
  codigo_serie TEXT NOT NULL REFERENCES series,
  origem TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  extraido_em TEXT NOT NULL,
  executado_em TEXT NOT NULL,
  linhas INTEGER NOT NULL CHECK(linhas > 0),
  status TEXT NOT NULL CHECK(status = 'ok'),
  ator TEXT NOT NULL,
  UNIQUE(codigo_serie, sha256)
);
CREATE TABLE observacoes (
  codigo_serie TEXT NOT NULL REFERENCES series,
  data_ref TEXT NOT NULL CHECK(length(data_ref)=10 AND substr(data_ref,9,2)='01'),
  valor REAL NOT NULL,
  id_carga INTEGER NOT NULL REFERENCES cargas,
  PRIMARY KEY(codigo_serie, data_ref)
);
CREATE TABLE metadados (
  codigo_serie TEXT NOT NULL REFERENCES series,
  chave TEXT NOT NULL,
  valor TEXT NOT NULL,
  PRIMARY KEY(codigo_serie, chave)
);
CREATE TABLE autorizacoes (
  proposta TEXT PRIMARY KEY,
  ator TEXT NOT NULL,
  expira_em REAL NOT NULL,
  consumida INTEGER NOT NULL DEFAULT 0 CHECK(consumida IN (0,1))
);
CREATE VIEW vw_ultima_observacao AS
SELECT o.* FROM observacoes o
WHERE o.data_ref = (SELECT MAX(p.data_ref) FROM observacoes p
                   WHERE p.codigo_serie=o.codigo_serie);
