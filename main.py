from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from lxml import etree

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/validate")
async def validate(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="Only .xml files are allowed")

    try:
        xml_bytes = await file.read()
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_bytes, parser)
    except etree.XMLSyntaxError as e:
        return {"status": "failed", "error": "XML is not well-formed", "details": str(e)}

    errors = []

    authors = root.xpath("//contrib[@contrib-type='author']")
    for author in authors:
        orcid = author.xpath(".//contrib-id[@contrib-id-type='orcid']")
        if not orcid:
            errors.append("Author missing ORCID.")

    if not root.xpath("//funding-group"):
        errors.append("Missing <funding-group> metadata.")

    if not root.xpath("//abstract"):
        errors.append("Manuscript is missing an <abstract>.")

    if not root.xpath("//ref-list/ref"):
        errors.append("No structured citations found in <ref-list>.")

    if errors:
        return {"status": "invalid", "errors": errors}

    return {"status": "success", "message": "JATS XML is perfectly formatted and compliant."}
