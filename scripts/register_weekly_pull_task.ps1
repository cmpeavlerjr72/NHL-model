# Registers (or replaces) ONLY the NHL-Model-weekly-pull task: Monday 06:00 local, interactive logon only.
# Remove with: Unregister-ScheduledTask -TaskName NHL-Model-weekly-pull -Confirm:$false
$root = 'C:\Users\devuser\NHL-Model'
$py = Join-Path $root '.venv\Scripts\python.exe'
$script = Join-Path $root 'scripts\chain_weekly_pull.py'
$action = New-ScheduledTaskAction -Execute $py -Argument ('"' + $script + '"') -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '06:00'
$settings = New-ScheduledTaskSettingsSet -Hidden -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId (whoami) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'NHL-Model-weekly-pull' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'NHL-Model weekly resumable NHL API pull (schedule sibling + pbp/box/shifts, retries empty shift charts)' -Force
