from kalibraux import (
    console,
    Colors,
    print_logo,
    banner,
    farewell,
    info,
    success,
    danger,
    warning,
    section,
    field,
    menu_item,
    separator,
    ProgressBar,
    Spinner,
    print_result_header,
    format_accent,
    format_highlight,
    format_error,
    format_ok,
    format_dim,
    LoadingAnimations,
    PingPongLoader,
    PromptInput,
    Dialog,
    StatusBar,
    ModelInfo,
    CommandList,
    FileReference,
    ToolResult,
    MessageStyle,
)
import time
import os


def test_colors():
    console.print("\n[bold]=== ЦВЕТОВАЯ ПАЛИТРА ===[/]\n")
    
    console.print(f"  [bold]Логотип (градиент):[/]")
    console.print(f"    [#{Colors.LOGO_START}]███[/] → [#{Colors.LOGO_END}]███[/]")
    console.print(f"    [#{Colors.LOGO_START}]#{Colors.LOGO_START}[/] → [#{Colors.LOGO_END}]#{Colors.LOGO_END}[/]")
    
    console.print(f"\n  [bold]Основные цвета:[/]")
    console.print(f"    [#{Colors.PURPLE}]Фиолетовый (#{Colors.PURPLE})[/] — [*], прогресс-бар")
    console.print(f"    [cyan]Голубой (cyan)[/] — акцент, [*] info")
    console.print(f"    [green]Зелёный (green)[/] — [+] успех, ОК")
    console.print(f"    [red]Красный (red)[/] — [!] ошибка, ошибочные значения")
    console.print(f"    [yellow]Жёлтый (yellow)[/] — выделение, предупреждения")
    console.print(f"    [dim]Dim (dim)[/] — подписи, разделители")
    console.print(f"    [bold]Bold (bold)[/] — заголовки, имена полей")


def test_logo():
    console.print("\n[bold]=== ЛОГОТИП ===[/]\n")
    print_logo()


def test_system_messages():
    console.print("\n[bold]=== СИСТЕМНЫЕ СООБЩЕНИЯ ===[/]\n")
    
    info("Информационное сообщение")
    success("Операция выполнена успешно")
    warning("Предупреждение")
    danger("Ошибка выполнения")


def test_spinner():
    console.print("\n[bold]=== СПИННЕР (Done/Fail) ===[/]\n")
    
    sp1 = Spinner("Загрузка данных")
    sp1.done("готово")
    
    sp2 = Spinner("Подключение к серверу")
    sp2.fail("ошибка соединения")


def test_progress_bar():
    console.print("\n[bold]=== ПРОГРЕСС-БАР ===[/]\n")
    
    with ProgressBar(total=5, prefix="Загрузка") as pb:
        for i in range(5):
            time.sleep(0.15)
            pb.update()


def test_loading_animation():
    console.print("\n[bold]=== АНИМАЦИЯ ЗАГРУЗКИ (ПИНГ-ПОНГ) ===[/]\n")
    
    console.print("  Режим: [.] → [*] → [\"] → [*] → [.] ...\n")
    
    console.print("  [cyan]Вариант 1: DOTS[/] (3 секунды)")
    with PingPongLoader("Обработка данных...", frames=LoadingAnimations.DOTS, interval=0.2):
        time.sleep(3)
    
    console.print("\n  [cyan]Вариант 2: SLASHES[/] (3 секунды)")
    with PingPongLoader("Подключение...", frames=LoadingAnimations.SLASHES, interval=0.15):
        time.sleep(3)
    
    console.print("\n  [cyan]Вариант 3: BARS[/] (3 секунды)")
    with PingPongLoader("Синхронизация...", frames=LoadingAnimations.BARS, interval=0.25):
        time.sleep(3)
    
    console.print("\n  [yellow]Полный тест 60 секунд:[/]")
    console.print("  Чтобы запустить полную 60-секундную анимацию,")
    console.print("  запустите test.py с аргументом --full60\n")


