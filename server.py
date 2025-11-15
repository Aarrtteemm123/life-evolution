import asyncio
import json
from aiohttp import web
import os
import time

from config import WORLD_WIDTH, WORLD_HEIGHT, FRAME_TIME, CELL_RADIUS
from models.world import World
from helpers import populate_world


# === Маршруты HTTP ===
async def index(request):
    """Отдаёт главную страницу."""
    return web.FileResponse("static/index.html")


async def client_simulation_loop(ws: web.WebSocketResponse, state: dict):
    """
    Отдельный цикл симуляции для каждого клиента.
    state = {
        "world": World,
        "sim_running": bool,
        "max_speed": bool,
        "last_state": dict,
    }
    """
    while not ws.closed:
        # === Режим "max speed": считаем тики, но НЕ шлём кадры на фронт ===
        if state["sim_running"] and state["max_speed"]:
            state["world"].update()
            # здесь нет build_render_state и send_str
            await asyncio.sleep(0)  # просто отдаём управление event loop
            continue

        # === Обычный режим (или пауза) c ограничением FPS и отрисовкой ===
        start_time = time.perf_counter()

        if state["sim_running"]:
            state["world"].update()

        state["last_state"] = build_render_state(state["world"])
        message = json.dumps(state["last_state"])

        try:
            await ws.send_str(message)
        except ConnectionResetError:
            break

        elapsed = time.perf_counter() - start_time
        delay = FRAME_TIME - elapsed

        if delay > 0:
            await asyncio.sleep(delay)
        else:
            await asyncio.sleep(0)


async def websocket_handler(request):
    """Обработчик WebSocket для фронтенда."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    print("🌐 Клиент подключён")

    # === Инициализируем отдельный мир ДЛЯ ЭТОГО клиента ===
    world = World(WORLD_WIDTH, WORLD_HEIGHT)
    populate_world(world)

    state = {
        "world": world,
        "sim_running": True,
        "max_speed": False,
        "last_state": build_render_state(world),
    }

    # при подключении сразу отправим статус
    await ws.send_str(json.dumps({
        "type": "status",
        "running": state["sim_running"],
        "max_speed": state["max_speed"],
    }))

    # запускаем клиентский цикл симуляции
    sim_task = asyncio.create_task(client_simulation_loop(ws, state))

    try:
        async for msg in ws:
            if msg.type != web.WSMsgType.TEXT:
                continue

            raw = msg.data.strip()

            # старый ping
            if raw == "ping":
                await ws.send_str("pong")
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if data.get("type") != "control":
                continue

            command = data.get("command")

            if command == "start":
                state["sim_running"] = True
                print("▶️  Simulation started via WS (client)")
                await ws.send_str(json.dumps({
                    "type": "status",
                    "running": state["sim_running"],
                    "max_speed": state["max_speed"],
                }))

            elif command == "stop":
                state["sim_running"] = False
                print("⏸️  Simulation stopped via WS (client)")
                await ws.send_str(json.dumps({
                    "type": "status",
                    "running": state["sim_running"],
                    "max_speed": state["max_speed"],
                }))

            elif command == "speed":
                max_speed = data.get("max_speed")
                if isinstance(max_speed, bool):
                    state["max_speed"] = max_speed
                    print(f"⚙️  Speed mode changed via WS (client): max_speed={max_speed}")
                await ws.send_str(json.dumps({
                    "type": "status",
                    "running": state["sim_running"],
                    "max_speed": state["max_speed"],
                }))

            elif command == "save":
                full_state = state["world"].to_dict()
                filename = f"world_state_tick_{state['world'].tick}.json"
                print(f"💾 Save requested via WS -> {filename}")

                await ws.send_str(json.dumps({
                    "type": "save",
                    "filename": filename,
                    "state": full_state,
                }))

            elif command == "load":
                save_state = data.get("state")
                if not isinstance(save_state, dict):
                    await ws.send_str(json.dumps({
                        "type": "status",
                        "running": state["sim_running"],
                        "max_speed": state["max_speed"],
                        "error": "invalid_state"
                    }))
                    continue

                try:
                    # создаём новый мир из словаря
                    new_world = World.from_dict(save_state)
                    state["world"] = new_world
                    state["last_state"] = build_render_state(new_world)
                    state["sim_running"] = True  # после загрузки продолжаем симуляцию

                    print(f"📂 World loaded via WS (client), tick={new_world.tick}")

                    # отправим статус и один кадр, чтобы фронт сразу обновился
                    await ws.send_str(json.dumps({
                        "type": "status",
                        "running": state["sim_running"],
                        "max_speed": state["max_speed"],
                        "loaded_tick": new_world.tick
                    }))
                    await ws.send_str(json.dumps(state["last_state"]))

                except Exception as e:
                    print(f"❌ Load failed: {e}")
                    await ws.send_str(json.dumps({
                        "type": "status",
                        "running": state["sim_running"],
                        "max_speed": state["max_speed"],
                        "error": "load_failed"
                    }))

    finally:
        print("❌ Клиент отключён")
        sim_task.cancel()
        await asyncio.gather(sim_task, return_exceptions=True)

    return ws


# === Формирование облегчённого state для фронта ===
def build_render_state(world: World) -> dict:
    """Формирует облегчённое состояние для фронта (только отрисовка и статистика)."""
    env = world.env

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


# === Инициализация приложения ===
app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)
app.router.add_static("/static/", path=os.path.join(os.getcwd(), "static"), name="static")

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
