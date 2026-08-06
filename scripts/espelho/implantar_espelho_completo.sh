#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EXPORTAR="$ROOT_DIR/scripts/espelho/exportar_estado_real.sh"
VALIDAR="$ROOT_DIR/scripts/espelho/validar_fidelidade.sh"
AREA_IA="$ROOT_DIR/backend/migrations/homologacao/20260806_area_ia_homologacao.sql"
VINCULO_MASTER="$ROOT_DIR/backend/migrations/homologacao/20260806_vincular_admin_master_espelho.sql"

: "${CTI_PRODUCAO_DATABASE_URL:?Defina CTI_PRODUCAO_DATABASE_URL com credencial exclusivamente de leitura.}"
: "${CTI_HOMOLOGACAO_DATABASE_URL:?Defina CTI_HOMOLOGACAO_DATABASE_URL do projeto espelho.}"
: "${CTI_HOMOLOGACAO_PROJECT_REF:?Defina CTI_HOMOLOGACAO_PROJECT_REF.}"

EXPECTED_REF="xhrikmksydsyalxkkyot"
if [[ "$CTI_HOMOLOGACAO_PROJECT_REF" != "$EXPECTED_REF" ]]; then
  echo "BLOQUEADO: destino não corresponde ao Supabase espelho autorizado ($EXPECTED_REF)." >&2
  exit 40
fi

for arquivo in "$EXPORTAR" "$VALIDAR" "$AREA_IA" "$VINCULO_MASTER"; do
  [[ -f "$arquivo" ]] || { echo "BLOQUEADO: arquivo obrigatório ausente: $arquivo" >&2; exit 41; }
done

if [[ "$CTI_PRODUCAO_DATABASE_URL" == "$CTI_HOMOLOGACAO_DATABASE_URL" ]]; then
  echo "BLOQUEADO: origem e destino são iguais." >&2
  exit 42
fi

printf '\n[1/5] Espelhando schema public e dados reais...\n'
bash "$EXPORTAR"

printf '\n[2/5] Validando fidelidade do public antes das extensões da IA...\n'
bash "$VALIDAR"

printf '\n[3/5] Criando schema isolado ia_homologacao...\n'
psql "$CTI_HOMOLOGACAO_DATABASE_URL" --set ON_ERROR_STOP=on --file="$AREA_IA"

printf '\n[4/5] Validando que o public permaneceu fiel após a área da IA...\n'
bash "$VALIDAR"

printf '\n[5/5] Preparação do vínculo ADMIN_MASTER...\n'
printf 'O vínculo exige que o usuário já exista no Supabase Auth do espelho.\n'
printf 'Execute o arquivo abaixo somente após criar esse usuário pelo Dashboard:\n%s\n' "$VINCULO_MASTER"

printf '\nPACOTE TÉCNICO CONCLUÍDO.\n'
printf 'Nenhuma escrita foi realizada no banco operacional.\n'
printf 'O schema public foi espelhado e validado; a IA foi criada em schema separado.\n'
