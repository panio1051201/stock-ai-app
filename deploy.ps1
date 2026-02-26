# 自動化部署腳本 (stock-ai-app)

$TargetEmail = "raycheng680120@gmail.com"

Write-Host "🚀 開始自動化部署程序..." -ForegroundColor Cyan

# 1. 檢查 Git 初始化
if (!(Test-Path .git)) {
    Write-Host "初始化 Git 倉庫..."
    git init
}

# 2. 設定使用者資訊 (如果沒設定)
git config user.email $TargetEmail
git config user.name "Ray Cheng"

# 3. 檢查遠端位址
$Remote = git remote get-url origin 2>$null
if (!$Remote) {
    Write-Host "🛑 尚未設定遠端倉庫 (origin)。" -ForegroundColor Yellow
    Write-Host "請手動執行: git remote add origin https://github.com/raycheng680120/[YOUR_REPO_NAME].git"
    # 這裡如果不確定 Repo 名稱，先暫停或是提示用戶
}

# 4. 提交變更
Write-Host "提交本地變更..."
git add .
git commit -m "Auto-deploy: Update client-side migration and render config [$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')]"

# 5. 推送到 GitHub
Write-Host "推送到 GitHub..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 部署成功！Render 將會自動感應變更並更新專案。" -ForegroundColor Green
} else {
    Write-Host "❌ 部署失敗。請檢查 GitHub 登入狀態或遠端倉庫設定。" -ForegroundColor Red
}
