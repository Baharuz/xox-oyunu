"""XOX: local, computer and LAN play. Python 3 standard library only."""
import json
import queue
import socket
import threading
import time
import math
import tkinter as tk
from tkinter import ttk, messagebox

START_SECONDS = 60
X_COLOR = "#1557b0"
O_COLOR = "#c62828"
WIN_COLOR = "#b7e4c7"


class Game:
    def __init__(self, timed=False, now=None):
        self.board = [""] * 9
        self.turn = "X"
        self.winner = None
        self.timed = timed
        self.clock = {"X": float(START_SECONDS), "O": float(START_SECONDS)}
        self.last_tick = time.monotonic() if now is None else now

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        elapsed = max(0, now - self.last_tick)
        self.last_tick = now
        if self.timed and self.winner is None:
            self.clock[self.turn] = max(0, self.clock[self.turn] - elapsed)
            if self.clock[self.turn] == 0:
                self.winner = "O" if self.turn == "X" else "X"
        return self.winner

    def move(self, index, now=None):
        self.tick(now)
        if self.winner is not None or not isinstance(index, int) or not 0 <= index < 9 or self.board[index]:
            return False
        player = self.turn
        self.board[index] = player
        self.winner = outcome(self.board)
        if self.winner is None:
            self.turn = "O" if player == "X" else "X"
        return True

    def state(self):
        return {"board": self.board, "turn": self.turn, "winner": self.winner,
                "timed": self.timed, "clock": self.clock}


LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
         (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))


def outcome(board):
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return "Draw" if all(board) else None


def winning_line(board):
    for line in LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return line
    return ()


def best_move(board):
    """Perfect-play O move, preferring fast wins and slow losses."""
    def score(b, player, depth):
        result = outcome(b)
        if result == "O":
            return 10 - depth
        if result == "X":
            return depth - 10
        if result == "Draw":
            return 0
        values = []
        for i, mark in enumerate(b):
            if not mark:
                b[i] = player
                values.append(score(b, "X" if player == "O" else "O", depth + 1))
                b[i] = ""
        return max(values) if player == "O" else min(values)

    choices = []
    for i, mark in enumerate(board):
        if not mark:
            board[i] = "O"
            choices.append((score(board, "X", 1), i))
            board[i] = ""
    return max(choices)[1] if choices else None


