import test from 'node:test'
import assert from 'node:assert/strict'
import { diaLocalCrm, ocorreuNoDiaCrm, registrosResumoCrm } from '../../frontend/src/services/crm-resumo.ts'

process.env.TZ = 'America/Sao_Paulo'

test('dia comercial brasileiro permanece correto depois de 21h', () => {
  const agora = new Date('2026-10-26T01:30:00Z')
  assert.equal(diaLocalCrm(agora), '2026-10-25')
  assert.equal(ocorreuNoDiaCrm('2026-10-25', agora), true)
  assert.equal(ocorreuNoDiaCrm('2026-10-26T01:00:00Z', agora), true)
  assert.equal(ocorreuNoDiaCrm('2026-10-26T03:01:00Z', agora), false)
  assert.equal(ocorreuNoDiaCrm('', agora), false)
  assert.equal(ocorreuNoDiaCrm('data inválida', agora), false)
})

test('zero só pode resultar de uma lista válida e vazia', () => {
  for (const payload of [null, undefined, {}, { detail: 'indisponível' }, 'erro']) {
    assert.throws(() => registrosResumoCrm(payload))
  }
  assert.deepEqual(registrosResumoCrm([]), [])
  assert.deepEqual(registrosResumoCrm({itens: []}), [])
  for (const chave of ['dados', 'itens', 'oportunidades', 'resultado', 'atividades', 'clientes', 'propostas', 'pedidos', 'vendas']) {
    assert.deepEqual(registrosResumoCrm({[chave]: [{id: 'real'}]}), [{id: 'real'}])
  }
})
