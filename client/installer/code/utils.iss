function ArchivoExiste(Nombre: String): Boolean;
begin
    Result := FileExists(ExpandConstant('{app}\'+Nombre));
end;

const
	
	TASK_NAME = 'Control Cliente';
	SCHTASKS_EXE = '{sys}\schtasks.exe';
