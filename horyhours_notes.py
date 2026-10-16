#!/usr/bin/env python3
"""HoryHours Notes: a tiny, dark, floating quick-note for Linux."""

from __future__ import annotations

import os
import signal
import sys
import zipfile
from datetime import datetime
from threading import Event, Thread
from typing import Callable, Optional

from PyQt6.QtCore import (
    QPoint,
    QRect,
    QRectF,
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QSettings,
    QTimer,
    QObject,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QAction,
    QFontDatabase,
    QPainter,
    QPainterPath,
    QPen,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedLayout,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QMessageBox,
    QMenu,
)


APP_NAME = "HoryHours Notes"
APP_VERSION = "0.1.1-beta"
ORGANIZATION = "HoryHours"
# Compact geometry keeps the note present without taking over the desktop.
BUBBLE_SIZE = 52
PANEL_SIZE = QSize(280, 260)
PANEL_MIN_SIZE = QSize(220, 180)
PANEL_SIZE_SETTING = "expandedSize"
MATCH_HISTORY_SETTING = "matchHistory"
MAX_HISTORY_ENTRIES = 124

# Based on the current task table for The Skeld. Among Us has common, short,
# and long tasks; it does not have an official "medium" category.
SKELD_TASKS = (
    (
        "Longas",
        "6 tarefas em várias etapas",
        (
            ("Alinhar saída do motor", "Motor superior → motor inferior"),
            ("Esvaziar lixo", "Cafeteria ou O2 → Depósito"),
            ("Abastecer motores", "Depósito → motor superior/inferior"),
            ("Inspecionar amostra", "MedBay; aguarde a análise"),
            ("Iniciar reator", "Reator"),
            ("Enviar escaneamento", "MedBay • tarefa visual"),
        ),
    ),
    (
        "Comuns",
        "Todos recebem quando esta categoria está ativa",
        (
            ("Consertar fiação", "3 painéis, na ordem indicada"),
            ("Passar o cartão", "Administração"),
        ),
    ),
    (
        "Curtas",
        "10 tarefas de conclusão rápida",
        (
            ("Calibrar distribuidor", "Elétrica"),
            ("Traçar rota", "Navegação"),
            ("Limpar filtro de O2", "O2"),
            ("Limpar ventilação", "Reator"),
            ("Destruir asteroides", "Armas • tarefa visual"),
            ("Desviar energia", "Elétrica → um dos sistemas"),
            ("Ativar escudos", "Escudos • tarefa visual"),
            ("Estabilizar direção", "Navegação"),
            ("Desbloquear manifolds", "Reator"),
            ("Enviar dados", "um sistema → Administração"),
        ),
    ),
)

SKELD_TASKS_BY_ROOM = (
    ("Administração", "2 tarefas", (("Passar o cartão", "Comum"), ("Enviar dados", "Curta"))),
    ("Armas", "1 tarefa", (("Destruir asteroides", "Curta • visual"),)),
    ("Cafeteria", "1 tarefa", (("Esvaziar lixo", "Longa"),)),
    ("Depósito", "2 tarefas", (("Abastecer motores", "Longa"), ("Esvaziar lixo", "Longa"))),
    ("Elétrica", "2 tarefas", (("Calibrar distribuidor", "Curta"), ("Desviar energia", "Curta"))),
    ("Escudos", "1 tarefa", (("Ativar escudos", "Curta • visual"),)),
    ("MedBay", "2 tarefas", (("Inspecionar amostra", "Longa"), ("Enviar escaneamento", "Longa • visual"))),
    ("Motores", "2 tarefas", (("Alinhar saída do motor", "Longa"), ("Abastecer motores", "Longa"))),
    ("Navegação", "3 tarefas", (("Traçar rota", "Curta"), ("Estabilizar direção", "Curta"), ("Enviar dados", "Curta"))),
    ("O2", "2 tarefas", (("Limpar filtro de O2", "Curta"), ("Esvaziar lixo", "Longa"))),
    ("Reator", "3 tarefas", (("Limpar ventilação", "Curta"), ("Iniciar reator", "Longa"), ("Desbloquear manifolds", "Curta"))),
)


def _task_categories(
    common: tuple[str, ...], short: tuple[str, ...], long: tuple[str, ...]
) -> tuple[tuple[str, str, tuple[tuple[str, str], ...]], ...]:
    return (
        ("Longas", f"{len(long)} tarefas", tuple((task, "") for task in long)),
        ("Comuns", f"{len(common)} tarefas compartilhadas", tuple((task, "") for task in common)),
        ("Curtas", f"{len(short)} tarefas", tuple((task, "") for task in short)),
    )


TASKS_BY_MAP = {
    "The Skeld": SKELD_TASKS,
    "MIRA HQ": _task_categories(
        ("Inserir código de identificação", "Consertar fiação"),
        (
            "Montar artefato", "Comprar bebida", "Traçar rota", "Limpar filtro de O2",
            "Limpar ventilação", "Desviar energia (Laboratório)", "Esvaziar lixo",
            "Abastecer motores", "Medir clima", "Ativar escudos", "Processar dados",
            "Executar diagnóstico", "Organizar amostras", "Desbloquear manifolds",
        ),
        ("Destruir asteroides", "Desviar energia (fora do Laboratório)", "Iniciar reator", "Enviar escaneamento", "Regar plantas"),
    ),
    "Polus": _task_categories(
        ("Consertar fiação", "Inserir chaves", "Escanear cartão de embarque", "Passar o cartão"),
        (
            "Alinhar telescópio", "Traçar rota", "Destruir asteroides", "Esvaziar lixo",
            "Encher recipientes", "Consertar nó climático (CA, MLG)", "Monitorar árvore",
            "Registrar temperatura", "Reparar broca", "Guardar artefatos",
            "Enviar escaneamento", "Desbloquear manifolds",
        ),
        (
            "Consertar nó climático (TB, IRO, PD, GI)", "Abastecer motores",
            "Inspecionar amostra", "Abrir canais de água", "Reiniciar Wi‑Fi",
            "Trocar jarro de água", "Iniciar reator", "Enviar dados",
        ),
    ),
    "The Airship": _task_categories(
        ("Inserir código de identificação", "Consertar fiação"),
        (
            "Limpar banheiro", "Limpar ventilação", "Descontaminar", "Desviar energia",
            "Vestir manequim", "Consertar chuveiro", "Montar hambúrguer", "Pegar toalhas",
            "Polir rubi", "Guardar pistolas", "Guardar rifles", "Organizar registros",
            "Estabilizar direção", "Enviar dados",
        ),
        (
            "Calibrar distribuidor", "Revelar fotos", "Esvaziar lixo", "Abastecer motores",
            "Reiniciar disjuntores", "Rebobinar fitas", "Iniciar ventiladores",
            "Desbloquear cofre", "Enviar dados",
        ),
    ),
    "The Fungle": _task_categories(
        ("Coletar amostras", "Inserir código de identificação", "Trocar peças", "Assar marshmallow"),
        (
            "Montar artefato", "Construir castelo de areia", "Coletar conchas", "Girar gerador",
            "Esvaziar lixo", "Encontrar sinal", "Consertar antena", "Consertar fiação",
            "Levantar pesos", "Monitorar cogumelo", "Jogar videogame", "Registrar temperatura",
            "Lançar frisbee",
        ),
        (
            "Cozinhar peixe", "Extrair combustível", "Ajudar critter", "Içar suprimentos",
            "Minerar minérios", "Polir gema", "Preparar vegetais", "Trocar jarro de água",
            "Regar plantas",
        ),
    ),
}


