#!/usr/bin/env bash
set -euo pipefail

: "${CTI_PRODUCAO_DATABASE_URL:?Defina CTI_PRODUCAO_DATABASE_URL com credencial de leitura do banco operacional.}"
: "${CTI_HOMOLOGACAO_DATABASE_URL:?Defina CTI_HOMOLOGACAO_DATABASE_URL com a conexão do Supabase espelho.}"

OUT_DIR="${OUT_DIR:-./artefatos-espelho}"
mkdir -p "$OUT_DIR"

SCHEMA_FILE="$OUT_DIR/cti_public_schema.sql"
DATA_FILE="$OUT_DIR/cti_public_data.dump"

# Extrai o estado real do schema public. Não usa migrations históricas como fonte final.
pg_dump "$CTI_PRODUCAO_DATABASE_URL" \
  --schema=public \
  --schema-only \
  --no-owner \
  --no-privileges \
  --quote-all-identifiers \
  --file="$SCHEMA_FILE"

# Copia os dados reais do schema public em formato customizado, sem tocar em auth/storage.
pg_dump "$CTI_PRODUCAO_DATABASE_URL" \
  --schema=public \
  --data-only \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file="$DATA_FILE"

# Restauração ocorre exclusivamente no banco espelho.
psql "$CTI_HOMOLOGACAO_DATABASE_URL" --set ON_ERROR_STOP=on --file="$SCHEMA_FILE"
pg_restore \
  --dbname="$CTI_HOMOLOGACAO_DATABASE_URL" \
  --data-only \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  "$DATA_FILE"

printf 'Espelho restaurado com esquema e dados reais do schema public.\n'
printf 'Arquivos gerados em: %s\n' "$OUT_DIR"
