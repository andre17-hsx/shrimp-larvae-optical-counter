@echo off
rem Lanza la cola de simulaciones de la noche y evita que Windows se duerma mientras corren.
rem Deja esta ventana ABIERTA: si la cierras, WSL apaga Ubuntu y se detienen los calculos.
rem Para cambiar los casos, edita la linea CASOS (nombres de carpetas en cfd_3d\casos).
set CASOS=p1_losa_gruesa p2_medio_grueso
echo Casos: %CASOS%
echo Inicio: %date% %time%
powershell -NoProfile -Command "$s='[DllImport(\"kernel32.dll\")] public static extern uint SetThreadExecutionState(uint f);'; Add-Type -MemberDefinition $s -Name P -Namespace W; [void][W.P]::SetThreadExecutionState(0x80000001); $sh=(& wsl.exe -d Ubuntu -- wslpath -a '%~dp0cola_noche.sh'); & wsl.exe -d Ubuntu -- bash $sh %CASOS%"
echo Fin: %date% %time%
echo Revisa cfd_3d\resultados\cola.log
pause
