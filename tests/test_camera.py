"""OpenCV boundaries are mocked; no physical webcam or windows are used."""

import importlib
import threading
import unittest
from unittest.mock import MagicMock, patch


class CameraTests(unittest.TestCase):
    def setUp(self):
        self.camera_module = importlib.import_module("src.face_detection")
        self.cv = MagicMock()
        self.cv.error = type("OpenCVError", (Exception,), {})
        self.np = MagicMock()
        self.capture = self.cv.VideoCapture.return_value
        self.capture.isOpened.return_value = True
        self.classifier = self.cv.CascadeClassifier.return_value
        self.classifier.empty.return_value = False
        self.classifier.detectMultiScale.return_value = [(10, 20, 40, 50)]
        self.frame = MagicMock()
        self.frame.shape = (480, 640, 3)
        self.capture.read.side_effect = [(True, self.frame), (False, None)]
        self.cv.waitKey.return_value = -1
        self.cv.getWindowProperty.return_value = 1
        self.stop = threading.Event()
        self.exit = threading.Event()

    def run_camera(self):
        with patch.dict("sys.modules", {"cv2": self.cv, "numpy": self.np}), \
                patch("sys.stderr"), patch("sys.stdout"):
            self.camera_module.open_user_camera(stop_event=self.stop, exit_event=self.exit)

    def test_accepts_cancellable_lifecycle(self):
        import inspect
        self.assertIn("stop_event", inspect.signature(self.camera_module.open_user_camera).parameters)

    def test_escape_releases_camera_and_owned_window(self):
        self.cv.waitKey.return_value = 27
        self.run_camera()
        self.assertTrue(self.exit.is_set())
        self.capture.release.assert_called_once()
        self.cv.destroyWindow.assert_called_once_with("Face Detector Hack")
        self.cv.destroyAllWindows.assert_not_called()

    def test_unavailable_device_releases_handle_without_opening_preview(self):
        self.capture.isOpened.return_value = False
        self.run_camera()
        self.capture.release.assert_called_once()
        self.cv.namedWindow.assert_not_called()
        self.assertFalse(self.exit.is_set())

    def test_disconnection_and_read_error_cleanup(self):
        for frames in ([(False, None)], self.cv.error("camera disconnected")):
            with self.subTest(frames=frames):
                self.capture.read.side_effect = frames
                self.capture.release.reset_mock()
                self.cv.destroyWindow.reset_mock()
                self.run_camera()
                self.capture.release.assert_called_once()
                self.cv.destroyWindow.assert_called_once_with("Face Detector Hack")

    def test_classifier_failure_does_not_open_device(self):
        self.classifier.empty.return_value = True
        self.run_camera()
        self.cv.VideoCapture.assert_not_called()

    def test_face_highlights_still_require_twenty_consecutive_frames(self):
        self.capture.read.side_effect = [(True, self.frame)] * 20 + [(False, None)]
        self.run_camera()
        self.assertEqual(self.classifier.detectMultiScale.call_count, 20)
        self.cv.rectangle.assert_called_once_with(
            self.frame, (10, 20), (50, 70), (0, 0, 255), 2)
        args, kwargs = self.classifier.detectMultiScale.call_args
        self.assertEqual(args[1:], (1.1, 8))
        self.assertEqual(kwargs, {"minSize": (40, 40)})
        self.cv.resize.assert_called_with(self.frame, (800, 600))
        self.assertEqual(self.cv.imshow.call_count, 20)

    def test_face_counter_resets_when_face_disappears(self):
        self.capture.read.side_effect = [(True, self.frame)] * 39 + [(False, None)]
        self.classifier.detectMultiScale.side_effect = (
            [[(10, 20, 40, 50)]] * 19 + [[]] + [[(10, 20, 40, 50)]] * 19)
        self.run_camera()
        self.cv.rectangle.assert_not_called()

    def test_stop_signal_prevents_further_frames(self):
        self.stop.set()
        self.run_camera()
        self.capture.read.assert_not_called()
        self.cv.VideoCapture.assert_not_called()
        self.cv.namedWindow.assert_not_called()

    def test_window_close_returns_without_exiting_simulator(self):
        self.cv.getWindowProperty.return_value = 0
        self.run_camera()
        self.capture.release.assert_called_once()
        self.assertFalse(self.exit.is_set())

    def test_stop_during_capture_releases_device_and_window(self):
        def stop_after_frame():
            self.stop.set()
            return True, self.frame
        self.capture.read.side_effect = stop_after_frame
        self.run_camera()
        self.capture.read.assert_called_once()
        self.capture.release.assert_called_once()
        self.cv.destroyWindow.assert_called_once_with("Face Detector Hack")
        self.cv.imshow.assert_not_called()

    def test_letterboxes_wide_camera_frames_without_stretching(self):
        self.frame.shape = (720, 1280, 3)
        self.run_camera()
        self.cv.resize.assert_called_once_with(self.frame, (800, 450))
        self.np.zeros.assert_called_once_with((600, 800, 3), dtype=self.np.uint8)

    def test_rendering_error_still_releases_camera(self):
        self.cv.imshow.side_effect = self.cv.error("preview unavailable")
        self.run_camera()
        self.capture.release.assert_called_once()
        self.cv.destroyWindow.assert_called_once_with("Face Detector Hack")


if __name__ == "__main__":
    unittest.main()
