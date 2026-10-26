"""Drive the actual presentation callbacks without a GUI or real time."""

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from test_resources import load_main


class EventLoop:
    def __init__(self):
        self.jobs = {}
        self.delays = []
        self.bindings = {}
        self.destroyed = False
        self.serial = 0

    def after(self, delay, callback):
        self.serial += 1
        self.jobs[self.serial] = callback
        self.delays.append(delay)
        return self.serial

    def after_cancel(self, job):
        del self.jobs[job]

    def bind(self, key, callback):
        self.bindings[key] = callback

    def protocol(self, key, callback):
        self.bindings[key] = callback

    def destroy(self):
        self.destroyed = True

    def step(self):
        job = next(iter(self.jobs))
        self.jobs.pop(job)()

    def drain(self):
        for _ in range(500):
            if not self.jobs:
                return
            self.step()
        raise AssertionError("Unexpected endless timer loop")


class AnimationTests(unittest.TestCase):
    def setUp(self):
        self.main, self.modules = load_main()
        self.assertTrue(callable(getattr(self.main, "Simulator", None)),
                        "The presentation needs cancellable Tk callbacks")
        self.root = EventLoop()
        self.app = self.main.Simulator(self.root)
        self.app.bgimage = MagicMock()
        self.app.camera = MagicMock()
        self.app.camera.is_alive.return_value = False
        self.shown = []
        self.app.updateImg = lambda number: self.shown.append(number)

    def test_original_frame_order_timing_and_sound_cues(self):
        events = []
        self.app.updateImg = lambda n: events.append(("image", n))
        self.main.winsound.PlaySound.side_effect = lambda path, flags: events.append(
            ("sound", Path(path).name))
        self.app.initiate()
        self.app.initiate()  # repeated clicks must not restart the prank
        self.root.drain()
        expected = [("sound", "noise1.wav"), ("image", 1),
                    ("sound", "noise2.wav"), ("image", 2),
                    ("sound", "noise3.wav"), ("image", 3),
                    ("sound", "loop.wav")]
        expected += [("image", n) for n in (4, 5, 7, 6, 7, 12, 8, 10, 9, 10, 11, 13)]
        expected += [("sound", "sound1.wav")]
        expected += [("image", 11), ("image", 13), ("sound", "noise1.wav")] * 20
        expected += [("sound", "noise1.wav"), ("image", 15),
                     ("sound", "noise1.wav"), ("image", 14),
                     ("sound", "noise1.wav"), ("image", 13), ("image", 16)]
        self.assertEqual(events, expected)
        # Sound-only cues consume no extra presentation time.
        self.assertEqual([n for n in self.root.delays if n],
                         [1000, 2000, 3000, 3000, 100, 100, 2000, 500, 1000,
                          500, 7000, 100, 400, 500, 6000, 10] + [1, 1] * 20
                         + [3000, 1000, 3000])

    def test_final_frame_stays_without_pending_animation_timer(self):
        self.app.initiate()
        self.root.drain()
        self.assertEqual(self.shown[-1], 16)
        self.assertFalse(self.root.destroyed)
        self.assertEqual(self.root.jobs, {})
        self.main.tk.Label.assert_called_with(
            self.root, text="Press ESC to exit", font=("Arial", 18),
            fg="white", bg="black", padx=12, pady=6)

    def test_escape_cancels_animation_and_releases_owned_resources(self):
        self.app.initiate()
        self.root.step()
        self.root.bindings["<Escape>"](None)
        self.assertTrue(self.root.destroyed)
        self.assertFalse(self.root.jobs)
        self.assertTrue(self.app.stop_camera.is_set())
        self.main.winsound.PlaySound.assert_called_with(None, 0)
        shown = list(self.shown)
        self.app.initiate()
        self.root.drain()
        self.assertEqual(self.shown, shown)
        self.app.close()  # cleanup must be idempotent

    def test_normal_window_close_uses_same_cleanup(self):
        self.root.bindings["WM_DELETE_WINDOW"]()
        self.assertTrue(self.root.destroyed)

    def test_missing_asset_fails_before_showing_fullscreen(self):
        with patch.object(self.main, "IMAGE_DIR", Path("missing-assets")):
            with self.assertRaisesRegex(FileNotFoundError, "bsod1.png"):
                self.app.validate_assets()

    def test_callback_failure_closes_and_cancels_timers(self):
        self.app.schedule(1, lambda: (_ for _ in ()).throw(OSError("broken image")))
        with patch("sys.stderr"):
            self.root.step()
        self.assertTrue(self.root.destroyed)
        self.assertFalse(self.root.jobs)

    def test_camera_escape_exits_whole_application(self):
        self.app.camera_exit.set()
        self.app.poll_camera()
        self.assertTrue(self.root.destroyed)

    def test_missing_sound_is_reported(self):
        with patch.object(self.main, "SOUND_DIR", Path("missing-sounds")):
            with self.assertRaisesRegex(FileNotFoundError, "noise1.wav"):
                self.app.validate_assets()

    def test_startup_delays_desktop_capture_and_camera_handoff(self):
        for name in ("withdraw", "geometry", "winfo_screenwidth", "winfo_screenheight",
                     "attributes", "deiconify", "focus_force"):
            setattr(self.root, name, MagicMock())
        with patch.object(self.main.threading, "Thread") as thread:
            thread.return_value.is_alive.return_value = True
            self.app.start()
            self.assertEqual(self.root.delays, [3000])
            self.main.pt.hotkey.assert_not_called()
            self.root.step()
            self.main.pt.hotkey.assert_called_once_with("win", "d")
            self.main.pt.screenshot.assert_not_called()
            self.assertEqual(self.root.delays[-1], 700)
            self.root.step()
            self.main.pt.screenshot.assert_called_once_with()
            self.root.attributes.assert_any_call("-fullscreen", True)
            thread.return_value.start.assert_called_once()
            self.app.bgimage.bind.assert_not_called()
            thread.return_value.is_alive.return_value = False
            self.root.step()
            self.app.bgimage.bind.assert_called_once_with("<Button-1>", self.app.initiate)

    def test_escape_during_startup_cancels_desktop_reveal(self):
        self.root.withdraw = MagicMock()
        self.app.start()
        self.root.bindings["<Escape>"](None)
        self.root.drain()
        self.main.pt.hotkey.assert_not_called()
        self.main.pt.screenshot.assert_not_called()

    def test_escape_after_final_frame(self):
        self.app.initiate()
        self.root.drain()
        self.root.bindings["<Escape>"](None)
        self.assertTrue(self.root.destroyed)
        self.assertFalse(self.root.jobs)

    def test_image_loading_uses_absolute_path_and_original_screen_size(self):
        self.root.winfo_screenwidth = lambda: 1920
        self.root.winfo_screenheight = lambda: 1080
        # Invoke the real renderer, mocked only at the file/GUI boundaries.
        self.main.Simulator.updateImg(self.app, 13)
        self.main.Image.open.assert_called_once_with(self.main.IMAGE_DIR / "bsod13.png")
        self.main.Image.open.return_value.__enter__.return_value.resize.assert_called_once_with(
            (1920, 1080), self.main.Image.Resampling.LANCZOS)
        self.app.bgimage.configure.assert_called_once()

    def test_main_finally_cleans_up_when_mainloop_is_interrupted(self):
        root = MagicMock()
        root.mainloop.side_effect = KeyboardInterrupt
        app = self.main.Simulator(root)
        app.camera = MagicMock()
        with patch.object(self.main.tk, "Tk", return_value=root), \
                patch.object(self.main, "Simulator", return_value=app), \
                self.assertRaises(KeyboardInterrupt):
            self.main.main()
        self.assertTrue(app.closed)
        root.destroy.assert_called_once()
        app.camera.join.assert_called_once_with(timeout=0.2)


if __name__ == "__main__":
    unittest.main()
