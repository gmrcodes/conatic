procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigFile: String;
  CacheDB: String;
  ResultCode: Integer;
begin
  // --- FASE 1: ANTES de empezar a borrar archivos ---
  if CurUninstallStep = usUninstall then
  begin
    // Detener y eliminar la tarea programada del Watchdog en schtasks
    EliminarScheduler();

    // Matar procesos activos para liberar bloqueos de archivos en Windows
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM launcher.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM cliente.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

    // Pregunta Conservar o eliminar configuración/base de datos
    ConfigFile := ExpandConstant('{app}\config_cliente.json');
    CacheDB := ExpandConstant('{app}\cache_cliente.db');

    if MsgBox('¿Desea eliminar por completo los archivos de configuración y la base de datos local?' + #13#10#13#10 +
              'Seleccione "Sí" para realizar una desinstalación 100% limpia.' + #13#10 +
              'Seleccione "No" si tiene planeado actualizar o reinstalar el software y desea conservar sus datos.', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Si el usuario selecciona "Sí":
      
      // Liberamos los archivos quitando el atributo oculto (+H) antes de destruirlos
      MostrarArchivo(ConfigFile);
      MostrarArchivo(CacheDB);

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
  end;
end;