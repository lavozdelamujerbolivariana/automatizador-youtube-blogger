import os
import json
import datetime
import time
import urllib.request
import urllib.parse
import base64
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------
# 1. Configuración e Identificadores
# ---------------------------------------------------------
SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/blogger'
]

BLOG_ID_CONFIGURADO = '3318214309328221768'

# Canal específico de Radio Al Son Del 23 (filtro estricto por programas)
CANAL_SON_DEL_23 = 'UCCoHvADohOJ0sWevJBZ9h9A'
PROGRAMAS_SON_DEL_23 = [
    "estudiantes de la patria",
    "latinoamerica en vivo",
    "el noticiero",
    "la hora en que habla el pueblo",
    "con chavez siempre"
]

# Resto de los canales de la red multiplataforma
CANALES_GENERALES = [
    'UCGfoI7v6hNipgiG8C_IJjfQ', # La Voz de la Mujer Bolivariana
    'UCFdk1wJb0spw84NkHPTk4tA', # Caricuao TV
    'UcqOThr_FTCgYvNohZhIf1Mg', # Curiosidades del Teatro Studio
    'UCd9OE1Xe4vwsEXRjFHJWOEg', # OEARECORDSTV
    'UChotD-TotPKfmSc-iuSnoiw', # ViticoTV
    'UC3-grdwTAlgMyKAHmfI2H1A', # DE LA MANO CON LAS COMUNIDADES
    'UC_sNkqifMBMc0-PsU-a4yKQ', # Misioncultura_ve
    'UCmn4qVXzaX1tgKqiKCcW8XQ', # TERRA TV
    'UCpu1ZMD4LeHhKz5jog-pWUA', # ATENCIÓN
    'UCNKeQ4b1jVeq-aqa4r88oFQ', # SiguarayaTV
    'UC8czaPbVT_prM4xruQ76rVQ', # Pablo Gabriel Lopez
    'UC4U5EL5MY86KBPzoBjijQEg', # PALESTINA 11 MIL AÑOS DE HISTORIA
    'UCi3lfrSRBD9DV44dkfDc_9Q', # CENTRAL BOLIVARIANA SOCIALISTA DE TRABAJADORES
    'UCJrFO9chbbwyAu5v9yXzrdg', # Análisis Situacional
    'UC1r5CJoV6SvS8Cw3I9bfn-Q', # 8Minutos Medio Alternativo
    'UCaVWm7UObDT5s6reiIOKDTw', # Milicia Bolivariana (Oficial)
    'UCCye2_ZqdodU84QVfNMVFMg', # Universidad Nacional de las Comunas
    'UCjzXvNX72fZC9RavcpTbrFw', # ConCienciaTV
    'UCPH59ZFi4yyursjwzg9p45w', # VEPACOTV
    'UCkoRw_UIiG1JNh3GfI7hH_g', # Universidad Internacional de las Comunicaciones
    'UCJ3Gcy7Z_CmqnbWjg7Nk1jw', # LOGROS DE LA PATRIA
    'UCJCrzzDcAoFd3i1x0QbxlEA', # RADIO ARSENAL 98.1 FM
    'UCSA0cyWzAEssd9Wli-8uFKg', # Colectivo La Piedrita
    'UCAW6jPZjjAizgvH5swBIDHQ', # MIPPCI
    'UCZSdNK_ZmMQcLTz-obKr-Dw', # teleSUR
    'UCCc2H9_eNnU7ucq2n7Sh3Rg', # La Iguana TV
    'UC_8sCVycu3FXidPNoZwOHqA', # Venezolana de Televisión
    'UCVyBnigIro9Dx2nqjPmSaoQ', # Cinemateca Nacional de Venezuela
    'UCtx06IhvaP3T0jbgGRN2n0Q'  # jesus r@jesusr7204
]

# ---------------------------------------------------------
# 2. Autenticación y Notificaciones
# ---------------------------------------------------------
def obtener_credenciales():
    token_env = os.environ.get('GOOGLE_TOKEN_JSON')
    if token_env:
        info_token = json.loads(token_env)
        return Credentials.from_authorized_user_info(info_token, SCOPES)
    
    if os.path.exists('token.json'):
        return Credentials.from_authorized_user_file('token.json', SCOPES)
    
    raise FileNotFoundError("No se encontraron credenciales en GOOGLE_TOKEN_JSON ni en token.json")

def enviar_notificaciones_telegram(mensaje):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chats_destino = ["5164937007", "-1002636268384"] # Chat personal y Grupo ComunaTv
    
    if not token:
        print("Telegram no configurado.")
        return
    
    for chat_id in chats_destino:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id, 
            'text': mensaje, 
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                print(f"✅ Notificación enviada a Telegram (ID: {chat_id}).")
        except Exception as e:
            print(f"❌ Error en Telegram para ID {chat_id}: {e}")

