import json
import datetime
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/blogger'
]

def obtener_autenticacion():
    creds = None
    
    # Si estamos en GitHub Actions, leemos el token desde una variable de entorno secreta
    if os.environ.get('GOOGLE_TOKEN_JSON'):
        token_info = json.loads(os.environ['GOOGLE_TOKEN_JSON'])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Esto solo se ejecuta si estás en tu PC de forma local por primera vez
            if os.path.exists('client_secret.json'):
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            else:
                raise Exception("No se encontraron credenciales válidas ni client_secret.json.")
    return creds

def obtener_videos_recientes(youtube, canales_ids):
    videos_a_incluir = []
    hace_una_semana = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat().replace('+00:00', 'Z')
    
    # ID de Al Son Del 23 y sus programas específicos
    ID_AL_SON_DEL_23 = 'UCCoHvADohOJ0sWevJBZ9h9A'
    PROGRAMAS_AL_SON_DEL_23 = [
        "con chavez siempre",
        "la hora en que habla el pueblo",
        "latinoamerica en vivo",
        "el noticiero"
    ]

    for channel_id in canales_ids:
        try:
            res_canal = youtube.channels().list(part='contentDetails', id=channel_id).execute()
            if 'items' not in res_canal or not res_canal['items']:
                continue
            uploads_playlist_id = res_canal['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            res_playlist = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=10
            ).execute()
            
            for item in res_playlist['items']:
                published_at = item['snippet']['publishedAt']
                titulo = item['snippet']['title'].lower()
                
                if published_at >= hace_una_semana:
                    # Filtro especial para Radio Al Son Del 23
                    if channel_id == ID_AL_SON_DEL_23:
                        if any(prog in titulo for prog in PROGRAMAS_AL_SON_DEL_23):
                            videos_a_incluir.append(item['snippet']['resourceId']['videoId'])
                    else:
                        videos_a_incluir.append(item['snippet']['resourceId']['videoId'])
        except Exception as e:
            print(f"Aviso: Omitiendo canal {channel_id} temporalmente.")
            
    return videos_a_incluir

def generar_codigo_reproductor_completo(playlist_id):
    """Genera el código HTML + JavaScript dinámico con la nueva playlist"""
    return f"""<!-- Contenedor Responsivo del Reproductor de Video -->
<div id="contenedor-reproductor-inteligente" style="position: relative; width: 100%; padding-bottom: 56.25%; height: 0; background: #000; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
    <iframe id="reproductor-web" 
            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
            src="" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
    </iframe>
</div>

<!-- Barra de Estado en Vivo -->
<div id="estado-transmision" style="font-family: Arial, sans-serif; font-size: 13px; color: #333; background: #f0f0f0; padding: 8px 12px; margin-top: 6px; text-align: center; font-weight: bold; border-radius: 4px;">
    Cargando señal...
</div>

<script>
// ======================================================
// CONFIGURACIÓN DE TUS CANALES Y TRANSMISIONES
// ======================================================
const CONFIG = {{
    playlistSemanalID: "{playlist_id}", 
    vtvLiveID: "A3cJBLyIGN0",          
    telesurLiveID: "live_stream?channel=UCZSdNK_ZmMQcLTz-obKr-Dw", 
    miEnVivoID: "EFN5c95eHqE", 
    transmisionEnVivoPropia: false
}};

function gestionarReproductor() {{
    const iframe = document.getElementById('reproductor-web');
    const estadoTexto = document.getElementById('estado-transmision');
    
    const ahora = new Date();
    const diaSemana = ahora.getDay();
    const hora = ahora.getHours();
    const minutos = ahora.getMinutes();
    const minutosTotales = hora * 60 + minutos;

    const min1700 = 17 * 60;
    const min2000 = 20 * 60;
    const min2359 = 23 * 60 + 59;

    let nuevaURL = "";
    let mensajeEstado = "";

    const esFinDeSemana = (diaSemana === 0 || diaSemana === 6);

    if (CONFIG.transmisionEnVivoPropia) {{
        nuevaURL = `https://www.youtube.com/embed/${{CONFIG.miEnVivoID}}?autoplay=1`;
        mensajeEstado = "🔴 TRANSMISIÓN EN VIVO ESPECIAL";
    }} 
    else if (esFinDeSemana) {{
        if (minutosTotales >= min1700 && minutosTotales < min2000) {{
            nuevaURL = `https://www.youtube.com/embed/${{CONFIG.vtvLiveID}}?autoplay=1`;
            mensajeEstado = "📡 VTV en Directo";
        }} 
        else if (minutosTotales >= min2000 && minutosTotales <= min2359) {{
            nuevaURL = `https://www.youtube.com/embed/${{CONFIG.telesurLiveID}}&autoplay=1`;
            mensajeEstado = "🌍 TeleSUR en Directo";
        }} 
        else {{
            nuevaURL = `https://www.youtube.com/embed/videoseries?list=${{CONFIG.playlistSemanalID}}&autoplay=1&loop=1`;
            mensajeEstado = "🎵 Programación Regular / Lista Dominical";
        }}
    }} 
    else {{
        if (minutosTotales >= min1700 && minutosTotales <= min2359) {{
            nuevaURL = `https://www.youtube.com/embed/${{CONFIG.vtvLiveID}}?autoplay=1`;
            mensajeEstado = "📡 VTV en Directo";
        }} 
        else {{
            nuevaURL = `https://www.youtube.com/embed/videoseries?list=${{CONFIG.playlistSemanalID}}&autoplay=1&loop=1`;
            mensajeEstado = "🎵 Programación Regular / Lista Semanal";
        }}
    }}

    if (iframe.src !== nuevaURL) {{
        iframe.src = nuevaURL;
        estadoTexto.innerText = mensajeEstado;
    }}
}}

window.onload = function() {{
    gestionarReproductor();
    setInterval(gestionarReproductor, 30000);
}};
</script>"""

