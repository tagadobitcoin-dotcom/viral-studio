import os, secrets, tempfile, subprocess, textwrap
from flask import Flask, request, Response, send_file, after_this_request
from PIL import Image, ImageDraw, ImageFont
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=65536
@app.before_request
def auth():
    if request.path=='/health': return
    p=os.getenv('STUDIO_PASSWORD')
    if not p: return 'Configurez STUDIO_PASSWORD dans Railway.',503
    a=request.authorization
    if not a or not secrets.compare_digest(a.username or '', 'studio') or not secrets.compare_digest(a.password or '',p):
        return Response('Connexion requise',401,{'WWW-Authenticate':'Basic realm="Viral Studio"'})
@app.get('/health')
def health(): return 'ok'
@app.get('/')
def index():
    return """<!doctype html><html lang=fr><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Viral Studio</title><style>body{background:#10131c;color:#edf1ff;font:16px system-ui;max-width:760px;margin:40px auto;padding:20px}textarea,input,button{box-sizing:border-box;width:100%;padding:14px;border-radius:12px;margin:8px 0;background:#202638;color:white;border:1px solid #424b65}button{background:#6455e7;font-weight:bold}small{color:#aab4cf}</style><h1>Viral Studio</h1><p>Studio de création • Version initiale</p><h2>Créer une vidéo originale</h2><form method=post action=/render><label>Titre</label><input name=title required maxlength=100><label>Script original (une scène par ligne, 1 à 12 scènes)</label><textarea name=script rows=10 required maxlength=2400></textarea><button>Générer le MP4 vertical</button></form><small>Rendu graphique original, narration synthétique française et texte à l'écran. Analyse automatique des liens et radar non disponibles dans cette version.</small></html>"""
@app.post('/render')
def render():
    title=request.form.get('title','').strip()[:100]
    lines=[x.strip() for x in request.form.get('script','').splitlines() if x.strip()]
    if not title or not 1<=len(lines)<=12 or sum(map(len,lines))>2400 or any(len(x)>300 for x in lines): return 'Script invalide : 1 à 12 lignes, 300 caractères maximum par ligne.',400
    import shutil
    d=tempfile.mkdtemp()
    @after_this_request
    def cleanup(response):
        if response.status_code!=200: shutil.rmtree(d,ignore_errors=True)
        return response
    try:
        font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        for i,line in enumerate(lines):
            im=Image.new('RGB',(720,1280),(16,20,34)); draw=ImageDraw.Draw(im)
            draw.rectangle((45,65,675,77),fill=(112,98,255))
            draw.text((45,110),'VIRAL STUDIO',font=ImageFont.truetype(font,28),fill=(165,155,255))
            draw.multiline_text((45,210),textwrap.fill(title,22),font=ImageFont.truetype(font,42),fill='white',spacing=12)
            draw.multiline_text((45,480),textwrap.fill(line,25),font=ImageFont.truetype(font,40),fill='white',spacing=14)
            draw.text((45,1160),f'{i+1:02d} / {len(lines):02d}',font=ImageFont.truetype(font,28),fill=(165,155,255))
            im.save(f'{d}/{i}.png')
            subprocess.run(['espeak-ng','-v','fr','-s','155','-w',f'{d}/{i}.wav','--',line],check=True,timeout=30)
            subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-i',f'{d}/{i}.png','-i',f'{d}/{i}.wav','-c:v','libx264','-preset','ultrafast','-threads','2','-pix_fmt','yuv420p','-r','25','-c:a','aac','-shortest',f'{d}/{i}.mp4'],check=True,timeout=90)
        with open(f'{d}/list.txt','w') as f:
            for i in range(len(lines)): f.write(f"file '{i}.mp4'\n")
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',f'{d}/list.txt','-c','copy',f'{d}/video.mp4'],check=True,timeout=60)
        response=send_file(f'{d}/video.mp4',as_attachment=True,download_name='viral-studio.mp4')
        response.call_on_close(lambda: shutil.rmtree(d,ignore_errors=True))
        return response
    except Exception:
        shutil.rmtree(d,ignore_errors=True)
        return 'Erreur de rendu.',500
