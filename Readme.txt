Módulos de Python
ApiAudios
El módulo ApiAudios es el encargado de conectar con la API de TTS (Text-to-Speech) y ejecutar Rhubarb para procesar el audio generado. Este módulo almacena los audios en la carpeta Audios y los mapeos de fonemas en la carpeta Mapps. Además, guarda un registro en texto de la consulta enviada al TTS (lo que el usuario quiere que el TTS pronuncie), lo cual puede ser útil para analizar retrasos o ayudar a Rhubarb a identificar fonemas con mayor precisión.

Este módulo puede probarse directamente desde el propio archivo Python en las últimas líneas, donde aparece el texto "Usar aquí", o desde la interfaz web, ingresando texto en el cuadro inferior y presionando el botón "Enviar". En futuras versiones, este cuadro se conectará a un modelo de lenguaje o un servicio de inteligencia, y estará orientado a escuchar al usuario en lugar de realizar pruebas.

Simple_server.py
El archivo simple_server.py es un servidor personalizado que mantiene la comunicación en tiempo real entre los distintos módulos del proyecto (con posibilidad de modificación según necesidades). Para inicializar tanto la interfaz como el servidor, es necesario ejecutar este archivo. El servidor utiliza dos puertos, que pueden ser configurados libremente por el desarrollador.

Archivos de la interfaz web
Los archivos index.html, scripts.js y styles.css conforman la estructura de la interfaz web:

Index.html: Contiene el código HTML básico para la visualización de la página.
Styles.css: Proporciona el diseño visual de la interfaz.
Scripts.js: Implementa las funcionalidades clave, como la conexión con el backend, la carga de los frames del avatar, la reproducción de audio y el mapeo de fonemas, así como la generación de audios de delay y la sincronización de imágenes para que el avatar hable.
Es crucial mantener la coherencia entre estos archivos, ya que cualquier modificación podría afectar la funcionalidad del proyecto.

Otros apartados
Maqueta, First-order-model, y .venv forman parte de la maqueta del sistema Agent Maker, utilizado para crear nuevos avatares de manera automática. Es importante revisar estos apartados para determinar si se deben continuar, reemplazar o eliminar del proyecto.
Futuras actualizaciones
Se recomienda lo siguiente para mejorar el proyecto en futuras versiones:

1)Integrar una base de datos para almacenar archivos estáticos.

2)Pulir funcionalidades existentes en búsqueda de un producto de mayor calidad.

3)Mejorar los audios de delay: Estos audios son frases cortas que se reproducen mientras el agente carga una respuesta. Actualmente, se utilizan frases genéricas como "Un momento" o "Estoy en ello". En futuras versiones, estas frases deberían tener más contexto en función de la solicitud del usuario. Por ejemplo, si el usuario pide realizar una acción, la frase de delay podría estar relacionada con esa acción; si el usuario hace una pregunta, la frase de delay debería reflejar que se está buscando una respuesta.

4)Agregar subtítulos para mejorar la accesibilidad y comprensión de lo que dice el avatar.

Si surge alguna duda o es necesario realizar modificaciones, se recomienda contactar con el supervisor del proyecto.

