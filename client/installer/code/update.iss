
function ExisteInstalacion(): Boolean;
var
  RutaPrevia: String;
begin
  Result := False;

  // Buscar en el registro si ya se había instalado antes (Forma más segura)
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{4A45C420-3DB4-4DF8-8524-DDEC42EC1468}_is1', 'InstallLocation', RutaPrevia) or
     RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{4A45C420-3DB4-4DF8-8524-DDEC42EC1468}_is1', 'InstallLocation', RutaPrevia) then
  begin
    if (RutaPrevia <> '') and DirExists(RutaPrevia) and FileExists(RutaPrevia + '\cliente.exe') then
    begin
      Result := True;
      Exit;
    end;
  end;

  // Fallback: Si no está en el registro, validamos la ruta por defecto usando {autopf}  
  RutaPrevia := ExpandConstant('{autopf}\Control Cliente');
  
  Result := DirExists(RutaPrevia) and FileExists(RutaPrevia + '\cliente.exe');
end;