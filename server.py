import asyncio
import json
import websockets

from helpers import populate_world
from world import World

# параметры
WIDTH, HEIGHT = 100, 100

# создание мира
world = World(WIDTH, HEIGHT)


populate_world(world)

clients = set()

async def broadcast_state():
    """Постоянно обновляет симуляцию и рассылает состояние всем клиентам."""
    while True:
        world.update()

        state = world.to_dict()
        message = json.dumps(state)

        if clients:
            await asyncio.gather(*(ws.send(message) for ws in clients), return_exceptions=True)

        await asyncio.sleep(0.1)  # ~10 FPS


async def handler(websocket):
    clients.add(websocket)
    try:
        print("🌐 Клиент подключён")
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)
        print("❌ Клиент отключён")


async def main():
    print('Server starting...')
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await broadcast_state()

if __name__ == "__main__":
    asyncio.run(main())
