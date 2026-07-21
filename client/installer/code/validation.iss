function EsNumero(S: String): Boolean;
var
  I: Integer;
begin
  Result := Length(S) > 0;

  if not Result then
    Exit;

  for I := 1 to Length(S) do
  begin
    if (Ord(S[I]) < Ord('0')) or (Ord(S[I]) > Ord('9')) then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

function ValidarIP(IP: String): Boolean;
var
  I, Puntos: Integer;
begin
  Result := False;

  if Trim(IP) = '' then
    Exit;

  Puntos := 0;

  for I := 1 to Length(IP) do
    if IP[I] = '.' then
      Inc(Puntos);

  Result := (Puntos = 3);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if (PaginaActualizacion <> nil) and (CurPageID = PaginaActualizacion.ID) then
  begin
    if RadioActualizar.Checked then
      ModoInstalacion := miActualizar
    else
      ModoInstalacion := miReinstalar;
    Exit;
  end;
  
  if CurPageID <> ConfigPage.ID then
    Exit;

  if not EsNumero(edtTerminal.Text) then
  begin
    MsgBox('Ingrese un número de terminal válido.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if not ValidarIP(edtIP.Text) then
  begin
    MsgBox('Ingrese una IP válida.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if not EsNumero(Trim(edtTiempo.Text)) then
  begin
    MsgBox('Por favor, ingrese un tiempo predeterminado válido (solo números enteros).', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
end;