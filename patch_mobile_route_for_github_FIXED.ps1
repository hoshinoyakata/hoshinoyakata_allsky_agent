# Ver.5.5 Mobile View - GitHub Desktop用 PowerShellパッチ 修正版
$ErrorActionPreference = "Stop"

$base = Get-Location
$app = Join-Path $base "web\app.py"
$templates = Join-Path $base "web\templates"
$mobileSrc = Join-Path $base "mobile.html"
$mobileDst = Join-Path $templates "mobile.html"

if (!(Test-Path $app)) {
  Write-Host "ERROR: web\app.py が見つかりません。hoshinoyakata_allsky_agent の一番上のフォルダで実行してください。" -ForegroundColor Red
  exit 1
}

if (!(Test-Path $templates)) {
  New-Item -ItemType Directory -Force -Path $templates | Out-Null
}

if (Test-Path $mobileSrc) {
  Copy-Item -Force $mobileSrc $mobileDst
  Write-Host "OK: mobile.html を web\templates にコピーしました。"
} elseif (Test-Path $mobileDst) {
  Write-Host "OK: web\templates\mobile.html は既にあります。"
} else {
  Write-Host "ERROR: mobile.html が見つかりません。mobile.html をこのフォルダ直下に置いてください。" -ForegroundColor Red
  exit 1
}

$text = Get-Content $app -Raw -Encoding UTF8

if ($text.Contains("@app.route('/mobile')") -or $text.Contains('@app.route("/mobile")')) {
  Write-Host "OK: /mobile は既に app.py に入っています。"
} else {
  $backup = "$app.backup_mobile_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
  Copy-Item -Force $app $backup
  Write-Host "backup: $backup"

  if ($text -notlike "*render_template*") {
    $text = $text -replace 'from flask import ([^\r\n]+)', 'from flask import $1, render_template'
  }

  $route = @'

@app.route('/mobile')
def mobile_view():
    return render_template('mobile.html')

'@

  $marker = "`n@app.route('/api/status')"
  if ($text.Contains($marker)) {
    $text = $text.Replace($marker, $route + $marker)
  } elseif ($text.Contains("`nif __name__")) {
    $text = $text.Replace("`nif __name__", $route + "`nif __name__")
  } else {
    $text = $text.TrimEnd() + $route
  }

  Set-Content -Path $app -Value $text -Encoding UTF8
  Write-Host "OK: web\app.py に /mobile を追加しました。"
}

Write-Host ""
Write-Host "完了。GitHub Desktopに戻って Commit to main → Push origin してください。" -ForegroundColor Green
Write-Host "Summary: Ver 5.5 mobile view"
