
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3, json, uuid, shutil

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "iskillsmasters.db"
MEDIA = BASE / "data" / "media"
MEDIA.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="iSkillsMasters Global CMS")
app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")
app.mount("/media", StaticFiles(directory=MEDIA), name="media")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT, country TEXT, event_date TEXT, deadline TEXT,
        description TEXT, accent TEXT, visible INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track TEXT, tier TEXT, ages TEXT, title TEXT, description TEXT, visible INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, filename TEXT, description TEXT, visible INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        album TEXT, filename TEXT, caption TEXT, visible INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, body TEXT, published INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS admins (
        email TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        active INTEGER DEFAULT 1
    );
    """)
    seed(cur)
    con.commit()
    con.close()

def seed(cur):
    defaults = {
        "site_name":"iSkillsMasters Global",
        "tagline":"Build locally. Compete regionally.",
        "hero_badge":"AFRICA'S BIGGEST CODING AND ROBOTICS COMPETITION 4 KIDS",
        "hero_title":"Code Festival",
        "hero_theme":"The Green Earth",
        "hero_description":"Empowering the next generation of innovators through coding and robotics across Africa.",
        "hero_partner":"Code Festival is a project of iSkillsMasters Global in partnership with Strathmore University, Lab Africa and Kampala International University.",
        "hero_cta":"Register Now",
        "hero_cta2":"Explore Categories",
        "finale_title":"East Africa Code Festival",
        "finale_subtitle":"The ultimate showdown of innovation and creativity in Mombasa, Kenya.",
        "finale_date":"August 13–15, 2026",
        "finale_venue":"Loha­na Hall, Mombasa",
        "contact_email":"info@iskillsmastersglobal.org",
        "contact_phone":"+254 704 010502",
        "contact_location":"Nairobi, Kenya"
    }
    for k,v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))

    if cur.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO events(city,country,event_date,deadline,description,accent) VALUES(?,?,?,?,?,?)",
            [
                ("Nairobi","Kenya","May 30, 2026","May 9, 2026","Silicon Savannah hosts the Kenyan nationals.","orange"),
                ("Kampala","Uganda","June 06, 2026","May 16, 2026","Kick off the championship in the Pearl of Africa.","blue")
            ]
        )

    if cur.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        rows=[]
        for track in ["Coding Challenge","Robotics Challenge"]:
            tiers=[
                ("Tier 1: Beginners","Under 10","Foundations","Learn core problem solving."),
                ("Tier 2: Explorers","10–14","Creative Systems","Build logical programs and automation."),
                ("Tier 3: Innovators","15–18","Advanced Build","Create real web, AI and embedded projects."),
                ("Tier 4: Visionaries","19–21","Advanced Systems","Develop larger-scale systems and intelligent products.")
            ]
            for tier,ages,title,desc in tiers:
                rows.append((track,tier,ages,title,desc))
        cur.executemany("INSERT INTO categories(track,tier,ages,title,description) VALUES(?,?,?,?,?)",rows)

    if cur.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
        cur.execute("INSERT INTO admins(email,name) VALUES(?,?)",("admin@iskillsmastersglobal.org","Website Administrator"))

def all_settings():
    con=db()
    rows=con.execute("SELECT key,value FROM settings").fetchall()
    con.close()
    return {r["key"]:r["value"] for r in rows}

def save_setting(key,value):
    con=db(); con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,value)); con.commit(); con.close()

def public_payload():
    con=db()
    events=[dict(x) for x in con.execute("SELECT * FROM events WHERE visible=1 ORDER BY id").fetchall()]
    categories=[dict(x) for x in con.execute("SELECT * FROM categories WHERE visible=1 ORDER BY track,id").fetchall()]
    resources=[dict(x) for x in con.execute("SELECT * FROM resources WHERE visible=1 ORDER BY id DESC").fetchall()]
    gallery=[dict(x) for x in con.execute("SELECT * FROM gallery WHERE visible=1 ORDER BY id DESC").fetchall()]
    announcements=[dict(x) for x in con.execute("SELECT * FROM announcements WHERE published=1 ORDER BY id DESC").fetchall()]
    con.close()
    return {"settings":all_settings(),"events":events,"categories":categories,"resources":resources,"gallery":gallery,"announcements":announcements}

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE/"static"/"index.html").read_text(encoding="utf-8")

@app.get("/admin", response_class=HTMLResponse)
def admin():
    return (BASE/"static"/"admin.html").read_text(encoding="utf-8")

@app.get("/api/public")
def api_public():
    return public_payload()

@app.post("/api/settings")
def api_settings(payload: dict):
    for k,v in payload.items():
        save_setting(k,str(v))
    return {"ok":True,"settings":all_settings()}

@app.post("/api/events")
def api_event(payload: dict):
    con=db()
    con.execute(
        "INSERT INTO events(city,country,event_date,deadline,description,accent,visible) VALUES(?,?,?,?,?,?,?)",
        (payload.get("city",""),payload.get("country",""),payload.get("event_date",""),payload.get("deadline",""),payload.get("description",""),payload.get("accent","blue"),1)
    )
    con.commit(); con.close(); return {"ok":True}

@app.put("/api/events/{event_id}")
def api_event_update(event_id:int,payload:dict):
    con=db(); con.execute(
        "UPDATE events SET city=?,country=?,event_date=?,deadline=?,description=?,accent=?,visible=? WHERE id=?",
        (payload.get("city"),payload.get("country"),payload.get("event_date"),payload.get("deadline"),payload.get("description"),payload.get("accent","blue"),1 if payload.get("visible",True) else 0,event_id)
    )
    con.commit(); con.close(); return {"ok":True}

@app.delete("/api/events/{event_id}")
def api_event_delete(event_id:int):
    con=db(); con.execute("DELETE FROM events WHERE id=?",(event_id,)); con.commit(); con.close(); return {"ok":True}

@app.post("/api/categories")
def api_category(payload:dict):
    con=db(); con.execute("INSERT INTO categories(track,tier,ages,title,description,visible) VALUES(?,?,?,?,?,1)",
        (payload.get("track"),payload.get("tier"),payload.get("ages"),payload.get("title"),payload.get("description")))
    con.commit(); con.close(); return {"ok":True}

@app.put("/api/categories/{item_id}")
def api_category_update(item_id:int,payload:dict):
    con=db(); con.execute("UPDATE categories SET track=?,tier=?,ages=?,title=?,description=?,visible=? WHERE id=?",
        (payload.get("track"),payload.get("tier"),payload.get("ages"),payload.get("title"),payload.get("description"),1 if payload.get("visible",True) else 0,item_id))
    con.commit(); con.close(); return {"ok":True}

@app.delete("/api/categories/{item_id}")
def api_category_delete(item_id:int):
    con=db(); con.execute("DELETE FROM categories WHERE id=?",(item_id,)); con.commit(); con.close(); return {"ok":True}

@app.post("/api/announcements")
def api_announcement(payload:dict):
    con=db(); con.execute("INSERT INTO announcements(title,body,published) VALUES(?,?,?)",(payload.get("title"),payload.get("body"),1 if payload.get("published",False) else 0))
    con.commit(); con.close(); return {"ok":True}

@app.delete("/api/announcements/{item_id}")
def api_announcement_delete(item_id:int):
    con=db(); con.execute("DELETE FROM announcements WHERE id=?",(item_id,)); con.commit(); con.close(); return {"ok":True}

@app.post("/api/upload/gallery")
async def upload_gallery(album:str=Form(...), caption:str=Form(""), file:UploadFile=File(...)):
    name=f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest=MEDIA/name
    with dest.open("wb") as f: shutil.copyfileobj(file.file,f)
    con=db(); con.execute("INSERT INTO gallery(album,filename,caption,visible) VALUES(?,?,?,1)",(album,name,caption)); con.commit(); con.close()
    return {"ok":True,"filename":name}

@app.delete("/api/gallery/{item_id}")
def api_gallery_delete(item_id:int):
    con=db(); row=con.execute("SELECT filename FROM gallery WHERE id=?",(item_id,)).fetchone()
    if row:
        try:(MEDIA/row["filename"]).unlink()
        except FileNotFoundError:pass
        con.execute("DELETE FROM gallery WHERE id=?",(item_id,)); con.commit()
    con.close(); return {"ok":True}

@app.post("/api/upload/resource")
async def upload_resource(title:str=Form(...), description:str=Form(""), file:UploadFile=File(...)):
    name=f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest=MEDIA/name
    with dest.open("wb") as f: shutil.copyfileobj(file.file,f)
    con=db(); con.execute("INSERT INTO resources(title,filename,description,visible) VALUES(?,?,?,1)",(title,name,description)); con.commit(); con.close()
    return {"ok":True,"filename":name}

@app.delete("/api/resources/{item_id}")
def api_resource_delete(item_id:int):
    con=db(); row=con.execute("SELECT filename FROM resources WHERE id=?",(item_id,)).fetchone()
    if row:
        try:(MEDIA/row["filename"]).unlink()
        except FileNotFoundError:pass
        con.execute("DELETE FROM resources WHERE id=?",(item_id,)); con.commit()
    con.close(); return {"ok":True}

@app.get("/api/health")
def health(): return {"ok":True,"service":"iSkillsMasters CMS"}

init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app",host="0.0.0.0",port=8000,reload=False)
