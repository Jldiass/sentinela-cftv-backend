param([int]$Count = 1, [string]$HostName = "localhost")
if ($Count -lt 1 -or $Count -gt 8) { throw "Count deve estar entre 1 e 8" }
$cameras = Invoke-RestMethod "http://$HostName`:8000/api/v1/cameras"
if ($cameras.Count -lt $Count) { throw "Cadastre pelo menos $Count câmeras em http://$HostName`:8000" }
for ($i = 0; $i -lt $Count; $i++) {
  $url = $cameras[$i].rtmp_url
  $toneFrequency = ($i + 1) * 220
  Start-Process ffmpeg -WindowStyle Hidden -ArgumentList @('-re','-f','lavfi','-i',"testsrc2=size=1280x720:rate=25",'-f','lavfi','-i',"sine=frequency=$toneFrequency`:sample_rate=48000",'-c:v','libx264','-preset','veryfast','-tune','zerolatency','-g','50','-c:a','aac','-f','flv',$url)
  Write-Host "Stream $($i+1) -> $url"
}
