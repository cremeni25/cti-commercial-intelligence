import { PGlite } from '@electric-sql/pglite'
import { readFileSync, writeFileSync } from 'node:fs'
import assert from 'node:assert/strict'
const db = new PGlite()
await db.exec('create role anon; create role authenticated; create role service_role bypassrls; create schema extensions; create schema auth; create table auth.users(id uuid primary key);')
// uuid-ossp is supplied by hosted Supabase; PGlite uses the built-in generator.
const baseline = readFileSync(new URL('./remote/production-schema-baseline.sql', import.meta.url),'utf8').replaceAll('uuid_generate_v4()', 'gen_random_uuid()')
await db.exec(baseline)
for (const migration of ['20261021101633_feiras_transacoes_isolamento.sql','20261021144323_feiras_edicao_idempotente.sql','20261021165000_feiras_provisionamento_defaults.sql']) {
 const sql = readFileSync(new URL('../../supabase/migrations/'+migration, import.meta.url),'utf8')
 await db.exec(sql)
 await db.exec(sql)
}
const results = await db.exec(readFileSync(new URL('./remote/real-database-regression.sql',import.meta.url),'utf8'))
const evidence = results.flatMap(r=>r.rows).find(r=>r.evidence)?.evidence
assert.equal(evidence?.checks_passed,13)
const remaining = await db.query('select count(*)::integer n from public.cti_users')
assert.equal(remaining.rows[0].n,0)
evidence.environment='PGlite with captured production schema; not remote Supabase capacity'
writeFileSync(new URL('./production-schema-results.json',import.meta.url),JSON.stringify(evidence,null,2)+'\n')
console.log(JSON.stringify(evidence,null,2))
await db.close()
