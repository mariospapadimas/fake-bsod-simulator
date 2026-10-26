# Fake BSOD Simulator

A Windows prank application with the original fullscreen desktop overlay,
multi-stage fake BSOD images, sound effects, and OpenCV face-detection preview.
This maintenance refactor preserves the presentation and playful scare sequence
while organizing the files and providing a responsive exit.

Repository: <https://github.com/mariospapadimas/fake-bsod-simulator>

<img width="850" height="601" alt="bsod11" src="https://github.com/user-attachments/assets/62af29df-5826-42df-af23-a06534435145" />

## Requirements and setup

- Windows with an interactive desktop and audio output (`winsound` is Windows-only).
- Python 3.9+ with Tkinter installed; automated checks were run on Python 3.11.
- A webcam for the original preview. An unavailable or disconnected camera is
  reported in the terminal, and the BSOD presentation can still proceed.
- Git for cloning and for the asset-preservation regression test.

From a terminal:

```powershell
git clone https://github.com/mariospapadimas/fake-bsod-simulator.git
cd fake-bsod-simulator
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src/main.py
```

Runtime dependencies are PyAutoGUI, Pillow, OpenCV (`opencv-python`), and NumPy.
Tkinter, threading, and winsound come with the standard Windows Python installation.
No global keyboard-hook dependency is used.

## Presentation and exit

1. After the original three-second preparation delay, Win+D reveals the desktop.
   After another 700 ms, a desktop screenshot becomes the fullscreen, topmost overlay.
2. The topmost **Face Detector Hack** preview opens at 800x600. It retains the
   original Haar cascade, detection parameters, aspect-ratio-preserving black
   bars, red face boxes after 20 consecutive detected frames, and the
   `Hahaha!!!` / `Bruh!!!` messages. Frames are previewed only; they are not recorded,
   uploaded, or saved.
3. Close the camera preview with its **X** button, then click the fullscreen
   overlay. As in the original implementation, the camera stage precedes the
   click-triggered animation. Camera failure also proceeds to this click stage.
4. After the original one-second trigger delay, the BSOD animation and sounds play.
5. The original final `bsod16.png` appears by itself. A cancellable callback
   scheduled for **3,000 milliseconds** later adds **Press ESC to exit**.
   The final image and message then remain visible until you exit.

**Press Esc while either application window has focus to close the entire
simulation**, including during the preview, the click-wait stage, and the animation.
Esc works before the hint appears as well. Alt+Tab, Alt+F4, Ctrl+Alt+Delete,
and normal Windows security/exit controls remain available; there is no
system-wide keyboard blocking. `block_all_keys(window)` ignores ordinary key
presses and releases only within the Tk fullscreen window and its children.
Modifier combinations and native system-key handling pass through, while Esc
retains its dedicated exit binding. The OpenCV preview retains its existing Esc
handling. No global hooks or input grabs are
installed, and destroying the Tk window removes its local keyboard bindings.
Before the overlay appears, the app is hidden during the short preparation delay,
so it cannot receive Esc until a window has focus.

The original image order and requested delays are retained:

```text
1 (2s), 2 (3s), 3 (3s), 4 (0.1s), 5 (0.1s), 7 (2s),
6 (0.5s), 7 (1s), 12 (0.5s), 8 (7s), 10 (0.1s), 9 (0.4s),
10 (0.5s), 11 (6s), 13 (0.01s),
20 repetitions of [11 (0.001s), 13 (0.001s)],
15 (3s), 14 (1s), 13 (3s), 16 (until exit)
```

`noise1.wav`, `noise2.wav`, and `noise3.wav` precede images 1, 2, and 3;
`loop.wav` starts at image 4; `sound1.wav` precedes the flash pairs.
`noise1.wav` plays after each flash pair and before images 15, 14, and 13,
including the original two adjacent triggers before image 15. Playback remains
asynchronous and interrupting, as originally implemented; `loop.wav` is not
made into a repeating audio loop.

Tk callbacks replace the blocking sleeps, including the extremely long final
sleep. Image decoding, screen resizing, audio dispatch, and OS timer resolution
still add overhead, especially to the original 1 ms flashes; these are requested
delays, not guarantees of exact physical display timing.

## Structure and resources

