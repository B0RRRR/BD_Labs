param([string]$in, [string]$pdf)
$ErrorActionPreference = "Stop"
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($in, $false, $false)
  foreach ($i in -20, -21) {
    $s = $d.Styles.Item($i)
    $s.Font.Name = "Times New Roman"; $s.Font.Size = 14; $s.Font.Bold = $false
    $s.ParagraphFormat.SpaceBefore = 0; $s.ParagraphFormat.SpaceAfter = 0
    $s.ParagraphFormat.LineSpacingRule = 1
  }
  $d.Styles.Item(-20).ParagraphFormat.LeftIndent = 0
  $d.Styles.Item(-21).ParagraphFormat.LeftIndent = 14
  $d.TablesOfContents.Item(1).Update()
  $d.Repaginate()
  $d.TablesOfContents.Item(1).Update()
  $d.Save()
  $d.ExportAsFixedFormat($pdf, 17)
  $pages = $d.ComputeStatistics(2)
  Write-Output "PAGES=$pages"
  $d.Close($false)
} finally { $w.Quit() }
