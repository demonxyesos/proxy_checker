import aiohttp
import asyncio
from pathlib import Path
from typing import Literal

#КОнфигурация
INPUT_FILE = "input.txt"
OUTPUT_WORKING = "working.txt"
OUTPUT_DEAD = "dead.txt"
OUTPUT_INVALID = "invalid.txt"

# Таймаут проверки
CHECK_TIMEOUT = 15

# URL для проверки прокси
TEST_URL = "http://ip-api.com/line"

# Имитация браузера
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# Макс. количество одновременных проверок
MAX_CONCURRENT_HTTP = 100
MAX_CONCURRENT_SOCKS5 = 50

#Цвета (Хочешь что бы было красиво скачай колораму, не хочешь что бы было красиво не качай колораму)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    USE_COLORS = True
except ImportError:
    USE_COLORS = False

def c_green(text): return f"{Fore.GREEN}{text}{Style.RESET_ALL}" if USE_COLORS else text
def c_red(text):   return f"{Fore.RED}{text}{Style.RESET_ALL}" if USE_COLORS else text
def c_yellow(text):return f"{Fore.YELLOW}{text}{Style.RESET_ALL}" if USE_COLORS else text
def c_cyan(text):  return f"{Fore.CYAN}{text}{Style.RESET_ALL}" if USE_COLORS else text


def print_banner():
    banner = f'''
 #####  ####### #       ######     ######  ######  ####### #     # #     #                                                                                                                  
#     # #     # #       #     #    #     # #     # #     #  #   #   #   #                                                                                                                   
#       #     # #       #     #    #     # #     # #     #   # #     # #                                                                                                                    
#  #### #     # #       #     #    ######  ######  #     #    #       #                                                                                                                     
#     # #     # #       #     #    #       #   #   #     #   # #      #                                                                                                                     
#     # #     # #       #     #    #       #    #  #     #  #   #     #                                                                                                                     
 #####  ####### ####### ######     #       #     # ####### #     #    #   

✦ We provide free proxy servers on Telegram ✦
✦ https://t.me/GOLD_PROXYBOT       | @scam_alkash ✦
'''
    print(banner)


async def check_proxy_http(proxy_line: str) -> Literal["working", "dead", "invalid"]:
    proxy_url = f"http://{proxy_line}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                TEST_URL,
                proxy=proxy_url,
                timeout=CHECK_TIMEOUT,
                headers={"User-Agent": USER_AGENT}
            ) as resp:
                if resp.status != 200:
                    return "dead"
                body = await resp.text()
                parts = body.strip().split(".")
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    return "working"
                return "invalid"
    except Exception:
        return "dead"


async def check_proxy_socks5(proxy_line: str) -> Literal["working", "dead", "invalid"]:
    try:
        from aiohttp_socks import ProxyConnector
    except ImportError:
        print(c_red("❌ Для SOCKS5 требуется 'aiohttp-socks'. Установите: pip install aiohttp-socks"))
        return "dead"

    try:
        proxy_url = f"socks5://{proxy_line}"
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                TEST_URL,
                timeout=CHECK_TIMEOUT,
                headers={"User-Agent": USER_AGENT}
            ) as resp:
                if resp.status != 200:
                    return "dead"
                body = await resp.text()
                parts = body.strip().split(".")
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    return "working"
                return "invalid"
    except Exception:
        return "dead"


def append_to_file(filename: str, line: str):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def clear_output_files():
    for name in [OUTPUT_WORKING, OUTPUT_DEAD, OUTPUT_INVALID]:
        Path(name).write_text('', encoding='utf-8')


async def check_and_log(proxy: str, index: int, total: int, check_func, semaphore: asyncio.Semaphore):
    async with semaphore:
        print(f"[{index}/{total}] Проверяю: {proxy}")
        status = await check_func(proxy)

        if status == "working":
            append_to_file(OUTPUT_WORKING, proxy)
            print(c_green("    → ✅ РАБОЧИЙ"))
        elif status == "dead":
            append_to_file(OUTPUT_DEAD, proxy)
            print(c_red("    → ❌ МЁРТВЫЙ"))
        else:
            append_to_file(OUTPUT_INVALID, proxy)
            print(c_yellow("    → ⚠️  Работает, но так себе"))


def choose_proxy_type():
    print("\nВыберите тип прокси:")
    print("1. HTTP  (рекомендуется для Telegram)")
    print("2. SOCKS5")
    while True:
        choice = input("Введите 1 или 2: ").strip()
        if choice == "1":
            return "http"
        elif choice == "2":
            return "socks5"
        else:
            print("Неверный ввод. Введите 1 или 2.")


async def process_proxies():
    proxy_type = choose_proxy_type()
    max_concurrent = MAX_CONCURRENT_HTTP if proxy_type == "http" else MAX_CONCURRENT_SOCKS5
    check_func = check_proxy_http if proxy_type == "http" else check_proxy_socks5

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(c_red("❌ Файл input.txt не найден!"))
        return

    if not lines:
        print(c_red("❌ Файл input.txt пуст!"))
        return

    total = len(lines)
    print(c_cyan(f"\nНайдено {total} прокси. Тип: {proxy_type.upper()}. Проверка до {max_concurrent} одновременно...\n"))
    clear_output_files()

    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [
        check_and_log(proxy, i + 1, total, check_func, semaphore)
        for i, proxy in enumerate(lines)
    ]

    await asyncio.gather(*tasks)

    def count_lines(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except:
            return 0

    print(c_cyan("\nПроверка завершена!"))
    print(c_green(f"   ✅ Рабочих:     {count_lines(OUTPUT_WORKING)}"))
    print(c_red(f"   ❌ Мёртвых:     {count_lines(OUTPUT_DEAD)}"))
    print(c_yellow(f"   ⚠️  Плохо работающих: {count_lines(OUTPUT_INVALID)}"))


if __name__ == '__main__':
    print_banner()
    asyncio.run(process_proxies())