def open_user_camera():
    # Εισαγωγή της βιβλιοθήκης OpenCV μέσα στη συνάρτηση
    import cv2
    import numpy as np
    # φορτώνει το έτοιμο μοντέλο αναγνώρισης προσώπου της OpenCV
    # Φόρτωση του Haar Cascade για την αναγνώριση μπροστινού προσώπου
    face_classifier = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # ανοίγει την κάμερα του χρήστη (0 = default webcam)
    # open the user's camera (0 = default webcam)
    video_capture = cv2.VideoCapture(0)

    # set camera resolution to 800x600
    # Ορισμός της ανάλυσης της κάμερας σε 800x600
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    # create a window and make it resizable
    # Δημιουργία ενός παραθύρου που μπορεί να αλλάξει μέγεθος
    cv2.namedWindow("Face Detector Hack", cv2.WINDOW_NORMAL)

    # resize the window to 800x600 for display
    cv2.resizeWindow("Face Detector Hack", 800, 600)

    # keep the window always on top
    # Διατήρηση του παραθύρου πάντα πάνω από τις άλλες εφαρμογές (Topmost)
    cv2.setWindowProperty("Face Detector Hack", cv2.WND_PROP_TOPMOST, 1)

    # πόσα frames αντιστοιχούν περίπου σε 0.5 sec (με ~30 FPS)
    FRAMES_THRESHOLD = 20
    face_counter = 0

    # Δημιουργία τετραγώνου γύρω από τα πρόσωπα που βρίσκονται στην εικόνα vid
    def detect_bounding_box(vid, counter):

        # αλλάζει την εικόνα σε grayscale για καλύτερη αναγνώριση προσώπων
        grey_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)

        # εντοπίζει πρόσωπα και επιστρέφει ορθογώνια (x, y, w, h)
        faces = face_classifier.detectMultiScale(
            grey_image,  # εικόνα σε grayscale
            1.1,  # scale factor (πόσο μειώνεται η εικόνα σε κάθε κλίμακα)
            8,  # min neighbors (πόσο αυστηρός είναι ο αλγόριθμος)
            minSize=(40, 40)  # ελάχιστο μέγεθος προσώπου
        )

        # αν βρέθηκε πρόσωπο αύξησε τον μετρητή
        if len(faces) > 0:
            counter += 1
        else:
            # αν δεν βρέθηκε, μηδένισε τον μετρητή
            counter = 0

        # ζωγράφισε τετράγωνο μόνο αν έχει μείνει αρκετό χρόνο
        # Εμφάνιση του κόκκινου κουτιού (0, 0, 255 είναι κόκκινο στο BGR format, όχι άσπρο!)
        if counter >= FRAMES_THRESHOLD:
            for (x, y, w, h) in faces:
                cv2.rectangle(
                    vid,
                    (x, y),
                    (x + w, y + h),
                    (0, 0, 255),  # BGR χρώμα (Κόκκινο στην προκειμένη περίπτωση)
                    2  # πάχος γραμμής
                )

        return counter

    recording = True

    # κεντρικό loop καταγραφής βίντεο
    while recording:
        # Ανάγνωση του τρέχοντος frame από την κάμερα
        result, video_frame = video_capture.read()

        # αν διαβάστηκε σωστά frame
        if result == 1:
            pass  # Έβγαλα το print("recording...") για να μη γεμίζει το terminal, αλλά τρέχει κανονικά!

        # αν απέτυχε η ανάγνωση, σταμάτα
        # Διακοπή του loop αν η κάμερα αποσυνδεθεί
        if result == 0:
            break

        # έλεγχος για πρόσωπα και ενημέρωση μετρητή
        face_counter = detect_bounding_box(video_frame, face_counter)

        # add your troll text
        # προσθήκη πράσινης ετικέτας "Press ESC to exit"
        cv2.putText(
            video_frame,
            "Click on the window then press ESC to exit.",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 255, 0),  # πράσινο χρώμα (BGR)
            1,
            cv2.LINE_AA  # ομαλές άκρες
        )

        # Προσθήκη των troll μηνυμάτων με κόκκινο χρώμα
        cv2.putText(
            video_frame,
            "Hahaha!!!",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            video_frame,
            "Bruh!!!",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

        # --- RESIZE FRAME TO 800x600 WITHOUT STRETCHING ---
        # Στόχος: Να προσαρμόσουμε το βίντεο σε 800x600 χωρίς να παραμορφωθεί (aspect ratio preservation)
        display_width = 800
        display_height = 600

        # Λήψη των αρχικών διαστάσεων του βίντεο
        orig_height, orig_width = video_frame.shape[:2]

        # Υπολογισμός της κλίμακας (scale) για πλάτος και ύψος
        scale_w = display_width / orig_width
        scale_h = display_height / orig_height

        # Επιλογή της μικρότερης κλίμακας για να χωρέσει ολόκληρη η εικόνα στην οθόνη
        scale = min(scale_w, scale_h)

        # Υπολογισμός των νέων διαστάσεων μετά το scaling
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # Αλλαγή μεγέθους της αρχικής εικόνας
        resized_frame = cv2.resize(video_frame, (new_width, new_height))

        # Δημιουργία ενός μαύρου "καμβά" (black canvas) στις τελικές διαστάσεις 800x600
        canvas = np.zeros((display_height, display_width, 3), dtype=np.uint8)

        # Υπολογισμός του κενού χώρου (μαύρες μπάρες) για να κεντραριστεί η εικόνα
        x_offset = (display_width - new_width) // 2
        y_offset = (display_height - new_height) // 2

        # Επικόλληση της νέας εικόνας στο κέντρο του μαύρου καμβά
        canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

        # show the properly resized frame (εμφάνιση του καμβά που δεν παραμορφώνει την εικόνα)
        cv2.imshow("Face Detector Hack", canvas)

        # περίμενε 1 ms για πάτημα πλήκτρου
        k = cv2.waitKey(1)

        # αν πατηθεί ESC (27), κλείσε
        if k % 256 == 27:
            print("Escape hit, closing...")
            break

    # απελευθέρωση κάμερας
    # Ελευθερώνουμε τους πόρους της κάμερας
    video_capture.release()

    # κλείσιμο όλων των παραθύρων OpenCV
    cv2.destroyAllWindows()


# Εκτέλεση της συνάρτησης για testing
#open_user_camera()
