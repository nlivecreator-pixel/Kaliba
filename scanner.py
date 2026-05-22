import asyncio
import time
import random
import sys
import os
import subprocess
import msvcrt
import base64
import threading
import re
import json
from typing import Optional

import aiohttp
from aiohttp import web
from aiohttp_socks import ProxyConnector

from uxheadset.kalibraux import (
    console,
    banner,
    farewell,
    info,
    success,
    danger,
    warning,
    section,
    field,
    ProgressBar,
    Colors,
    separator,
)


# ── Suppress asyncio ProactorBasePipeTransport error spam ──
if sys.platform == "win32":
    from asyncio.proactor_events import _ProactorBasePipeTransport

    _original_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

    def _patched_call_connection_lost(self, exc):
        """Silence ConnectionResetError spam on Windows ProactorEventLoop."""
        if exc is not None and isinstance(exc, ConnectionResetError):
            return
        try:
            _original_call_connection_lost(self, exc)
        except ConnectionResetError:
            pass

    _ProactorBasePipeTransport._call_connection_lost = _patched_call_connection_lost


PROTOCOL_SOURCES = {
    "Http/Socks5": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    ],
    "Vless": [
        "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt",
    ],
    "Hysteria": [
        "https://raw.githubusercontent.com/hysteria-lists/hysteria/main/hysteria.txt",
    ],
}



TIMEOUT = 10
MAX_PROXIES = 1500


def detect_proxy_type(proxy: str) -> str:
    """Detect proxy type from URL patterns or common conventions."""
    p = proxy.lower()
    if p.startswith("vless://"):
        return "VLESS"
    if p.startswith("hysteria://"):
        return "HYSTERIA"
    if p.startswith("socks5://"):
        return "SOCKS5"
    if p.startswith("socks4://"):
        return "SOCKS4"
    if p.startswith("http://") or p.startswith("https://"):
        return "HTTP"
    # Default assumption for raw host:port from public lists
    return "HTTP"

def is_valid_vless_uuid(proxy: str) -> bool:
    """Verify if the Vless config contains a valid UUID."""
    if not proxy.startswith("vless://"):
        return False
    # Vless format: vless://uuid@host:port...
    # UUID regex: 8-4-4-4-12 hex characters
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, proxy, re.IGNORECASE)
    return match is not None


def normalize_proxy(proxy: str) -> str:
    """Strip protocol prefix or parse host:port from VLESS/Hysteria configs."""
    p = proxy.lower()
    if p.startswith("vless://") or p.startswith("hysteria://"):
        # Format: protocol://uuid@host:port?query#fragment
        try:
            # Remove protocol
            content = p.split("://", 1)[1]
            # Get host:port (part before '?' or '#')
            address_part = content.split("?", 1)[0].split("#", 1)[0]
            # Remove uuid if present
            if "@" in address_part:
                address_part = address_part.split("@", 1)[1]
            return address_part
        except Exception:
            return proxy
            
    for prefix in ("http://", "https://", "socks5://", "socks4://"):
        if p.startswith(prefix):
            return proxy[len(prefix):]
    return proxy


async def fetch_proxies(session: aiohttp.ClientSession, url: str) -> list[str]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
            proxies = []
            for line in text.strip().splitlines():
                line = line.strip()
                if line and ":" in line:
                    proxies.append(line.strip())
            return proxies
    except Exception:
        return []


def select_speed_test_mode() -> int:
    options = [
        "50 proxies (Testing)",
        "250 proxies",
        "500 proxies",
        "1000 proxies",
        "Full scan (No limit)"
    ]
    current = 0
    
    while True:
        console.print()
        section("SPEED TEST")
        for i, opt in enumerate(options):
            marker = "[cyan]●[/]" if i == current else "[dim]○[/]"
            console.print(f"  {marker} {opt}")
        console.print("\n  [dim](Use ↑/↓ arrows and Enter to select)[/]")
        
        lines_to_clear = len(options) + 6
        key = msvcrt.getch()
        
        for _ in range(lines_to_clear):
            sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()

        if key == b'\xe0': 
            key = msvcrt.getch()
            if key == b'H': current = (current - 1) % len(options)
            elif key == b'P': current = (current + 1) % len(options)
        elif key == b'\r': 
            return [50, 250, 500, 1000, 1500][current]

