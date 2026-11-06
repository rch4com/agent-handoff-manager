<#
.SYNOPSIS
  Host smoke test: install the skill from the public repo (pinned SHA) into a throw-away repo, ask a host
  agent to WRITE a handoff, then verify the record with the core itself (not with the agent's report).
.DESCRIPTION
  Runs real host CLIs, which spend model credits and execute the skill with the host's own permissions.
  Run it yourself; it never touches your real repositories (temp dirs only). copilot/opencode/agy run in a narrow-permission mode by default (the agent may only execute `python ...`; the payload is prepared by this script). Use -ComposePayload to let the agent compose the payload (needs broader permissions).
.EXAMPLE
  pwsh -File scripts/host_smoke.ps1 -Target copilot,opencode,agy -Python C:/Users/me/AppData/Local/Python/pythoncore-3.14-64/python.exe
  pwsh -File scripts/host_smoke.ps1 -DryRun     # install + core check only, no agent is started
#>
param(
  [string]$Target = '',   # comma separated: copilot,opencode,agy,codex,claude (a string because `pwsh -File` does not split lists)
  [string]$Python = 'python',
  [string]$Sha = '',
  [string]$OpenCodeModel = 'opencode/big-pickle',
  [switch]$ComposePayload,  # agent writes the payload itself (needs broad write/shell permission); default: script prepares it, agent only runs the core
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$repo = 'rch4com/agent-handoff-manager'
if (-not $Sha) { $Sha = (git ls-remote "https://github.com/$repo" HEAD).Split("`t")[0] }
$agentId = @{ copilot = 'github-copilot'; opencode = 'opencode'; agy = 'antigravity'; codex = 'codex'; claude = 'claude-code' }
$writerName = @{ copilot = 'copilot'; opencode = 'opencode'; agy = 'antigravity'; codex = 'codex'; claude = 'claude-code' }
$results = @()
$valid = @('copilot', 'opencode', 'agy', 'codex', 'claude')
$targets = @($Target -split '[,\s]+' | Where-Object { $_ })
if ($DryRun -and -not $targets) { $targets = @('codex') }
foreach ($bad in ($targets | Where-Object { $valid -notcontains $_ })) { throw "Unknown target '$bad'. Valid: $($valid -join ', ')" }
if (-not $targets) { throw "Pass -Target <comma separated: $($valid -join ', ')> or -DryRun" }
foreach ($h in $targets) {
  $dir = Join-Path $env:TEMP ("ahm-smoke-$h-" + [guid]::NewGuid().ToString('n').Substring(0, 6))
  New-Item -ItemType Directory $dir | Out-Null
  Push-Location $dir
  try {
    git init -q -b main .; 'print(1)' | Set-Content app.py; git add -A
    git -c user.email=t@t -c user.name=t commit -q -m init
    gh skill install $repo agent-handoff-manager --agent $agentId[$h] --scope project --pin $Sha | Out-Null
    $core = Get-ChildItem -Recurse -Filter handoff.py -Path . | Where-Object { $_.FullName -notmatch '\\\.git\\' } | Select-Object -First 1
    $ver = & $Python $core.FullName --version
    if ($DryRun) { $results += "[dry-run] $h install OK, core: $ver ($dir)"; continue }
    $facts = "mission 'Add logging to app.py'; agent $($writerName[$h]); in_progress ['edit app.py']; changed_files [{path app.py, owner $($writerName[$h])}]; validation [{command 'python app.py', result not_run, evidence ''}]; next_action 'Add a logging call to app.py and run python app.py'; failed_attempts ['tried print(): no timestamps']"
    $narrow = ($h -in @('copilot', 'opencode', 'agy')) -and -not $ComposePayload
    if ($narrow) {
      # Narrow mode: payload prepared here; the agent may only run `python ...` (no file edits, no other commands).
      $payloadObj = [ordered]@{ agent = $writerName[$h]; mission = 'Add logging to app.py'; in_progress = @('edit app.py')
        changed_files = @(@{ path = 'app.py'; owner = $writerName[$h] }); validation = @(@{ command = 'python app.py'; result = 'not_run'; evidence = '' })
        next_action = 'Add a logging call to app.py and run python app.py'; failed_attempts = @('tried print(): no timestamps') }
      $payloadObj | ConvertTo-Json -Depth 5 | Set-Content payload.tmp.json -Encoding utf8
      $rel = (Resolve-Path -Relative $core.FullName).Replace([string][char]92, '/') -replace '^\./', ''
      $prompt = "Use the agent-handoff-manager skill. The payload file payload.tmp.json already exists in the current directory (prepared by the user; do not edit or delete it). Run exactly: python $rel --repo . write --payload payload.tmp.json --depth rich (plain python on PATH) and report the printed id and revision."
    } else {
      $prompt = "Use the agent-handoff-manager skill to write a handoff with --depth rich. Record only these facts: $facts. Python is $Python . Put the payload file in your temp dir and delete it afterwards. Report the printed id and revision. Do not edit repository files."
    }
    switch ($h) {
      'copilot'  { if ($narrow) { copilot -p $prompt '--allow-tool=shell(python)' --deny-tool='shell(rm)' --deny-tool='shell(git push)' } else { copilot -p $prompt --allow-tool='shell' } }
      'opencode' {
        if ($narrow) { $env:OPENCODE_PERMISSION = '{"bash":{"python *":"allow","*":"deny"},"edit":"deny","webfetch":"deny"}' }
        try { opencode run -m $OpenCodeModel $prompt } finally { Remove-Item Env:OPENCODE_PERMISSION -ErrorAction SilentlyContinue }
      }
      'agy'      {
        if ($narrow) {
          # session-only settings REPLACE the allow list: reads, a few read-only commands and `python ...`; writes/rm/push denied
          $agySettings = '{"permissions":{"allow":["read_file(*)","command(Get-Content)","command(Get-ChildItem)","command(Test-Path)","command(git status)","command(regex:^python(?:\\s.*)?$)"],"deny":["write_file(*)","command(rm *)","command(git push*)"]}}'
          agy -p $prompt --settings $agySettings
        } else { agy -p $prompt }
      }
      'codex'    { codex exec --skip-git-repo-check -s workspace-write $prompt }
      'claude'   { claude -p $prompt --allowedTools 'Bash(python:*)' 'Read' 'Write' 'Skill' }
    }
    if (Test-Path payload.tmp.json) { Remove-Item payload.tmp.json }
    # Judge by the core, not by what the agent said.
    $list = & $Python $core.FullName --repo . list --status all | ConvertFrom-Json
    $rec = $list | Where-Object { $_.payload.mission -eq 'Add logging to app.py' } | Select-Object -First 1
    $doc = (& $Python $core.FullName --repo . doctor | ConvertFrom-Json).ok
    $dirty = (git status --porcelain -- app.py).Length -gt 0
    if ($rec -and $doc -and -not $dirty) {
      $results += "PASS $h : id=$($rec.id) depth=$($rec.depth) agent=$($rec.payload.agent) doctor_ok=$doc app.py_untouched=$(-not $dirty)"
    } else {
      $results += "FAIL $h : record_found=$([bool]$rec) doctor_ok=$doc app.py_modified=$dirty (dir: $dir)"
    }
  } catch { $results += "ERROR $h : $($_.Exception.Message) (dir: $dir)" }
  finally { Pop-Location }
}
Write-Output ("=== host smoke summary (pinned " + $Sha.Substring(0, 7) + ") ===")
$results
