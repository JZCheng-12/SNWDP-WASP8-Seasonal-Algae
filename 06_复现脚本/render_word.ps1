$projectRoot = Split-Path -Parent $PSScriptRoot
$paramDocxName = '南水北调中线WASP8_季节率定与情景汇报.docx'
if ($args.Count -ge 1) { $paramDocxName = [string]$args[0] }
$ErrorActionPreference = 'Stop'
$docxPath = Join-Path (Join-Path $projectRoot '05_report') $paramDocxName
$qaDir = Join-Path $projectRoot '_qa_render'
New-Item -ItemType Directory -Force -Path $qaDir | Out-Null
$pdfPath = Join-Path $qaDir ([IO.Path]::GetFileNameWithoutExtension($paramDocxName) + '.pdf')

$wordApp = $null
$wordDoc = $null
try {
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordDoc = $wordApp.Documents.Open($docxPath, $false, $true)
    $wordDoc.ExportAsFixedFormat($pdfPath, 17)
    Write-Output $pdfPath
} finally {
    if ($null -ne $wordDoc) { $wordDoc.Close(0) }
    if ($null -ne $wordApp) { $wordApp.Quit() }
    if ($null -ne $wordDoc) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordDoc) }
    if ($null -ne $wordApp) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) }
}