def select_protocol() -> str:
    protocols = list(PROTOCOL_SOURCES.keys())
    current = 0
    
    while True:
        console.print()
        section("SELECT PROTOCOL")
        for i, p in enumerate(protocols):
            marker = "[cyan]●[/]" if i == current else "[dim]○[/]"
            console.print(f"  {marker} {p}")
        console.print("\n  [dim](Use ↑/↓ arrows and Enter to select)[/]")
        
        lines_to_clear = len(protocols) + 6
        key = msvcrt.getch()
        
        for _ in range(lines_to_clear):
            sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()

        if key == b'\xe0': 
            key = msvcrt.getch()
            if key == b'H': current = (current - 1) % len(protocols)
            elif key == b'P': current = (current + 1) % len(protocols)
        elif key == b'\r': 
            return protocols[current]

async def gather_proxies(protocol: str) -> list[str]:
    seen: set[str] = set()
    all_proxies: list[str] = []
    sources = PROTOCOL_SOURCES.get(protocol, [])

    section("FETCHING PROXIES")
    info(f"Protocol: [{Colors.ACCENT}]{protocol}[/]")
    info(f"Sources: {len(sources)}")
    separator()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_proxies(session, url) for url in sources]
        results = await asyncio.gather(*tasks)

    total = 0
    for i, (url, proxies) in enumerate(zip(sources, results)):
        source_name = url.rsplit("/", 2)[-2]
        console.print(f"  [{Colors.ACCENT}]{source_name}[/] — [{Colors.YELLOW}]{len(proxies)}[/] proxies")
        total += len(proxies)
        for p in proxies:
            if p not in seen:
                seen.add(p)
                all_proxies.append(p)
                if len(all_proxies) >= MAX_PROXIES:
                    break
        if len(all_proxies) >= MAX_PROXIES:
            break

    random.shuffle(all_proxies)
    all_proxies = all_proxies[:MAX_PROXIES]

    console.print()
    success(f"Fetched [{Colors.YELLOW}]{len(all_proxies)}[/] unique proxies from {len(sources)} sources")
    console.print()
    return all_proxies


async def verify_vless_with_xray(proxy: str, timeout: int = 10) -> bool:
    """Truly verify a VLESS proxy using the xray binary."""
    try:
        # Extract UUID, Host, Port from vless://uuid@host:port...
        p = proxy.lower()
        content = p.split("://", 1)[1]
        address_part = content.split("?", 1)[0].split("#", 1)[0]
        uuid = ""
        host_port = ""
        if "@" in address_part:
            uuid, host_port = address_part.split("@", 1)
        else:
            # Fallback if uuid is missing (though it's required for VLESS)
            return False
        
        host, port = host_port.split(":", 1)
        
        # Use a random local port for the SOCKS inbound to avoid collisions
        local_port = random.randint(10000, 60000)
        config = {
            "inbounds": [{
                "port": local_port,
                "protocol": "socks",
                "settings": { "auth": "noauth" }
            }],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": host,
                        "port": int(port),
                        "users": [{ "id": uuid, "encryption": "none" }]
                    }]
                }
            }],
            "log": { "loglevel": "none" }
        }
        
        config_path = os.path.abspath(f"temp_xray_{local_port}.json")
        with open(config_path, "w") as f:
            json.dump(config, f)
            
        # Start Xray
        # Use absolute path for config
        # Redirect stderr to a separate file to catch why it fails
        err_log = f"xray_err_{local_port}.log"
        with open(err_log, "w") as ef:
            process = subprocess.Popen(
                ["xray", "-config", config_path],
                stdout=subprocess.DEVNULL,
                stderr=ef,
                text=True
            )
        
        try:
            # Give Xray a moment to start
            await asyncio.sleep(2) # Increased to 2 seconds to be safe
            
            # Check if process is still running
            if process.poll() is not None:
                # Log error for debugging
                with open("xray_debug.log", "a") as f:
                    with open(err_log, "r") as ef:
                        err_content = ef.read()
                        f.write(f"Xray failed (port {local_port}): {err_content}\n")
                return False
            
            # Try to connect to google via the local SOCKS proxy
            connector = ProxyConnector.from_url(f"socks5://127.0.0.1:{local_port}")
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get("https://www.google.com", timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status == 200:
                        return True
                    else:
                        with open("xray_debug.log", "a") as f:
                            f.write(f"Connection status: {resp.status}\n")
        except Exception as e:
            with open("xray_debug.log", "a") as f:
                f.write(f"Exception: {e}\n")
            pass
        finally:
            process.terminate()
            # Wait a bit for process to die
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Clean up config file
            if os.path.exists(config_path):
                os.remove(config_path)

            process.terminate()
            # Wait a bit for process to die
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            if os.path.exists(config_path):
                os.remove(config_path)
                
    except Exception:
        pass
    return False


async def check_proxy(
    proxy: str,
    timeout: int = TIMEOUT,
) -> Optional[dict]:
    start = time.monotonic()
    proxy_type = detect_proxy_type(proxy)
    proxy_clean = normalize_proxy(proxy)

    # Truly verify VLESS using Xray binary
    if proxy_type == "VLESS":
        if await verify_vless_with_xray(proxy, timeout):
            elapsed = round((time.monotonic() - start) * 1000)
            return {
                "proxy": proxy,
                "clean": proxy_clean,
                "type": proxy_type,
                "ms": elapsed,
                "status": "online"
            }
        return None

    # If it's HYSTERIA, do a simple TCP port check (since Xray support for Hysteria 2 is separate)
    if proxy_type == "HYSTERIA":
        try:
            host, port = proxy_clean.split(":", 1)
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, int(port)), 
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            
            elapsed = round((time.monotonic() - start) * 1000)
            return {
                "proxy": proxy,
                "clean": proxy_clean,
                "type": proxy_type,
                "ms": elapsed,
                "status": "reachable"
            }
        except Exception:
            pass
        return None

    # For HTTP/SOCKS, perform a real request to google.com
    scheme_map = {
        "SOCKS5": "socks5",
        "SOCKS4": "socks4",
        "HTTP": "http"
    }
    scheme = scheme_map.get(proxy_type, "http")

    try:
        connector = ProxyConnector.from_url(f"{scheme}://{proxy_clean}")
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                "https://www.google.com",
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
            ) as resp:
                if resp.status == 200:
                    elapsed = round((time.monotonic() - start) * 1000)
                    return {
                        "proxy": proxy,
                        "clean": proxy_clean,
                        "type": proxy_type,
                        "ms": elapsed,
                        "status": "online"
                    }
    except Exception:
        pass
    return None


