"""Navegação web supervisionada. Não envia formulários nem executa JavaScript arbitrário."""
import ipaddress
import os
import socket
from urllib.parse import urlparse


def validar_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Apenas endereços HTTPS públicos são permitidos")
    host = parsed.hostname.lower().rstrip(".")
    dominios = [d.strip().lower() for d in os.getenv("ASHLEY_BROWSER_ALLOWED_DOMAINS", "").split(",") if d.strip()]
    if not dominios or not any(host == d or host.endswith("." + d) for d in dominios):
        raise ValueError("Domínio não autorizado; configure ASHLEY_BROWSER_ALLOWED_DOMAINS")
    if host == "localhost" or host.endswith(".local"):
        raise ValueError("Endereço interno bloqueado")
    for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        endereco = ipaddress.ip_address(item[4][0])
        if not endereco.is_global:
            raise ValueError("Endereço privado ou reservado bloqueado")
    return url


async def consultar_pagina(url: str) -> dict:
    """Inspeciona texto e título de um site autorizado; sem cookies persistidos."""
    validar_url(url)
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        cdp = os.getenv("ASHLEY_BROWSER_CDP_URL", "")
        if cdp:
            browser = await p.chromium.connect_over_cdp(cdp, timeout=15000)
            context = await browser.new_context(accept_downloads=False)
        else:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=False)
        try:
            # Bloqueia redirecionamentos para domínios não autorizados e rede interna.
            async def filtrar(route):
                try:
                    validar_url(route.request.url)
                except (ValueError, OSError):
                    await route.abort()
                    return
                await route.continue_()
            await context.route("**/*", filtrar)
            page = await context.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            return {"url": page.url, "titulo": (await page.title())[:250],
                    "texto": (await page.locator("body").inner_text(timeout=10000))[:12000],
                    "status_http": response.status if response else None,
                    "modo": "consulta_sem_envio"}
        finally:
            await context.close()
            await browser.close()
