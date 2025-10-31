Dim shell, cmd
Set shell = CreateObject("WScript.Shell")
cmd = "C:\JarvisBridge\scripts\run_jarvis_hidden.cmd"
shell.Run """" & cmd & """", 0, False