def _reduced_motion_requested() -> bool:
    """Honor the desktop equivalent of prefers-reduced-motion when available."""
    return os.environ.get("HORYHOURS_REDUCED_MOTION", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _ui_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Prefer a calm, readable UI face while keeping a sensible Linux fallback."""
    families = QFontDatabase.families()
    for family in ("IBM Plex Sans", "Noto Sans", "Cantarell", "Liberation Sans"):
        if family in families:
            font = QFont(family, size, weight)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            return font
    return QFont("Sans", size, weight)


def _history_entry_text(entry: dict[str, str]) -> str:
    return f"HoryHours Notes — partida\nData: {entry['savedAt']}\n\n{entry['note']}\n"


def _history_entry_filename(entry: dict[str, str], index: int) -> str:
    safe_date = "".join(
        character if character.isalnum() else "-" for character in entry["savedAt"]
    ).strip("-")
    return f"horyhours-partida-{index + 1:03d}-{safe_date}.txt"


class GlobalShortcutListener(QObject):
    """Listen for HoryHours shortcuts globally on X11/XWayland."""

    triggered = pyqtSignal()
    taskSwitcherTriggered = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._stop = Event()
        self._thread: Optional[Thread] = None
        self._display = None
        self._root = None
        self.available = False

    def start(self) -> bool:
        if not QApplication.platformName().lower().startswith("xcb"):
            return False
        try:
            from Xlib import X, XK, display, error

            connection = display.Display()
            root = connection.screen().root
            space_keycode = connection.keysym_to_keycode(XK.string_to_keysym("space"))
            task_switcher_keycode = connection.keysym_to_keycode(XK.string_to_keysym("h"))
            keycodes = {
                space_keycode: self.triggered,
                task_switcher_keycode: self.taskSwitcherTriggered,
            }
            modifiers_by_keycode = {
                space_keycode: X.ControlMask | X.ShiftMask,
                task_switcher_keycode: X.ControlMask | X.ShiftMask | X.Mod1Mask,
            }
            error_handler = error.CatchError()
            connection.set_error_handler(error_handler)
            for lock_mask in (0, X.LockMask, X.Mod2Mask, X.LockMask | X.Mod2Mask):
                for keycode, modifiers in modifiers_by_keycode.items():
                    root.grab_key(keycode, modifiers | lock_mask, True, X.GrabModeAsync, X.GrabModeAsync)
            connection.sync()
            if error_handler.get_error() is not None:
                connection.close()
                return False
        except Exception:
            try:
                connection.close()
            except (UnboundLocalError, Exception):
                pass
            return False

        self._display = connection
        self._root = root
        self._x_event = X
        self._key_actions = {
            keycode: signal for keycode, signal in keycodes.items()
        }
        self._stop.clear()
        self._thread = Thread(target=self._run, name="horyhours-global-shortcut", daemon=True)
        self._thread.start()
        self.available = True
        return True

    def _run(self) -> None:
        import select

        while not self._stop.is_set() and self._display is not None:
            ready, _, _ = select.select([self._display.fileno()], [], [], 0.25)
            if not ready:
                continue
            while self._display.pending_events():
                event = self._display.next_event()
                if event.type == self._x_event.KeyPress:
                    action = self._key_actions.get(event.detail)
                    if action is not None:
                        action.emit()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.4)
        if self._root is not None:
            try:
                self._root.ungrab_key(0, 0)
                self._display.sync()
                self._display.close()
            except Exception:
                pass
        self._display = None
        self._root = None
        self.available = False


class DragSurface(QWidget):
    """A small surface that can move the frameless parent window."""

    pressed = pyqtSignal(QPoint)
    dragged = pyqtSignal(QPoint)
    released = pyqtSignal()
    tripleClicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._pressed = False
        self._drag_press_position: Optional[QPoint] = None
        self._system_move_started = False
        self._mouse_grabbed = False
        self._title_click_count = 0
        self._title_click_timer = QTimer(self)
        self._title_click_timer.setSingleShot(True)
        self._title_click_timer.setInterval(520)
        self._title_click_timer.timeout.connect(self._reset_title_clicks)

    def _reset_title_clicks(self) -> None:
        self._title_click_count = 0

    def _clicked_title(self, event) -> bool:
        child = self.childAt(event.position().toPoint())
        return bool(child and child.objectName() == "heading")

    @staticmethod
    def _is_wayland() -> bool:
        return QApplication.platformName().lower().startswith("wayland")

    @staticmethod
    def _is_x11() -> bool:
        return QApplication.platformName().lower().startswith("xcb")

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            if self.objectName() == "header" and self._clicked_title(event):
                self._title_click_count = self._title_click_count + 1
                self._title_click_timer.start()
                if self._title_click_count == 3:
                    self._reset_title_clicks()
                    self.tripleClicked.emit()
            self._pressed = True
            self._drag_press_position = event.globalPosition().toPoint()
            self._system_move_started = False
            self.pressed.emit(self._drag_press_position)

            if self._is_x11():
                # X11/XWayland allows a normal mouse grab, so the compact
                # bubble keeps receiving movement even after leaving itself.
                self.grabMouse()
                self._mouse_grabbed = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._pressed:
            global_position = event.globalPosition().toPoint()
            if (
                self._is_wayland()
                and self._drag_press_position is not None
                and not self._system_move_started
                and (global_position - self._drag_press_position).manhattanLength()
                >= QApplication.startDragDistance()
            ):
                # Start only after the click has become a drag, otherwise
                # Wayland can consume the release event needed by the click.
                window_handle = self.window().windowHandle()
                self._system_move_started = bool(
                    window_handle and window_handle.startSystemMove()
                )

            # Wayland's compositor owns the pointer after startSystemMove().
            # On X11/offscreen platforms, retain a small manual fallback.
            if not self._system_move_started:
                self.dragged.emit(global_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._pressed and event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self._drag_press_position = None
            self._system_move_started = False
            if self._mouse_grabbed:
                self.releaseMouse()
                self._mouse_grabbed = False
            self.released.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class Bubble(DragSurface):
    """The only visible surface while the note is collapsed."""

    clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("bubble")
        self.setFixedSize(BUBBLE_SIZE, BUBBLE_SIZE)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Abrir nota rápida")
        self.setAccessibleName("Abrir HoryHours Notes")
        self._press_position: Optional[QPoint] = None
        self._did_drag = False
        self._pressed_visual = False
        self._hovered = False
        self._has_active_note = False

    def set_has_active_note(self, active: bool) -> None:
        if self._has_active_note != active:
            self._has_active_note = active
            self.setToolTip("Partida em andamento — abrir nota" if active else "Abrir nota rápida")
            self.update()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.globalPosition().toPoint()
            self._did_drag = False
            self._pressed_visual = True
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._press_position is not None:
            current = event.globalPosition().toPoint()
            if (current - self._press_position).manhattanLength() > 5:
                self._did_drag = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        was_dragging = self._did_drag
        if self._system_move_started and self._press_position is not None:
            final_position = event.globalPosition().toPoint()
            was_dragging = was_dragging or (
                (final_position - self._press_position).manhattanLength()
                >= QApplication.startDragDistance()
            )
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._press_position = None
        self._did_drag = False
        self._pressed_visual = False
        self.update()
        if not was_dragging and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Pressing the ball gives the exact small tactile scale recommended by
        # the UI guidelines, while hover only changes luminance.
        scale = 0.96 if self._pressed_visual else 1.0
        size = float(self.width())
        painter.translate(size / 2, size / 2)
        painter.scale(scale, scale)
        painter.translate(-size / 2, -size / 2)

        # A restrained halo keeps the ball readable without turning it into a
        # large glowing widget.
        halo = QPainterPath()
        halo.addEllipse(QRectF(3, 3, size - 6, size - 6))
        painter.fillPath(halo, QColor("#3B392F" if self._hovered else "#2B2923"))

        ball = QPainterPath()
        ball.addEllipse(QRectF(4, 4, size - 8, size - 8))
        painter.fillPath(ball, QColor("#1B1913"))
        outline = "#B8D48A" if self._has_active_note else ("#C4BBAA" if self._hovered else "#514D43")
        painter.setPen(QPen(QColor(outline), 1.6 if self._has_active_note else 1.1))
        painter.drawPath(ball)

        if self._has_active_note:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#B8D48A"))
            painter.drawEllipse(QRectF(size - 13, 7, 6, 6))

        painter.setPen(QColor("#E9E3D7"))
        painter.setFont(_ui_font(22, QFont.Weight.DemiBold))
        painter.drawText(
            QRectF(0, size * 0.25, size, size * 0.5),
            Qt.AlignmentFlag.AlignCenter,
            "✦",
        )


class ResizeHandle(QWidget):
    """An unobtrusive bottom-right handle for the expanded note."""

    def __init__(self, note: "FloatingNote", parent: QWidget) -> None:
        super().__init__(parent)
        self._note = note
        self._manual_origin: Optional[QPoint] = None
        self._manual_geometry: Optional[QRect] = None
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setToolTip("Redimensionar nota")
        self.setAccessibleName("Redimensionar nota")

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() != Qt.MouseButton.LeftButton or self._note._animating:
            event.ignore()
            return

        window_handle = self._note.windowHandle()
        native_resize = bool(
            window_handle
            and window_handle.startSystemResize(
                Qt.Edge.RightEdge | Qt.Edge.BottomEdge
            )
        )
        if not native_resize:
            self._manual_origin = event.globalPosition().toPoint()
            self._manual_geometry = self._note.geometry()
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._manual_origin is None or self._manual_geometry is None:
            super().mouseMoveEvent(event)
            return

        delta = event.globalPosition().toPoint() - self._manual_origin
        self._note.resize(
            max(
                self._note.panel.minimumWidth(),
                self._manual_geometry.width() + delta.x(),
            ),
            max(
                self._note.panel.minimumHeight(),
                self._manual_geometry.height() + delta.y(),
            ),
        )
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            self._manual_origin = None
            self._manual_geometry = None
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SkeldTasksDialog(QDialog):
    """A light, scrollable reference for Among Us tasks."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("tasks-dialog")
        self.setWindowTitle("Tarefas")
        self.setModal(True)
        self.setMinimumSize(390, 430)
        self.resize(430, 530)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 15, 16, 16)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.tasks_title = QLabel("Tarefas", self)
        self.tasks_title.setObjectName("tasks-title")
        self.tasks_title.setFont(_ui_font(15, QFont.Weight.DemiBold))
        self.tasks_subtitle = QLabel("Guia rápido em português", self)
        self.tasks_subtitle.setObjectName("tasks-subtitle")
        title_box.addWidget(self.tasks_title)
        title_box.addWidget(self.tasks_subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        close = QToolButton(self)
        close.setObjectName("tasks-close-button")
        close.setText("×")
        close.setToolTip("Fechar tarefas")
        close.setAccessibleName("Fechar lista de tarefas")
        close.clicked.connect(self.reject)
        header.addWidget(close)
        outer.addLayout(header)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)

        self.map_selector = QComboBox(self)
        self.map_selector.setObjectName("map-selector")
        self.map_selector.setToolTip("Escolher mapa")
        self.map_selector.setAccessibleName("Escolher mapa de Among Us")
        self.map_selector.addItems(TASKS_BY_MAP.keys())
        self.map_selector.setCurrentText("The Skeld")
        self.map_selector.currentTextChanged.connect(self._set_map)
        controls.addWidget(self.map_selector, 1)

        view_switcher = QFrame(self)
        view_switcher.setObjectName("task-view-switcher")
        switcher_layout = QHBoxLayout(view_switcher)
        switcher_layout.setContentsMargins(3, 3, 3, 3)
        switcher_layout.setSpacing(3)
        self.category_view = QToolButton(view_switcher)
        self.category_view.setObjectName("task-view-button")
        self.category_view.setText("Categoria")
        self.category_view.setCheckable(True)
        self.category_view.setChecked(True)
        self.category_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.category_view.clicked.connect(lambda: self._set_view("category"))
        self.room_view = QToolButton(view_switcher)
        self.room_view.setObjectName("task-view-button")
        self.room_view.setText("Por sala")
        self.room_view.setCheckable(True)
        self.room_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.room_view.clicked.connect(lambda: self._set_view("room"))
        switcher_layout.addWidget(self.category_view)
        switcher_layout.addWidget(self.room_view)
        controls.addWidget(view_switcher, 1)
        outer.addLayout(controls)

        scroll = QScrollArea(self)
        scroll.setObjectName("tasks-scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(scroll)
        content.setObjectName("tasks-content")
        self.sections = QVBoxLayout(content)
        self.sections.setContentsMargins(0, 0, 0, 0)
        self.sections.setSpacing(6)
        self._view_mode = "category"
        self._map_name = "The Skeld"
        self._render_sections()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _set_view(self, mode: str) -> None:
        if self._view_mode == mode:
            self.category_view.setChecked(mode == "category")
            self.room_view.setChecked(mode == "room")
            return
        self._view_mode = mode
        self.category_view.setChecked(mode == "category")
        self.room_view.setChecked(mode == "room")
        self._render_sections()

    def _set_map(self, map_name: str) -> None:
        self._map_name = map_name
        self.tasks_subtitle.setText(f"Guia rápido • {map_name}")
        is_skeld = map_name == "The Skeld"
        self.room_view.setEnabled(is_skeld)
        self.room_view.setToolTip("Ver tarefas por sala" if is_skeld else "Por sala disponível no The Skeld")
        if not is_skeld and self._view_mode == "room":
            self._view_mode = "category"
            self.category_view.setChecked(True)
        self._render_sections()

    def _render_sections(self) -> None:
        while self.sections.count():
            item = self.sections.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        groups = (
            SKELD_TASKS_BY_ROOM
            if self._map_name == "The Skeld" and self._view_mode == "room"
            else TASKS_BY_MAP[self._map_name]
        )
        for title_text, detail, tasks in groups:
            section = QFrame(self)
            section.setObjectName("task-section")
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(12, 10, 12, 10)
            section_layout.setSpacing(3)
            section_header = QHBoxLayout()
            section_header.setContentsMargins(0, 0, 0, 2)
            section_header.setSpacing(8)
            section_title = QLabel(title_text, section)
            section_title.setObjectName("task-section-title")
            section_title.setFont(_ui_font(10, QFont.Weight.DemiBold))
            section_detail = QLabel(detail, section)
            section_detail.setObjectName("task-section-detail")
            section_detail.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            section_header.addWidget(section_title)
            section_header.addStretch(1)
            section_header.addWidget(section_detail)
            section_layout.addLayout(section_header)
            for task_name, location in tasks:
                task_text = f"<span>•</span> <b>{task_name}</b>"
                if location:
                    task_text += f" <em>— {location}</em>"
                task = QLabel(task_text, section)
                task.setObjectName("task-row")
                task.setTextFormat(Qt.TextFormat.RichText)
                task.setWordWrap(True)
                section_layout.addWidget(task)
            self.sections.addWidget(section)
        self.sections.addStretch(1)


class MatchHistoryDialog(QDialog):
    """Local archive with export and confirmed removal controls."""

    def __init__(
        self,
        parent: QWidget,
        entries: list[dict[str, str]],
        remove_entry: Callable[[int], None],
    ) -> None:
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self._entries = list(entries)
        self._remove_entry = remove_entry
        self.setObjectName("history-dialog")
        self.setWindowTitle("Histórico de partidas")
        self.setModal(True)
        self.setMinimumSize(340, 380)
        self.resize(360, 500)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel("Histórico de partidas", self)
        title.setObjectName("history-title")
        title.setFont(_ui_font(14, QFont.Weight.DemiBold))
        self.history_subtitle = QLabel(self)
        self.history_subtitle.setObjectName("history-subtitle")
        title_box.addWidget(title)
        title_box.addWidget(self.history_subtitle)
        header.addLayout(title_box)
        header.addStretch(1)
        export_all = QToolButton(self)
        export_all.setObjectName("history-export-all-button")
        export_all.setText("Exportar tudo")
        export_all.setToolTip("Exportar todas as partidas em um arquivo .zip")
        export_all.setAccessibleName("Exportar todas as partidas em arquivo ZIP")
        export_all.clicked.connect(lambda: self._export_all(self._entries))
        self.export_all_button = export_all
        header.addWidget(export_all)
        close = QToolButton(self)
        close.setObjectName("history-close-button")
        close.setText("×")
        close.setToolTip("Fechar histórico")
        close.setAccessibleName("Fechar histórico de partidas")
        close.clicked.connect(self.reject)
        header.addWidget(close)
        outer.addLayout(header)

        scroll = QScrollArea(self)
        scroll.setObjectName("history-scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(scroll)
        content.setObjectName("history-content")
        self.records = QVBoxLayout(content)
        self.records.setContentsMargins(0, 0, 0, 0)
        self.records.setSpacing(8)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        self._render_entries()

    def _render_entries(self) -> None:
        while self.records.count():
            item = self.records.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if self._entries:
            self.history_subtitle.setText(
                f"{len(self._entries)} de {MAX_HISTORY_ENTRIES} partidas armazenadas"
            )
            for index, entry in enumerate(self._entries):
                card = QFrame(self)
                card.setObjectName("history-entry")
                entry_layout = QHBoxLayout(card)
                entry_layout.setContentsMargins(8, 8, 10, 8)
                entry_layout.setSpacing(7)
                rail = QFrame(card)
                rail.setObjectName("history-timeline-rail")
                rail.setFixedWidth(9)
                rail_layout = QVBoxLayout(rail)
                rail_layout.setContentsMargins(0, 1, 0, 1)
                rail_layout.setSpacing(0)
                marker = QLabel("•", rail)
                marker.setObjectName("history-timeline-marker")
                marker.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
                rail_layout.addWidget(marker)
                rail_layout.addStretch(1)
                entry_layout.addWidget(rail)
                entry_content = QWidget(card)
                card_layout = QVBoxLayout(entry_content)
                card_layout.setContentsMargins(10, 9, 10, 9)
                card_layout.setSpacing(5)
                timestamp = QLabel(entry["savedAt"], card)
                timestamp.setObjectName("history-entry-date")
                timestamp.setFont(_ui_font(9, QFont.Weight.DemiBold))
                note = QLabel(entry["note"], card)
                note.setObjectName("history-entry-note")
                note.setWordWrap(True)
                note.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                actions = QHBoxLayout()
                actions.setContentsMargins(0, 0, 0, 0)
                actions.setSpacing(5)
                export = QToolButton(card)
                export.setObjectName("history-export-button")
                export.setText("Exportar .txt")
                export.setToolTip("Exportar esta nota como arquivo de texto")
                export.clicked.connect(
                    lambda checked=False, saved_entry=entry, saved_index=index: self._export_entry(
                        saved_entry, saved_index
                    )
                )
                remove = QToolButton(card)
                remove.setObjectName("history-remove-button")
                remove.setText("Remover")
                remove.setToolTip("Remover esta partida do histórico")
                remove.clicked.connect(lambda checked=False, saved_index=index: self._confirm_remove(saved_index))
                actions.addWidget(export)
                actions.addWidget(remove)
                actions.addStretch(1)
                card_layout.addWidget(timestamp)
                card_layout.addWidget(note)
                card_layout.addLayout(actions)
                entry_layout.addWidget(entry_content, 1)
                self.records.addWidget(card)
        else:
            self.history_subtitle.setText("Nenhuma partida registrada ainda")
            empty = QLabel("Ao terminar uma partida, clique em Concluído para arquivar a nota atual.", self)
            empty.setObjectName("history-empty")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            self.records.addWidget(empty, 1)
        self.export_all_button.setEnabled(bool(self._entries))
        self.records.addStretch(1)

    def _confirm_remove(self, index: int) -> None:
        result = QMessageBox.question(
            self,
            "Remover partida?",
            "Esta nota será removida do histórico local e não poderá ser recuperada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        self._remove_entry(index)
        del self._entries[index]
        self._render_entries()

    def _export_entry(self, entry: dict[str, str], index: int) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar nota da partida",
            _history_entry_filename(entry, index),
            "Arquivo de texto (*.txt)",
        )
        if not filename:
            return
        if not filename.lower().endswith(".txt"):
            filename += ".txt"
        try:
            with open(filename, "w", encoding="utf-8") as exported:
                exported.write(_history_entry_text(entry))
        except OSError as error:
            QMessageBox.warning(self, "Não foi possível exportar", str(error))

    def _export_all(self, entries: list[dict[str, str]]) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar todas as partidas",
            "horyhours-partidas.zip",
            "Arquivo ZIP (*.zip)",
        )
        if not filename:
            return
        if not filename.lower().endswith(".zip"):
            filename += ".zip"
        try:
            with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
                for index, entry in enumerate(entries):
                    archive.writestr(_history_entry_filename(entry, index), _history_entry_text(entry))
        except OSError as error:
            QMessageBox.warning(self, "Não foi possível exportar", str(error))


class FloatingNote(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(ORGANIZATION, APP_NAME)
        self._drag_origin: Optional[QPoint] = None
        self._window_origin = QPoint()
        self._is_expanded = False
        self._animating = False
        self._animation: Optional[QPropertyAnimation] = None
        self._last_panel_size = QSize(PANEL_SIZE)
        self._reduced_motion = _reduced_motion_requested()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(280)
        self._save_timer.timeout.connect(self._save_note)

        self.setWindowTitle("HoryNotes")
        self._hide_from_task_switcher = self.settings.value(
            "hideFromTaskSwitcher", False, type=bool
        )
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("floating-note")
        self.setMinimumSize(BUBBLE_SIZE, BUBBLE_SIZE)
        self.resize(BUBBLE_SIZE, BUBBLE_SIZE)

        self.bubble = Bubble(self)
        self.bubble.clicked.connect(self.expand)
        self.bubble.pressed.connect(self._begin_drag)
        self.bubble.dragged.connect(self._move_from_global)
        self.bubble.released.connect(self._finish_drag)

        self.panel = self._build_panel()
        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.bubble)
        self.stack.addWidget(self.panel)
        self.stack.setCurrentWidget(self.bubble)

        self._load_note()
        self._restore_position()
        self._last_panel_size = self._load_panel_size()

        self._toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Space"), self)
        self._toggle_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._toggle_shortcut.activated.connect(self.toggle)

        self._task_switcher_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Shift+H"), self)
        self._task_switcher_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._task_switcher_shortcut.activated.connect(self._toggle_task_switcher_visibility)

        escape = QShortcut(QKeySequence("Escape"), self)
        escape.setContext(Qt.ShortcutContext.WindowShortcut)
        escape.activated.connect(self.collapse)

    def _build_panel(self) -> QFrame:
        panel = QFrame(self)
        panel.setObjectName("panel")
        panel.setMinimumSize(PANEL_MIN_SIZE)
        panel.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored,
        )

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(6, 6, 6, 5)
        outer.setSpacing(4)

        header = DragSurface(panel)
        header.setObjectName("header")
        header.setFixedHeight(23)
        header.pressed.connect(self._begin_drag)
        header.dragged.connect(self._move_from_global)
        header.released.connect(self._finish_drag)
        header.tripleClicked.connect(self._toggle_task_switcher_visibility)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)

        heading = QLabel("HoryNotes", header)
        heading.setObjectName("heading")
        heading.setFont(_ui_font(8, QFont.Weight.DemiBold))
        heading.setAccessibleName("HoryNotes")
        heading.setToolTip("3 cliques alternam o Alt+Tab • Ctrl+Alt+Shift+H")
        header_layout.addWidget(heading)

        minimize = QToolButton()
        minimize.setObjectName("minimize-button")
        minimize.setText("—")
        minimize.setToolTip("Encolher para a bolinha")
        minimize.setAccessibleName("Encolher nota")
        minimize.clicked.connect(self.collapse)

        tasks = QToolButton()
        tasks.setObjectName("tasks-button")
        tasks.setText("☷")
        tasks.setToolTip("Ver tarefas da The Skeld")
        tasks.setAccessibleName("Abrir lista de tarefas da The Skeld")
        tasks.clicked.connect(self._show_skeld_tasks)

        done = QToolButton()
        done.setObjectName("done-button")
        done.setText("Concluído")
        done.setToolTip("Arquivar nota e iniciar outra")
        done.setAccessibleName("Arquivar a nota desta partida")
        done.setEnabled(False)
        done.clicked.connect(self._complete_match)
        self.done_button = done

        history = QToolButton()
        history.setObjectName("history-button")
        history.setText("◷")
        history.setToolTip("Ver histórico de partidas")
        history.setAccessibleName("Abrir histórico de partidas")
        history.clicked.connect(self._show_history)
        self.history_button = history

        overflow = QToolButton()
        overflow.setObjectName("overflow-button")
        overflow.setText("⋯")
        overflow.setToolTip("Mais ações")
        overflow.setAccessibleName("Mais ações")
        overflow.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        overflow_menu = QMenu(overflow)
        history_action = QAction("Histórico de partidas", overflow_menu)
        history_action.triggered.connect(self._show_history)
        tasks_action = QAction("Tarefas da The Skeld", overflow_menu)
        tasks_action.triggered.connect(self._show_skeld_tasks)
        overflow_menu.addAction(history_action)
        overflow_menu.addAction(tasks_action)
        overflow.setMenu(overflow_menu)
        overflow.setVisible(False)
        self.overflow_button = overflow
        self.tasks_button = tasks

        close = QToolButton()
        close.setObjectName("close-button")
        close.setText("×")
        close.setToolTip("Sair")
        close.setAccessibleName("Sair do HoryHours Notes")
        close.clicked.connect(self.close)

        header_layout.addWidget(done)
        header_layout.addStretch(1)
        header_layout.addWidget(history)
        header_layout.addWidget(tasks)
        header_layout.addWidget(overflow)
        header_layout.addWidget(minimize)
        header_layout.addWidget(close)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(header)

        self.editor = QTextEdit(panel)
        self.editor.setObjectName("editor")
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText("Anote o que está acontecendo nesta partida...")
        self.editor.setTabChangesFocus(False)
        self.editor.setFont(_ui_font(12))
        self.editor.textChanged.connect(self._schedule_save)
        self.editor.textChanged.connect(self._update_done_enabled)
        outer.addWidget(self.editor, 1)
        self.resize_handle = ResizeHandle(self, panel)
        return panel

    def _apply_window_flags(self) -> None:
        window_type = (
            Qt.WindowType.Tool
            if self._hide_from_task_switcher
            else Qt.WindowType.Window
        )
        self.setWindowFlags(
            window_type
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

    def _toggle_task_switcher_visibility(self) -> None:
        was_visible = self.isVisible()
        geometry = self.geometry()
        self._hide_from_task_switcher = not self._hide_from_task_switcher
        self.settings.setValue("hideFromTaskSwitcher", self._hide_from_task_switcher)
        self._apply_window_flags()
        self.setGeometry(geometry)
        if was_visible:
            self.show()
            self.raise_()
            QTimer.singleShot(0, self._raise_again)

    def _raise_again(self) -> None:
        if self.isVisible():
            self.raise_()

    def _update_header_actions(self) -> None:
        if not hasattr(self, "overflow_button"):
            return
        compact = self._is_expanded and self.width() < 280
        self.history_button.setVisible(not compact)
        self.tasks_button.setVisible(not compact)
        self.overflow_button.setVisible(compact)

    def _show_skeld_tasks(self) -> None:
        if self._animating:
            return
        dialog = SkeldTasksDialog(self)
        dialog.exec()

    def set_global_shortcut_active(self, active: bool) -> None:
        """Avoid toggling twice when X11 receives the global accelerator."""
        self._toggle_shortcut.setEnabled(not active)
        self._task_switcher_shortcut.setEnabled(not active)

    def _load_history(self) -> list[dict[str, str]]:
        stored = self.settings.value(MATCH_HISTORY_SETTING, [])
        if not isinstance(stored, list):
            return []
        entries: list[dict[str, str]] = []
        for entry in stored:
            if not isinstance(entry, dict):
                continue
            note = entry.get("note")
            saved_at = entry.get("savedAt")
            if isinstance(note, str) and isinstance(saved_at, str):
                entries.append({"note": note, "savedAt": saved_at})
        return entries[:MAX_HISTORY_ENTRIES]

    def _complete_match(self) -> None:
        note = self.editor.toPlainText().strip()
        if not note:
            self._show_done_feedback("—", "Nada para arquivar")
            return
        entries = self._load_history()
        entries.insert(
            0,
            {
                "note": note,
                "savedAt": datetime.now().astimezone().strftime("%d/%m/%Y • %H:%M"),
            },
        )
        self.settings.setValue(MATCH_HISTORY_SETTING, entries[:MAX_HISTORY_ENTRIES])
        self.editor.clear()
        self._save_note()
        self.settings.sync()
        self._show_done_feedback("Salvo", "Nota arquivada")

    def _update_done_enabled(self) -> None:
        has_note = bool(self.editor.toPlainText().strip())
        self.done_button.setEnabled(has_note)
        self.bubble.set_has_active_note(has_note)

    def _show_done_feedback(self, symbol: str, tooltip: str) -> None:
        self.done_button.setText(symbol)
        self.done_button.setToolTip(tooltip)

        def reset() -> None:
            self.done_button.setText("Concluído")
            self.done_button.setToolTip("Arquivar nota e iniciar outra")

        QTimer.singleShot(1100, reset)

    def _show_history(self) -> None:
        if self._animating:
            return
        dialog = MatchHistoryDialog(self, self._load_history(), self._remove_history_entry)
        dialog.exec()

    def _remove_history_entry(self, index: int) -> None:
        entries = self._load_history()
        if not 0 <= index < len(entries):
            return
        del entries[index]
        self.settings.setValue(MATCH_HISTORY_SETTING, entries)
        self.settings.sync()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        if self._is_expanded:
            self.panel.setGeometry(self.rect())
            self._update_header_actions()
        if hasattr(self, "resize_handle") and self._is_expanded:
            self.resize_handle.move(
                self.panel.width() - self.resize_handle.width(),
                self.panel.height() - self.resize_handle.height(),
            )
        if self._is_expanded and not self._animating:
            self._last_panel_size = QSize(self.size())
            self._save_panel_size()

    def _schedule_save(self) -> None:
        self._save_timer.start()

    def _save_note(self) -> None:
        self.settings.setValue("note", self.editor.toPlainText())
        self.settings.sync()

    def _load_note(self) -> None:
        self.editor.setPlainText(str(self.settings.value("note", "")))

    def _size_limited_to_screen(self, size: QSize) -> QSize:
        area = self._screen_area()
        if area is None:
            return QSize(size)
        return QSize(min(size.width(), area.width()), min(size.height(), area.height()))

    def _load_panel_size(self) -> QSize:
        stored = self.settings.value(PANEL_SIZE_SETTING)
        if not isinstance(stored, QSize) or not stored.isValid():
            return self._size_limited_to_screen(PANEL_SIZE)
        if (
            stored.width() < PANEL_MIN_SIZE.width()
            or stored.height() < PANEL_MIN_SIZE.height()
        ):
            return self._size_limited_to_screen(PANEL_SIZE)
        return self._size_limited_to_screen(stored)

    def _save_panel_size(self) -> None:
        size = self._size_limited_to_screen(self._last_panel_size)
        if (
            size.width() < PANEL_MIN_SIZE.width()
            or size.height() < PANEL_MIN_SIZE.height()
        ):
            size = self._size_limited_to_screen(PANEL_SIZE)
        self.settings.setValue(PANEL_SIZE_SETTING, size)
        self.settings.sync()

    def _restore_position(self) -> None:
        stored = self.settings.value("position")
        if isinstance(stored, QPoint):
            self.move(self._clamp_position(stored, QSize(BUBBLE_SIZE, BUBBLE_SIZE)))
            return

        screen = QApplication.primaryScreen()
        if screen is None:
            self.move(24, 24)
            return
        area = screen.availableGeometry()
        self.move(area.right() - BUBBLE_SIZE - 24, area.bottom() - BUBBLE_SIZE - 24)

    def _screen_area(self):
        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen else None

    def _clamp_position(self, position: QPoint, size: QSize) -> QPoint:
        area = self._screen_area()
        if area is None:
            return position
        max_x = max(area.left(), area.right() - size.width() + 1)
        max_y = max(area.top(), area.bottom() - size.height() + 1)
        return QPoint(
            max(area.left(), min(position.x(), max_x)),
            max(area.top(), min(position.y(), max_y)),
        )

    def _begin_drag(self, global_position: QPoint) -> None:
        self.raise_()
        self._drag_origin = global_position
        self._window_origin = self.frameGeometry().topLeft()

    def _move_from_global(self, global_position: QPoint) -> None:
        if self._drag_origin is None:
            self._begin_drag(global_position)
        delta = global_position - self._drag_origin
        self.move(self._clamp_position(self._window_origin + delta, self.size()))

    def _finish_drag(self) -> None:
        if self._drag_origin is not None:
            self._save_position()
        self._drag_origin = None

    def _save_position(self) -> None:
        # Both states now share their top-left corner, so restoring this
        # position also restores the exact origin of the morph animation.
        self.settings.setValue("position", self.pos())

    def moveEvent(self, event) -> None:  # noqa: N802 - Qt API
        # Native Wayland moves update the top-level window directly, so keep
        # the latest location even if the compositor consumes the final drag
        # event before it reaches the child surface.
        if self._drag_origin is not None and not self._animating:
            self._save_position()
        super().moveEvent(event)

    def toggle(self) -> None:
        if self._animating:
            return
        self.raise_()
        self.expand() if not self._is_expanded else self.collapse()

    def expand(self) -> None:
        if self._is_expanded or self._animating:
            return

        self.raise_()
        self.activateWindow()

        # Keep the upper-left corner fixed: the bubble becomes the upper-left
        # tip of the editor instead of expanding away from its lower-right.
        start = QRect(self.pos(), QSize(BUBBLE_SIZE, BUBBLE_SIZE))
        target_position = self._clamp_position(start.topLeft(), self._last_panel_size)
        target = QRect(target_position, self._last_panel_size)
        self._is_expanded = True
        self.stack.setCurrentWidget(self.panel)
        self._animate_geometry(start, target, self._finish_expand)

    def _finish_expand(self) -> None:
        self.setMinimumSize(PANEL_MIN_SIZE)
        self._update_header_actions()
        self.editor.setFocus()

    def collapse(self) -> None:
        if not self._is_expanded or self._animating:
            return

        # Collapse into the same upper-left tip used to open the panel.
        start = QRect(self.pos(), self.size())
        self.setMinimumSize(BUBBLE_SIZE, BUBBLE_SIZE)
        target_position = self._clamp_position(
            start.topLeft(),
            QSize(BUBBLE_SIZE, BUBBLE_SIZE),
        )
        target = QRect(target_position, QSize(BUBBLE_SIZE, BUBBLE_SIZE))
        self._animate_geometry(start, target, self._finish_collapse)

    def _animate_geometry(self, start: QRect, target: QRect, finished) -> None:
        if self._animation is not None:
            self._animation.stop()

        self._animating = True
        self.setGeometry(start)
        animation = QPropertyAnimation(self, b"geometry", self)
        animation.setDuration(1 if self._reduced_motion else 520)
        animation.setStartValue(start)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def on_finished() -> None:
            self._animating = False
            self._animation = None
            finished()

        animation.finished.connect(on_finished)
        self._animation = animation
        animation.start()

    def _finish_collapse(self) -> None:
        self.stack.setCurrentWidget(self.bubble)
        self._is_expanded = False
        self._save_position()

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.key() == Qt.Key.Key_Escape and self._is_expanded:
            self.collapse()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().showEvent(event)
        # Re-raise after the platform window exists, while keeping focus
        # untouched so the note does not steal typing from other apps.
        self.raise_()
        QTimer.singleShot(0, self.raise_)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self._animation is not None:
            self._animation.stop()
        self._save_timer.stop()
        self._save_note()
        self._save_panel_size()
        self._save_position()
        event.accept()


APP_STYLE = """
QWidget#floating-note {
    background: transparent;
}

QFrame#panel {
    /* Anchors: #14120B (editor), #2B2923 (panel), #1B1913 (header/bubble). */
    background: #2B2923;
    border: 1px solid #514D43;
    border-radius: 22px;
}

QFrame#header {
    background: #1B1913;
    border: 1px solid #514D43;
    border-radius: 14px;
}

QLabel#heading {
    color: #B8B09F;
    letter-spacing: 1px;
}

QToolButton#tasks-button, QToolButton#done-button, QToolButton#history-button,
QToolButton#overflow-button,
QToolButton#minimize-button, QToolButton#close-button,
QToolButton#tasks-close-button, QToolButton#history-close-button {
    border: 1px solid transparent;
    border-radius: 11px;
    color: #E9E3D7;
    font-size: 14px;
    font-weight: 500;
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
    padding: 0;
}

QToolButton#tasks-button, QToolButton#history-button, QToolButton#overflow-button,
QToolButton#minimize-button {
    background: #3B392F;
}

QToolButton#tasks-button:hover, QToolButton#history-button:hover, QToolButton#overflow-button:hover,
QToolButton#minimize-button:hover {
    background: #514D43;
    border-color: #C4BBAA;
}

QToolButton#tasks-button:pressed, QToolButton#history-button:pressed, QToolButton#overflow-button:pressed,
QToolButton#minimize-button:pressed {
    background: #1B1913;
}

QToolButton#close-button {
    background: #3B392F;
    color: #D1C5B5;
}

QToolButton#close-button:hover {
    background: #514D43;
    border-color: #D1C5B5;
}

QToolButton#close-button:pressed {
    background: #1B1913;
}

QToolButton#done-button {
    background: #47503A;
    color: #EDF0DD;
    border-radius: 5px;
    font-size: 9px;
    font-weight: 700;
    min-width: 59px;
    max-width: 59px;
    padding: 0 4px;
}

QToolButton#done-button:hover {
    background: #5F6D4B;
    border-color: #D8E6B3;
}

QToolButton#done-button:pressed {
    background: #313A28;
}

QToolButton#done-button:disabled {
    background: #2D3028;
    color: #717766;
}

QToolButton#tasks-button:focus,
QToolButton#done-button:focus,
QToolButton#history-button:focus,
QToolButton#overflow-button:focus,
QToolButton#minimize-button:focus,
QToolButton#close-button:focus,
QToolButton#tasks-close-button:focus,
QToolButton#history-close-button:focus {
    border-color: #C4BBAA;
}

QDialog#tasks-dialog {
    background: #2B2923;
    border: 1px solid #5C574C;
    border-radius: 16px;
}

QDialog#history-dialog {
    background: #2B2923;
    border: 1px solid #514D43;
    border-radius: 20px;
}

QFrame#task-view-switcher {
    background: #242118;
    border: none;
    border-radius: 9px;
}

QToolButton#task-view-button {
    color: #B8B09F;
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 600;
    min-height: 26px;
    padding: 3px 9px;
}

QToolButton#task-view-button:hover {
    color: #E9E3D7;
    background: #2B2923;
}

QToolButton#task-view-button:checked {
    color: #E9E3D7;
    background: #3B392F;
}

QMenu {
    background: #242118;
    border: 1px solid #514D43;
    border-radius: 9px;
    color: #E9E3D7;
    padding: 4px;
}

QMenu::item {
    border-radius: 6px;
    padding: 6px 18px 6px 9px;
}

QMenu::item:selected {
    background: #3B392F;
}

QLabel#tasks-title {
    color: #E9E3D7;
}

QLabel#tasks-subtitle, QLabel#task-section-detail {
    color: #B8B09F;
}

QComboBox#map-selector {
    color: #E9E3D7;
    background: #242118;
    border: 1px solid #5C574C;
    border-radius: 9px;
    font-size: 10px;
    font-weight: 600;
    min-width: 112px;
    min-height: 26px;
    padding: 3px 22px 3px 9px;
}

QComboBox#map-selector:hover, QComboBox#map-selector:focus {
    border-color: #C4BBAA;
}

QComboBox#map-selector::drop-down {
    border: none;
    width: 18px;
}

QComboBox#map-selector QAbstractItemView {
    color: #E9E3D7;
    background: #242118;
    border: 1px solid #514D43;
    selection-background-color: #3B392F;
    outline: none;
}

QLabel#history-title {
    color: #E9E3D7;
}

QLabel#history-subtitle, QLabel#history-entry-date, QLabel#history-empty {
    color: #B8B09F;
}

QToolButton#tasks-close-button {
    background: #3B392F;
    color: #D1C5B5;
}

QToolButton#history-close-button {
    background: #3B392F;
    color: #D1C5B5;
}

QToolButton#history-export-all-button, QToolButton#history-export-button {
    color: #E9E3D7;
    background: #3B392F;
    border: 1px solid #514D43;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 600;
    padding: 5px 8px;
}

QToolButton#history-remove-button {
    color: #D9BBB3;
    background: #3C2C29;
    border: 1px solid #634039;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 600;
    padding: 5px 8px;
}

QToolButton#history-export-all-button {
    padding-left: 9px;
    padding-right: 8px;
}

QToolButton#history-export-all-button:hover, QToolButton#history-export-button:hover {
    background: #514D43;
    border-color: #C4BBAA;
}

QToolButton#history-remove-button:hover {
    color: #F0D0C7;
    background: #52352F;
    border-color: #8C5B50;
}

QToolButton#history-export-all-button:pressed, QToolButton#history-export-button:pressed {
    background: #1B1913;
}

QToolButton#history-remove-button:pressed {
    background: #2E201E;
}

QToolButton#history-export-all-button:disabled {
    color: #717766;
    background: #2D3028;
    border-color: #3B392F;
}

QToolButton#tasks-close-button:hover, QToolButton#history-close-button:hover {
    background: #514D43;
    border-color: #D1C5B5;
}

QToolButton#tasks-close-button:pressed, QToolButton#history-close-button:pressed {
    background: #1B1913;
}

QScrollArea#tasks-scroll {
    background: transparent;
    border: none;
}

QScrollArea#history-scroll {
    background: transparent;
    border: none;
}

QWidget#tasks-content {
    background: transparent;
}

QWidget#history-content {
    background: transparent;
}

QFrame#task-section {
    background: #242118;
    border: none;
    border-radius: 10px;
}

QFrame#history-entry {
    background: #1B1913;
    border: 1px solid #514D43;
    border-radius: 13px;
}

QFrame#history-entry:hover {
    background: #211F18;
    border-color: #777061;
}

QFrame#history-timeline-rail {
    background: transparent;
    border: none;
}

QLabel#history-timeline-marker {
    color: #B8D48A;
    font-size: 19px;
    line-height: 0.6;
}

QLabel#history-entry-note {
    color: #E9E3D7;
}

QLabel#task-section-title {
    color: #E9E3D7;
    letter-spacing: 0.3px;
}

QLabel#task-row {
    color: #D1C5B5;
    background: transparent;
    border: none;
    padding: 2px 0;
}

QLabel#task-row span {
    color: #B8D48A;
}

QLabel#task-row em {
    color: #A49D8E;
    font-style: normal;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 0;
}

QScrollBar::handle:vertical {
    background: #514D43;
    border-radius: 4px;
    min-height: 28px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QTextEdit#editor {
    color: #E9E3D7;
    background: #14120B;
    border: 1px solid #514D43;
    border-radius: 14px;
    padding: 9px 10px;
    selection-background-color: #514D43;
    selection-color: #E9E3D7;
    font-size: 13px;
    line-height: 1.35;
}

QTextEdit#editor:focus {
    border: 1px solid #C4BBAA;
}

"""


def _prefer_xwayland_for_window_management() -> None:
    """Use XWayland when available for keep-above and the global shortcut."""
    if os.environ.get("HORYHOURS_NATIVE_WAYLAND") == "1":
        return
    platform = os.environ.get("QT_QPA_PLATFORM", "").lower()
    if platform and "xcb" not in platform:
        return
    if (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        and os.environ.get("DISPLAY")
    ):
        os.environ["QT_QPA_PLATFORM"] = "xcb"


def main() -> int:
    _prefer_xwayland_for_window_management()
    app = QApplication(sys.argv)
    app.setDesktopFileName("horyhours-notes")
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION)
    app.setStyle("Fusion")
    app.setFont(_ui_font(10))
    app.setStyleSheet(APP_STYLE)

    note = FloatingNote()
    global_shortcut = GlobalShortcutListener()
    if global_shortcut.start():
        global_shortcut.triggered.connect(note.toggle)
        global_shortcut.taskSwitcherTriggered.connect(note._toggle_task_switcher_visibility)
        note.set_global_shortcut_active(True)
    app.aboutToQuit.connect(global_shortcut.stop)
    note.show()

    shutdown_requested = False

    def _handle_sigint(signum, frame) -> None:
        del signum, frame
        nonlocal shutdown_requested
        shutdown_requested = True

    def _process_sigint() -> None:
        if not shutdown_requested:
            return
        signal_timer.stop()
        note.close()
        app.quit()

    signal.signal(signal.SIGINT, _handle_sigint)
    signal_timer = QTimer()
    signal_timer.setInterval(100)
    signal_timer.timeout.connect(_process_sigint)
    signal_timer.start()

    if "--smoke-test" in sys.argv:
        QTimer.singleShot(80, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
