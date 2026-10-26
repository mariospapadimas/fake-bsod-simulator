"""Non-interactive structure and resource regression checks."""

import hashlib
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "956bcad4f16eb10e871886f6aa579df51ea572f8"


def load_main():
    # None of these boundaries may open windows, play audio, or send input.
    modules = {name: MagicMock() for name in (
        "tkinter", "PIL", "PIL.Image", "PIL.ImageTk", "pyautogui",
        "winsound", "keyboard", "cv2", "numpy",
    )}
    with patch.dict(sys.modules, modules):
        sys.modules.pop("src.main", None)
        return importlib.import_module("src.main"), modules


class ResourceTests(unittest.TestCase):
    def test_source_structure(self):
        for name in ("src/main.py", "src/face_detection.py", "requirements.txt"):
            self.assertTrue((ROOT / name).is_file(), name)
        self.assertFalse((ROOT / "Main.py").exists())
        self.assertFalse((ROOT / "FaceRecognitionProjectForBsod.py").exists())

    def test_all_assets_match_original_git_blobs(self):
        expected = [f"bsod{i}.png" for i in range(1, 17)]
        expected += ["noise1.wav", "noise2.wav", "noise3.wav", "loop.wav", "sound1.wav"]
        actual = list((ROOT / "assets/images").glob("*.png"))
        actual += list((ROOT / "assets/sounds").glob("*.wav"))
        self.assertEqual(sorted(p.name for p in actual), sorted(expected))
        for path in actual:
            with self.subTest(asset=path.name):
                original = subprocess.check_output(
                    ["git", "show", f"{BASELINE}:{path.name}"], cwd=ROOT
                )
                self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),
                                 hashlib.sha256(original).digest())

    def test_import_has_no_gui_audio_camera_or_input_side_effects(self):
        main, modules = load_main()
        for name in ("tkinter", "pyautogui", "winsound", "cv2", "keyboard"):
            self.assertEqual(modules[name].mock_calls, [], name)
        self.assertTrue(callable(main.main))

    def test_paths_resolve_from_an_unrelated_working_directory(self):
        main, _ = load_main()
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                self.assertEqual(main.IMAGE_DIR, ROOT / "assets/images")
                self.assertEqual(main.SOUND_DIR, ROOT / "assets/sounds")
                self.assertTrue((main.IMAGE_DIR / "bsod16.png").is_file())
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
