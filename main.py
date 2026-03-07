import flet as ft
import random
import asyncio
import json
import os

# --- КОНФІГУРАЦІЯ ---
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

SCORE_FILE = "high_scores.json"

def get_high_scores():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r") as f:
                return sorted(json.load(f), reverse=True)[:5]
        except: return [0]
    return [0]

def save_high_score(new_score):
    if new_score <= 0: return
    scores = get_high_scores()
    if new_score not in scores:
        scores.append(new_score)
        scores = sorted(scores, reverse=True)[:5]
        with open(SCORE_FILE, "w") as f: json.dump(scores, f)

async def main(page: ft.Page):
    page.title = "Flet Tetris Ultra Safe"
    page.horizontal_alignment = "center"
    page.bgcolor = ft.Colors.BLACK
    page.window.width = 450
    page.window.height = 950

    cols, rows = 10, 20
    board = [[None for _ in range(cols)] for _ in range(rows)]
    
    state = {
        "score": 0, "level": 1, "running": False, "paused": False, 
        "cur_pos": [4, 18], "cur_type": 'O', "cur_blocks": [],
        "next_type": 'I', "speed": 0.5, "move_dir": None
    }

    # --- UI СІТКА ---
    cells = []
    for y in range(rows - 1, -1, -1):
        row_cells = [ft.Container(width=25, height=25, bgcolor="#111111", border=ft.Border.all(0.5, "#222222"), border_radius=3) for _ in range(cols)]
        cells.append(ft.Row(row_cells, spacing=2, alignment="center"))
    grid = ft.Column(cells, spacing=2, horizontal_alignment="center")

    # Вікно NEXT зробимо трохи ширшим (5x4), щоб фігура "I" не виходила за межі
    next_cells = []
    for _ in range(4):
        next_row = [ft.Container(width=15, height=15, bgcolor="transparent", border_radius=2) for _ in range(5)]
        next_cells.append(ft.Row(next_row, spacing=1))
    
    next_box = ft.Container(
        content=ft.Column([ft.Text("NEXT", size=12, weight="bold"), ft.Column(next_cells, spacing=1)], horizontal_alignment="center"),
        padding=10, bgcolor="#222222", border_radius=10
    )

    score_label = ft.Text("SCORE: 0", size=20, weight="bold")
    level_label = ft.Text("LVL: 1", size=18, color="yellow")
    pause_btn = ft.IconButton(icon=ft.Icons.PAUSE, on_click=lambda _: toggle_pause())
    top_info = ft.Row([ft.Column([score_label, level_label], spacing=0), next_box, pause_btn], alignment="spaceBetween", width=340)

    # --- ЛОГІКА З ПЕРЕВІРКОЮ МЕЖ (Safety First) ---
    def update_ui():
        # 1. Очищуємо поле
        for y in range(rows):
            for x in range(cols):
                cells[rows-1-y].controls[x].bgcolor = board[y][x] if board[y][x] else "#111111"
        
        if state["running"] and not state["paused"]:
            # 2. Малюємо тінь (ghost)
            g_y = state["cur_pos"][1]
            while not check_collision([state["cur_pos"][0], g_y - 1], state["cur_blocks"]): g_y -= 1
            for bx, by in state["cur_blocks"]:
                tx, ty = state["cur_pos"][0] + bx, g_y + by
                if 0 <= tx < cols and 0 <= ty < rows:
                    cells[rows-1-ty].controls[tx].bgcolor = "#222222"

            # 3. Малюємо активну фігуру
            for bx, by in state["cur_blocks"]:
                tx, ty = state["cur_pos"][0] + bx, state["cur_pos"][1] + by
                if 0 <= tx < cols and 0 <= ty < rows:
                    cells[rows-1-ty].controls[tx].bgcolor = COLORS[state["cur_type"]]

        # 4. Оновлюємо вікно NEXT
        for r in range(4):
            for c in range(5): next_cells[r].controls[c].bgcolor = "transparent"
        for bx, by in SHAPES[state["next_type"]]:
            # bx+1 для центрування
            if 0 <= 1-by < 4 and 0 <= bx+1 < 5:
                next_cells[1-by].controls[bx+1].bgcolor = COLORS[state["next_type"]]
        page.update()

    def check_collision(pos, blocks):
        for bx, by in blocks:
            x, y = pos[0] + bx, pos[1] + by
            if x < 0 or x >= cols or y < 0: return True
            if y < rows and board[y][x]: return True
        return False

    def move(dx, dy):
        if not state["running"] or state["paused"]: return False
        if not check_collision([state["cur_pos"][0] + dx, state["cur_pos"][1] + dy], state["cur_blocks"]):
            state["cur_pos"][0] += dx
            state["cur_pos"][1] += dy
            return True
        return False

    def rotate():
        if not state["running"] or state["paused"] or state["cur_type"] == 'O': return
        new_blocks = [(-y, x) for x, y in state["cur_blocks"]]
        for dx in [0, -1, 1, -2, 2]: # Wall kick
            if not check_collision([state["cur_pos"][0] + dx, state["cur_pos"][1]], new_blocks):
                state["cur_pos"][0] += dx
                state["cur_blocks"][:] = new_blocks
                update_ui()
                break

    def freeze():
        for bx, by in state["cur_blocks"]:
            tx, ty = state["cur_pos"][0] + bx, state["cur_pos"][1] + by
            if 0 <= tx < cols and 0 <= ty < rows:
                board[ty][tx] = COLORS[state["cur_type"]]
        
        new_board = [row for row in board if None in row]
        cleared = rows - len(new_board)
        if cleared > 0:
            for _ in range(cleared): new_board.append([None for _ in range(cols)])
            board[:] = new_board
            bonus = {1: 100, 2: 300, 3: 700, 4: 1500}
            state["score"] += bonus.get(cleared, 100) * state["level"]
            state["level"] = (state["score"] // 500) + 1
            state["speed"] = max(0.1, 0.5 - (state["level"] - 1) * 0.05)
            score_label.value = f"SCORE: {state['score']}"; level_label.value = f"LVL: {state['level']}"
        
        # Спавн нової фігури
        state["cur_type"] = state["next_type"]
        state["cur_blocks"][:] = list(SHAPES[state["cur_type"]])
        state["cur_pos"][:] = [3 if state["cur_type"] == 'I' else 4, 18]
        state["next_type"] = random.choice(list(SHAPES.keys()))
        
        if check_collision(state["cur_pos"], state["cur_blocks"]):
            state["running"] = False
            show_menu()

    async def game_loop():
        while state["running"]:
            await asyncio.sleep(state["speed"])
            if not state["paused"]:
                if not move(0, -1): freeze()
                update_ui()

    # --- КЕРУВАННЯ ---
    def create_action_btn(icon, dx, dy):
        async def on_down(e):
            if not state["running"] or state["paused"]: return
            state["move_dir"] = (dx, dy)
            move(dx, dy); update_ui()
            await asyncio.sleep(0.2)
            while state["move_dir"] == (dx, dy):
                if move(dx, dy): update_ui()
                else: break
                await asyncio.sleep(0.07)
        async def on_up(e): state["move_dir"] = None

        return ft.GestureDetector(
            content=ft.Container(content=ft.Icon(icon, size=40, color="white"), width=80, height=80, bgcolor="#333333", border_radius=15, alignment=ft.Alignment(0,0)),
            on_tap_down=on_down, on_tap_up=on_up, on_tap_cancel=on_up
        )

    controls = ft.Row([
        create_action_btn(ft.Icons.ARROW_LEFT, -1, 0),
        ft.GestureDetector(content=ft.Container(content=ft.Icon(ft.Icons.ROTATE_RIGHT, size=40, color="white"), width=80, height=80, bgcolor="#333333", border_radius=15, alignment=ft.Alignment(0,0)), on_tap=lambda _: rotate()),
        create_action_btn(ft.Icons.ARROW_RIGHT, 1, 0),
        create_action_btn(ft.Icons.ARROW_DOWNWARD, 0, -1),
    ], alignment="center", spacing=10)

    game_view = ft.Column([top_info, grid, ft.Container(height=10), controls], horizontal_alignment="center")

    def toggle_pause():
        state["paused"] = not state["paused"]
        pause_btn.icon = ft.Icons.PLAY_ARROW if state["paused"] else ft.Icons.PAUSE
        page.update()

    def start_game(e):
        board[:] = [[None for _ in range(cols)] for _ in range(rows)]
        state.update({"score": 0, "level": 1, "running": True, "paused": False, "speed": 0.5})
        state["cur_type"] = random.choice(list(SHAPES.keys()))
        state["cur_blocks"][:] = list(SHAPES[state["cur_type"]])
        state["next_type"] = random.choice(list(SHAPES.keys()))
        page.controls.clear(); page.add(game_view); page.update()
        asyncio.create_task(game_loop())

    def show_menu():
        save_high_score(state["score"])
        page.controls.clear()
        scores = get_high_scores()
        page.add(ft.Column([
            ft.Text("TETRIS ULTRA", size=50, weight="bold", color=COLORS['T']),
            ft.ElevatedButton("START GAME", on_click=start_game, width=220, height=60),
            ft.Text("TOP SCORES:", size=24, color="yellow"),
            *[ft.Text(f"{s}", size=20) for s in scores]
        ], horizontal_alignment="center", alignment="center", spacing=20))
        page.update()

    show_menu()

ft.run(main)
