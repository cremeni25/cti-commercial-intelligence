#!/usr/bin/env bash
set -euo pipefail

: "${CTI_PRODUCAO_DATABASE_URL:?Defina CTI_PRODUCAO_DATABASE_URL.}"
: "${CTI_HOMOLOGACAO_DATABASE_URL:?Defina CTI_HOMOLOGACAO_DATABASE_URL.}"
: "${CTI_HOMOLOGACAO_PROJECT_REF:?Defina o project ref do espelho.}"

EXPECTED_PROJECT_REF="xhrikmksydsyalxkkyot"
if [[ "$CTI_HOMOLOGACAO_PROJECT_REF" != "$EXPECTED_PROJECT_REF" ]] || [[ "$CTI_HOMOLOGACAO_DATABASE_URL" != *"$EXPECTED_PROJECT_REF"* ]]; then
  printf 'ERRO: destino de homologação não autorizado.\n' >&2
  exit 20
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PROD_SCHEMA="$TMP_DIR/producao_schema.txt"
HOMO_SCHEMA="$TMP_DIR/homologacao_schema.txt"
PROD_OBJECTS="$TMP_DIR/producao_objects.txt"
HOMO_OBJECTS="$TMP_DIR/homologacao_objects.txt"
PROD_COUNTS="$TMP_DIR/producao_counts.txt"
HOMO_COUNTS="$TMP_DIR/homologacao_counts.txt"

schema_query="
select table_name || '|' || column_name || '|' || data_type || '|' || udt_name || '|' || is_nullable || '|' || coalesce(column_default,'')
from information_schema.columns
where table_schema = 'public'
order by table_name, ordinal_position;
"

objects_query="
select 'TABLE|' || tablename from pg_tables where schemaname='public'
union all
select 'VIEW|' || viewname from pg_views where schemaname='public'
union all
select 'SEQUENCE|' || sequencename from pg_sequences where schemaname='public'
union all
select 'FUNCTION|' || p.proname || '|' || pg_get_function_identity_arguments(p.oid)
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public'
union all
select 'POLICY|' || tablename || '|' || policyname || '|' || cmd || '|' || coalesce(qual,'') || '|' || coalesce(with_check,'')
from pg_policies where schemaname='public'
order by 1;
"

psql "$CTI_PRODUCAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$schema_query" > "$PROD_SCHEMA"
psql "$CTI_HOMOLOGACAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$schema_query" > "$HOMO_SCHEMA"
diff -u "$PROD_SCHEMA" "$HOMO_SCHEMA"

psql "$CTI_PRODUCAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$objects_query" > "$PROD_OBJECTS"
psql "$CTI_HOMOLOGACAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$objects_query" > "$HOMO_OBJECTS"
diff -u "$PROD_OBJECTS" "$HOMO_OBJECTS"

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

psql "$CTI_PRODUCAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$count_query" | psql "$CTI_PRODUCAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -AtF '|' > "$PROD_COUNTS"
psql "$CTI_HOMOLOGACAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atc "$count_query" | psql "$CTI_HOMOLOGACAO_DATABASE_URL" -X -v ON_ERROR_STOP=1 -AtF '|' > "$HOMO_COUNTS"
diff -u "$PROD_COUNTS" "$HOMO_COUNTS"

printf 'Validação concluída: estrutura, objetos, políticas e contagens do schema public são equivalentes.\n'