async def scan_proxies(proxies: list[str]) -> list[dict]:
    results: list[dict] = []
    working: list[dict] = []
    console.print()

    with ProgressBar(total=len(proxies), prefix="Scanning proxies") as pb:
        sem = asyncio.Semaphore(50)

        async def worker(p: str):
            async with sem:
                result = await check_proxy(p)
                if result:
                    working.append(result)
                pb.update()
                return result

        tasks = [worker(p) for p in proxies]
        await asyncio.gather(*tasks)

    console.print()
    success(f"Scanned [{Colors.YELLOW}]{len(proxies)}[/] proxies")
    success(f"Working: [{Colors.GREEN}]{len(working)}[/]  Failed: [{Colors.RED}]{len(proxies) - len(working)}[/]")
    console.print()

    results = sorted(working, key=lambda x: x["ms"])
    return results


def show_results(results: list[dict]):
    section("WORKING PROXIES")

    if not results:
        danger("No working proxies found")
        return

    field("Total working", str(len(results)), Colors.OK)
    field("Fastest", f"{results[0]['proxy']} [{Colors.ACCENT}]{results[0]['ms']}ms[/]")
    field("Slowest", f"{results[-1]['proxy']} [{Colors.YELLOW}]{results[-1]['ms']}ms[/]")
    field("Average", f"{sum(r['ms'] for r in results) // len(results)}ms", Colors.HIGHLIGHT)
    separator()
    console.print()

    console.print(f"  [bold]{'PROXY':<25} {'TYPE':<8} {'LATENCY':<10} {'STATUS':<16}[/]")
    console.print(f"  [dim]{'─'*65}[/]")

    for i, r in enumerate(results, 1):
        ms_color = Colors.GREEN if r["ms"] < 2000 else (Colors.YELLOW if r["ms"] < 5000 else Colors.RED)
        type_color = Colors.CYAN if r["type"] == "SOCKS5" else (Colors.YELLOW if r["type"] == "SOCKS4" else Colors.ACCENT)
        
        # Handle potentially long Vless/Hysteria links
        display_proxy = r['proxy']
        if len(display_proxy) > 30:
            display_proxy = display_proxy[:27] + "..."
            
        console.print(
            f"  [{Colors.DIM}]{i:>3}.[/] "
            f"[{Colors.ACCENT}]{display_proxy:<30}[/] "
            f"[{type_color}]{r['type']:<8}[/] "
            f"[{ms_color}]{r['ms']:<5}ms[/]  "
            f"[{Colors.GREEN}]{r['status']:<16}[/]"
        )

    console.print()


