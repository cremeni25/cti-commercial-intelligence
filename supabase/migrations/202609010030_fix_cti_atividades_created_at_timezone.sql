-- Corrige a semântica temporal de cti_atividades.created_at.
-- O campo histórico foi criado como timestamp without time zone, porém os valores
-- foram gravados em UTC. O frontend interpretava esses valores como hora local,
-- deslocando a criação em +3h no Brasil e podendo fazê-la parecer posterior ao
-- encerramento (concluida_em, que já é timestamptz).
--
-- Esta migração NÃO altera o instante real registrado: apenas explicita que o
-- timestamp existente representa UTC.

alter table public.cti_atividades
  alter column created_at type timestamptz
  using created_at at time zone 'UTC';
