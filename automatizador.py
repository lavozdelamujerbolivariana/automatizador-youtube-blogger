import os
import json
import datetime
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/blogger'
]

# Si el ID directo falla, el script intentará buscar tu blog automáticamente
BLOG_ID_CONFIGURADO = '3318214309328221768'

CANAL_VOZ_MUJER = 'UCGfoI7v6hNipgiG8C_IJjfQ'
CANAL_SON_DEL_23 = 'UCCoHvADohOJ0sWevJBZ9h9A'

PROGRAMAS_SON_DEL_23 = [
    "pueblo comunicador",
    "misión en amor mayor",
    "avance comunal",
    "la nota cultural"
]

def obtener_credenciales():
    token_env = os.environ.get('GOOGLE_TOKEN_JSON')
    if token_env:
        info_token = json.loads(token_env)
        return Credentials.from_authorized_user_info(info_token, SCOPES)
    
    if os.path.exists('token.json'):
        return Credentials.from_authorized_user_file('token.json', SCOPES)
    
    raise FileNotFoundError("No se encontraron credenciales en GOOGLE_TOKEN_JSON ni en token.json")

def main():
    creds = obtener_credenciales()
    youtube = build('youtube', 'v3', credentials=creds)
    blogger = build('blogger', 'v3', credentials=creds)

    # Verificar blogs disponibles en la cuenta para evitar errores 404
    try:
        user_blogs = blogger.blogs().listByUser(userId='self').execute()
        if 'items' in user_blogs and len(user_blogs['items']) > 0:
            print("Blogs encontrados en tu cuenta:")
            for b in user_blogs['items']:
                print(f" - Nombre: {b['name']} | ID: {b['id']} | URL: {b['url']}")
            # Usa automáticamente el primer blog válido encontrado
            blog_id = user_blogs['items'][0]['id']
        else:
            blog_id = BLOG_ID_CONFIGURADO
    except Exception as e:
        print(f"No se pudo listar los blogs automáticamente: {e}")
        blog_id = BLOG_ID_CONFIGURADO

    fecha_hoy = datetime.date.today()
    hace_siete_dias = fecha_hoy - datetime.timedelta(days=7)
    publicado_despues = hace_siete_dias.strftime('%Y-%m-%dT00:00:00Z')

    videos_recolectados = []

    # Recolectar videos de La Voz de la Mujer Bolivariana
    res_mujer = youtube.search().list(
        part='snippet',
        channelId=CANAL_VOZ_MUJER,
        publishedAfter=publicado_despues,
        type='video',
        maxResults=25
    ).execute()
    for item in res_mujer.get('items', []):
        videos_recolectados.append(item['id']['videoId'])

    # Recolectar videos filtrados de Radio Al Son Del 23
    res_son = youtube.search().list(
        part='snippet',
        channelId=CANAL_SON_DEL_23,
        publishedAfter=publicado_despues,
        type='video',
        maxResults=25
    ).execute()
    for item in res_son.get('items', []):
        titulo = item['snippet']['title'].lower()
        if any(prog in titulo for prog in PROGRAMAS_SON_DEL_23):
            videos_recolectados.append(item['id']['videoId'])

    if not videos_recolectados:
        print("No se encontraron videos nuevos en los últimos 7 días. Finalizando.")
        return

    # Crear Playlist en YouTube
    nombre_playlist = f"Resumen Comunal Semanal - {fecha_hoy.strftime('%d/%m/%Y')}"
    playlist = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': nombre_playlist,
                'description': 'Compilación automatizada de la programación semanal.'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }
    ).execute()

    playlist_id = playlist['id']
    print(f"Playlist creada con éxito. ID: {playlist_id}")

    for video_id in videos_recolectados:
        try:
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
            time.sleep(1)
        except HttpError as err:
            print(f"Advertencia al agregar video {video_id}: {err}")

    # Publicar en Blogger
    codigo_iframe = f'''<div style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; background: #000; border-radius: 8px; overflow: hidden;">
    <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
            src="https://www.youtube.com/embed/videoseries?list={playlist_id}&autoplay=1" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
    </iframe>
</div>'''

    blog_post = {
        'title': nombre_playlist,
        'content': f"<p>Compartimos la programación y resumen audiovisual correspondiente a esta semana:</p>{codigo_iframe}"
    }

    post_creado = blogger.posts().insert(
        blogId=blog_id,
        body=blog_post
    ).execute()

    print(f"Publicación creada con éxito en Blogger. URL: {post_creado.get('url')}")

if __name__ == '__main__':
    main()
