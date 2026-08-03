begin;

alter table public.cti_users
  add column if not exists gestor_responsavel text;

update public.cti_users u
set gestor_responsavel = coalesce(u.gestor_responsavel, gestor.nome)
from public.cti_users gestor
where u.superior_id = gestor.id
  and (u.gestor_responsavel is null or trim(u.gestor_responsavel) = '');

commit;
