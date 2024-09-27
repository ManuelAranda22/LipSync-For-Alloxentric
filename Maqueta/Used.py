import os
import cv2
import numpy as np
import face_recognition
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE = os.path.join(PROJECT_ROOT, "Public", "Avatares", "secretaria.jpg")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
RHUBARB_PATH = "rhubarb"  # Asegúrate de que Rhubarb esté en tu PATH

# Crear directorio de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_image(path):
    """Carga una imagen desde el path especificado."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se pudo encontrar la imagen en {path}")
    
    image = cv2.imread(path)
    if image is None:
        raise ValueError(f"No se pudo cargar la imagen desde {path}")
    
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def detect_face_landmarks(image):
    """Detecta los puntos de referencia faciales en la imagen."""
    face_landmarks_list = face_recognition.face_landmarks(image)
    if not face_landmarks_list:
        raise ValueError("No se detectaron rostros en la imagen")
    
    return face_landmarks_list[0]['top_lip'], face_landmarks_list[0]['bottom_lip']

def modify_lips(image, top_lip, bottom_lip, frame_index, vertical_factor=0.0, horizontal_factor=0.0):
    """
    Modifica los labios según el índice del fotograma de una manera más natural.
    """
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    
    center_x = sum(p[0] for p in top_lip + bottom_lip) / len(top_lip + bottom_lip)
    center_y = sum(p[1] for p in top_lip + bottom_lip) / len(top_lip + bottom_lip)
    
    # Definir diferentes formas de boca
    mouth_shapes = [
        (0.0, 0.0),    # Boca cerrada
        (0.1, -0.05),  # Ligeramente abierta
        (0.2, -0.1),   # Más abierta
        (0.3, -0.15),  # Aún más abierta
        (0.4, -0.2),   # Muy abierta
        (0.3, -0.15),  # Comenzando a cerrar
        (0.2, -0.1),   # Más cerrada
        (0.1, -0.05),  # Casi cerrada
        (0.0, 0.0),    # Cerrada nuevamente
    ]
    
    base_vertical, base_horizontal = mouth_shapes[frame_index]
    vertical_factor += base_vertical
    horizontal_factor += base_horizontal
    
    modified_top_lip = []
    modified_bottom_lip = []
    
    for x, y in top_lip:
        dx = (x - center_x) * horizontal_factor
        dy = (y - center_y) * vertical_factor
        modified_top_lip.append((x + dx, y - dy))
    
    for x, y in bottom_lip:
        dx = (x - center_x) * horizontal_factor
        dy = (y - center_y) * vertical_factor
        modified_bottom_lip.append((x + dx, y + dy))
    
    # Suavizar las curvas de los labios
    modified_top_lip = smooth_curve(modified_top_lip)
    modified_bottom_lip = smooth_curve(modified_bottom_lip)
    
    # Dibujar los labios modificados
    draw.polygon(modified_top_lip + modified_bottom_lip[::-1], outline="red", fill="pink")
    
    return np.array(pil_image)

def smooth_curve(points, smoothness=0.2):
    """
    Aplica un suavizado a una curva definida por puntos.
    """
    smoothed = []
    for i in range(len(points)):
        prev = points[i-1]
        curr = points[i]
        next = points[(i+1) % len(points)]
        
        smoothed_x = curr[0] + smoothness * (prev[0] + next[0] - 2 * curr[0])
        smoothed_y = curr[1] + smoothness * (prev[1] + next[1] - 2 * curr[1])
        
        smoothed.append((smoothed_x, smoothed_y))
    
    return smoothed

def generate_key_frames(image, top_lip, bottom_lip):
    """Genera los 9 fotogramas clave para Rhubarb."""
    frames = []
    for i in range(9):
        modified_image = modify_lips(image, top_lip, bottom_lip, i)
        frames.append(modified_image)
    return frames

def save_frames(frames):
    """Guarda los fotogramas en el directorio de salida."""
    for i, frame in enumerate(frames):
        output_path = os.path.join(OUTPUT_DIR, f"frame_{i+1}.png")
        Image.fromarray(frame).save(output_path)
        logging.info(f"Fotograma guardado: {output_path}")

def run_rhubarb(audio_file):
    """Ejecuta Rhubarb con los fotogramas generados."""
    output_json = os.path.join(OUTPUT_DIR, "output.json")
    image_files = [os.path.join(OUTPUT_DIR, f"frame_{i+1}.png") for i in range(9)]
    
    command = [RHUBARB_PATH, "-f", "json", "-o", output_json, audio_file] + image_files
    
    try:
        subprocess.run(command, check=True)
        logging.info(f"Rhubarb se ejecutó exitosamente. Salida guardada en {output_json}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al ejecutar Rhubarb: {e}")
        raise

class FrameAdjuster:
    def __init__(self, frames, top_lip, bottom_lip):
        self.frames = frames
        self.current_frame = 0
        self.adjusted_frames = frames.copy()
        self.top_lip = top_lip
        self.bottom_lip = bottom_lip

        self.root = tk.Tk()
        self.root.title("Ajuste de Fotogramas")

        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()

        self.prev_button = tk.Button(self.root, text="Anterior", command=self.prev_frame)
        self.prev_button.pack(side=tk.LEFT)

        self.next_button = tk.Button(self.root, text="Siguiente", command=self.next_frame)
        self.next_button.pack(side=tk.RIGHT)

        self.save_button = tk.Button(self.root, text="Guardar", command=self.save_adjustments)
        self.save_button.pack()

        # Controles de ajuste
        self.vertical_scale = tk.Scale(self.root, from_=-0.5, to=0.5, resolution=0.05, orient=tk.HORIZONTAL, label="Apertura Vertical", command=self.adjust_frame)
        self.vertical_scale.set(0.0)
        self.vertical_scale.pack()

        self.horizontal_scale = tk.Scale(self.root, from_=-0.5, to=0.5, resolution=0.05, orient=tk.HORIZONTAL, label="Estiramiento Horizontal", command=self.adjust_frame)
        self.horizontal_scale.set(0.0)
        self.horizontal_scale.pack()

        self.show_frame()

    def show_frame(self):
        image = Image.fromarray(self.adjusted_frames[self.current_frame])
        image = image.resize((400, 400))
        self.photo = ImageTk.PhotoImage(image=image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.root.title(f"Ajuste de Fotogramas - Frame {self.current_frame + 1}")

    def prev_frame(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.show_frame()

    def next_frame(self):
        if self.current_frame < len(self.frames) - 1:
            self.current_frame += 1
            self.show_frame()

    def adjust_frame(self, _=None):
        vertical_factor = self.vertical_scale.get()
        horizontal_factor = self.horizontal_scale.get()
        
        adjusted_image = modify_lips(
            self.frames[self.current_frame],
            self.top_lip,
            self.bottom_lip,
            self.current_frame,
            vertical_factor,
            horizontal_factor
        )
        
        self.adjusted_frames[self.current_frame] = adjusted_image
        self.show_frame()

    def save_adjustments(self):
        self.root.quit()

    def run(self):
        self.root.mainloop()
        return self.adjusted_frames

def main():
    try:
        # Cargar la imagen
        image = load_image(INPUT_IMAGE)
        logging.info(f"Imagen cargada exitosamente desde {INPUT_IMAGE}")

        # Detectar puntos de referencia faciales
        top_lip, bottom_lip = detect_face_landmarks(image)
        logging.info("Puntos de referencia faciales detectados")

        # Generar fotogramas clave
        frames = generate_key_frames(image, top_lip, bottom_lip)
        logging.info("Fotogramas clave generados")

        # Ajustar fotogramas manualmente
        adjuster = FrameAdjuster(frames, top_lip, bottom_lip)
        adjusted_frames = adjuster.run()
        logging.info("Ajustes manuales completados")

        # Guardar fotogramas ajustados
        save_frames(adjusted_frames)

        # Ejecutar Rhubarb
        audio_file = filedialog.askopenfilename(title="Selecciona el archivo de audio", filetypes=[("WAV files", "*.wav")])
        if audio_file:
            run_rhubarb(audio_file)
        else:
            logging.warning("No se seleccionó archivo de audio. Rhubarb no se ejecutó.")

        messagebox.showinfo("Proceso Completado", "La generación de avatares y sincronización labial ha sido completada.")

    except Exception as e:
        logging.error(f"Error en el proceso: {e}")
        messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    main()