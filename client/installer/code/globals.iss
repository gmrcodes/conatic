type
  TModoInstalacion = (
    miNueva,
    miActualizar,
    miReinstalar
  );
  
var

  ConfigPage: TWizardPage;
  PaginaActualizacion: TWizardPage;
  
  lblTerminal: TNewStaticText;
  edtTerminal: TNewEdit;
  
  lblIP: TNewStaticText;
  edtIP: TNewEdit;

  chkOffline: TNewCheckBox;
  lblTiempo: TNewStaticText;
  edtTiempo: TNewEdit;

  ModoInstalacion: TModoInstalacion;