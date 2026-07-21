
var  
  
  RadioActualizar: TRadioButton;
  RadioReinstalar: TRadioButton;
  
procedure CrearPaginaActualizacion();
begin
  PaginaActualizacion :=
    CreateCustomPage(
      wpWelcome,
      'Instalación existente',
      'Se detectó una instalación anterior.');

  RadioActualizar := TRadioButton.Create(PaginaActualizacion.Surface);
  RadioActualizar.Parent := PaginaActualizacion.Surface;
  RadioActualizar.Caption := 'Actualizar (conservar configuración)';
  RadioActualizar.Checked := True;
  RadioActualizar.Top := 20;
  RadioActualizar.Left := 0;

  RadioReinstalar := TRadioButton.Create(PaginaActualizacion.Surface);
  RadioReinstalar.Parent := PaginaActualizacion.Surface;
  RadioReinstalar.Caption := 'Reinstalar (eliminar configuración)';
  RadioReinstalar.Top := 45;
  RadioReinstalar.Left := 0;
end;

procedure InitializeWizard();
begin

  ModoInstalacion := miNueva;

	if ExisteInstalacion() then
		CrearPaginaActualizacion();

  ConfigPage :=
    CreateCustomPage(
      wpSelectDir,
      'Configuración del Cliente',
      'Ingrese los datos del terminal');

  lblTerminal := TNewStaticText.Create(ConfigPage);
  lblTerminal.Parent := ConfigPage.Surface;
  lblTerminal.Caption := 'Número de Terminal';
  lblTerminal.Left := ScaleX(0);
  lblTerminal.Top := ScaleY(10);
  
  edtTerminal := TNewEdit.Create(ConfigPage);
  edtTerminal.Parent := ConfigPage.Surface;
  edtTerminal.Left := ScaleX(0);
  edtTerminal.Top := lblTerminal.Top + 18;
  edtTerminal.Width := ScaleX(120);
  edtTerminal.Text := '1';
  
  lblIP := TNewStaticText.Create(ConfigPage);
  lblIP.Parent := ConfigPage.Surface;
  lblIP.Caption := 'Dirección IP del Servidor';
  lblIP.Left := ScaleX(0);
  lblIP.Top := edtTerminal.Top + 40;
  
  edtIP := TNewEdit.Create(ConfigPage);
  edtIP.Parent := ConfigPage.Surface;
  edtIP.Left := ScaleX(0);
  edtIP.Top := lblIP.Top + 18;
  edtIP.Width := ScaleX(180);
  edtIP.Text := '127.0.0.1';

  // Casilla de verificación para Modo Offline
  chkOffline := TNewCheckBox.Create(ConfigPage);
  chkOffline.Parent := ConfigPage.Surface;
  chkOffline.Left := ScaleX(0);
  chkOffline.Top := edtIP.Top + ScaleY(35);
  chkOffline.Width := ScaleX(320);
  chkOffline.Caption := 'Permitir modo offline (Sincronización local si cae el servidor)';
  chkOffline.Checked := True;

  // Etiqueta para el Tiempo Predeterminado
  lblTiempo := TNewStaticText.Create(ConfigPage);
  lblTiempo.Parent := ConfigPage.Surface;
  lblTiempo.Caption := 'Tiempo predeterminado por sesión (minutos)';
  lblTiempo.Left := ScaleX(0);
  lblTiempo.Top := chkOffline.Top + ScaleY(30);

  // Cuadro de texto para el Tiempo Predeterminado
  edtTiempo := TNewEdit.Create(ConfigPage);
  edtTiempo.Parent := ConfigPage.Surface;
  edtTiempo.Left := ScaleX(0);
  edtTiempo.Top := lblTiempo.Top + ScaleY(18);
  edtTiempo.Width := ScaleX(80);
  edtTiempo.Text := '60';
      
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  
  // Si la página a mostrar es la de Configuración (IP/Terminal) y el modo es Actualizar, la saltamos
  if (ConfigPage <> nil) and (PageID = ConfigPage.ID) and (ModoInstalacion = miActualizar) then
  begin
    Result := True;
  end;
end;