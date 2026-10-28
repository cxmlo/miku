!macro preInit
  ExecWait 'taskkill /F /IM miku-core.exe /IM miku_ui.exe /IM "Miku Desktop.exe" /T'
!macroend

!macro customInstall
  CreateDirectory "$LOCALAPPDATA\Miku Desktop"
  Delete "$LOCALAPPDATA\Miku Desktop\miku-core.exe"
  IfFileExists "$INSTDIR\resources\binaries\miku-core\miku-core.exe" 0 +3
    CreateDirectory "$LOCALAPPDATA\Miku Desktop\miku-core"
    CopyFiles /SILENT "$INSTDIR\resources\binaries\miku-core\*.*" "$LOCALAPPDATA\Miku Desktop\miku-core"
  IfFileExists "$INSTDIR\binaries\miku-core\miku-core.exe" 0 +3
    CreateDirectory "$LOCALAPPDATA\Miku Desktop\miku-core"
    CopyFiles /SILENT "$INSTDIR\binaries\miku-core\*.*" "$LOCALAPPDATA\Miku Desktop\miku-core"
  IfFileExists "$INSTDIR\miku-core\miku-core.exe" 0 +3
    CreateDirectory "$LOCALAPPDATA\Miku Desktop\miku-core"
    CopyFiles /SILENT "$INSTDIR\miku-core\*.*" "$LOCALAPPDATA\Miku Desktop\miku-core"

  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone" "" "Enviar a Mi teléfono (Miku)"
  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone" "Icon" "$INSTDIR\Miku Desktop.exe,0"
  WriteRegStr HKCU "Software\Classes\*\shell\MikuSendToPhone\command" "" 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "$$p=$$args[0]; if ($$p) { try { Invoke-RestMethod -Uri \"http://127.0.0.1:8000/api/desktop/send_file_to_phone\" -Method Post -ContentType \"application/json\" -Body (@{path=$$p} | ConvertTo-Json) -TimeoutSec 5 } catch {} }" \"%1\"'

  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone" "" "Enviar a Mi teléfono (Miku)"
  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone" "Icon" "$INSTDIR\Miku Desktop.exe,0"
  WriteRegStr HKCU "Software\Classes\Directory\shell\MikuSendToPhone\command" "" 'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "$$p=$$args[0]; if ($$p) { try { Invoke-RestMethod -Uri \"http://127.0.0.1:8000/api/desktop/send_file_to_phone\" -Method Post -ContentType \"application/json\" -Body (@{path=$$p} | ConvertTo-Json) -TimeoutSec 5 } catch {} }" \"%1\"'
!macroend

!macro customUnInstall
  RMDir /r "$LOCALAPPDATA\Miku Desktop\miku-core"
  DeleteRegKey HKCU "Software\Classes\*\shell\MikuSendToPhone"
  DeleteRegKey HKCU "Software\Classes\Directory\shell\MikuSendToPhone"
!macroend
