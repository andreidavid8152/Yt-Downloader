from pytube import YouTube
from flask import Flask, render_template, request, send_file, make_response, session
from pytube.exceptions import LiveStreamError, RegexMatchError 
import os, random, time, threading, subprocess


# Configuracion inicial de la app, se renombra la carpeta donde esta almacenado los templates, url y la carpeta de los archivos estaticos (css, images, js)
app = Flask(__name__, template_folder='../templates', static_url_path='/assets', static_folder='../assets')
app.secret_key = 'tu_clave_secreta_123_21_20'

#Se define la ruta para la pagina principal
@app.route('/')
def index():
    return render_template('index.html')

# Se define la ruta para el formulario de descarga
@app.route('/', methods=['POST'])
def showRequest():
    url = request.form.get('url') #Se obtiene la URL del formulario
    formato = request.form.get('select')
    session['url'] = url
    session['formato'] = formato
    media = show_Qualities(url, formato) #Se llama a la funcion de descarga
    title = YouTube(url).title
    return {'media': media, 'title': title}


@app.route('/download', methods=['POST'])
def download():
    archivos_Descargados = []
    numero_aleatorio = random.randint(100000, 999999)
    itag = request.data.decode('utf-8')  # Supongamos que el nombre de archivo se envía como texto
    url = session.get('url')
    formato_descarga = session.get('formato')
    yt = YouTube(url)
    
    stream = yt.streams.get_by_itag(itag)

    titulo = stream.title.replace(' ', '_')


    if formato_descarga == 'mp3':
        file_path = stream.download(output_path="/tmp/", filename="MinimalTools_"+ titulo + f'_{numero_aleatorio}.mp3')
        archivos_Descargados.append(file_path)
    elif formato_descarga == 'mp4':
        file_path = stream.download(output_path="/tmp/", filename=titulo + f'_{numero_aleatorio}.mp4')
        stream_audio = yt.streams.get_by_itag(251)
        audio_path = stream_audio.download(output_path="/tmp/", filename=titulo.replace(' ', '_') + f'_{numero_aleatorio}.mp3');
        archivos_Descargados.append(file_path)
        archivos_Descargados.append(audio_path)
        file_path = add_audio_to_video(file_path, audio_path)
        archivos_Descargados.append(file_path)
    
    # Extrae el nombre de archivo del file_path
    file_name = os.path.basename(file_path)

    response = make_response(send_file(file_path))

    # Establece el encabezado Content-Disposition con el nombre de archivo
    response.headers['Content-Disposition'] = f'attachment; filename={file_name}'

    #Elimina los archivos después de enviar la respuesta
    for a in archivos_Descargados:
        delayed_delete(a, 0.3)

    return response

def delayed_delete(file_path, delay):
    def delete_file():
        time.sleep(delay)
        os.remove(file_path)

    threading.Thread(target=delete_file).start()

def add_audio_to_video(video_path, audio_path):
    nombre_archivo = os.path.basename(video_path)
    directorio = os.path.dirname(video_path)

    nuevo_nombre_archivo = f'MinimalTools_{nombre_archivo}'
    output_path = os.path.join(directorio, nuevo_nombre_archivo)

    command = f'ffmpeg -y -i {video_path} -i {audio_path} -c:v copy -c:a aac {output_path}'
    process = subprocess.Popen(command, shell=True)
    process.communicate()  # Espera a que termine ffmpeg

    return output_path


def show_Qualities(url, formato):


    try:
        yt = YouTube(url)
    except RegexMatchError as e:
        return 'Ingrese una url valida.'
    
    if(formato == 'mp4'):   
        try:
            streams = [stream for stream in yt.streams if (stream.mime_type.startswith('video/webm'))]
        except LiveStreamError as e:
            return 'El video no puede ser procesado porque aun esta en vivo, Intentelo mas tarde.'
        
        streams = sorted(streams, key=lambda x: (-int(x.resolution[:-1]), -int(x.fps)))
        # Crear una lista de descripciones de las opciones de streaming
        stream_descriptions =  ""
        # Crear un conjunto para mantener un registro de las resoluciones únicas
        resoluciones_unicas = set()
        for stream in streams:

            # Obtener la resolución actual
            resolucion_actual = stream.resolution
            resolucion_actual = int(resolucion_actual.replace('p', ''))

            # Verificar si la resolución actual ya ha sido agregada
            if resolucion_actual not in resoluciones_unicas:
                # Agregar la resolución actual al conjunto de resoluciones únicas
                resoluciones_unicas.add(resolucion_actual)
                stream_descriptions += f'<div class="mb-2"><button onclick="descarga({stream.itag})" type="submit" value"{stream.itag}" class="w-40 relative inline-flex items-center justify-center p-0.5 mb-2 mr-2 overflow-hidden text-sm font-medium text-gray-900 rounded-lg group bg-gradient-to-br from-green-400 to-blue-600 group-hover:from-green-400 group-hover:to-blue-600 hover:text-white dark:text-white focus:ring-4 focus:outline-none focus:ring-green-200 dark:focus:ring-green-800"> <span class="w-full relative px-5 py-2.5 transition-all ease-in duration-75 bg-white dark:bg-gray-900 rounded-md group-hover:bg-opacity-0"> {stream.resolution} | {round(stream.filesize_mb, 1)} MB </span></button></div>'

    elif(formato == 'mp3'):
        try:
            streams = yt.streams.filter(only_audio=True)
        except LiveStreamError as e:
            return "El audio no se puede procesar porque aun esta en vivo, Intentelo mas tarde."
        streams = sorted(streams, key=lambda x: int(x.abr.rstrip('kbps')), reverse=True)
        # Crear una lista de descripciones de las opciones de streaming
        stream_descriptions = ""
        # Crear un conjunto para mantener un registro de las resoluciones únicas
        resoluciones_unicas = set()
        for stream in streams:
            # Obtener la resolución actual
            resolucion_actual = stream.abr
            if resolucion_actual not in resoluciones_unicas:
                resoluciones_unicas.add(resolucion_actual)
                stream_descriptions += f'<div class="mb-2"><button onclick="descarga({stream.itag})" type="submit" value"{stream.itag}" class="w-40 relative inline-flex items-center justify-center p-0.5 mb-2 mr-2 overflow-hidden text-sm font-medium text-gray-900 rounded-lg group bg-gradient-to-br from-green-400 to-blue-600 group-hover:from-green-400 group-hover:to-blue-600 hover:text-white dark:text-white focus:ring-4 focus:outline-none focus:ring-green-200 dark:focus:ring-green-800"> <span class="w-full relative px-5 py-2.5 transition-all ease-in duration-75 bg-white dark:bg-gray-900 rounded-md group-hover:bg-opacity-0"> {stream.abr} | {round(stream.filesize_mb, 1)} MB </span></button></div>'      
    
    return stream_descriptions
