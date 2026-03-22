"""
main.py
SafeStride — Kivy UI entry point.
Screens: SplashScreen → AuthScreen → MainScreen (Indoor/Outdoor)
"""

import os
import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from dotenv import load_dotenv

from safe_stride_app import SafeStrideApp

load_dotenv()
Window.clearcolor = (0.95, 0.95, 0.95, 1)


# ════════════════════════════════════════════════════════════════
# Global app coordinator (shared across all screens)
# ════════════════════════════════════════════════════════════════
app_core = SafeStrideApp()


# ════════════════════════════════════════════════════════════════
# Splash Screen
# ════════════════════════════════════════════════════════════════
class SplashScreen(Screen):
    def on_enter(self):
        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)
        layout.add_widget(Label(
            text="[b]SafeStride[/b]",
            markup=True,
            font_size="36sp",
            color=(0.1, 0.1, 0.1, 1),
        ))
        layout.add_widget(Label(
            text="Real-Time Scene Intelligence\nfor the Visually Impaired",
            font_size="16sp",
            halign="center",
            color=(0.3, 0.3, 0.3, 1),
        ))
        layout.add_widget(Label(text="Loading...", font_size="14sp", color=(0.5, 0.5, 0.5, 1)))
        self.add_widget(layout)
        Clock.schedule_once(self._check_session, 2.0)

    def _check_session(self, dt):
        if app_core.restore_session():
            threading.Thread(target=self._init_hardware, daemon=True).start()
        else:
            self.manager.current = "auth"

    def _init_hardware(self):
        app_core.start()
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "main"), 0)


# ════════════════════════════════════════════════════════════════
# Auth Screen — Login / Register
# ════════════════════════════════════════════════════════════════
class AuthScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=40, spacing=16)

        layout.add_widget(Label(
            text="[b]SafeStride[/b]",
            markup=True,
            font_size="30sp",
            size_hint_y=0.15,
            color=(0.1, 0.1, 0.1, 1),
        ))

        self.phone_input = TextInput(
            hint_text="Phone number",
            multiline=False,
            size_hint_y=None,
            height=48,
            input_type="number",
        )
        self.pass_input = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=48,
        )

        layout.add_widget(self.phone_input)
        layout.add_widget(self.pass_input)

        btn_row = GridLayout(cols=2, spacing=10, size_hint_y=None, height=52)
        login_btn = Button(text="Login", background_color=(0.2, 0.5, 0.8, 1))
        register_btn = Button(text="Register", background_color=(0.3, 0.65, 0.45, 1))
        login_btn.bind(on_press=self._do_login)
        register_btn.bind(on_press=self._show_register)
        btn_row.add_widget(login_btn)
        btn_row.add_widget(register_btn)

        layout.add_widget(btn_row)
        self.status_label = Label(text="", font_size="13sp", color=(0.7, 0.2, 0.2, 1))
        layout.add_widget(self.status_label)
        self.add_widget(layout)

    def _do_login(self, instance):
        phone = self.phone_input.text.strip()
        password = self.pass_input.text.strip()
        if not phone or not password:
            self.status_label.text = "Please fill in all fields."
            return
        self.status_label.text = "Authenticating..."
        threading.Thread(target=self._login_thread, args=(phone, password), daemon=True).start()

    def _login_thread(self, phone, password):
        success = app_core.authenticate(phone, password)
        if success:
            app_core.start()
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "main"), 0)
        else:
            Clock.schedule_once(
                lambda dt: setattr(self.status_label, "text", "Login failed. Check credentials."),
                0,
            )

    def _show_register(self, instance):
        self.manager.current = "register"


