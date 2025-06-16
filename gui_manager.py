import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.animation import Animation
from kivy.core.window import Window
from datetime import datetime
from zoneinfo import ZoneInfo
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
import python_weather
import asyncio
import pyttsx3
import re
import server

class MainLabel(Label):
    border_alpha = NumericProperty(0.2)
    pulse_speed  = NumericProperty(1.0)
    scale_trigger = NumericProperty(0)
    font_scale = NumericProperty(50)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.calculate_font_size)
        self.bind(text=self.calculate_font_size)
        self._start_pulse()

    def calculate_font_size(self, *args):
        if not self.text or not all(self.size):
            self.font_scale = 50
            return
            
        self.text_size = self.size
        base_font_size = min(self.width, self.height) / 10
        text_length = len(self.text)
        available_area = self.width * self.height
        
        if text_length > 0 and available_area > 0:
            estimated_size = (available_area / text_length) ** 0.5 * 0.8
            font_size = max(12, min(estimated_size, base_font_size))
        else:
            font_size = base_font_size
        
        self.font_scale = font_size

    def _start_pulse(self):
        half = self.pulse_speed / 2.0
        anim = Animation(border_alpha=0.8, duration=half) + \
               Animation(border_alpha=0.2, duration=half)
        anim.repeat = True
        anim.start(self)

    def speed_up_glow(self, factor: float):
        Animation.cancel_all(self, 'border_alpha')
        self.pulse_speed = self.pulse_speed * factor
        self._start_pulse()

    def slow_down_glow(self, factor: float):
        Animation.cancel_all(self, 'border_alpha')
        self.pulse_speed = self.pulse_speed / factor
        self._start_pulse()


