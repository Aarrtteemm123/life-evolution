from world import World

if __name__ == "__main__":
    from gene import Gene
    from trigger import Trigger
    from action import Action

    # создаем мир
    world = World(50, 50)

    # добавляем клетку
    g = Gene("energy", Trigger(5, "LESS"), Action("ABSORB", substance_name="glucose"))
    from cell import Cell
    cell = Cell(position=(25.0, 25.0))
    cell.genes.append(g)
    world.cells.append(cell)

    # шаги симуляции
    for _ in range(10):
        world.update()

    # сохранить
    world.save("simulation_state.json")

    # загрузить
    restored = World.load("simulation_state.json")
    print("Restored tick:", restored.tick)

