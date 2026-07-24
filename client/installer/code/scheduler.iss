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
  ComandoPS: String;
begin
  // Construcción del script de PowerShell contra ahorro de energía e inactividad (Idle)
  ComandoPS :=
    '$action = New-ScheduledTaskAction -Execute "' + GetLauncherPath() + '"; ' +
    '$trigger = New-ScheduledTaskTrigger -AtLogOn; ' +
    '$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -DontStopOnIdleEnd; ' +
    '$principal = New-ScheduledTaskPrincipal -RunLevel Highest; ' +
    'Register-ScheduledTask -TaskName "Control Cliente" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force;';

  Exito := Exec(
    ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' + ComandoPS + '"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    CodigoSalida
  );

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