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
begin
  Exito :=
    Exec(
      ExpandConstant('{sys}\schtasks.exe'),

      '/Create ' +
      '/TN "Control Cliente" ' +
      '/TR "' + GetLauncherPath() + '" ' +
      '/SC ONLOGON ' +
      '/RL HIGHEST ' +
      '/F',

      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      CodigoSalida);

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