async def subscription_handler(request):
    results = request.app.get('results', [])
    
    if not results:
        return web.Response(text="No working proxies found", status=404)
    
    lines = [r['proxy'].strip() for r in results]
    content = "\n".join(lines)
    
    if request.query.get('base64') == '1':
        b64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        return web.Response(text=b64_content, content_type='text/plain')
        
    return web.Response(text=content, content_type='text/plain')

def run_server_thread(results):
    """Runs the subscription server in a separate thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = web.Application()
    app['results'] = results
    app.router.add_get('/sub', subscription_handler)
    
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    try:
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        loop.run_until_complete(site.start())
    except Exception as e:
        # We can't use console.print easily here if it's not thread-safe, 
        # but kalibraux's console is generally okay for simple prints.
        print(f"Server Error: {e}")
    
    loop.run_forever()

async def start_subscription_server(results):
    # This function is now deprecated in favor of run_server_thread
    pass


def generate_telegram_links(results: list[dict]):
    filename = f"telegram_proxies_{int(time.time())}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for r in results:
            if r['type'] in ["SOCKS5", "SOCKS4"]:
                # tg://socks?server=host&port=port
                host, port = r['clean'].split(":", 1)
                f.write(f"tg://socks?server={host}&port={port}\n")
    success(f"Generated Telegram links in [{Colors.ACCENT}]{filename}[/]")
    console.print()

def show_menu(results: list[dict]):
    options = [
        "Save it in TXT",
        "Generate Telegram Links",
        "Start Subscription Server",
        "Exit"
    ]
    current = 0
    server_runner = None
    
    while True:
        console.print()
        section("OPTIONS")
        for i, opt in enumerate(options):
            marker = "[cyan]●[/]" if i == current else "[dim]○[/]"
            console.print(f"  {marker} {opt}")
        console.print("\n  [dim](Use ↑/↓ arrows and Enter to select)[/]")
        
        lines_to_clear = len(options) + 6
        key = msvcrt.getch()
        
        for _ in range(lines_to_clear):
            sys.stdout.write("\033[F\033[K")
        sys.stdout.flush()

        if key == b'\xe0': 
            key = msvcrt.getch()
            if key == b'H': current = (current - 1) % len(options)
            elif key == b'P': current = (current + 1) % len(options)
        elif key == b'\r': 
            choice = current
            if choice == 0:
                filename = f"proxies_{int(time.time())}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# Working proxies: {len(results)}\n\n")
                    for r in results:
                        f.write(f"{r['proxy']}\n")
                success(f"Exported {len(results)} proxies to [{Colors.ACCENT}]{filename}[/]")
                time.sleep(2)
            elif choice == 1:
                if results:
                    generate_telegram_links(results)
                else:
                    danger("No working proxies to generate links")
                time.sleep(2)
            elif choice == 2:
                if not results:
                    danger("No working proxies to host")
                    time.sleep(2)
                    continue
                
                try:
                    # Start server in a separate background thread to avoid blocking the CLI menu
                    threading.Thread(target=run_server_thread, args=(results,), daemon=True).start()
                    success("Subscription server started!")
                    # Try to get local IP for easier access
                    try:
                        import socket
                        local_ip = socket.gethostbyname(socket.gethostname())
                    except:
                        local_ip = "127.0.0.1"
                    
                    info(f"Local Link: http://{local_ip}:8080/sub")
                    info(f"Base64 Link: http://{local_ip}:8080/sub?base64=1")
                    warning("The server will run until you exit the program")
                    time.sleep(3)
                except Exception as e:
                    danger(f"Failed to start server: {e}")
                    time.sleep(2)
            elif choice == 3:
                break



def load_proxies_from_file(filepath: str) -> list[str]:
    """Load proxy list from a text file (for context menu integration)."""
    proxies = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and ":" in line:
                    proxies.append(line)
        info(f"Loaded {len(proxies)} proxies from [{Colors.ACCENT}]{filepath}[/]")
    except Exception as e:
        danger(f"Failed to load proxies from file: {e}")
    return proxies


async def main():
    banner(subtitle="Proxy Scanner")

    # Speed Test Selection
    max_proxies = select_speed_test_mode()
    global MAX_PROXIES
    MAX_PROXIES = max_proxies
    success(f"Speed test enabled (MAX_PROXIES = {MAX_PROXIES})")

    protocol = select_protocol()
    proxies = await gather_proxies(protocol)
    if not proxies:
        danger("Failed to fetch any proxies")
        return

    results = await scan_proxies(proxies)
    show_results(results)
    show_menu(results)

    farewell()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print()
        warning("Interrupted by user")
        console.print()
