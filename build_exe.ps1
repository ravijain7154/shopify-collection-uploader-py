$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconsole --onefile --name ShopifyCollectionUploader upload_collections_gui.py

Write-Host ""
Write-Host "Build complete."
Write-Host "EXE location: .\\dist\\ShopifyCollectionUploader.exe"
