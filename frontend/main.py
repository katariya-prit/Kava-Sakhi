"""
frontend/main.py
CustomTkinter GUI (advanced Tkinter) — HIGH ANIMATION / HIGH UI edition.
Contains NO business logic and NO OpenAI calls directly — it only talks
to the local server via HTTP requests. This keeps frontend/server cleanly
separated.

Animations included:
 - Window fade-in on launch
 - Breathing / gradient header background
 - Pulsing avatar glow
 - Pulsing online/offline status dot
 - Message bubbles slide + fade in
 - Smooth (tweened) auto-scroll
 - WhatsApp-style bouncing 3-dot typing indicator (canvas based)
 - Hover / press micro-animations on buttons
 - Animated focus glow on the input field

Make sure the server (server/app.py) is running before you start this.
"""

import customtkinter as ctk
import tkinter as tk
import requests
import threading
import uuid
import math
from datetime import datetime

SERVER_URL = "http://127.0.0.1:5000"
SESSION_ID = str(uuid.uuid4())  # unique per app run

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------- Palette ----------------
COLOR_BG = "#0f1117"
COLOR_HEADER = "#161923"
COLOR_HEADER_ALT = "#1c2236"
COLOR_USER_BUBBLE = "#3b82f6"
COLOR_USER_BUBBLE_HOVER = "#2563eb"
COLOR_BOT_BUBBLE = "#1e2230"
COLOR_TEXT = "#e5e7eb"
COLOR_MUTED = "#8b8f9c"
COLOR_ONLINE = "#22c55e"
COLOR_ONLINE_DIM = "#0f4d2b"
COLOR_OFFLINE = "#ef4444"
COLOR_ACCENT = "#818cf8"
COLOR_BORDER_IDLE = "#242938"


def lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors (t in [0,1])."""
    t = max(0.0, min(1.0, t))
    c1, c2 = c1.lstrip("#"), c2.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = round(r1 + (r2 - r1) * t)
    g = round(g1 + (g2 - g1) * t)
    b = round(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


# ============================================================
# Bouncing 3-dot typing indicator (canvas based)
# ============================================================
class TypingBubble(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_BOT_BUBBLE, corner_radius=16)
        self.canvas = tk.Canvas(
            self, width=54, height=26, bg=COLOR_BOT_BUBBLE, highlightthickness=0
        )
        self.canvas.pack(padx=14, pady=12)
        self.dots = [
            self.canvas.create_oval(0, 0, 8, 8, fill=COLOR_MUTED, outline="")
            for _ in range(3)
        ]
        self._frame = 0
        self._running = True
        self._animate()

    def _animate(self):
        if not self._running:
            return
        for i, dot in enumerate(self.dots):
            phase = self._frame * 0.28 - i * 0.7
            y = 13 + math.sin(phase) * 5
            x = 10 + i * 17
            self.canvas.coords(dot, x - 4, y - 4, x + 4, y + 4)
        self._frame += 1
        self.after(40, self._animate)

    def stop(self):
        self._running = False


class ChatbotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self._alive = True
        self._typing_widget = None
        self._typing_wrapper = None

        self.title("Kava Sakhi - AI Chatbot")
        self.geometry("700x760")
        self.minsize(520, 560)
        self.configure(fg_color=COLOR_BG)

        # start invisible, fade in once built
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._row = 0

        self._build_header()
        self._build_chat_area()
        self._build_input_area()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.check_server_health()
        self._welcome_message()

        self._fade_in_window()
        self.after(150, self._animate_header)
        self.after(150, self._animate_avatar)

    # ============================================================
    # WINDOW-LEVEL ANIMATIONS
    # ============================================================
    def _fade_in_window(self, alpha=0.0):
        if not self._alive:
            return
        alpha = min(alpha + 0.08, 1.0)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            return
        if alpha < 1.0:
            self.after(20, lambda: self._fade_in_window(alpha))

    def _on_close(self):
        self._alive = False
        self.destroy()

    # ============================================================
    # HEADER
    # ============================================================
    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color=COLOR_HEADER, height=64, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(1, weight=1)

        self.avatar = ctk.CTkLabel(
            self.header, text="🪷", font=("Segoe UI Emoji", 22),
            fg_color=COLOR_USER_BUBBLE, corner_radius=20, width=40, height=40,
        )
        self.avatar.grid(row=0, column=0, padx=(16, 10), pady=12)

        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", pady=10)

        ctk.CTkLabel(
            title_box, text="Kava Sakhi", font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT
        ).pack(anchor="w")

        status_row = ctk.CTkFrame(title_box, fg_color="transparent")
        status_row.pack(anchor="w")

        self.status_dot = ctk.CTkLabel(
            status_row, text="●", font=("Segoe UI", 10), text_color=COLOR_OFFLINE
        )
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            status_row, text="Connecting...", font=("Segoe UI", 11), text_color=COLOR_MUTED
        )
        self.status_label.pack(side="left", padx=(4, 0))

        self.new_chat_btn = ctk.CTkButton(
            self.header, text="+ New Chat", width=100, height=32,
            fg_color="transparent", border_width=1, border_color=COLOR_MUTED,
            hover_color="#232838", font=("Segoe UI", 12),
            command=self.new_chat,
        )
        self.new_chat_btn.grid(row=0, column=2, padx=16, pady=12)
        self.new_chat_btn.bind("<Enter>", lambda e: self._tween_widget_border(
            self.new_chat_btn, COLOR_MUTED, COLOR_ACCENT))
        self.new_chat_btn.bind("<Leave>", lambda e: self._tween_widget_border(
            self.new_chat_btn, COLOR_ACCENT, COLOR_MUTED))

    def _animate_header(self, frame=0):
        if not self._alive:
            return
        t = (math.sin(frame * 0.02) + 1) / 2
        color = lerp_color(COLOR_HEADER, COLOR_HEADER_ALT, t)
        try:
            self.header.configure(fg_color=color)
        except Exception:
            return
        self.after(50, lambda: self._animate_header(frame + 1))

    def _animate_avatar(self, frame=0):
        if not self._alive:
            return
        t = (math.sin(frame * 0.05) + 1) / 2
        color = lerp_color(COLOR_USER_BUBBLE, COLOR_ACCENT, t)
        try:
            self.avatar.configure(fg_color=color)
        except Exception:
            return
        self.after(55, lambda: self._animate_avatar(frame + 1))

    # ============================================================
    # CHAT AREA
    # ============================================================
    def _build_chat_area(self):
        self.chat_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLOR_BG, scrollbar_button_color="#2a2f3d",
            scrollbar_button_hover_color="#3a3f4d",
        )
        self.chat_frame.grid(row=1, column=0, padx=6, pady=(6, 0), sticky="nsew")
        self.chat_frame.grid_columnconfigure(0, weight=1)

    # ============================================================
    # INPUT AREA
    # ============================================================
    def _build_input_area(self):
        input_frame = ctk.CTkFrame(self, fg_color=COLOR_HEADER, corner_radius=0, height=76)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.grid_propagate(False)
        input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message here...",
            height=44,
            corner_radius=22,
            font=("Segoe UI", 14),
            fg_color="#1e2230",
            border_width=2,
            border_color=COLOR_BORDER_IDLE,
        )
        self.entry.grid(row=0, column=0, padx=(16, 10), pady=16, sticky="ew")
        self.entry.bind("<Return>", lambda event: self.send_message())
        self.entry.bind("<FocusIn>", lambda e: self._tween_widget_border(
            self.entry, COLOR_BORDER_IDLE, COLOR_ACCENT))
        self.entry.bind("<FocusOut>", lambda e: self._tween_widget_border(
            self.entry, COLOR_ACCENT, COLOR_BORDER_IDLE))

        self.send_btn = ctk.CTkButton(
            input_frame, text="➤", width=44, height=44, corner_radius=22,
            font=("Segoe UI", 16, "bold"), fg_color=COLOR_USER_BUBBLE,
            hover_color="#2563eb", command=self.send_message,
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 16), pady=16)
        self.send_btn.bind("<Enter>", lambda e: self._tween_widget_fg(
            self.send_btn, COLOR_USER_BUBBLE, COLOR_USER_BUBBLE_HOVER))
        self.send_btn.bind("<Leave>", lambda e: self._tween_widget_fg(
            self.send_btn, COLOR_USER_BUBBLE_HOVER, COLOR_USER_BUBBLE))

    # ---- generic hover/focus tween helpers ----
    def _tween_widget_fg(self, widget, c_from, c_to, step=0, steps=6):
        if not self._alive:
            return
        t = step / steps
        try:
            widget.configure(fg_color=lerp_color(c_from, c_to, t))
        except Exception:
            return
        if step < steps:
            self.after(15, lambda: self._tween_widget_fg(widget, c_from, c_to, step + 1, steps))

    def _tween_widget_border(self, widget, c_from, c_to, step=0, steps=6):
        if not self._alive:
            return
        t = step / steps
        try:
            widget.configure(border_color=lerp_color(c_from, c_to, t))
        except Exception:
            return
        if step < steps:
            self.after(15, lambda: self._tween_widget_border(widget, c_from, c_to, step + 1, steps))

    def _animate_send_press(self):
        self.send_btn.configure(width=38, height=38)
        self.after(90, lambda: self.send_btn.configure(width=44, height=44))

    # ============================================================
    # SERVER HEALTH
    # ============================================================
    def check_server_health(self):
        def _check():
            try:
                r = requests.get(f"{SERVER_URL}/health", timeout=3)
                online = r.status_code == 200
            except Exception:
                online = False
            self.after(0, lambda: self._update_status(online))

        threading.Thread(target=_check, daemon=True).start()

    def _update_status(self, online):
        if online:
            self.status_label.configure(text="Online")
            self._pulse_status(True)
        else:
            self.status_dot.configure(text_color=COLOR_OFFLINE)
            self.status_label.configure(text="Server offline")
            self.add_bubble(
                f"⚠️ Cannot reach server. Make sure server/app.py is running at {SERVER_URL}.",
                sender="bot",
            )

    def _pulse_status(self, online, frame=0):
        if not self._alive:
            return
        if not online:
            self.status_dot.configure(text_color=COLOR_OFFLINE)
            return
        t = (math.sin(frame * 0.15) + 1) / 2
        try:
            self.status_dot.configure(text_color=lerp_color(COLOR_ONLINE_DIM, COLOR_ONLINE, t))
        except Exception:
            return
        self.after(60, lambda: self._pulse_status(True, frame + 1))

    # ============================================================
    # WELCOME
    # ============================================================
    def _welcome_message(self):
        self.add_bubble("Hi! I'm Kava Sakhi 🪷 — how can I help you today?", sender="bot")

    # ============================================================
    # CHAT BUBBLES (slide + fade in)
    # ============================================================
    def add_bubble(self, text, sender="user", animate=True):
        is_user = sender == "user"
        bubble_color = COLOR_USER_BUBBLE if is_user else COLOR_BOT_BUBBLE
        anchor_side = "e" if is_user else "w"
        timestamp = datetime.now().strftime("%I:%M %p")

        wrapper = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        wrapper.grid(row=self._row, column=0, sticky=anchor_side, padx=10, pady=6)
        self._row += 1

        bubble = ctk.CTkLabel(
            wrapper,
            text=text,
            wraplength=440,
            justify="left",
            fg_color=COLOR_BG if animate else bubble_color,
            text_color="white" if is_user else COLOR_TEXT,
            corner_radius=16,
            font=("Segoe UI", 13),
            padx=14,
            pady=10,
        )
        slide_offset = 70
        start_pad = (0, slide_offset) if is_user else (slide_offset, 0)
        bubble.pack(anchor=anchor_side, padx=start_pad if animate else 0)

        time_label = ctk.CTkLabel(
            wrapper, text=timestamp, font=("Segoe UI", 9), text_color=COLOR_MUTED
        )
        time_label.pack(anchor=anchor_side, padx=4, pady=(2, 0))

        self._scroll_to_bottom_smooth()

        if animate:
            self._animate_bubble_in(bubble, COLOR_BG, bubble_color, is_user, slide_offset)

        return bubble

    def _animate_bubble_in(self, bubble, c_from, c_to, is_user, offset, step=0, steps=10):
        if not self._alive:
            return
        t = step / steps
        eased = ease_out_cubic(t)
        color = lerp_color(c_from, c_to, eased)
        pad = round(offset * (1 - eased))
        try:
            bubble.configure(fg_color=color)
            bubble.pack_configure(padx=(0, pad) if is_user else (pad, 0))
        except Exception:
            return
        if step < steps:
            self.after(16, lambda: self._animate_bubble_in(
                bubble, c_from, c_to, is_user, offset, step + 1, steps))
        else:
            self._scroll_to_bottom_smooth()

    # ============================================================
    # SMOOTH SCROLL
    # ============================================================
    def _scroll_to_bottom_smooth(self):
        try:
            canvas = self.chat_frame._parent_canvas
            self.update_idletasks()
            start = canvas.yview()[0]
        except Exception:
            return
        self._scroll_step(canvas, start, 1.0, 0, 8)

    def _scroll_step(self, canvas, start, end, step, steps):
        if not self._alive:
            return
        t = step / steps
        pos = start + (end - start) * ease_out_cubic(t)
        try:
            canvas.yview_moveto(pos)
        except Exception:
            return
        if step < steps:
            self.after(12, lambda: self._scroll_step(canvas, start, end, step + 1, steps))

    # ============================================================
    # TYPING INDICATOR
    # ============================================================
    def _show_typing_indicator(self):
        wrapper = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        wrapper.grid(row=self._row, column=0, sticky="w", padx=10, pady=6)
        self._row += 1

        widget = TypingBubble(wrapper)
        widget.pack(anchor="w")

        self._typing_wrapper = wrapper
        self._typing_widget = widget
        self._scroll_to_bottom_smooth()

    def _clear_typing_indicator(self):
        if self._typing_widget:
            self._typing_widget.stop()
        if self._typing_wrapper:
            self._typing_wrapper.destroy()
        self._typing_widget = None
        self._typing_wrapper = None

    # ============================================================
    # SEND MESSAGE
    # ============================================================
    def send_message(self):
        user_text = self.entry.get().strip()
        if not user_text:
            return

        self.entry.delete(0, "end")
        self.add_bubble(user_text, sender="user")
        self._show_typing_indicator()
        self._animate_send_press()

        self.send_btn.configure(state="disabled")
        self.entry.configure(state="disabled")

        threading.Thread(target=self.call_server, args=(user_text,), daemon=True).start()

    def call_server(self, user_text):
        try:
            r = requests.post(
                f"{SERVER_URL}/api/chat",
                json={"session_id": SESSION_ID, "message": user_text},
                timeout=60,
            )
            data = r.json()
            reply = data.get("reply") or f"⚠️ Error: {data.get('error', 'Unknown error')}"
        except Exception as e:
            reply = f"⚠️ Could not reach server: {e}"

        self.after(0, lambda: self.finish_response(reply))

    def finish_response(self, reply):
        self._clear_typing_indicator()
        self.add_bubble(reply, sender="bot")
        self.send_btn.configure(state="normal")
        self.entry.configure(state="normal")
        self.entry.focus()

    # ============================================================
    # NEW CHAT
    # ============================================================
    def new_chat(self):
        global SESSION_ID
        SESSION_ID = str(uuid.uuid4())

        self._clear_typing_indicator()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self._row = 0

        self._welcome_message()


if __name__ == "__main__":
    app = ChatbotApp()
    app.mainloop()