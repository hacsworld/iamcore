Write-Host "==> Installing HACS Local Core deps..."
Set-Location core
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
Start-Process -FilePath .\venv\Scripts\python.exe -ArgumentList "app.py" -WindowStyle Hidden
Set-Location ..

Write-Host "==> Building agent..."
Set-Location agent
go mod tidy
go build -o hacs-agent.exe main.go
Write-Host "==> Agent built at agent\hacs-agent.exe"
Set-Location ..
Write-Host "==> Done. Start agent with: .\agent\hacs-agent.exe"
