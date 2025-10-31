Set-Location C:\JarvisBridge
git add -A | Out-Null
$changes = git status --porcelain
if ($changes) {
    $ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    git commit -m "AutoSnapshot - $ts" | Out-Null
    git push origin main | Out-Null
}
