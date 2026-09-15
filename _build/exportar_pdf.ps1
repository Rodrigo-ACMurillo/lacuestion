# Abre el .docx con Word, cuenta páginas y exporta una vista previa en PDF.
param(
  [string]$Docx = "L:\periodico\LA_CUESTION_periodico.docx",
  [string]$Pdf  = "L:\periodico\_build\tmp\vista_previa.pdf"
)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($Docx, $false, $true)
  $d.Repaginate()
  Write-Output ("Paginas segun Word: " + $d.ComputeStatistics(2))
  Write-Output ("Secciones: " + $d.Sections.Count)
  $d.SaveAs([ref]$Pdf, [ref]17)
  Write-Output ("PDF: " + $Pdf)
  $d.Close([ref]0)
} catch {
  Write-Output ("ERROR: " + $_.Exception.Message)
} finally {
  $w.Quit()
}
