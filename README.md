# Моды для Forged Alliance Forever

Это рабочее пространство для нескольких независимых модов к **Supreme Commander: Forged Alliance** и **Forged Alliance Forever (FAF)**.

## Структура

Каждый мод находится в отдельной папке внутри `mods/`:

```text
mods/
  название-мода/
    mod_info.lua
    README.md
    ...файлы этого мода...
```

`mod_info.lua` находится в корне конкретного мода. Игровые файлы и хуки хранятся внутри той же папки. Не помещайте файлы разных модов в общий каталог.

## Инструкции для агента

Перед созданием или изменением мода агент должен прочитать [AGENTS.md](AGENTS.md). Там описаны правила структуры, разработки и проверки модов.

## Моды в проекте

- [Seraphim T1 Missile Launcher](mods/seraphim-t1-missile-launcher/README.md) — мобильная ракетная установка Seraphim T1.
- [Seraphim T1 Mobile Shield](mods/seraphim-t1-mobile-shield/README.md) — экспериментальный мобильный юнит с направленным персональным щитом.
- [Seraphim ACU Test Generator](mods/seraphim-acu-test-generator/README.md) — тестовое улучшение командира Серафимов с большой генерацией ресурсов и билд-павера.
- [Seraphim Rework](mods/seraphim-rework/README.md) — набор изменений Seraphim; сейчас содержит цепочку фабрикаторов материи T1–T3.

## Справка FAF

- [Фракции FAF: особенности, сильные и слабые стороны](docs/factions.md)
- [Wiki FAF по моддингу](https://wiki.faforever.com/Development/Modding)
- [Репозиторий FAF и пример `mod_info.lua`](https://github.com/FAForever/fa/blob/develop/mod_info.lua)
