insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'documentos-comerciais-cti',
  'documentos-comerciais-cti',
  false,
  10485760,
  array['application/vnd.openxmlformats-officedocument.wordprocessingml.document']::text[]
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
