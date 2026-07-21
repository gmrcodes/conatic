procedure OcultarArchivo(const Archivo: String);
var
  Codigo: Integer;
begin
  Exec(
    ExpandConstant('{cmd}'),
    '/C attrib +H "' + Archivo + '"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    Codigo
  );
end;

procedure MostrarArchivo(const Archivo: String);
var
  Codigo: Integer;
begin
  if FileExists(Archivo) then
  begin
    // Quitar los atributos de Oculto (+H) y de Solo Lectura (+R) si existieran
    Exec(
      ExpandConstant('{cmd}'),
      '/C attrib -H -R "' + Archivo + '"',
      '',
      SW_HIDE,
      ewWaitUntilTerminated,
      Codigo
    );
  end;
end;