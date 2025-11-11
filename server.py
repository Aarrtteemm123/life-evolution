import asyncio
import json
from aiohttp import web
import os
import time

from config import WORLD_WIDTH, WORLD_HEIGHT, FRAME_TIME, CELL_RADIUS
from models.world import World
from helpers import populate_world


# === Симуляция ===
world = World(WORLD_WIDTH, WORLD_HEIGHT)
populate_world(world)

# === Глобальное хранилище клиентов ===
websocket_clients = set()

# === Маршруты HTTP ===
async def index(request):
    """Отдаёт главную страницу."""
    return web.FileResponse("static/index.html")


async def websocket_handler(request):
    """Обработчик WebSocket для фронтенда."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    websocket_clients.add(ws)
    print("🌐 Клиент подключён")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = msg.data.strip()
                if data == "ping":
                    await ws.send_str("pong")
    finally:
        websocket_clients.remove(ws)
        print("❌ Клиент отключён")

    return ws


# === Основной цикл симуляции ===
def build_render_state(world: World) -> dict:
    """Формирует облегчённое состояние для фронта (только отрисовка и статистика)."""
    env = world.env

    # минимальная сетка веществ: только нужные поля
    substances = []
    for (x, y), subs in env.grid.grid.items():
        for s in subs:
            if s.concentration <= 0:
                continue
            substances.append({
                "x": x,
                "y": y,
                "type": s.type,
                "concentration": s.concentration,
            })

    # только позиции клеток
    cells = [{"position": c.position, "color_hex": c.color_hex} for c in env.cells]

    return {
        "tick": world.tick,
        "tick_time_ms": world.tick_time_ms,
        "cell_radius": CELL_RADIUS,
        "environment": {
            "grid": {
                "width": env.grid.width,
                "height": env.grid.height,
                "substances": substances,
            },
            "cells": cells,
            "env_stats": env.env_stats.to_dict(),
        },
    }


async def simulation_loop():
    while True:
        start_time = time.perf_counter()

        # === Логика симуляции ===
        world.update()
        state = build_render_state(world)
        message = json.dumps(state)

        # === Рассылка клиентам ===
        if websocket_clients:
            await asyncio.gather(
                *(ws.send_str(message) for ws in websocket_clients),
                return_exceptions=True
            )

        # === Вычисляем время цикла ===
        elapsed = time.perf_counter() - start_time
        delay = FRAME_TIME - elapsed

        # === Адаптивная пауза ===
        if delay > 0:
            await asyncio.sleep(delay)
        else:
            # если симуляция занимает дольше чем 1/FPS, не тормозим цикл
            await asyncio.sleep(0.000001)


# === Инициализация приложения ===
async def on_startup(app):
    app["sim_task"] = asyncio.create_task(simulation_loop())
    print("🚀 Simulation started...")


async def on_shutdown(app):
    app["sim_task"].cancel()
    await asyncio.gather(app["sim_task"], return_exceptions=True)
    print("🛑 Simulation stopped.")


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)
app.router.add_static("/static/", path=os.path.join(os.getcwd(), "static"), name="static")

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
