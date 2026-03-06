import flet as ft
import random
import asyncio

# М'ЯКА ПАЛІТРА
COLORS = {
    'I': '#48D1CC', 'J': '#4169E1', 'L': '#CD853F',
    'O': '#EEDD82', 'S': '#3CB371', 'T': '#9370DB', 'Z': '#CD5C5C'
}

SHAPES = {
    'I': [(0, 0), (1, 0), (2, 0), (3, 0)],
    'J': [(0, 1), (0, 0), (1, 0), (2, 0)],
    'L': [(0, 0), (1, 0), (2, 0), (2, 1)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'S': [(0, 0), (1, 0), (1, 1), (2, 1)],
    'T': [(0, 0), (1, 0), (2, 0), (1, 1)],
    'Z': [(0, 1), (1, 1), (1, 0), (2, 0)]
}

async def main(page: ft.Page):
    page.title = "Flet Tetris"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLACK # ВИПРАВЛЕНО: Colors з великої літери
    
    # Налаштування вікна для ПК
    page.window.width = 400
    page.window.height = 800

    cols, rows = 10, 20
    board = [[None for _ in range(cols)] for _ in range(rows)]
    state = {"score": 0, "running": True}

    cells = []
    for y in range(rows - 1, -1, -1):
        row_cells = []
        for x in range(cols):
            container = ft.Container(
                width=30, height=30,
                bgcolor="#111111", # Темний фон клітинки
                border=ft.border.all(0.5, "#222222"),
                border_radius=3
            )
            row_cells.append(container)
        cells.append(ft.Row(row_cells, spacing=2, alignment=ft.MainAxisAlignment.CENTER))
    
    grid = ft.Column(cells, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    score_label = ft.Text(f"SCORE: 0", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    cur_pos = [4, 18]
    cur_type = random.choice(list(SHAPES.keys()))
    cur_blocks = list(SHAPES[cur_type])

    def update_board():
        for y in range(rows):
            for x in range(cols):
                color = board[y][x]
                cells[rows-1-y].controls[x].bgcolor = color if color else "#111111"
        
        # Тінь (Ghost)
        g_y = cur_pos[1]
        while not check_collision([cur_pos[0], g_y - 1], cur_blocks):
            g_y -= 1
        for bx, by in cur_blocks:
            if 0 <= g_y + by < rows:
                cells[rows-1-(g_y+by)].controls[cur_pos[0]+bx].bgcolor = "#333333"

        # Активна фігура
        for bx, by in cur_blocks:
            if 0 <= cur_pos[1] + by < rows:
                cells[rows-1-(cur_pos[1]+by)].controls[cur_pos[0]+bx].bgcolor = COLORS[cur_type]
        page.update()

    def check_collision(pos, blocks):
        for bx, by in blocks:
            x, y = pos[0] + bx, pos[1] + by
            if x < 0 or x >= cols or y < 0: return True
            if y < rows and board[y][x]: return True
        return False

    async def game_loop():
        while state["running"]:
            await asyncio.sleep(0.5)
            if not move(0, -1):
                freeze()
            update_board()

    def move(dx, dy):
        new_pos = [cur_pos[0] + dx, cur_pos[1] + dy]
        if not check_collision(new_pos, cur_blocks):
            cur_pos[0], cur_pos[1] = new_pos
            return True
        return False

    def rotate():
        if cur_type == 'O': return
        new_blocks = [(-y, x) for x, y in cur_blocks]
        for dx in [0, -1, 1, -2, 2]:
            if not check_collision([cur_pos[0]+dx, cur_pos[1]], new_blocks):
                cur_pos[0] += dx
                cur_blocks[:] = new_blocks
                break
        update_board()

    def freeze():
        nonlocal cur_type, cur_blocks
        for bx, by in cur_blocks:
            if 0 <= cur_pos[1] + by < rows:
                board[cur_pos[1]+by][cur_pos[0]+bx] = COLORS[cur_type]
        
        # Очищення ліній
        new_board = [row for row in board if None in row]
        cleared = rows - len(new_board)
        if cleared > 0:
            for _ in range(cleared):
                new_board.append([None for _ in range(cols)])
            board[:] = new_board
            state["score"] += cleared * 100
            score_label.value = f"SCORE: {state['score']}"

        cur_type = random.choice(list(SHAPES.keys()))
        cur_blocks[:] = list(SHAPES[cur_type])
        cur_pos[0], cur_pos[1] = 4, 18
        if check_collision(cur_pos, cur_blocks):
            state["running"] = False

    # Кнопки
    controls = ft.Row([
        ft.ElevatedButton("←", on_click=lambda _: (move(-1, 0), update_board())),
        ft.ElevatedButton("ROT", on_click=lambda _: rotate()),
        ft.ElevatedButton("→", on_click=lambda _: (move(1, 0), update_board())),
        ft.ElevatedButton("↓", on_click=lambda _: (move(0, -1), update_board())),
    ], alignment=ft.MainAxisAlignment.CENTER)

    page.add(score_label, grid, controls)
    asyncio.create_task(game_loop())

ft.app(target=main)
