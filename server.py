import asyncio
import json
from aiohttp import web
import os

from config import WORLD_WIDTH, WORLD_HEIGHT, FPS
from world import World
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
async def simulation_loop():
    while True:
        world.update()
        state = world.to_dict()
        message = json.dumps(state)

        # Рассылаем всем подключённым клиентам
        if websocket_clients:
            await asyncio.gather(
                *(ws.send_str(message) for ws in websocket_clients),
                return_exceptions=True
            )

        await asyncio.sleep(1 / FPS)


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
