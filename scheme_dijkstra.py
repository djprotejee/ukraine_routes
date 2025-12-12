from graphviz import Digraph

# Створення орієнтованого графа блок-схеми
dot = Digraph('Dijkstra_Flow', format='png')
dot.attr(rankdir='TB', size='8,12')

dot.attr('graph', fontname='DejaVu Sans')
dot.attr('node',  fontname='DejaVu Sans')
dot.attr('edge',  fontname='DejaVu Sans')

# Вузли
dot.node('A', 'Початок', shape='oval')

dot.node(
    'B',
    'Ініціалізація:\nvertices, INF,\nзаповнення distances=INF,\nprevious=None, visited=[],\nsteps=[], distances[source]=0',
    shape='ellipse'
)

dot.node(
    'C',
    'len(visited) < len(vertices) ?',
    shape='diamond'
)

dot.node(
    'D',
    'current = None,\ncurrent_dist = INF',
    shape='ellipse'
)

dot.node(
    'E',
    'Цикл за v ∈ vertices:\nякщо v не в visited\nі distances[v] < current_dist:\nоновити current, current_dist',
    shape='ellipse'
)

dot.node(
    'F',
    'current is None ?',
    shape='diamond'
)

dot.node(
    'G',
    'break (решта вершин\nнедосяжні)',
    shape='ellipse'
)

dot.node(
    'H',
    'visited.append(current)',
    shape='ellipse'
)

dot.node(
    'I',
    'target не None\nі current == target ?',
    shape='diamond'
)

dot.node(
    'J',
    'Додати Step з\ncurrent, neighbor=None,\nnew_distance=None,\nкопією distances\nта visited',
    shape='ellipse'
)

dot.node(
    'K',
    'break (ціль досягнуто)',
    shape='ellipse'
)

dot.node(
    'L',
    'Для кожного\nneighbor, weight ∈ graph.neighbors(current)',
    shape='ellipse'
)

dot.node(
    'M',
    'neighbor ∈ visited ?',
    shape='diamond'
)

dot.node(
    'N',
    'alt = distances[current] + weight',
    shape='ellipse'
)

dot.node(
    'O',
    'alt < distances[neighbor] ?',
    shape='diamond'
)

dot.node(
    'P',
    'Оновити:\n distances[neighbor] = alt,\n previous[neighbor] = current,\n додати Step з\nnew_distance = alt',
    shape='ellipse'
)

dot.node(
    'Q',
    'Додати Step з\nnew_distance = None\n(релаксація не покращує шлях)',
    shape='ellipse'
)

dot.node(
    'R',
    'Повернення до\nнаступного neighbor',
    shape='ellipse'
)

dot.node(
    'S',
    'target не None ?',
    shape='diamond'
)

dot.node(
    'T',
    'path = _reconstruct_path(previous,\nsource, target),\n total = distances[target]\n(або None, якщо path порожній)',
    shape='ellipse'
)

dot.node(
    'U',
    'path = [],\n total = None',
    shape='ellipse'
)

dot.node(
    'V',
    'Повернути\nDijkstraResult(distances,\nprevious, path, total,\nsteps, time_ms)',
    shape='ellipse'
)

dot.node('W', 'Кінець', shape='oval')

# Стрілки

dot.edge('A', 'B')
dot.edge('B', 'C')

# Головний цикл while len(visited) < len(vertices)
dot.edge('C', 'D', label='Так')
dot.edge('C', 'S', label='Ні')

dot.edge('D', 'E')
dot.edge('E', 'F')

dot.edge('F', 'G', label='Так')
dot.edge('G', 'S')  # вихід з циклу до завершення

dot.edge('F', 'H', label='Ні')
dot.edge('H', 'I')

# Перевірка досягнення цілі
dot.edge('I', 'J', label='Так')
dot.edge('J', 'K')
dot.edge('K', 'S')

dot.edge('I', 'L', label='Ні')

# Цикл по сусідах
dot.edge('L', 'M')

dot.edge('M', 'L', label='Так')  # neighbor вже в visited – переходимо до наступного
dot.edge('M', 'N', label='Ні')

dot.edge('N', 'O')

dot.edge('O', 'P', label='Так')
dot.edge('O', 'Q', label='Ні')

dot.edge('P', 'R')
dot.edge('Q', 'R')
dot.edge('R', 'L')  # до наступного сусіда

# Після завершення while – вибір гілки за наявністю target
dot.edge('S', 'T', label='Так')
dot.edge('S', 'U', label='Ні')

dot.edge('T', 'V')
dot.edge('U', 'V')

dot.edge('V', 'W')

# Збереження у файл
dot.render('dijkstra_flow_diagram', cleanup=True)
print("✅ Блок-схему збережено як dijkstra_flow_diagram.png")
