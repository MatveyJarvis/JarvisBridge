' Запускает переданный .cmd/.bat скрыто (без консоли)
CreateObject("Wscript.Shell").Run """" & WScript.Arguments(0) & """", 0, False