class App:
    def __init__(self, root):
        self.root = root
        root.title("XOX Oyunu")
        root.resizable(False, False)
        self.mode = tk.StringVar(value="2 kişilik (aynı bilgisayar)")
        self.active_mode = "2 kişilik (aynı bilgisayar)"
        self.timed = tk.BooleanVar(value=False)
        self.address = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")
        self.status = tk.StringVar()
        self.turn_label = tk.StringVar()
        self.x_clock = tk.StringVar()
        self.o_clock = tk.StringVar()
        self.game = Game()
        self.remote_state = None
        self.connection = None
        self.listener = None
        self.events = queue.Queue()
        self.net_role = None
        self.connected = False
        self.generation = 0

        frame = ttk.Frame(root, padding=14)
        frame.grid()
        ttk.Label(frame, text="Oyun modu").grid(row=0, column=0, sticky="w")
        mode_box = ttk.Combobox(frame, textvariable=self.mode, state="readonly", width=23,
                     values=("2 kişilik (aynı bilgisayar)", "Bilgisayara karşı", "Ağda ev sahibi", "Ağa katıl"))
        mode_box.grid(row=0, column=1, columnspan=2)
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self.start())
        ttk.Checkbutton(frame, text="Zaman modu (oyuncu başına 60 sn)", variable=self.timed,
                        command=self.start).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        self.network_fields = ttk.Frame(frame)
        self.network_fields.grid(row=2, column=0, columnspan=3, pady=3)
        ttk.Label(self.network_fields, text="Ev sahibi IP").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.network_fields, textvariable=self.address, width=17).grid(row=0, column=1)
        ttk.Label(self.network_fields, text="Port").grid(row=0, column=2, padx=(12, 2))
        ttk.Entry(self.network_fields, textvariable=self.port, width=7).grid(row=0, column=3)
        ttk.Button(frame, text="Yeni oyun", command=self.start).grid(row=3, column=0, columnspan=3, pady=4)
        self.turn_widget = tk.Label(frame, textvariable=self.turn_label, font=("Arial", 18, "bold"), pady=4)
        self.turn_widget.grid(row=4, column=0, columnspan=3, pady=(8, 0))
        clocks = ttk.Frame(frame)
        clocks.grid(row=5, column=0, columnspan=3, pady=5)
        tk.Label(clocks, textvariable=self.x_clock, fg=X_COLOR, font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10)
        tk.Label(clocks, textvariable=self.o_clock, fg=O_COLOR, font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10)
        self.x_bar = ttk.Progressbar(clocks, length=140, maximum=START_SECONDS)
        self.o_bar = ttk.Progressbar(clocks, length=140, maximum=START_SECONDS)
        self.x_bar.grid(row=1, column=0, padx=8)
        self.o_bar.grid(row=1, column=1, padx=8)
        self.buttons = []
        board_frame = ttk.Frame(frame)
        board_frame.grid(row=6, column=0, columnspan=3, pady=10)
        for i in range(9):
            button = tk.Button(board_frame, text=" ", font=("Arial", 27, "bold"), width=4, height=2,
                               command=lambda n=i: self.play(n))
            button.grid(row=i // 3, column=i % 3, padx=2, pady=2)
            self.buttons.append(button)
        ttk.Label(frame, textvariable=self.status, wraplength=350, font=("Arial", 11, "bold")).grid(row=7, column=0, columnspan=3)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.update_network_fields()
        self.render()
        root.after(100, self.loop)

    def close_network(self):
        self.generation += 1
        self.connected = False
        for sock in (self.connection, self.listener):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
        self.connection = self.listener = None

    def start(self):
        self.update_network_fields()
        self.close_network()
        self.net_role = None
        self.remote_state = None
        mode = self.mode.get()
        self.active_mode = mode
        if mode in ("Ağda ev sahibi", "Ağa katıl"):
            try:
                port = int(self.port.get())
                if not 1 <= port <= 65535:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Port hatası", "1 ile 65535 arasında bir port girin.")
                return
        self.game = Game(self.timed.get())
        if mode == "Ağda ev sahibi":
            self.net_role = "host"
            generation = self.generation
            threading.Thread(target=self.host, args=(port, generation), daemon=True).start()
        elif mode == "Ağa katıl":
            self.net_role = "client"
            generation = self.generation
            threading.Thread(target=self.join, args=(self.address.get(), port, generation), daemon=True).start()
        self.render()

    def update_network_fields(self):
        if self.mode.get() in ("Ağda ev sahibi", "Ağa katıl"):
            self.network_fields.grid()
        else:
            self.network_fields.grid_remove()

    def host(self, port, generation):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener = server
            server.bind(("0.0.0.0", port))
            server.listen(1)
            self.events.put((generation, "listening", port))
            conn, _ = server.accept()
            self.events.put((generation, "connected", conn))
            self.read_messages(conn, generation)
        except OSError as exc:
            self.events.put((generation, "error", str(exc)))

    def join(self, address, port, generation):
        try:
            conn = socket.create_connection((address, port), timeout=8)
            conn.settimeout(None)
            self.events.put((generation, "connected", conn))
            self.read_messages(conn, generation)
        except OSError as exc:
            self.events.put((generation, "error", str(exc)))

    def read_messages(self, conn, generation):
        try:
            with conn.makefile("r", encoding="utf-8") as source:
                for line in source:
                    self.events.put((generation, "message", json.loads(line)))
        except (OSError, ValueError) as exc:
            self.events.put((generation, "error", str(exc)))
        finally:
            self.events.put((generation, "disconnected", None))

    def send(self, data):
        if self.connection:
            try:
                self.connection.sendall((json.dumps(data) + "\n").encode("utf-8"))
            except OSError:
                self.connected = False

    def play(self, index):
        if self.net_role == "client":
            state = self.remote_state
            if self.connected and state and state["turn"] == "O" and state["winner"] is None and not state["board"][index]:
                self.send({"type": "move", "index": index})
            return
        if self.net_role == "host" and (not self.connected or self.game.turn != "X"):
            return
        if self.active_mode == "Bilgisayara karşı" and self.game.turn != "X":
            return
        if self.game.move(index):
            self.after_move()

    def after_move(self):
        if self.net_role == "host":
            self.send({"type": "state", "state": self.game.state()})
        self.render()
        if self.active_mode == "Bilgisayara karşı" and self.game.turn == "O" and self.game.winner is None:
            self.root.after(300, self.ai_play)

    def ai_play(self):
        if self.active_mode == "Bilgisayara karşı" and self.game.turn == "O" and self.game.winner is None:
            index = best_move(self.game.board)
            if index is not None and self.game.move(index):
                self.after_move()

    def loop(self):
        while True:
            try:
                generation, kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if generation != self.generation:
                continue
            if kind == "listening":
                self.status.set(f"Port {value} dinleniyor; diğer bilgisayar bağlanabilir.")
            elif kind == "connected":
                self.connection = value
                self.connected = True
                if self.net_role == "host":
                    self.game.last_tick = time.monotonic()
                    self.send({"type": "state", "state": self.game.state()})
            elif kind == "message" and isinstance(value, dict):
                if self.net_role == "host" and value.get("type") == "move":
                    index = value.get("index")
                    if self.connected and self.game.turn == "O" and self.game.move(index):
                        self.after_move()
                elif self.net_role == "client" and value.get("type") == "state":
                    self.remote_state = value.get("state")
            elif kind in ("error", "disconnected"):
                self.connected = False
                if kind == "error":
                    self.status.set("Ağ hatası: " + str(value))
        if self.net_role != "client" and (self.net_role != "host" or self.connected):
            previous = self.game.winner
            self.game.tick()
            if self.net_role == "host" and self.connected and self.game.timed:
                self.send({"type": "state", "state": self.game.state()})
            if previous != self.game.winner and self.net_role == "host":
                self.send({"type": "state", "state": self.game.state()})
        self.render()
        self.root.after(100, self.loop)

    def render(self):
        state = self.remote_state if self.net_role == "client" else self.game.state()
        if state is None:
            self.turn_label.set("Bağlanıyor…")
            self.status.set("Ev sahibine bağlanılıyor…")
            return
        line = winning_line(state["board"])
        for i, button in enumerate(self.buttons):
            mark = state["board"][i]
            button.configure(text=mark or " ", fg=X_COLOR if mark == "X" else O_COLOR if mark == "O" else "#222222",
                             bg=WIN_COLOR if i in line else "#f4f4f4",
                             activebackground=WIN_COLOR if i in line else "#e6e6e6")
        if state["timed"]:
            self.x_clock.set(f"X: {math.ceil(state['clock']['X'])} sn")
            self.o_clock.set(f"O: {math.ceil(state['clock']['O'])} sn")
            self.x_bar.configure(maximum=START_SECONDS, value=state["clock"]["X"])
            self.o_bar.configure(maximum=START_SECONDS, value=state["clock"]["O"])
        else:
            self.x_clock.set("X: zaman modu kapalı")
            self.o_clock.set("O: zaman modu kapalı")
            self.x_bar.configure(value=0)
            self.o_bar.configure(value=0)
        if self.net_role and not self.connected:
            self.turn_label.set("Rakip bekleniyor")
            self.turn_widget.configure(fg="#333333")
            if self.net_role == "host" and self.listener:
                self.status.set("Rakip bekleniyor… Ev sahibinin yerel IP adresini paylaşın.")
            elif self.net_role == "client":
                self.status.set("Bağlantı bekleniyor veya kesildi.")
            return
        result = state["winner"]
        if self.active_mode == "Bilgisayara karşı":
            if result == "Draw":
                self.turn_label.set("Berabere")
            elif result == "O":
                self.turn_label.set("Bilgisayar kazandı")
            elif result == "X":
                self.turn_label.set("Kazandın")
            else:
                self.turn_label.set("Sıra sende" if state["turn"] == "X" else "Bilgisayar düşünüyor")
            self.status.set("Sen: X — Bilgisayar: O")
        else:
            if result == "Draw":
                self.turn_label.set("Berabere")
            elif result:
                self.turn_label.set(f"{result} kazandı")
            else:
                self.turn_label.set(f"Sıra: {state['turn']}")
            self.status.set("Sen: " + ("X" if self.net_role == "host" else "O") if self.net_role else "")
        self.turn_widget.configure(fg=X_COLOR if (result or state["turn"]) == "X" else O_COLOR if (result or state["turn"]) == "O" else "#333333")

    def close(self):
        self.close_network()
        self.root.destroy()


if __name__ == "__main__":
    App(tk.Tk()).root.mainloop()

