"""Verify window-local bindings without sending real keyboard input."""

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from test_animation import EventLoop
from test_resources import load_main


class KeyboardTests(unittest.TestCase):
    def setUp(self):
        self.main, self.modules = load_main()
        self.root = EventLoop()
        self.app = self.main.Simulator(self.root)

    def test_block_all_keys_is_installed_on_the_application_window(self):
        self.assertTrue(callable(getattr(self.main, "block_all_keys", None)))
        self.assertIn("<KeyPress>", self.root.bindings)
        self.assertIn("<KeyRelease>", self.root.bindings)

    def test_ordinary_key_presses_and_releases_are_suppressed(self):
        for sequence in ("<KeyPress>", "<KeyRelease>"):
            for key in ("a", "A", "space", "Return", "Tab", "ISO_Left_Tab",
                        "Left", "Delete", "F11"):
                with self.subTest(sequence=sequence, key=key):
                    self.assertEqual(self.root.bindings[sequence](
                        SimpleNamespace(keysym=key)), "break")

    def test_control_alt_meta_and_windows_combinations_pass_through(self):
        for kind in ("KeyPress", "KeyRelease"):
            for modifier in ("Control", "Alt", "Meta", "Mod4"):
                for key in ("Tab", "F4", "Delete", "Escape", "d"):
                    with self.subTest(kind=kind, modifier=modifier, key=key):
                        self.assertIsNone(self.root.bindings[f"<{modifier}-{kind}>"](
                            SimpleNamespace(keysym=key)))

    def test_escape_and_native_system_keys_are_not_suppressed(self):
        for kind in ("KeyPress", "KeyRelease"):
            for key in ("Escape", "F10", "Alt_L", "Alt_R", "Control_L", "Control_R",
                        "Shift_L", "Shift_R", "Win_L", "Win_R", "Super_L", "Super_R",
                        "Meta_L", "Meta_R"):
                with self.subTest(kind=kind, key=key):
                    self.assertIsNone(self.root.bindings[f"<{kind}>"](
                        SimpleNamespace(keysym=key)))

    def test_escape_still_uses_application_cleanup(self):
        self.assertIn("<KeyPress>", self.root.bindings)
        self.root.bindings["<Escape>"](SimpleNamespace(keysym="Escape"))
        self.assertTrue(self.app.closed)
        self.assertTrue(self.root.destroyed)
        self.assertTrue(self.app.stop_camera.is_set())
        self.main.winsound.PlaySound.assert_called_once_with(None, 0)

    def test_filter_only_binds_the_supplied_window(self):
        window = MagicMock()
        self.assertTrue(callable(getattr(self.main, "block_all_keys", None)))
        self.main.block_all_keys(window)
        self.assertEqual({call[0] for call in window.mock_calls}, {"bind"})
        self.assertTrue(all(call.args[0] not in ("<Escape>", "<Alt-F4>")
                            for call in window.bind.call_args_list))
        self.assertFalse(self.modules["keyboard"].mock_calls)
        self.assertFalse(self.modules["tkinter"].mock_calls)

    def test_other_windows_have_no_keyboard_restrictions(self):
        other_window = EventLoop()
        self.assertIn("<KeyPress>", self.root.bindings)
        self.app.close()
        self.assertEqual(other_window.bindings, {})


if __name__ == "__main__":
    unittest.main()
