import cv2
import matplotlib.pyplot as plt

points = []

def onclick(event):

    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        points.append((x, y))
        print(f"Punto seleccionado: ({x}, {y})")

        # Dibujar un círculo en el punto seleccionado
        plt.plot(x, y, 'ro') 
        plt.draw()

# Cargar la imagen
image = cv2.imread("Public/Avatares/secretaria.jpg")

if image is None:
    print("Error: No se pudo cargar la imagen. Verifica la ruta.")
else:

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Mostrar la imagen con matplotlib
    fig, ax = plt.subplots()
    ax.imshow(image_rgb)
    ax.set_title("Haz clic en la imagen para seleccionar los puntos")
    
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    
    plt.show()

    fig.canvas.mpl_disconnect(cid)

    # Imprimir los puntos seleccionados
    print("Puntos seleccionados:", points)
