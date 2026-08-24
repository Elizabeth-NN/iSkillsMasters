# iSkillsMasters Global — CMS Full Product

This is a **standalone functional CMS-first website product** based on the current iSkillsMasters Global public structure and the supplied architectural blueprint. It is built so an authorised website administrator can manage routine content without editing source code.

## Included

- Public website
- Admin CMS
- SQLite content store
- Event management
- Competition category management
- Announcement publishing
- PDF/resource upload and removal
- Pictorial/gallery upload and removal
- Homepage settings
- Finale/event settings
- Contact/global settings
- Media storage
- Mobile responsive interface

## Run

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open:
- Public site: http://127.0.0.1:8000
- CMS: http://127.0.0.1:8000/admin

## Architecture

Browser → FastAPI → SQLite + media storage → Public/CMS UI

The public structure follows the supplied blueprint: Home, Categories, Downloads, Pictorials and Contact.

## Important scope

This is the functional product layer created before receiving the original repository. It is deliberately designed so that it can later be integrated into the original iSkillsMastersGlobal codebase rather than forcing a source-code rebuild.
