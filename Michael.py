import cv2
import pyautogui
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import pyttsx3
from kivy.core.window import Window

# Inicialización del motor de pyttsx3
motor_audio = pyttsx3.init()

voices = motor_audio.getProperty('voices')  # Lista de voces disponibles
motor_audio.setProperty('voice', voices[0].id)  # Configuración de tipo de voz especificada

motor_audio.setProperty('volume', 1.0)  # Volumen de la voz
motor_audio.setProperty('rate', 150)  # Velocidad de habla

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)


class MainWidget(BoxLayout):
    pass


class InputField(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temp_text = ''  # Variable para almacenar el texto temporalmente
        Clock.schedule_interval(self.check_cursor_on_execute, 0.1)  # Verifica cada 0.1 segundos

    # Método para añadir texto al TextInput
    def update_text(self, text):
        self.ids.my_text_input.text += text

    # Método para eliminar el último carácter del TextInput
    def delete_last_char(self):
        current_text = self.ids.my_text_input.text
        if current_text:
            self.ids.my_text_input.text = current_text[:-1]

    # Método para reproducir por audio el texto ingresado
    def clear_input_text(self):
        self.temp_text = self.ids.my_text_input.text
        if self.temp_text:
            motor_audio.say(self.temp_text)
            motor_audio.runAndWait()
        self.ids.my_text_input.text = ''

    # Método para verificar si el cursor está sobre el botón Execute
    def check_cursor_on_execute(self, dt):
        mouse_x, mouse_y = Window.mouse_pos
        execute_button = self.ids.execute_button
        button_x, button_y = execute_button.to_window(*execute_button.pos)
        button_width, button_height = execute_button.size

        # Verifica si el cursor está dentro de los límites del botón Execute
        if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
            # Cambia el color del botón a amarillo para indicar el clic
            execute_button.background_color = [1, 1, 0, 1]  # Amarillo en RGBA

            # Simula el clic del botón
            execute_button.dispatch('on_release')

            # Restaura el color original después de un retraso
            Clock.schedule_once(lambda dt: self.reset_execute_button_color(), 0.2)

    # Método para restaurar el color del botón Execute
    def reset_execute_button_color(self):
        execute_button = self.ids.execute_button
        execute_button.background_color = [1, 1, 1, 1]  # Blanco (o el color original)


class CameraField(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.update_frame, 1.0 / 30)

    # Método para mostrar el cursor con el rostro
    def update_frame(self, dt):
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                face_center_x = x + w // 2
                face_center_y = y + h // 2

                screen_width, screen_height = pyautogui.size()

                # Factor de sensibilidad
                sensitivity_factor = 2  # Incrementa este valor para mayor sensibilidad

                # Movimiento del cursor del mouse con sensibilidad ajustada
                # Primero mapeamos las posiciones relativas
                mapped_x = screen_width - (face_center_x * screen_width // cap.get(3))
                mapped_y = face_center_y * screen_height // cap.get(4)

                # Luego aplicamos el factor de sensibilidad
                target_x = int((mapped_x - screen_width / 2) * sensitivity_factor + screen_width / 2)
                target_y = int((mapped_y - screen_height / 2) * sensitivity_factor + screen_height / 2)

                # Limitar el cursor dentro de los bordes de la pantalla
                target_x = max(0, min(screen_width - 1, target_x))
                target_y = max(0, min(screen_height - 1, target_y))

                pyautogui.moveTo(target_x, target_y)

                cv2.circle(frame, (50, 50), 30, (0, 0, 255),
                           -1)  # Dibujar un círculo rojo en la esquina superior izquierda

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
                texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.image_widget.texture = texture


class PredictedTextField(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prediction_buttons = []
        self.hover_time = 0.7
        self.word_dictionary = {
            # Verbos comunes
            'estar': ['estoy', 'estás', 'está', 'estamos', 'están', 'estaría', 'estábamos', 'estuvieron', 'están',
                      'estarán'],
            'ser': ['soy', 'eres', 'es', 'somos', 'son', 'seré', 'sería', 'fui', 'fuimos', 'serán', 'sido'],
            'tener': ['tengo', 'tienes', 'tiene', 'tenemos', 'tienen', 'tendría', 'tuve', 'tenían', 'tendremos',
                      'tendrá'],
            'hacer': ['hago', 'haces', 'hace', 'hacemos', 'hacen', 'haré', 'haría', 'hizo', 'hacíamos', 'hicieron'],
            'ir': ['voy', 'vas', 'va', 'vamos', 'van', 'fui', 'irá', 'íbamos', 'van', 'vayan', 'fueron', 'iría'],
            'decir': ['digo', 'dices', 'dice', 'decimos', 'dicen', 'dije', 'diré', 'decía', 'diría', 'dijeron'],
            'poder': ['puedo', 'puedes', 'puede', 'podemos', 'pueden', 'podría', 'pudimos', 'podrían', 'puedo',
                      'podríamos'],
            'querer': ['quiero', 'quieres', 'quiere', 'queremos', 'quieren', 'quería', 'quisiera', 'querrán', 'quiso'],
            'ver': ['veo', 'ves', 've', 'vemos', 'ven', 'vi', 'vio', 'vería', 'veremos', 'verán'],
            'dar': ['doy', 'das', 'da', 'damos', 'dan', 'dio', 'daba', 'daré', 'daría', 'dado', 'darán'],

            # Pronombres
            'yo': ['mi', 'me', 'conmigo', 'mis', 'mío', 'mía'],
            'tu': ['te', 'contigo', 'tuyo', 'tuya', 'tus', 'vosotros', 'tuyos', 'tuyas'],
            'el': ['él', 'ella', 'ello', 'ellos', 'ellas', 'suyo', 'suyos', 'suyas', 'su', 'sus'],
            'nosotros': ['nos', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'con nosotros'],
            'ustedes': ['su', 'sus', 'de ustedes', 'con ustedes'],

            # Preguntas comunes
            'que': ['qué', 'quién', 'quiénes', 'cuál', 'cuáles', 'por qué', 'qué tal', 'cuánto', 'cuánta', 'cuántos',
                    'cuántas'],
            'como': ['cómo', 'cuándo', 'cuánto', 'cuánta', 'dónde', 'cómo estás', 'de qué forma', 'por qué',
                     'para qué'],

            # Saludos y cortesía
            'hola': ['buenos días', 'buenas tardes', 'buenas noches', 'qué tal', 'saludos', 'hola a todos'],
            'gracias': ['por favor', 'de nada', 'muchas gracias', 'mil gracias', 'agradecido', 'gracias a ti'],
            'adios': ['hasta luego', 'nos vemos', 'hasta pronto', 'chau', 'hasta mañana', 'despedida', 'adiós',
                      'cuídate'],

            # Necesidades básicas
            'quiero': ['necesito', 'deseo', 'quisiera', 'me gustaría', 'tengo ganas de', 'busco'],
            'puedo': ['podría', 'podrías', 'pueden', 'me permites', 'sería posible', 'puedo ayudar',
                      'podrías ayudarme'],
            'ayuda': ['ayúdame', 'auxilio', 'socorro', 'apoyo', 'colaboración', 'necesito ayuda', 'puedes ayudarme'],

            # Tiempo
            'hoy': ['ayer', 'mañana', 'ahora', 'luego', 'pronto', 'pasado mañana', 'anteayer'],
            'dia': ['día', 'tarde', 'noche', 'semana', 'mes', 'año', 'días', 'mañanas', 'tardes', 'noches'],
            'tiempo': ['clima', 'momento', 'segundos', 'minutos', 'horas', 'ocasión', 'época', 'siempre', 'nunca',
                       'frecuencia'],

            # Estados
            'bien': ['mal', 'regular', 'excelente', 'perfecto', 'más o menos', 'mejor', 'peor'],
            'feliz': ['triste', 'enojado', 'cansado', 'contento', 'preocupado', 'deprimido', 'animado', 'motivado'],
            'enfermo': ['sano', 'agotado', 'recuperado', 'débil', 'fuerte', 'dolor', 'fatiga'],

            # Emociones
            'amor': ['odio', 'aprecio', 'admiración', 'afecto', 'enamoramiento', 'alegría'],
            'miedo': ['valentía', 'temor', 'respeto', 'nervios', 'tensión', 'estrés', 'calma'],
            'paz': ['guerra', 'tranquilidad', 'conflicto', 'serenidad', 'armonía', 'tensión'],

            # Acciones cotidianas
            'comer': ['desayunar', 'almorzar', 'cenar', 'merendar', 'beber', 'tomar', 'masticar', 'ingerir'],
            'dormir': ['descansar', 'reposar', 'acostarse', 'despertar', 'soñar', 'quedarse dormido', 'levantarse'],
            'trabajar': ['laborar', 'esforzarse', 'estudiar', 'preparar', 'colaborar', 'asistir', 'supervisar'],
            'jugar': ['divertirse', 'participar', 'competir', 'ganar', 'perder', 'entrenar', 'esforzarse'],

            # Palabras de frecuencia
            'siempre': ['nunca', 'a veces', 'frecuentemente', 'diariamente', 'constantemente', 'ocasionalmente',
                        'rara vez'],
            'todos': ['cada', 'ninguno', 'algunos', 'varios', 'unos pocos', 'la mayoría', 'pocos'],
            'casi': ['apenas', 'aproximadamente', 'en su mayoría', 'completamente', 'parcialmente']
        }

        # Crear botones iniciales
        self.create_prediction_buttons(list(self.word_dictionary.keys())[:12])

        # Programar la vinculación del TextInput para después de que la aplicación esté lista
        Clock.schedule_once(self.bind_text_input, 0)
        Clock.schedule_interval(self.check_hover_buttons, 0.5)

    def bind_text_input(self, dt):
        """Vincula el TextInput una vez que la aplicación está lista"""
        app = App.get_running_app()
        if app and app.root:
            input_field = app.root.ids.input_field.ids.my_text_input
            input_field.bind(text=self.on_text_change)

    def create_prediction_buttons(self, words):
        # Limpiar botones existentes
        self.clear_widgets()
        self.prediction_buttons = []

        # Crear nuevos botones
        for word in words:
            button = Button(text=word)
            button.hover_timer = None
            button.bind(on_release=self.update_input_field)
            button.original_background_color = button.background_color[:]
            self.add_widget(button)
            self.prediction_buttons.append(button)

    def on_text_change(self, instance, value):
        if not value:
            # Si no hay texto, mostrar palabras iniciales
            self.create_prediction_buttons(list(self.word_dictionary.keys())[:12])
            return

        # Obtener la última palabra siendo escrita
        current_word = value.split()[-1].lower() if value.split() else ''

        # Buscar predicciones
        predictions = []

        # Buscar en keys del diccionario
        for key in self.word_dictionary.keys():
            if key.startswith(current_word):
                predictions.append(key)

        # Buscar en valores del diccionario
        for values in self.word_dictionary.values():
            for word in values:
                if word.startswith(current_word) and word not in predictions:
                    predictions.append(word)

        # Limitar a 12 predicciones y actualizar botones
        predictions = predictions[:12]
        if predictions:
            self.create_prediction_buttons(predictions)
        else:
            # Si no hay predicciones, mostrar palabras relacionadas con la última palabra completa
            last_complete_word = value.split()[-2].lower() if len(value.split()) > 1 else ''
            if last_complete_word in self.word_dictionary:
                self.create_prediction_buttons(self.word_dictionary[last_complete_word])
            else:
                # Si no hay palabras relacionadas, mostrar palabras iniciales
                self.create_prediction_buttons(list(self.word_dictionary.keys())[:12])

    def update_input_field(self, instance):
        app = App.get_running_app()
        if not app or not app.root:
            return

        input_field = app.root.ids.input_field.ids.my_text_input
        current_text = input_field.text

        # Separar el texto en palabras
        words = current_text.split()

        if words:
            # Reemplazar la última palabra con la predicción seleccionada
            words[-1] = instance.text
        else:
            # Si no hay palabras, simplemente agregar la predicción
            words = [instance.text]

        # Actualizar el texto del input
        input_field.text = ' '.join(words) + ' '

        # Cambiar color del botón temporalmente
        instance.background_color = [1, 1, 0, 1]
        Clock.schedule_once(lambda dt: self.reset_button_color(instance), 0.2)

    def reset_button_color(self, button):
        button.background_color = button.original_background_color

    def check_hover_buttons(self, dt):
        mouse_x, mouse_y = Window.mouse_pos
        for button in self.prediction_buttons:
            button_x, button_y = button.to_window(*button.pos)
            button_width, button_height = button.size

            if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                if button.hover_timer is None:
                    button.hover_timer = Clock.schedule_once(
                        lambda dt, btn=button: self.trigger_button(btn),
                        self.hover_time
                    )
            else:
                if button.hover_timer is not None:
                    button.hover_timer.cancel()
                    button.hover_timer = None

    def trigger_button(self, button):
        button.dispatch('on_release')
        button.hover_timer = None


class KeyBoard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Diccionario para almacenar referencias a las teclas
        self.keys = []

        rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.', ','],
            [' ', 'delete']
        ]

        for row in rows:
            row_layout = BoxLayout()
            for key in row:
                if key == ' ':
                    key_button = Button(text=key, size_hint_x=0.8)
                elif key == 'delete':
                    key_button = Button(text=key, size_hint_x=0.2)
                else:
                    key_button = Button(text=key)

                # Almacena el color de fondo original
                key_button.original_background_color = key_button.background_color[:]

                key_button.bind(on_release=self.key_pressed)
                row_layout.add_widget(key_button)
                self.keys.append(key_button)  # Almacena la referencia de la tecla
            self.add_widget(row_layout)

        # Variables para manejar el swype
        self.last_key = None
        self.swype_delay = 0.7  # Retraso en segundos
        self.swype_triggered = False

        # Programar la verificación periódica del cursor
        Clock.schedule_interval(self.check_swype, 0.1)  # Cada 0.1 segundos

    def key_pressed(self, instance):
        input_field = App.get_running_app().root.ids.input_field
        if instance.text != 'delete':
            input_field.update_text(instance.text)
        else:
            input_field.delete_last_char()

        # Resaltar la tecla en amarillo
        instance.background_color = [1, 1, 0, 1]  # Amarillo en RGBA

        # Programar el restablecimiento del color después de 0.2 segundos
        Clock.schedule_once(lambda dt: self.reset_key_color(instance), 0.2)

    def reset_key_color(self, key):
        # Restablecer al color de fondo original
        key.background_color = key.original_background_color

    def check_swype(self, dt):
        mouse_x, mouse_y = Window.mouse_pos
        # Convertir la posición del mouse a la posición relativa del teclado
        keyboard_pos = self.to_window(*self.pos)
        keyboard_width, keyboard_height = self.size
        relative_x = mouse_x - keyboard_pos[0]
        relative_y = mouse_y - keyboard_pos[1]

        if 0 <= relative_x <= keyboard_width and 0 <= relative_y <= keyboard_height:
            # Iterar sobre las teclas para ver si el cursor está sobre alguna
            for key in self.keys:
                key_x, key_y = key.to_window(*key.pos)
                key_width, key_height = key.size
                if key_x <= mouse_x <= key_x + key_width and key_y <= mouse_y <= key_y + key_height:
                    if self.last_key != key:
                        self.last_key = key
                        self.swype_triggered = False
                        Clock.schedule_once(lambda dt: self.trigger_key(key), self.swype_delay)
                    break
        else:
            self.last_key = None

    def trigger_key(self, key):
        if self.last_key == key and not self.swype_triggered:
            key.dispatch('on_release')
            self.swype_triggered = True


class HomeApp(App):
    def on_stop(self):
        # Libera la cámara al cerrar la aplicación
        cap.release()
        cv2.destroyAllWindows()



HomeApp().run()