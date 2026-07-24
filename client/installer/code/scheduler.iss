function GetLauncherPath(): String;
begin
  Result := ExpandConstant('{app}\launcher.exe');
end;

function SchedulerExiste(): Boolean;
var
  CodigoSalida: Integer;
  Exito: Boolean;
begin
  Exito :=
    Exec(
      ExpandConstant('{sys}\schtasks.exe'),
      '/Query /TN "Control Cliente"',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      CodigoSalida);

  Result := Exito and (CodigoSalida = 0);
end;

function DetenerScheduler(): Boolean;
var
  CodigoSalida: Integer;
  Exito: Boolean;
begin
  Exito :=
    Exec(
      ExpandConstant('{sys}\schtasks.exe'),
      '/End /TN "Control Cliente"',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      CodigoSalida);

  Result := Exito;
end;

function CrearScheduler(): Boolean;
var
  CodigoSalida: Integer;
  Exito: Boolean;
  XmlPath: String;
  XmlContenido: String;
begin
  XmlPath := ExpandConstant('{tmp}\task_config.xml');

  // Construcción del XML para Windows Task Scheduler v1.2
  XmlContenido :=
    '<?xml version="1.0" encoding="UTF-16"?>' + #13#10 +
    '<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">' + #13#10 +
    '  <Triggers>' + #13#10 +
    '    <LogonTrigger>' + #13#10 +
    '      <Enabled>true</Enabled>' + #13#10 +
    '    </LogonTrigger>' + #13#10 +
    '  </Triggers>' + #13#10 +
    '  <Principals>' + #13#10 +
    '    <Principal id="Author">' + #13#10 +
    '      <RunLevel>HighestAvailable</RunLevel>' + #13#10 + // Ejecuta con los máximos privilegios disponibles
    '    </Principal>' + #13#10 +
    '  </Principals>' + #13#10 +
    '  <Settings>' + #13#10 +
    '    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>' + #13#10 +
    '    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>' + #13#10 + // Permite ejecución en BATERÍA
    '    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>' + #13#10 + // No se detiene si desconectan el cable
    '    <AllowHardTerminate>false</AllowHardTerminate>' + #13#10 +
    '    <StartWhenAvailable>true</StartWhenAvailable>' + #13#10 +
    '    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>' + #13#10 +
    '    <IdleSettings>' + #13#10 +
    '      <StopOnIdleEnd>false</StopOnIdleEnd>' + #13#10 +
    '      <RestartOnIdle>false</RestartOnIdle>' + #13#10 +
    '    </IdleSettings>' + #13#10 +
    '    <AllowStartOnDemand>true</AllowStartOnDemand>' + #13#10 +
    '    <Enabled>true</Enabled>' + #13#10 +
    '    <Hidden>false</Hidden>' + #13#10 +
    '    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>' + #13#10 + // Sin límite de tiempo (no se mata a las 72 horas)
    '    <Priority>7</Priority>' + #13#10 +
    '  </Settings>' + #13#10 +
    '  <Actions Context="Author">' + #13#10 +
    '    <Exec>' + #13#10 +
    '      <Command>' + GetLauncherPath() + '</Command>' + #13#10 +
    '    </Exec>' + #13#10 +
    '  </Actions>' + #13#10 +
    '</Task>';

  // Guardar archivo XML temporal
  SaveStringToFile(XmlPath, XmlContenido, False);

  // Crear la tarea importando la configuración XML
  Exito :=
    Exec(
      ExpandConstant('{sys}\schtasks.exe'),
      '/Create /TN "Control Cliente" /XML "' + XmlPath + '" /F',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      CodigoSalida);

  // Borrar el archivo temporal
  DeleteFile(XmlPath);

  Result := Exito and (CodigoSalida = 0);
end;

function EliminarScheduler(): Boolean;
var
  CodigoSalida: Integer;
  Exito: Boolean;
begin
  DetenerScheduler();

  Exito :=
    Exec(
      ExpandConstant('{sys}\schtasks.exe'),
      '/Delete /TN "Control Cliente" /F',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      CodigoSalida);

  Result := Exito and (CodigoSalida = 0);
end;

function RepararScheduler(): Boolean;
begin
  if SchedulerExiste() then
    EliminarScheduler();

  Result := CrearScheduler();
end;