def enviar_whatsapp_twilio(mensaje):
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    from_whatsapp = os.environ.get('TWILIO_WHATSAPP_FROM')
    to_whatsapp = os.environ.get('WHATSAPP_TO_GROUP')

    if not all([account_sid, auth_token, from_whatsapp, to_whatsapp]):
        print("Twilio/WhatsApp no configurado. Saltando.")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    auth_str = f"{account_sid}:{auth_token}"
    encoded_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
    
    data = urllib.parse.urlencode({
        'From': from_whatsapp,
        'To': to_whatsapp,
        'Body': mensaje
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Authorization', f'Basic {encoded_auth}')
        with urllib.request.urlopen(req) as response:
            print("✅ Mensaje enviado a WhatsApp con éxito.")
    except Exception as e:
        print(f"❌ Error al enviar WhatsApp: {e}")

def actualizar_reproductor_en_blogger(blogger, blog_id, nuevo_playlist_id):
    try:
        print("Buscando la entrada del reproductor inteligente en Blogger...")
        posts = blogger.posts().list(blogId=blog_id, q="playlistSemanalID").execute()
        
        if 'items' in posts and len(posts['items']) > 0:
            post = posts['items'][0]
            post_id = post['id']
            contenido_actual = post['content']
            
            nuevo_contenido = re.sub(
                r'(playlistSemanalID\s*:\s*["\'])([^"\']+)(["\'])',
                r'\1' + nuevo_playlist_id + r'\3',
                contenido_actual
            )
            
            if nuevo_contenido != contenido_actual:
                blogger.posts().patch(
                    blogId=blog_id,
                    postId=post_id,
                    body={'content': nuevo_contenido}
                ).execute()
                print(f"✅ Reproductor inteligente actualizado en Blogger con la playlist: {nuevo_playlist_id}")
            else:
                print("ℹ️ El reproductor ya tenía asignado este ID de playlist.")
        else:
            print("⚠️ No se encontró la entrada con 'playlistSemanalID' en Blogger. El resumen semanal se publicó normalmente.")
    except Exception as e:
        print(f"❌ Error al intentar actualizar el reproductor en Blogger: {e}")

# ---------------------------------------------------------
# 3. Función Principal
# ---------------------------------------------------------
def main():
    creds = obtener_credenciales()
    youtube = build('youtube', 'v3', credentials=creds)
    blogger = build('blogger', 'v3', credentials=creds)

    try:
        user_blogs = blogger.blogs().listByUser(userId='self').execute()
        if 'items' in user_blogs and len(user_blogs['items']) > 0:
            blog_id = user_blogs['items'][0]['id']
        else:
            blog_id = BLOG_ID_CONFIGURADO
    except Exception as e:
        print(f"Aviso al listar blogs: {e}")
        blog_id = BLOG_ID_CONFIGURADO

    fecha_hoy = datetime.date.today()
    hace_siete_dias = fecha_hoy - datetime.timedelta(days=7)
    publicado_despues = hace_siete_dias.strftime('%Y-%m-%dT00:00:00Z')

    videos_recolectados = []
    print("Iniciando recolección de videos...")

    # A. Recolectar con filtro estricto para Radio Al Son Del 23
    try:
        res_son = youtube.search().list(
            part='snippet',
            channelId=CANAL_SON_DEL_23,
            publishedAfter=publicado_despues,
            type='video',
            maxResults=30
        ).execute()

        for item in res_son.get('items', []):
            titulo_original = item['snippet']['title']
            titulo_lower = titulo_original.lower()
            if any(prog in titulo_lower for prog in PROGRAMAS_SON_DEL_23):
                vid = item['id']['videoId']
                if not any(v['id'] == vid for v in videos_recolectados):
                    videos_recolectados.append({'title': titulo_original, 'id': vid})
    except HttpError as err:
        print(f"Error al consultar Radio Al Son Del 23: {err}")

    # B. Recolectar canales generales
    for canal_id in CANALES_GENERALES:
        try:
            res = youtube.search().list(
                part='snippet',
                channelId=canal_id,
                publishedAfter=publicado_despues,
                type='video',
                maxResults=10
            ).execute()

            for item in res.get('items', []):
                titulo_original = item['snippet']['title']
                vid = item['id']['videoId']
                if not any(v['id'] == vid for v in videos_recolectados):
                    videos_recolectados.append({'title': titulo_original, 'id': vid})
            time.sleep(0.5)
        except HttpError as err:
            print(f"Error al consultar el canal {canal_id}: {err}")

    if not videos_recolectados:
        print("No se encontraron videos nuevos en los canales durante los últimos 7 días.")
        return

    print(f"Total de videos únicos recolectados: {len(videos_recolectados)}")

    # ---------------------------------------------------------
    # 4. Crear Playlist en YouTube
    # ---------------------------------------------------------
    nombre_playlist = f"Resumen Comunal Semanal - {fecha_hoy.strftime('%d/%m/%Y')}"
    
    playlist = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': nombre_playlist,
                'description': 'Compilación automatizada de la programación multiplataforma comunitaria.'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }
    ).execute()

    playlist_id = playlist['id']
    print(f"Playlist creada con éxito. ID: {playlist_id}")

    # Sincronización automática con el reproductor del blog
    actualizar_reproductor_en_blogger(blogger, blog_id, playlist_id)

    for video_item in videos_recolectados:
        video_id = video_item['id']
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

    # ---------------------------------------------------------
    # 5. Publicar en Blogger
    # ---------------------------------------------------------
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

    url_blog_post = post_creado.get('url')
    print(f"Publicación creada con éxito en Blogger. URL: {url_blog_post}")

    # ---------------------------------------------------------
    # 6. Enviar Alertas (Telegram y WhatsApp con detalle de programas)
    # ---------------------------------------------------------
    titulos_muestra = "\n".join([f"• {v['title']}" for v in videos_recolectados[:5]])

    mensaje_difusion = (
        f"📢 *NUEVA PROGRAMACIÓN MULTIPLATAFORMA* 📡\n"
        f"📅 Fecha: `{fecha_hoy.strftime('%d/%m/%Y')}`\n\n"
        f"Se han recopilado *{len(videos_recolectados)}* contenidos comunitarios. Algunos destacados:\n\n"
        f"{titulos_muestra}\n\n"
        f"🔗 *Ver la parrilla completa en el blog:* {url_blog_post}"
    )

    enviar_notificaciones_telegram(mensaje_difusion)
    enviar_whatsapp_twilio(mensaje_difusion)

if __name__ == '__main__':
    main()