def test_loading_60sec():
    console.clear()
    console.print("\n[bold]=== 60-СЕКУНДНАЯ АНИМАЦИЯ ЗАГРУЗКИ ===[/]\n")
    console.print("  Режим: [<] → [/] → [>] → [/] → [<] ...\n")
    console.print("  Нажмите Ctrl+C чтобы остановить досрочно.\n")
    
    try:
        with PingPongLoader("Загрузка ресурсов...", frames=LoadingAnimations.SLASHES, interval=0.12, color=Colors.PURPLE):
            time.sleep(60)
    except KeyboardInterrupt:
        console.print("\r\n  [yellow]Прервано пользователем[/]\n")
    
    console.print("\n[bold green]Тест завершён.[/]")


def test_banner():
    console.print("\n[bold]=== БАННЕР ===[/]\n")
    banner(cls=False, subtitle="KalibraUX — UI библиотека")


def test_section_and_fields():
    console.print("\n[bold]=== СЕКЦИИ И ПОЛЯ ===[/]\n")
    
    section("ИНФОРМАЦИЯ")
    
    field("Имя", "Алексей")
    field("Код", "A-12345", Colors.ACCENT)
    field("Статус", "Активен", Colors.OK)
    field("Приоритет", "Высокий", Colors.HIGHLIGHT)
    field("Описание", "")
    console.print("      Обычный текст без выделения")
    field("Теги", "")
    console.print(f"      {format_accent('tag1')}, {format_accent('tag2')}, {format_accent('tag3')}")


def test_menu():
    console.print("\n[bold]=== ГЛАВНОЕ МЕНЮ ===[/]\n")
    
    console.print("  [bold]ГЛАВНОЕ МЕНЮ[/]")
    separator(42)
    menu_item("1", "Экран 1")
    menu_item("2", "Экран 2")
    menu_item("3", "Экран 3")
    menu_item("4", "Экран 4")
    menu_item("S", "Настройки")
    menu_item("I", "Информация")
    menu_item("0", "Выход")
    separator(42)


def test_formatters():
    console.print("\n[bold]=== ФОРМАТТЕРЫ ===[/]\n")
    
    console.print(f"  Акцент: {format_accent('выделенный текст')}")
    console.print(f"  Выделение: {format_highlight('важное значение')}")
    console.print(f"  Ошибка: {format_error('неверные данные')}")
    console.print(f"  ОК: {format_ok('успешно')}")
    console.print(f"  Dim: {format_dim('подзаголовок')}")


def test_farewell():
    console.print("\n[bold]=== ПРОЩАНИЕ ===[/]\n")
    console.print("  (экран будет очищен при реальном использовании)")
    console.print("  Логотип + текст 'До скорых встреч!'")