# ════════════════════════════════════════════════════════════════
# Register Screen
# ════════════════════════════════════════════════════════════════
class RegisterScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=40, spacing=12)
        layout.add_widget(Label(text="Create Account", font_size="24sp",
                                size_hint_y=0.12, color=(0.1, 0.1, 0.1, 1)))

        self.name_input = TextInput(hint_text="Full name", multiline=False,
                                    size_hint_y=None, height=46)
        self.phone_input = TextInput(hint_text="Phone number", multiline=False,
                                     size_hint_y=None, height=46, input_type="number")
        self.pass_input = TextInput(hint_text="Password (min 8 chars)", password=True,
                                    multiline=False, size_hint_y=None, height=46)
        self.contact_input = TextInput(hint_text="Emergency contact phone",
                                       multiline=False, size_hint_y=None, height=46,
                                       input_type="number")

        for w in [self.name_input, self.phone_input,
                  self.pass_input, self.contact_input]:
            layout.add_widget(w)

        reg_btn = Button(text="Register", background_color=(0.3, 0.65, 0.45, 1),
                         size_hint_y=None, height=52)
        back_btn = Button(text="Back to Login", background_color=(0.6, 0.6, 0.6, 1),
                          size_hint_y=None, height=44)
        reg_btn.bind(on_press=self._do_register)
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "auth"))

        layout.add_widget(reg_btn)
        layout.add_widget(back_btn)
        self.status_label = Label(text="", font_size="13sp", color=(0.7, 0.2, 0.2, 1))
        layout.add_widget(self.status_label)
        self.add_widget(layout)

    def _do_register(self, instance):
        name = self.name_input.text.strip()
        phone = self.phone_input.text.strip()
        password = self.pass_input.text.strip()
        contact = self.contact_input.text.strip()

        if not all([name, phone, password, contact]):
            self.status_label.text = "All fields are required."
            return
        if len(password) < 8:
            self.status_label.text = "Password must be at least 8 characters."
            return

        self.status_label.text = "Creating account..."
        threading.Thread(
            target=self._register_thread,
            args=(name, phone, password, contact),
            daemon=True,
        ).start()

    def _register_thread(self, name, phone, password, contact):
        success = app_core.register(name, phone, password, contact)
        if success:
            app_core.start()
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "main"), 0)
        else:
            Clock.schedule_once(
                lambda dt: setattr(self.status_label, "text", "Registration failed."),
                0,
            )


# ════════════════════════════════════════════════════════════════
# Main Screen — mode selection + SOS
# ════════════════════════════════════════════════════════════════
class MainScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=24, spacing=16)

        name = app_core.user.get("name", "User")
        layout.add_widget(Label(
            text=f"Welcome, {name}",
            font_size="20sp",
            size_hint_y=0.1,
            color=(0.1, 0.1, 0.1, 1),
        ))

        # Mode buttons
        indoor_btn = Button(
            text="Indoor Mode\n(Scene Intelligence)",
            background_color=(0.85, 0.55, 0.15, 1),
            halign="center",
        )
        outdoor_btn = Button(
            text="Outdoor Mode\n(GPS Navigation)",
            background_color=(0.2, 0.5, 0.8, 1),
            halign="center",
        )
        sos_btn = Button(
            text="SOS",
            background_color=(0.8, 0.15, 0.15, 1),
            font_size="20sp",
            size_hint_y=0.15,
        )

        indoor_btn.bind(on_press=self._go_indoor)
        outdoor_btn.bind(on_press=self._go_outdoor)
        sos_btn.bind(on_press=self._trigger_sos)

        layout.add_widget(indoor_btn)
        layout.add_widget(outdoor_btn)
        layout.add_widget(sos_btn)

        self.status_label = Label(text="", font_size="13sp", color=(0.3, 0.3, 0.3, 1))
        layout.add_widget(self.status_label)
        self.add_widget(layout)

    def _go_indoor(self, instance):
        self.manager.current = "indoor"

    def _go_outdoor(self, instance):
        self.manager.current = "outdoor"

    def _trigger_sos(self, instance):
        self.status_label.text = "Sending SOS..."
        threading.Thread(target=app_core.trigger_sos, daemon=True).start()
        self.status_label.text = "SOS sent to emergency contact."


