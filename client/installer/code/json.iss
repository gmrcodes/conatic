
var
 ConfigFile: String; 

procedure CrearConfigJson();
var
  Contenido: String;
  StrOffline: String;
  RutaCarpeta: String;
begin
  // Apunta a la carpeta LOCALAPPDATA\ControlClienteApp
  RutaCarpeta := ExpandConstant('{localappdata}\ControlClienteApp');

  // Crea la carpeta si no existe
  if not DirExists(RutaCarpeta) then
    ForceDirectories(RutaCarpeta);

  ConfigFile := RutaCarpeta + '\config_cliente.json';

  // Si es actualización y el archivo existe, respetamos la configuración previa
  if (ModoInstalacion = miActualizar) and FileExists(ConfigFile) then
    Exit;
  
  // Si es reinstalación, eliminamos el archivo previo
  if (ModoInstalacion = miReinstalar) and FileExists(ConfigFile) then
  begin    
    DeleteFile(ConfigFile);
  end;

  // Mapear el estado del CheckBox al formato correcto de JSON (minúsculas)
  if chkOffline.Checked then
    StrOffline := 'true'
  else
    StrOffline := 'false';

  Contenido :=
    '{' + #13#10 +
    '    "id_cliente": "' + Trim(edtTerminal.Text) + '",' + #13#10 +
    '    "server_ip": "' + Trim(edtIP.Text) + '",' + #13#10 +
    '    "permitir_offline": ' + StrOffline + ',' + #13#10 +
    '    "tiempo_predeterminado_minutos": ' + Trim(edtTiempo.Text) + #13#10 +
    '}';

  SaveStringToFile(ConfigFile, Contenido, False);

end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    CrearConfigJson();   

    if not RepararScheduler() then
    begin
      MsgBox(
        'No fue posible registrar el inicio automático del cliente.',
        mbError,
        MB_OK);
    end;
  end;
end;