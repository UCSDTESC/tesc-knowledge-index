param(
    [Parameter(Mandatory=$true)]
    [string]$Topic,

    [int]$Limit = 75,

    [int]$ExtractLimit = 50
)

$safeName = $Topic.ToLower().Replace(" ", "_").Replace("/", "_").Replace("\", "_")

Write-Host ""
Write-Host "=== Local search before live enrichment: $Topic ==="
tesc-drive search "$Topic" --limit $Limit

Write-Host ""
Write-Host "=== Live Drive search via rohan: $Topic ==="
tesc-drive drive-search "$Topic" --account rohan --links --limit $Limit

Write-Host ""
Write-Host "=== Live Drive search via contact: $Topic ==="
tesc-drive drive-search "$Topic" --account contact --links --limit $Limit

Write-Host ""
Write-Host "=== Extracting text for topic files via contact ==="
tesc-drive extract --account contact --query "$Topic" --limit $ExtractLimit

Write-Host ""
Write-Host "=== Local search after live enrichment + extraction: $Topic ==="
tesc-drive search "$Topic" --limit $Limit

Write-Host ""
Write-Host "=== Exporting links ==="
tesc-drive export-links "$Topic" --out "exports/${safeName}_links.md" --limit $Limit

Write-Host ""
Write-Host "=== Creating advisor report ==="
tesc-drive report "$Topic" --out "exports/${safeName}_report.md" --limit $Limit

Write-Host ""
Write-Host "=== Creating packet ==="
tesc-drive packet "$Topic" --out "exports/${safeName}_packet" --limit $Limit