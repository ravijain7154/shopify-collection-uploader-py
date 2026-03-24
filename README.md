# Shopify Smart Collection Uploader (Python + Desktop)

Upload smart collections to a Shopify store from a CSV column that contains JSON payloads.

## Requirements
- Python 3.10+ recommended
- Windows PowerShell (for build script)

## Local Setup
1. Install dependencies:
```powershell
python -m pip install -r requirements.txt
```

2. Ensure your CSV file is in the project root:
- File: `VariableFromFile.csv`
- Column: `VariableFromFile`
- Each cell must contain a JSON object with top-level key `smart_collection`.

Example cell value:
```json
{"smart_collection": {"title": "Summer Picks", "rules": [], "published": true}}
```

## Run (CLI)
```powershell
python upload_collections.py
```

You will be prompted for:
- Shopify store URL/domain (e.g. `myshop.myshopify.com`)
- API key (X-Shopify-Access-Token)

## Run (Desktop App)
```powershell
python upload_collections_gui.py
```

## Build Desktop EXE
```powershell
.\build_exe.ps1
```

The executable will be created here:
- `dist\ShopifyCollectionUploader.exe`

## Notes
- API version is set to `2021-04` in `upload_collections.py`.
- The request header used is `X-Shopify-Access-Token`.
