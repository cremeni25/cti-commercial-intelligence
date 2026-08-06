#!/usr/bin/env bash
set -euo pipefail

: "${CTI_PRODUCAO_DATABASE_URL:?Defina CTI_PRODUCAO_DATABASE_URL.}"
: "${CTI_HOMOLOGACAO_DATABASE_URL:?Defina CTI_HOMOLOGACAO_DATABASE_URL.}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PROD_SCHEMA="$TMP_DIR/producao_schema.txt"
HOMO_SCHEMA="$TMP_DIR/homologacao_schema.txt"
PROD_COUNTS="$TMP_DIR/producao_counts.txt"
HOMO_COUNTS="$TMP_DIR/homologacao_counts.txt"

schema_query="
select table_name || '|' || column_name || '|' || data_type || '|' || is_nullable || '|' || coalesce(column_default,'')
from information_schema.columns
where table_schema = 'public'
order by table_name, ordinal_position;
"

psql "$CTI_PRODUCAO_DATABASE_URL" -Atc "$schema_query" > "$PROD_SCHEMA"
psql "$CTI_HOMOLOGACAO_DATABASE_URL" -Atc "$schema_query" > "$HOMO_SCHEMA"

diff -u "$PROD_SCHEMA" "$HOMO_SCHEMA"

count_query="
select format(
  'select %L as tabela, count(*)::bigint as total from public.%I;',
  tablename,
  tablename
)
from pg_tables
where schemaname = 'public'
order by tablename;
"

psql "$CTI_PRODUCAO_DATABASE_URL" -Atc "$count_query" | psql "$CTI_PRODUCAO_DATABASE_URL" -AtF '|' > "$PROD_COUNTS"
psql "$CTI_HOMOLOGACAO_DATABASE_URL" -Atc "$count_query" | psql "$CTI_HOMOLOGACAO_DATABASE_URL" -AtF '|' > "$HOMO_COUNTS"

diff -u "$PROD_COUNTS" "$HOMO_COUNTS"

printf 'Validação concluída: colunas e contagens do schema public são equivalentes.\n'
