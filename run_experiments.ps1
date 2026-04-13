param(
    [double]$TimeBudget = 28.0,
    [int]$Workers = 1,
    [int]$Limit = 0
)

$cmd = @(
    "src/experiments.py",
    "--folders", "sm_j10", "sm_j20",
    "--approaches", "topo_seq", "id_ssgs", "lft_ssgs", "ga",
    "--time-budget", $TimeBudget,
    "--workers", $Workers
)

if ($Limit -gt 0) {
    $cmd += @("--limit", $Limit)
}

python @cmd
