-- Sequência 1 de 6 — Banco / Modelagem definitiva
-- Consolida chaves estrangeiras do núcleo operacional já existentes de fato no banco.
-- Política de exclusão permanece NO ACTION (padrão) para evitar cascatas destrutivas.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_oportunidades_cliente_id_fkey') THEN
    ALTER TABLE public.cti_oportunidades
      ADD CONSTRAINT cti_oportunidades_cliente_id_fkey
      FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_oportunidades_responsavel_id_fkey') THEN
    ALTER TABLE public.cti_oportunidades
      ADD CONSTRAINT cti_oportunidades_responsavel_id_fkey
      FOREIGN KEY (responsavel_id) REFERENCES public.cti_users(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_propostas_cliente_id_fkey') THEN
    ALTER TABLE public.cti_propostas
      ADD CONSTRAINT cti_propostas_cliente_id_fkey
      FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_propostas_oportunidade_id_fkey') THEN
    ALTER TABLE public.cti_propostas
      ADD CONSTRAINT cti_propostas_oportunidade_id_fkey
      FOREIGN KEY (oportunidade_id) REFERENCES public.cti_oportunidades(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_pedidos_cliente_id_fkey') THEN
    ALTER TABLE public.cti_pedidos
      ADD CONSTRAINT cti_pedidos_cliente_id_fkey
      FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_pedidos_proposta_id_fkey') THEN
    ALTER TABLE public.cti_pedidos
      ADD CONSTRAINT cti_pedidos_proposta_id_fkey
      FOREIGN KEY (proposta_id) REFERENCES public.cti_propostas(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_atividades_cliente_id_fkey') THEN
    ALTER TABLE public.cti_atividades
      ADD CONSTRAINT cti_atividades_cliente_id_fkey
      FOREIGN KEY (cliente_id) REFERENCES public.clientes(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_atividades_oportunidade_id_fkey') THEN
    ALTER TABLE public.cti_atividades
      ADD CONSTRAINT cti_atividades_oportunidade_id_fkey
      FOREIGN KEY (oportunidade_id) REFERENCES public.cti_oportunidades(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_atividades_proposta_id_fkey') THEN
    ALTER TABLE public.cti_atividades
      ADD CONSTRAINT cti_atividades_proposta_id_fkey
      FOREIGN KEY (proposta_id) REFERENCES public.cti_propostas(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_atividades_pedido_id_fkey') THEN
    ALTER TABLE public.cti_atividades
      ADD CONSTRAINT cti_atividades_pedido_id_fkey
      FOREIGN KEY (pedido_id) REFERENCES public.cti_pedidos(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_atividades_usuario_id_fkey') THEN
    ALTER TABLE public.cti_atividades
      ADD CONSTRAINT cti_atividades_usuario_id_fkey
      FOREIGN KEY (usuario_id) REFERENCES public.cti_users(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_ia_conversas_usuario_id_fkey') THEN
    ALTER TABLE public.cti_ia_conversas
      ADD CONSTRAINT cti_ia_conversas_usuario_id_fkey
      FOREIGN KEY (usuario_id) REFERENCES public.cti_users(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_ia_mensagens_usuario_id_fkey') THEN
    ALTER TABLE public.cti_ia_mensagens
      ADD CONSTRAINT cti_ia_mensagens_usuario_id_fkey
      FOREIGN KEY (usuario_id) REFERENCES public.cti_users(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_ia_auditoria_conversa_id_fkey') THEN
    ALTER TABLE public.cti_ia_auditoria
      ADD CONSTRAINT cti_ia_auditoria_conversa_id_fkey
      FOREIGN KEY (conversa_id) REFERENCES public.cti_ia_conversas(id);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'cti_ia_auditoria_usuario_id_fkey') THEN
    ALTER TABLE public.cti_ia_auditoria
      ADD CONSTRAINT cti_ia_auditoria_usuario_id_fkey
      FOREIGN KEY (usuario_id) REFERENCES public.cti_users(id);
  END IF;
END $$;