# ════════════════════════════════════════════════════════════════
# Indoor Screen
# ════════════════════════════════════════════════════════════════
class IndoorScreen(Screen):
    _event = None

    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=24, spacing=12)
        layout.add_widget(Label(text="Scene Intelligence — Indoor",
                                font_size="18sp", size_hint_y=0.1,
                                color=(0.1, 0.1, 0.1, 1)))

        self.scene_label = Label(
            text="Analysing scene...",
            font_size="16sp",
            halign="center",
            text_size=(Window.width - 48, None),
            color=(0.2, 0.2, 0.2, 1),
        )
        layout.add_widget(self.scene_label)

        scan_btn = Button(text="Scan Now", background_color=(0.85, 0.55, 0.15, 1),
                          size_hint_y=None, height=52)
        scan_btn.bind(on_press=self._scan)

        back_btn = Button(text="Back", background_color=(0.55, 0.55, 0.55, 1),
                          size_hint_y=None, height=44)
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "main"))

        layout.add_widget(scan_btn)
        layout.add_widget(back_btn)
        self.add_widget(layout)

        # Auto-scan every 3 seconds
        self._event = Clock.schedule_interval(self._auto_scan, 3)

    def on_leave(self):
        if self._event:
            self._event.cancel()

    def _scan(self, instance=None):
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _auto_scan(self, dt):
        self._scan()

    def _scan_thread(self):
        description = app_core.process_frame()
        Clock.schedule_once(
            lambda dt: setattr(self.scene_label, "text", description), 0
        )
        app_core.tts.speak(description)


# ════════════════════════════════════════════════════════════════
# Outdoor Screen
# ════════════════════════════════════════════════════════════════
class OutdoorScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=24, spacing=12)
        layout.add_widget(Label(text="GPS Navigation — Outdoor",
                                font_size="18sp", size_hint_y=0.1,
                                color=(0.1, 0.1, 0.1, 1)))

        self.dest_input = TextInput(
            hint_text="Enter destination (e.g. Hyderabad Railway Station)",
            multiline=False,
            size_hint_y=None,
            height=48,
        )
        layout.add_widget(self.dest_input)

        go_btn = Button(text="Get Directions", background_color=(0.2, 0.5, 0.8, 1),
                        size_hint_y=None, height=52)
        go_btn.bind(on_press=self._navigate)

        self.steps_label = Label(
            text="",
            font_size="14sp",
            halign="left",
            text_size=(Window.width - 48, None),
            color=(0.2, 0.2, 0.2, 1),
        )

        back_btn = Button(text="Back", background_color=(0.55, 0.55, 0.55, 1),
                          size_hint_y=None, height=44)
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "main"))

        layout.add_widget(go_btn)
        layout.add_widget(self.steps_label)
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def _navigate(self, instance):
        destination = self.dest_input.text.strip()
        if not destination:
            self.steps_label.text = "Please enter a destination."
            return
        self.steps_label.text = "Fetching route..."
        threading.Thread(
            target=self._navigate_thread,
            args=(destination,),
            daemon=True,
        ).start()

    def _navigate_thread(self, destination):
        steps = app_core.navigate(destination)
        text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps)) if steps else "No route found."
        Clock.schedule_once(lambda dt: setattr(self.steps_label, "text", text), 0)
        # Speak each step
        for step in steps:
            app_core.tts.speak_blocking(step)


# ════════════════════════════════════════════════════════════════
# App root
# ════════════════════════════════════════════════════════════════
class SafeStrideKivyApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(AuthScreen(name="auth"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(IndoorScreen(name="indoor"))
        sm.add_widget(OutdoorScreen(name="outdoor"))
        return sm

    def on_stop(self):
        app_core.stop()


if __name__ == "__main__":
    SafeStrideKivyApp().run()
