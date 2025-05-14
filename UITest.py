from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config

# Fullscreen and disable multitouch emulation
Config.set('graphics', 'fullscreen', 'auto')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

class KioskApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)

        btn1 = Button(text='Open Door', font_size=32, on_press=self.open_door)
        btn2 = Button(text='Shutdown', font_size=32, on_press=self.shutdown)

        layout.add_widget(btn1)
        layout.add_widget(btn2)
        return layout

    def open_door(self, instance):
        print("Door opened (placeholder action)")

    def shutdown(self, instance):
        print("Shutdown (placeholder action)")
        App.get_running_app().stop()

KioskApp().run()