```text
fake-bsod-simulator/
├── .github/
│   └── workflows/
│       └── python-tests.yml # Headless Python 3.11 CI
├── src/
│   ├── main.py
│   └── face_detection.py
├── assets/
│   ├── images/             # bsod1.png through bsod16.png
│   └── sounds/             # noise1/2/3.wav, loop.wav, sound1.wav
├── tests/
│   ├── test_resources.py
│   ├── test_animation.py
│   ├── test_camera.py
│   └── test_keyboard.py
├── README.md
└── requirements.txt
```

All 16 original PNGs and five WAVs are moved byte-for-byte. The regression suite
compares their SHA-256 hashes with Git revision
`956bcad4f16eb10e871886f6aa579df51ea572f8`, the original main revision used for
this refactor. No assets are regenerated or edited.

Asset paths use `pathlib.Path` relative to the source location. The application
can be launched from another working directory using an absolute path to
`src/main.py`; `python -m src.main` also works from the repository root.
The desktop screenshot now stays in memory instead of writing `desktop.png`.

Exit cancels pending application callbacks, including the delayed exit hint,
stops sound playback, destroys the Tk window, and signals the camera worker to
stop. Camera cleanup releases its
capture handle and closes its own OpenCV window on normal exit, window close,
disconnection, and handled OpenCV errors. Missing image or sound files produce
a path-specific error before entering fullscreen. Rendering/playback failures
stop the presentation and run cleanup.

The camera runs in a daemon worker so a stalled native webcam driver cannot
freeze Tk. Shutdown waits at most 0.2 seconds for that worker. Python cannot
forcibly interrupt a permanently blocked native camera call: if the preview
stalls, focus the fullscreen overlay and press Esc. In this exceptional case,
Windows reclaims the camera/window resources when the process exits rather than
the worker completing its normal cleanup.

## Automated tests

From the repository root, using Python 3.11 and a clone containing the baseline
Git revision above:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```

The tests use Python's standard-library `unittest` runner and mocks; no third-party
packages are needed to run them. They cover source layout, both import modes,
all 21 asset hashes, working-directory-independent paths, frame/sound order and
requested delays, startup/camera handoff, final-frame holding, the 3,000 ms hint
delay and early cancellation, window-local keyboard filtering and system-key
pass-through, Esc, timer cleanup, camera cleanup and detection behavior, and
missing/unavailable resources.

All desktop, GUI, audio, and webcam boundaries are mocked. Automated tests never
launch the fullscreen simulation, capture real webcam frames, play sounds, send
real hotkeys, or alter host settings. These checks do not constitute real-hardware
or live visual testing.

## GitHub Actions

[Python tests](https://github.com/mariospapadimas/fake-bsod-simulator/actions/workflows/python-tests.yml)
runs on pushes to every branch and pull requests targeting `main`.
The workflow in `.github/workflows/python-tests.yml` uses one Ubuntu job with
Python 3.11, official actions pinned to verified commit SHAs, and
`permissions: contents: read`.

It discovers and runs the complete `unittest` suite described above, failing on
test failures, no discovered tests, or no executed tests. Full Git history is
checked out so the original asset-hash comparison can run. The tests require
only the Python standard library and Git, so CI installs no third-party runtime
packages. GUI, desktop input, webcam, and audio interactions are mocked throughout;
the workflow never launches the actual BSOD application.

Run the same tests locally with `python -m unittest discover -s tests -v` from
the repository root. CI adds the empty-suite/execution guards to this discovery
and test run. Its result verifies mocked behavior, not physical webcam, sound,
Windows focus, or fullscreen rendering.

## Use and asset rights

This project is for educational, entertainment, and prank purposes. Run it only
on systems and with camera access you have permission to use. The included
dramatic images and flashing scare effects are part of the original presentation.

Some included images, sounds, visual assets, or screenshots may be copyrighted
by their respective owners. Their inclusion does not establish ownership or
redistribution rights, and this refactor makes no additional license grant.
If you hold rights to an asset and want it removed or credited differently,
please [open an issue](https://github.com/mariospapadimas/fake-bsod-simulator/issues)
or contact the repository owner. Users must verify the rights needed to
redistribute assets in forks or other modifications.

The project is provided as-is for educational purposes. No LICENSE file has been
added, and asset licensing has not been independently verified.
