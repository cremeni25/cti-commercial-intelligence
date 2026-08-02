"use client"

import { useEffect } from "react"

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return

    const register = async () => {
      try {
        const registros = await navigator.serviceWorker.getRegistrations()
        await Promise.all(
          registros
            .filter((registro) => registro.scope.endsWith("/"))
            .map((registro) => registro.unregister()),
        )
        await navigator.serviceWorker.register("/sw.js", { scope: "/crm-app/" })
      } catch (error) {
        console.error("Falha ao registrar PWA CTI CRM:", error)
      }
    }

    void register()
  }, [])

  return null
}
