!macro preInit
  ExecWait 'taskkill /F /IM miku-core.exe /IM miku_ui.exe /T'
!macroend

!macro customInstall
  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone" "" "Enviar a Mi teléfono (Miku)"
  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone" "Icon" "$INSTDIR\Miku Desktop.exe,0"
  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone\command" "" 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "$$p=$$args[0]; if ($$p) { try { Invoke-RestMethod -Uri \"http://127.0.0.1:8000/api/desktop/send_file_to_phone\" -Method Post -ContentType \"application/json\" -Body (@{path=$$p} | ConvertTo-Json) -TimeoutSec 5 } catch {} }" \"%1\"'

  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone" "" "Enviar a Mi teléfono (Miku)"
  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone" "Icon" "$INSTDIR\Miku Desktop.exe,0"
  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone\command" "" 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "$$p=$$args[0]; if ($$p) { try { Invoke-RestMethod -Uri \"http://127.0.0.1:8000/api/desktop/send_file_to_phone\" -Method Post -ContentType \"application/json\" -Body (@{path=$$p} | ConvertTo-Json) -TimeoutSec 5 } catch {} }" \"%1\"'
!macroend

!macro customUnInstall
  DeleteRegKey HKCU "Software\Classes\*\shell\MikuSendToPhone"
  DeleteRegKey HKCU "Software\Classes\Directory\shell\MikuSendToPhone"
!macroend
