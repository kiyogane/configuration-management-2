"""Построение графа зависимостей и операции над ним."""


def build_graph(repo, root, substring=""):
    """Построить граф зависимостей от root обходом BFS с рекурсией.

    Возвращает словарь {вершина: [прямые зависимости]} в порядке
    обхода. Пакеты, имя которых содержит substring, не учитываются
    (вместе со всем, что достижимо только через них). Уже посещенные
    вершины повторно не раскрываются, поэтому циклы не приводят к
    бесконечному обходу.
    """
    graph = {}
    bfs_level(repo, [root], graph, substring)
    return graph


def bfs_level(repo, level, graph, substring):
    """Обработать один уровень BFS и рекурсивно перейти к следующему."""
    if not level:
        return
    next_level, planned = [], set()
    for node in level:
        graph[node] = []
        for dep in repo.dependencies(node):
            if substring and substring in dep.name:
                continue
            graph[node].append(dep)
            if dep not in graph and dep not in planned:
                planned.add(dep)
                next_level.append(dep)
    next_level = [node for node in next_level if node not in graph]
    bfs_level(repo, next_level, graph, substring)


def find_cycle(graph):
    """Найти один цикл в графе (список вершин) или вернуть None."""
    state = {}
    for start in graph:
        if start not in state:
            cycle = cycle_from(graph, start, state, [])
            if cycle:
                return cycle
    return None


def cycle_from(graph, node, state, path):
    """DFS-поиск цикла (active — вершина на текущем пути)."""
    state[node] = "active"
    path.append(node)
    for dep in graph.get(node, []):
        if state.get(dep) == "active":
            return path[path.index(dep):] + [dep]
        if dep not in state:
            cycle = cycle_from(graph, dep, state, path)
            if cycle:
                return cycle
    state[node] = "done"
    path.pop()
    return None


def edge_count(graph):
    """Число ребер графа."""
    return sum(len(deps) for deps in graph.values())