def test_opencode_elements():
    console.print("\n[bold]=== ЭЛЕМЕНТЫ В СТИЛЕ OPENCODE ===[/]\n")
    
    console.print("  [bold]┌── Prompt Input ──┐[/]")
    console.print("  [dim]│  ┌────────────────────────────────────┐  │[/]")
    console.print("  [dim]│  │[/] [bold]>[/] [dim]Введите сообщение...              [/] [dim]│[/]")
    console.print("  [dim]│  │[/] [dim]@[/][dim]файл[/] [dim]/[/][dim]!команда[/] [dim]────────────────────│[/]")
    console.print("  [dim]└────────────────────────────────────┘  │[/]")
    console.print("  [bold]└─────────────────────────────────────────┘[/]\n")
    
    console.print("  [bold]┌── Диалог выбора ──┐[/]")
    console.print("  [dim]│  [cyan]●[/] Claude 3.5 Sonnet        [/][dim]│[/]")
    console.print("  [dim]│  [cyan]○[/] GPT-4o                    [/][dim]│[/]")
    console.print("  [dim]│  [cyan]○[/] Gemini 2.5 Pro            [/][dim]│[/]")
    console.print("  [dim]│  [cyan]○[/] Claude 4 Opus               [/][dim]│[/]")
    console.print("  [dim]│                                   [/][dim]│[/]")
    console.print("  [dim]│[/]  [bold]─────────────────────────────   [/][dim]│[/]")
    console.print("  [dim]│[/]  [green][ Enter ][/][dim]  [red][ Отмена ][/][dim]                │[/]")
    console.print("  [bold]└─────────────────────────────────────────┘[/]\n")
    
    section("КОМАНДЫ (/)")
    console.print(f"    [cyan]/help[/]    — показать справку")
    console.print(f"    [cyan]/models[/]  — список моделей")
    console.print(f"    [cyan]/connect[/] — добавить провайдер")
    console.print(f"    [cyan]/editor[/]  — открыть редактор")
    console.print(f"    [cyan]/export[/]  — экспорт сессии")
    console.print(f"    [cyan]/exit[/]    — выход")
    console.print()
    
    section("ФАЙЛЫ (@)")
    console.print(f"    [yellow]@[/]{format_accent('src/main.py')}")
    console.print(f"    [yellow]@[/]{format_accent('src/utils/helpers.py')}")
    console.print(f"    [yellow]@[/]{format_accent('config.json')}")
    console.print()
    
    section("КОМАНДЫ ОБОЛОЧКИ (!)")
    console.print(f"    [red]![/] {format_accent('ls -la')}")
    console.print(f"    [red]![/] {format_accent('git status')}")
    console.print(f"    [red]![/] {format_accent('npm run build')}")
    console.print()
    
    section("СТАТУС-БАР")
    console.print("  [dim]╔════════════════════════════════════════════════════════════╗[/]")
    console.print(f"  [dim]║[/]  [cyan]KalibraUX[/]  [dim]│[/]  [green]● Claude 3.5[/]  [dim]│[/]  [yellow]2.3K / 128K tokens[/]  [dim]│[/]  [dim]Ctrl+H[/]  [dim]║[/]")
    console.print("  [dim]╚════════════════════════════════════════════════════════════╝[/]")
    console.print()
    
    section("ВЫВОД ИНСТРУМЕНТА")
    console.print("  [bold]┌──[/] [green]bash[/] [bold]`ls -la[/] [bold]──┐[/]")
    console.print("  [dim]│[/]  total 42                                              [/][dim]│[/]")
    console.print("  [dim]│[/]  drwxr-xr-x  5 user  staff   160 Jan 10 12:00 .[/] [dim]│[/]")
    console.print("  [dim]│[/]  -rw-r--r--  1 user  staff  2048 Jan 10 12:00 main.py[/] [dim]│[/]")
    console.print("  [dim]│[/]  -rw-r--r--  1 user  staff   512 Jan 10 12:00 config.json[/] [dim]│[/]")
    console.print("  [bold]└────────────────────────────────────────────────────────────┘[/]")
    console.print()
    
    section("ШОРТКАТЫ")
    console.print("    [dim]Ctrl+X[/] + [dim]C[/]  — лидер-ключ")
    console.print("    [dim]Ctrl+X[/] + [dim]M[/]  — модели")
    console.print("    [dim]Ctrl+X[/] + [dim]E[/]  — редактор")
    console.print("    [dim]Ctrl+X[/] + [dim]Q[/]  — выход")
    console.print("    [dim]Ctrl+X[/] + [dim]X[/]  — экспорт")


def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full60":
        test_loading_60sec()
        return
    
    console.clear()
    console.print("[bold magenta]╔════════════════════════════════════════════╗[/]")
    console.print("[bold magenta]║   KALIBRAUX ДЕМО — ВСЕ UI-ЭЛЕМЕНТЫ        ║[/]")
    console.print("[bold magenta]╚════════════════════════════════════════════╝[/]\n")
    
    test_banner()
    test_logo()
    test_colors()
    test_system_messages()
    test_spinner()
    test_progress_bar()
    test_loading_animation()
    test_opencode_elements()
    test_section_and_fields()
    test_menu()
    test_formatters()
    test_farewell()
    
    console.print("\n[dim]──────────────────────────────────────────────[/]")
    console.print("[bold]Тест завершён. Все элементы продемонстрированы.[/]")
    console.print("[dim]Полная 60-секундная анимация: python test.py --full60[/]")
    console.print()


if __name__ == "__main__":
    main()