def crear_playlist_y_publicar(blog_id, canales_ids):
    creds = obtener_autenticacion()
    youtube = build('youtube', 'v3', credentials=creds)
    blogger = build('blogger', 'v3', credentials=creds)
    
    print("Buscando videos recientes en los canales...")
    videos_ids = obtener_videos_recientes(youtube, canales_ids)
    
    if not videos_ids:
        print("No hay videos nuevos de estos canales en los últimos 7 días.")
        return

    titulo_playlist = f"Resumen Semanal - {datetime.date.today().strftime('%d/%m/%Y')}"
    body_playlist = {
        'snippet': {
            'title': titulo_playlist,
            'description': 'Lista de reproducción generada automáticamente con los contenidos de la semana.'
        },
        'status': {'privacyStatus': 'public'}
    }
    playlist_res = youtube.playlists().insert(part='snippet,status', body=body_playlist).execute()
    playlist_id = playlist_res['id']
    print(f"Playlist creada en YouTube con ID: {playlist_id}")
    
    for vid_id in videos_ids:
        try:
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {'kind': 'youtube#video', 'videoId': vid_id}
                    }
                }
            ).execute()
        except Exception:
            pass

    codigo_reproductor_html = generar_codigo_reproductor_completo(playlist_id)

    # 1. Publicar en Blogger
    blog_post = {
        'title': f"Resumen Comunal Semanal - {datetime.date.today().strftime('%d/%m/%Y')}",
        'content': f"<p>Compartimos la programación y resumen audiovisual correspondiente a esta semana:</p>{codigo_reproductor_html}"
    }
    blogger.posts().insert(blogId=blog_id, body=blog_post).execute()
    print("✅ Entrada semanal publicada en Blogger.")

    # 2. Guardar el archivo HTML con la nueva playlist
    with open("reproductor_actualizado.html", "w", encoding="utf-8") as f:
        f.write(codigo_reproductor_html)
    print("✅ Código guardado en 'reproductor_actualizado.html'.")

if __name__ == '__main__':
    canales_a_monitorear = [
        'UCGfoI7v6hNipgiG8C_IJjfQ', # LA VOZ DE LA MUJER BOLIVARIANA
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
        'UCCoHvADohOJ0sWevJBZ9h9A', # Radio Al Son Del 23 - 94.7 fm (Filtrado por programas)
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
    
    MI_BLOG_ID = '5984162053367331695'
    
    crear_playlist_y_publicar(MI_BLOG_ID, canales_a_monitorear)