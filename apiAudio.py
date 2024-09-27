import requests
import datetime
import subprocess
import sys
import time
import threading

# URL de la API TTS
url = 'http://35.215.229.147:8002/default/inference'

def log_time(start_time, step_name):
    duration = time.time() - start_time
    print(f"{step_name} tomó {duration:.2f} segundos")
    return time.time()

def obtener_audio(texto):
    start_time = time.time()
    params = {'text': texto}

    # Realizar la solicitud
    response = requests.post(url, json=params)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    audio_filename = f'public/audio/audio_{timestamp}.wav'
    
    with open(audio_filename, 'wb') as audio_file:
        audio_file.write(response.content)

    print(f"Audio guardado como {audio_filename}")
    log_time(start_time, "Obtener audio (TTS)")
    return audio_filename

def guardar_transcripcion(texto, audio_filename):
    start_time = time.time()
    transcripcion_filename = f'public/transcriptions/{audio_filename.split("/")[-1]}.txt'
    
    with open(transcripcion_filename, 'w', encoding='utf-8') as trans_file:
        trans_file.write(texto)
    
    print(f"Transcripción guardada como {transcripcion_filename}")
    log_time(start_time, "Guardar transcripción")
    return transcripcion_filename

def generar_fonemas(audio_filename, transcripcion_filename):
    start_time = time.time()
    mapp_filename = f'public/mapps/{audio_filename.split("/")[-1]}.json'
    
    # Comando para ejecutar Rhubarb Lip Sync
    rhubarb_command = [
    'rhubarb', audio_filename,
    '--dialogFile', transcripcion_filename,
    '--recognizer', 'phonetic',
    '--exportFormat', 'json',
    '-o', mapp_filename,
]

    # Ejecutar Rhubarb en un hilo separado
    subprocess.run(rhubarb_command)

    print(f"Fonemas generados y guardados en {mapp_filename}")
    log_time(start_time, "Generar fonemas (Rhubarb)")
    return mapp_filename

def guardar_ultimo_archivo(audio_filename, mapp_filename):
    start_time = time.time()
    
    with open('public/ultimo_archivo.txt', 'w') as ultimo_archivo:
        ultimo_archivo.write(f'{audio_filename}\n{mapp_filename}')
    
    print(f"Último audio y mapeo guardados en public/ultimo_archivo.txt")
    log_time(start_time, "Guardar último archivo")

def main(texto):
    total_start_time = time.time()

    # Generar y guardar
    audio_filename = obtener_audio(texto)    
    transcripcion_filename = guardar_transcripcion(texto, audio_filename)  
    
    # Generar fonemas en un hilo separado
    mapp_filename = generar_fonemas(audio_filename, transcripcion_filename)
    guardar_ultimo_archivo(audio_filename, mapp_filename)

    log_time(total_start_time, "Ejecucion")

# Usar Aqui
if __name__ == "__main__":
    texto = sys.argv[1] if len(sys.argv) > 1 else "si, escribenos y te contamos como podemos ayudar"
    main(texto)
