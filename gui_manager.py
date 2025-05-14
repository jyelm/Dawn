import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock, mainthread


RUNTIME = 5

class GUIManagerApp(App):
    def build(self):
        layout = BoxLayout()
        self.label = Label(text="Listening...", font_size='32sp')
        layout.add_widget(self.label)

        # Schedule auto-close after 30 seconds
        self.timeout_event = Clock.schedule_once(self.close_app, RUNTIME)

        return layout

    def close_app(self, dt):
        App.get_running_app().stop()

    @mainthread
    def cancel_timeout(self):
        if self.timeout_event:
            self.timeout_event.cancel()   # valid method
            self.timeout_event = None
            print("Auto-close canceled.")

    def update_text(self, new_text):
        def _update(dt):
            self.label.text = new_text
        Clock.schedule_once(_update)
    @mainthread
    def stop_app(self):
# this will safely run on the GUI thread
        App.get_running_app().stop()



# Store the app instance globally so other modules can interact with it
_app_instance = None

def start_gui():
    global _app_instance
    _app_instance = GUIManagerApp()
    _app_instance.run()
    return _app_instance  # Optional, if you want to return it to the caller

def cancel_gui_timeout():
    if _app_instance:
        _app_instance.cancel_timeout()

def force_close_gui():
    if _app_instance:
        _app_instance.stop_app() 

def update_gui_text(new_text):
    if _app_instance:
        _app_instance.update_text(new_text)



#Seperate callable class
class GUIService:
    def __init__(self):
        self.app = None
        self.thread = None

    def start(self):
        def run_gui():
            self.app = GUIManagerApp()
            self.app.run()

        self.thread = threading.Thread(target=run_gui)
        self.thread.start()

    def update(self, text):
        if self.app:
            self.app.update_text(text)

    def cancel_timeout(self):
        if self.app:
            self.app.cancel_timeout()

    def stop(self):
        if self.app:
            self.app.stop_app()






# This block only runs if you directly run this file (for testing)
#if __name__ == "__main__":
#    start_gui()
