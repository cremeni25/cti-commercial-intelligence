#!/usr/bin/env bash
set -euo pipefail

: "${CTI_PRODUCAO_DATABASE_URL:?Defina CTI_PRODUCAO_DATABASE_URL com credencial exclusivamente de leitura.}"
: "${CTI_HOMOLOGACAO_DATABASE_URL:?Defina CTI_HOMOLOGACAO_DATABASE_URL com a conexão do Supabase espelho.}"
: "${CTI_HOMOLOGACAO_PROJECT_REF:?Defina o project ref esperado do Supabase espelho.}"

EXPECTED_PROJECT_REF="xhrikmksydsyalxkkyot"
if [[ "$CTI_HOMOLOGACAO_PROJECT_REF" != "$EXPECTED_PROJECT_REF" ]]; then
  printf 'ERRO: project ref de destino não autorizado: %s\n' "$CTI_HOMOLOGACAO_PROJECT_REF" >&2
  exit 10
fi

if [[ "$CTI_PRODUCAO_DATABASE_URL" == "$CTI_HOMOLOGACAO_DATABASE_URL" ]]; then
  printf 'ERRO: origem e destino são iguais. Operação interrompida.\n' >&2
  exit 11
fi

if [[ "$CTI_HOMOLOGACAO_DATABASE_URL" != *"$EXPECTED_PROJECT_REF"* ]]; then
  printf 'ERRO: a URL de destino não contém o project ref autorizado.\n' >&2
  exit 12
fi

OUT_DIR="${OUT_DIR:-./artefatos-espelho}"
mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

SCHEMA_FILE="$OUT_DIR/cti_public_schema.sql"
DATA_FILE="$OUT_DIR/cti_public_data.dump"
MANIFEST_FILE="$OUT_DIR/manifesto.sha256"

# O destino deve estar vazio. A verificação impede restauração sobre outro sistema.
existing_tables="$(psql "$CTI_HOMOLOGACAO_DATABASE_URL" -Atc "select count(*) from pg_tables where schemaname='public';")"
if [[ "$existing_tables" != "0" ]]; then
  printf 'ERRO: o schema public do espelho contém %s tabela(s). Nenhuma restauração foi executada.\n' "$existing_tables" >&2
  exit 13
fi

# Extrai o estado real do schema public. Migrations históricas não são a fonte final.
pg_dump "$CTI_PRODUCAO_DATABASE_URL" \
  --schema=public \
  --schema-only \
  --no-owner \
  --no-privileges \
  --quote-all-identifiers \
  --file="$SCHEMA_FILE"

# Copia somente dados do schema public. auth, storage e secrets não são exportados.
pg_dump "$CTI_PRODUCAO_DATABASE_URL" \
  --schema=public \
  --data-only \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="$DATA_FILE"

chmod 600 "$SCHEMA_FILE" "$DATA_FILE"
sha256sum "$SCHEMA_FILE" "$DATA_FILE" > "$MANIFEST_FILE"
chmod 600 "$MANIFEST_FILE"

# Restauração ocorre exclusivamente no project ref autorizado.
psql "$CTI_HOMOLOGACAO_DATABASE_URL" --set ON_ERROR_STOP=on --single-transaction --file="$SCHEMA_FILE"
pg_restore \
  --dbname="$CTI_HOMOLOGACAO_DATABASE_URL" \
  --data-only \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  "$DATA_FILE"

printf 'Espelho restaurado a partir do estado real do schema public.\n'
printf 'Destino autorizado: %s\n' "$EXPECTED_PROJECT_REF"
printf 'Artefatos protegidos em: %s\n' "$OUT_DIR"
