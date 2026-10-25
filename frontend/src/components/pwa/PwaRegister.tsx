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
            .filter((registro) => [`${window.location.origin}/`].includes(registro.scope) && [registro.active, registro.waiting, registro.installing].some(worker => worker?.scriptURL === `${window.location.origin}/sw.js`))
            .map((registro) => registro.unregister()),
        )
        const registration = await navigator.serviceWorker.register("/sw.js", { scope: "/crm-app", updateViaCache: "none" })
        await registration.update()
        if (registration.waiting) registration.waiting.postMessage({ type: "SKIP_WAITING" })
      } catch (error) {
        console.error("Falha ao registrar PWA CTI CRM:", error)
      }
    }

    void register()
  }, [])

  return null
}
