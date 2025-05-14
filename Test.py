from gui_manager import GUIService
import threading
import time

def background_event(gui):
    time.sleep(3)
    print("[Event] Detected voice input")
    gui.update("Heard you!")
    gui.cancel_timeout()

    time.sleep(2)
    print("[Event] Shutting down GUI")
    gui.stop()

if __name__ == "__main__":
    gui = GUIService()
    gui.start()

    # Simulate input from another thread (like a mic listener)
    threading.Thread(target=background_event, args=(gui,)).start()



