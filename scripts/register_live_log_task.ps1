# Registers (or replaces) ONLY the NHL-Model-live-log task. Read-only loggers; no stored password
# (runs only while the user is logged on).
# Remove with: Unregister-ScheduledTask -TaskName NHL-Model-live-log -Confirm:$false
$root = 'C:\Users\devuser\NHL-Model'
$py = Join-Path $root '.venv\Scripts\python.exe'
$script = Join-Path $root 'scripts\chain_live_log.py'
$arg = '"' + $script + '"'
$action = New-ScheduledTaskAction -Execute $py -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At '09:00'
# Repetition params exist only on the -Once set; borrow its Repetition object (09:00 + 14h30m = 23:30).
$rep = (New-ScheduledTaskTrigger -Once -At '09:00' -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Hours 14 -Minutes 30)).Repetition
$trigger.Repetition = $rep
$settings = New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 25)
$principal = New-ScheduledTaskPrincipal -UserId (whoami) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'NHL-Model-live-log' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'NHL-Model read-only forward loggers (goalies, Kalshi, DKeX) every 30 min 09:00-23:30' -Force
