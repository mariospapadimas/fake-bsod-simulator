"""Original desktop prank presentation, driven by cancellable Tk callbacks."""

from pathlib import Path
import sys
import threading
import tkinter as tk

import pyautogui as pt
from PIL import Image, ImageTk
import winsound

if __package__:
    from .face_detection import open_user_camera
else:
    from face_detection import open_user_camera

PROJECT_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = PROJECT_DIR / "assets" / "images"
SOUND_DIR = PROJECT_DIR / "assets" / "sounds"
SOUNDS = ("noise1.wav", "noise2.wav", "noise3.wav", "loop.wav", "sound1.wav")


def block_all_keys(window):
    """Suppress ordinary Tk keys only in this toplevel and its child widgets.

    Leave modified keys and native system-key handling to Tk/Windows. Never
    replace Tk's global bindings, grab input, or install an OS keyboard hook.
    Destroying the owned window also removes these local bindings.
    """
    def suppress(event):
        if event.keysym in {
            "Escape", "F10", "Alt_L", "Alt_R", "Control_L", "Control_R",
            "Shift_L", "Shift_R", "Win_L", "Win_R", "Super_L", "Super_R",
            "Meta_L", "Meta_R",
        }:
            return None
        return "break"

    def allow(event):
        return None

    for kind in ("KeyPress", "KeyRelease"):
        window.bind(f"<{kind}>", suppress)
        # Specific modifier patterns take precedence over the generic filter.
        # In particular, Alt events must reach Tk's native Windows handlers.
        for modifier in ("Control", "Alt", "Meta", "Mod4"):
            window.bind(f"<{modifier}-{kind}>", allow)


def animation():
    """Yield (image, delay in ms, sound) in the original Main.py order.

    A missing image is a sound-only cue; a missing delay holds the final frame.
    Keep the sound after each flash pair, including the last pair.
    """
    yield from (
        (1, 2000, "noise1.wav"), (2, 3000, "noise2.wav"),
        (3, 3000, "noise3.wav"), (4, 100, "loop.wav"),
        (5, 100, None), (7, 2000, None), (6, 500, None),
        (7, 1000, None), (12, 500, None), (8, 7000, None),
        (10, 100, None), (9, 400, None), (10, 500, None),
        (11, 6000, None), (13, 10, None),
        (None, 0, "sound1.wav"),
    )
    for _ in range(20):
        yield (11, 1, None)
        yield (13, 1, None)
        yield (None, 0, "noise1.wav")
    yield from (
        (15, 3000, "noise1.wav"), (14, 1000, "noise1.wav"),
        (13, 3000, "noise1.wav"), (16, None, None),
    )


class Simulator:
    def __init__(self, root):
        self.root = root
        self.timers = set()
        self.closed = False
        self.started = False
        self.bgimage = None
        self.camera = None
        self.stop_camera = threading.Event()
        self.camera_exit = threading.Event()
        block_all_keys(self.root)
        self.root.bind("<Escape>", self.close)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def validate_assets(self):
        paths = [IMAGE_DIR / f"bsod{i}.png" for i in range(1, 17)]
        paths += [SOUND_DIR / name for name in SOUNDS]
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(f"Required asset is missing: {path}")

    def schedule(self, delay, callback):
        if self.closed:
            return

        def run():
            self.timers.discard(timer)
            if not self.closed:
                try:
                    callback()
                except Exception as error:
                    print(f"Simulation stopped: {error}", file=sys.stderr)
                    self.close()

        timer = self.root.after(delay, run)
        self.timers.add(timer)

    def start(self):
        self.validate_assets()
        self.root.withdraw()
        self.schedule(3000, self.show_desktop)

    def show_desktop(self):
        # Preserve the original Win+D desktop reveal and 700 ms settling time.
        pt.hotkey("win", "d")
        self.schedule(700, self.show_overlay)

    def show_overlay(self):
        # No desktop.png is written to the checkout or the caller's directory.
        desktop = pt.screenshot()
        bg = ImageTk.PhotoImage(desktop)
        self.root.geometry("{}x{}+0+0".format(self.root.winfo_screenwidth(),
                                             self.root.winfo_screenheight()))
        self.bgimage = tk.Label(self.root, image=bg,
                                width=self.root.winfo_screenwidth(),
                                height=self.root.winfo_screenheight(), borderwidth=0)
        self.bgimage.image = bg
        self.bgimage.place(x=0, y=0)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.deiconify()
        self.root.focus_force()
        # The preview still precedes click-to-start. A worker keeps a stalled
        # camera driver from blocking Tk's Escape/close event handling.
        self.camera = threading.Thread(
            target=open_user_camera,
            kwargs={"stop_event": self.stop_camera, "exit_event": self.camera_exit},
            name="bsod-camera", daemon=True,
        )
        self.camera.start()
        self.poll_camera()

    def poll_camera(self):
        if self.camera_exit.is_set():
            self.close()
        elif self.camera is not None and self.camera.is_alive():
            self.schedule(33, self.poll_camera)
        elif not self.closed:
            # Closing the camera window proceeds to the original click trigger.
            self.bgimage.bind("<Button-1>", self.initiate)
            self.root.focus_force()

    def updateImg(self, number):
        with Image.open(IMAGE_DIR / f"bsod{number}.png") as source:
            img = source.resize(
                (self.root.winfo_screenwidth(), self.root.winfo_screenheight()),
                Image.Resampling.LANCZOS,
            )
        bg = ImageTk.PhotoImage(img)
        self.bgimage.configure(image=bg, cursor="none")
        self.bgimage.image = bg

    def initiate(self, event=None):
        if self.started or self.closed:
            return
        self.started = True
        self.frames = iter(animation())
        self.schedule(1000, self.advance)

    def advance(self):
        number, delay, sound = next(self.frames)
        if sound is not None:
            winsound.PlaySound(str(SOUND_DIR / sound),
                               winsound.SND_FILENAME | winsound.SND_ASYNC
                               | winsound.SND_NODEFAULT)
        if number is not None:
            self.updateImg(number)
        if delay is None:
            self.exit_hint = tk.Label(
                self.root, text="Press ESC to exit", font=("Arial", 18),
                fg="white", bg="black", padx=12, pady=6,
            )
            self.exit_hint.place(relx=0.5, rely=0.95, anchor="s")
        else:
            self.schedule(delay, self.advance)

    def close(self, event=None):
        if self.closed:
            return
        self.closed = True
        self.stop_camera.set()
        for timer in tuple(self.timers):
            try:
                self.root.after_cancel(timer)
            except tk.TclError:
                pass
        self.timers.clear()
        try:
            winsound.PlaySound(None, 0)
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = Simulator(root)
    try:
        app.start()
        root.mainloop()
    finally:
        app.close()
        if app.camera is not None:
            # Bound exit time even if a faulty driver never returns from read().
            app.camera.join(timeout=0.2)


if __name__ == "__main__":
    main()
