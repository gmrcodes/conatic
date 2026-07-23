function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // 1. Detener tarea programada antes de matar procesos
  EliminarScheduler();

  // 2. Matar procesos con /F (Forzado) y /T (Árbol de procesos)
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM launcher.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM cliente.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  // 3. Pausa de 1 segundo para dar tiempo a Windows de liberar los handles de archivos
  Sleep(1000);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigFile: String;
  CacheDB: String;  
begin
  // --- FASE 1: ANTES de empezar a borrar archivos ---
  if CurUninstallStep = usUninstall then
  begin    

    // Pregunta Conservar o eliminar configuración/base de datos
    ConfigFile := ExpandConstant('{localappdata}\ControlClienteApp\config_cliente.json');
    CacheDB := ExpandConstant('{localappdata}\ControlClienteApp\cache_cliente.db');

    if MsgBox('¿Desea eliminar por completo los archivos de configuración y la base de datos local?' + #13#10#13#10 +
              'Seleccione "Sí" para realizar una desinstalación 100% limpia.' + #13#10 +
              'Seleccione "No" si tiene planeado actualizar o reinstalar el software y desea conservar sus datos.', 
              mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Si el usuario selecciona "Sí":
        // Eliminación física inmediata
        if FileExists(ConfigFile) then
          DeleteFile(ConfigFile);
          
        if FileExists(CacheDB) then
          DeleteFile(CacheDB);
      end;
  end;

  // --- FASE 2: DESPUÉS de que el motor de Inno Setup borró los archivos del registro ---
  if CurUninstallStep = usPostUninstall then
  begin
    // Si el usuario eligió "No" en el paso anterior, los archivos JSON/DB permanecerán allí.
    // Si eligió "Sí", la carpeta quedará vacía y esta llamada la eliminará del disco sin dejar rastro.
    DelTree(ExpandConstant('{app}'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\ControlClienteApp'), True, True, True);
  end;
end;