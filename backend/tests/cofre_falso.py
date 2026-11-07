"""Supabase Storage em memória para testar o cofre do agente sem rede."""
from types import SimpleNamespace


class _Bucket:
    def __init__(self, arquivos):
        self.arquivos = arquivos

    def download(self, caminho):
        if caminho not in self.arquivos:
            raise Exception("{'statusCode': 404, 'error': 'not_found', 'message': 'Object not found'}")
        return self.arquivos[caminho]

    def upload(self, caminho, conteudo, opcoes=None):
        if caminho in self.arquivos and str((opcoes or {}).get("upsert", "false")).lower() != "true":
            raise Exception("{'statusCode': 409, 'error': 'Duplicate', 'message': 'The resource already exists'}")
        self.arquivos[caminho] = bytes(conteudo)
        return SimpleNamespace(path=caminho)

    def list(self, pasta, opcoes=None):
        prefixo = pasta.rstrip("/") + "/"
        return [{"name": c[len(prefixo):]} for c in self.arquivos if c.startswith(prefixo) and "/" not in c[len(prefixo):]]


class StorageFalso:
    def __init__(self):
        self.buckets: dict[str, dict] = {}
        self.publicos: dict[str, bool] = {}

    def get_bucket(self, nome):
        if nome not in self.buckets:
            raise Exception("Bucket not found")
        return {"id": nome}

    def create_bucket(self, nome, options=None):
        self.buckets.setdefault(nome, {})
        self.publicos[nome] = bool((options or {}).get("public"))

    def from_(self, nome):
        return _Bucket(self.buckets.setdefault(nome, {}))


def instalar(monkeypatch):
    from services import cofre_agente, notificacoes_push

    storage = StorageFalso()
    monkeypatch.setattr(cofre_agente, "_supabase", lambda: SimpleNamespace(storage=storage))
    monkeypatch.setattr(cofre_agente, "_PROVISIONADO", False)
    monkeypatch.setattr(notificacoes_push, "_CHAVES_CACHE", None)
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    return storage