class BoxScreen(BoxLayout):
    displayed_response = StringProperty("")
    _full_text = StringProperty("")
    _char_index = NumericProperty(0)
    _word_index = NumericProperty(0)
    current_time = StringProperty("")
    local_weather = StringProperty("Loading Weather...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_time(0)
        self.animate_response("Listening...")
        Clock.schedule_interval(self.update_time, 1)
        self._words = []
        self._animation_mode = "char"  # "char" or "word"
        self.history_shown = False
        self.content_area = self.ids.get("content_area")
        self.main_label = self.ids.get("main_label")
        self._history_scroll = None

        
        threading.Thread(
            target=self._fetch_weather_in_thread,
            args=("Dallas, TX",),
            daemon=True
        ).start()

    def _fetch_weather_in_thread(self, location: str):
        weather_text = asyncio.run(self._get_local_weather(location))
        Clock.schedule_once(lambda dt: setattr(self, "local_weather", weather_text), 0)

    async def _get_local_weather(self, location: str) -> str:
        client = python_weather.Client(unit=python_weather.IMPERIAL)
        try:
            weather = await client.get(location)
            lines = []

            for daily in weather.daily_forecasts[:3]:
                lines.append(
                    f"{daily.date}: High {daily.highest_temperature}°F, "
                    f"Low {daily.lowest_temperature}°F"
                )
            lines.append(
                f"""Now: {weather.temperature}°F, feels like {weather.feels_like}°F
        Humidity: {weather.humidity}%
        Wind: {weather.wind_speed} mph {weather.wind_direction}
        """
            )
            return "\n".join(lines)
        finally:
            await client.close()

    def update_time(self, dt):    
        now_chicago = datetime.now(tz=ZoneInfo("America/Chicago"))
        date = now_chicago.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.current_time = date

    def on__char_index(self, _, idx):
        self.displayed_response = self._full_text[:int(idx)]
    
    def on__word_index(self, _, idx):
        if self._words and idx <= len(self._words):
            self.displayed_response = " ".join(self._words[:int(idx)])

    def get_speech_duration(self, text):
        """Estimate speech duration based on text length and average speaking rate"""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()  #removes the huge think block from the duration

        # Average speaking rate: ~150-200 words per minute
        words = len(text.split())
        estimated_duration = (words / 180) * 60  # 180 WPM = 3 words per second
        return max(1.0, estimated_duration)  # Minimum 1 second

    def animate_response(self, new_text, duration=None, mode="char"):
        """
        Animate text appearance
        mode: "char" for character-by-character, "word" for word-by-word
        duration: if None, will estimate based on speech
        """
        self._animation_mode = mode
        
        # Estimate duration if not provided
        if duration is None:
            duration = self.get_speech_duration(new_text)
        
        # Speed up glow during animation
        factor = 0.25
        for child in self.walk(restrict=True):
            if isinstance(child, MainLabel):
                child.speed_up_glow(factor)

        def on_complete(*_):
            for child in self.walk(restrict=True):
                if isinstance(child, MainLabel):
                    child.slow_down_glow(factor)

        self._full_text = new_text
        
        if mode == "word":
            # Word-by-word animation
            self._words = new_text.split()
            self._word_index = 0
            anim = Animation(_word_index=len(self._words), duration=duration)
        else:
            # Character-by-character animation
            self._char_index = 0
            anim = Animation(_char_index=len(new_text), duration=duration)
        
        anim.bind(on_complete=on_complete)
        anim.start(self)

    def animate_with_speech_sync(self, text, use_word_mode=False):
        """
        Animate text synchronized with TTS speech
        """
        duration = self.get_speech_duration(text)
        mode = "word" if use_word_mode else "char"
        self.animate_response(text, duration=duration, mode=mode)
    # Inside BoxScreen
    def show_history_messages(self):
        messages = server.get_messages(limit=50)
        layout = BoxLayout(orientation='vertical', size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for msg in messages:
            layout.add_widget(Label(text=msg, size_hint_y=None, height=40, font_name="fonts/JetBrainsMono-ExtraBold.ttf",
                                     text_size=self.size, halign="center", valign="center"))
        scroll = ScrollView()
        scroll.add_widget(layout)
        self._history_scroll = scroll

        if self.content_area:
            self.content_area.clear_widgets()
            self.content_area.add_widget(scroll)

    # Example of toggling when user taps or swipes:
    def on_touch_up(self, touch):
        # single‐tap shows history (if it isn’t already shown)
        if not touch.is_double_tap and not self.history_shown:
            self.show_history_messages()
            self.history_shown = True
            return True
        return super().on_touch_up(touch)

    def on_touch_down(self, touch):
        # double‐tap hides history (if it is shown)
        if touch.is_double_tap and self.history_shown:
            self.hide_history()
            self.history_shown = False
            return True
        return super().on_touch_down(touch)

    def show_history(self):
        # your code to switch to the history layout
        # Display history in the content area
        self.show_history_messages()

    def hide_history(self):
        # Restore the main label in the content area
        if self.content_area:
            self.content_area.clear_widgets()
            if self.main_label:
                self.content_area.add_widget(self.main_label)




class GUIManagerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timeout_event = None
        
    def build(self):
        Builder.load_file('boxscreen.kv')
        return BoxScreen()
        
    @mainthread
    def stop_app(self):
        App.get_running_app().stop()
    
    def update(self, text, sync_with_speech=False, word_mode=False):
        server.add_message(text)
        """
        Update the display text
        sync_with_speech: if True, animation duration matches estimated speech time
        word_mode: if True, animate word-by-word instead of character-by-character
        """
        if sync_with_speech:

            Clock.schedule_once(
                lambda dt: self.root.animate_with_speech_sync(text, word_mode), 0
            )   #self.root connects to the widget made in the build function
        else:
            Clock.schedule_once(lambda dt: self.root.animate_response(text), 0)


class GUIService:
    def __init__(self):
        self.app = None
        self.thread = None

    def start(self):
        def run_gui():
            self.app = GUIManagerApp()
            self.app.run()
        run_gui()
    
    def update(self, text, sync_with_speech=False, word_mode=False):
        if self.app:
            self.app.update(text, sync_with_speech, word_mode)

    def stop(self):
        if self.app:
            self.app.stop_app()


if __name__ == "__main__":
    GUIService().start()