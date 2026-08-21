param(
    [Parameter(Mandatory = $true)] [string] $Presentation,
    [Parameter(Mandatory = $true)] [string] $AnimationConfig,
    [Parameter(Mandatory = $true)] [string] $OutputDir,
    [Parameter(Mandatory = $true)] [string] $EvidencePath,
    [string] $ExpectedPptxSha256 = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-RepoPath {
    param([string] $Value, [string] $Label, [bool] $MustExist = $false)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "$Label is empty"
    }
    $full = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Value))
    $root = [System.IO.Path]::GetFullPath((Get-Location).Path)
    if (-not $full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes repository root: $Value"
    }
    if ($MustExist -and -not (Test-Path -LiteralPath $full)) {
        throw "$Label does not exist: $full"
    }
    return $full
}

function Get-Sha256 {
    param([string] $Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-SampledColorCount {
    param([System.Drawing.Bitmap] $Bitmap)
    $colors = New-Object 'System.Collections.Generic.HashSet[string]'
    $stepX = [Math]::Max(1, [int]($Bitmap.Width / 32))
    $stepY = [Math]::Max(1, [int]($Bitmap.Height / 18))
    for ($y = 0; $y -lt $Bitmap.Height; $y += $stepY) {
        for ($x = 0; $x -lt $Bitmap.Width; $x += $stepX) {
            $pixel = $Bitmap.GetPixel($x, $y)
            [void] $colors.Add("$($pixel.R),$($pixel.G),$($pixel.B)")
        }
    }
    return $colors.Count
}

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class PptTargetWindow {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
}
"@

function Capture-PowerPointWindow {
    param(
        [IntPtr] $Hwnd,
        [string] $Path
    )

    $rect = New-Object PptTargetWindow+RECT
    if (-not [PptTargetWindow]::GetWindowRect($Hwnd, [ref] $rect)) {
        throw "GetWindowRect failed for PowerPoint slideshow HWND=$Hwnd"
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 640 -or $height -lt 360) {
        throw "PowerPoint slideshow window is unexpectedly small: ${width}x${height}"
    }

    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
        $colorCount = Get-SampledColorCount -Bitmap $bitmap
        if ($colorCount -lt 8) {
            throw "Captured slideshow frame appears blank/unavailable (sampled colors=$colorCount). The self-hosted runner must run in an interactive logged-in desktop session."
        }
        $parent = Split-Path -Parent $Path
        if ($parent) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
        return [ordered]@{
            width = $width
            height = $height
            sampled_color_count = $colorCount
            sha256 = Get-Sha256 -Path $Path
        }
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$pptxPath = Resolve-RepoPath -Value $Presentation -Label "Presentation" -MustExist $true
$animationPath = Resolve-RepoPath -Value $AnimationConfig -Label "AnimationConfig" -MustExist $true
$outputPath = Resolve-RepoPath -Value $OutputDir -Label "OutputDir"
$evidenceFullPath = Resolve-RepoPath -Value $EvidencePath -Label "EvidencePath"

New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
$evidenceParent = Split-Path -Parent $evidenceFullPath
if ($evidenceParent) {
    New-Item -ItemType Directory -Force -Path $evidenceParent | Out-Null
}

$pptxSha = Get-Sha256 -Path $pptxPath
if ($ExpectedPptxSha256) {
    $expected = $ExpectedPptxSha256.Trim().ToLowerInvariant()
    if ($pptxSha -ne $expected) {
        throw "PPTX SHA-256 mismatch: expected=$expected actual=$pptxSha"
    }
}

$config = Get-Content -LiteralPath $animationPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([int] $config.version -ne 1) {
    throw "animations.json version must be 1"
}
$slideProperties = @($config.slides.PSObject.Properties)
if ($slideProperties.Count -eq 0) {
    throw "animations.json contains no animated slides"
}

$sessionName = [Environment]::GetEnvironmentVariable("SESSIONNAME")
$interactive = [Environment]::UserInteractive
if (-not $interactive) {
    throw "PowerPoint Desktop gate requires an interactive Windows desktop session"
}

$evidence = [ordered]@{
    status = "FAIL"
    contract_version = "1"
    target_player = "Microsoft PowerPoint Desktop"
    pptx = $Presentation
    pptx_sha256 = $pptxSha
    animation_config = $AnimationConfig
    animation_config_sha256 = Get-Sha256 -Path $animationPath
    windows_session_name = $sessionName
    user_interactive = $interactive
    powerpoint_version = $null
    animated_slide_count = $slideProperties.Count
    captured_state_count = 0
    slides = @()
    failure = $null
    scope = "Real target-player slideshow playback on an interactive, licensed Microsoft PowerPoint Desktop session."
}

$ppt = $null
$presentationObject = $null
$slideShowWindow = $null
$exitCode = 1

try {
    try {
        $ppt = New-Object -ComObject PowerPoint.Application
    }
    catch {
        throw "Microsoft PowerPoint Desktop COM automation is unavailable. Install and license desktop PowerPoint on this self-hosted runner. $($_.Exception.Message)"
    }

    $evidence.powerpoint_version = [string] $ppt.Version
    $ppt.Visible = -1

    # ReadOnly=true, Untitled=false, WithWindow=false.
    $presentationObject = $ppt.Presentations.Open($pptxPath, -1, 0, 0)
    $settings = $presentationObject.SlideShowSettings
    # ppShowAll=1, ppSlideShowManualAdvance=1.
    $settings.RangeType = 1
    $settings.AdvanceMode = 1
    $settings.LoopUntilStopped = 0

    $slideShowWindow = $settings.Run()
    if ($null -eq $slideShowWindow) {
        throw "PowerPoint did not create a SlideShowWindow"
    }
    Start-Sleep -Milliseconds 1200

    $view = $slideShowWindow.View
    $hwnd = [IntPtr]([long] $slideShowWindow.HWND)
    if ($hwnd -eq [IntPtr]::Zero) {
        throw "PowerPoint slideshow returned a null HWND"
    }

    foreach ($slideProperty in $slideProperties) {
        $slideKey = [string] $slideProperty.Name
        if ($slideKey -notmatch '^(\d+)-') {
            throw "animation slide key must start with a numeric slide index: $slideKey"
        }
        $slideIndex = [int] $Matches[1]
        $groupProperties = @($slideProperty.Value.groups.PSObject.Properties | Sort-Object { [int] $_.Value.order })
        if ($groupProperties.Count -eq 0) {
            throw "$slideKey has no animation groups"
        }

        $orders = @($groupProperties | ForEach-Object { [int] $_.Value.order })
        for ($i = 0; $i -lt $orders.Count; $i++) {
            if ($orders[$i] -ne ($i + 1)) {
                throw "$slideKey animation orders must be contiguous 1..N"
            }
            if ([string] $groupProperties[$i].Value.trigger -ne "on-click") {
                throw "$slideKey target-player gate v1 supports on-click groups only"
            }
        }

        # ResetSlide=true so state 0 is the actual pre-click state.
        $view.GotoSlide($slideIndex, -1)
        Start-Sleep -Milliseconds 900
        if ([int] $view.Slide.SlideIndex -ne $slideIndex) {
            throw "PowerPoint failed to navigate to slide $slideIndex"
        }

        $stateRows = @()
        for ($state = 0; $state -le $groupProperties.Count; $state++) {
            if ($state -gt 0) {
                $group = $groupProperties[$state - 1]
                $view.Next()
                $durationMs = 0
                try {
                    $durationMs = [int]([double] $group.Value.duration * 1000)
                }
                catch {
                    $durationMs = 0
                }
                Start-Sleep -Milliseconds ([Math]::Max(700, $durationMs + 450))
                if ([int] $view.Slide.SlideIndex -ne $slideIndex) {
                    throw "Slide $slideIndex advanced before expected click effect $state completed"
                }
            }

            $fileName = "slide-{0:D2}-state-{1:D2}.png" -f $slideIndex, $state
            $capturePath = Join-Path $outputPath $fileName
            $capture = Capture-PowerPointWindow -Hwnd $hwnd -Path $capturePath
            $visibleGroups = @()
            if ($state -gt 0) {
                $visibleGroups = @($groupProperties[0..($state - 1)] | ForEach-Object { [string] $_.Name })
            }
            $hiddenGroups = @()
            if ($state -lt $groupProperties.Count) {
                $hiddenGroups = @($groupProperties[$state..($groupProperties.Count - 1)] | ForEach-Object { [string] $_.Name })
            }
            $stateRows += [ordered]@{
                state = $state
                after_clicks = $state
                visible_animation_groups = $visibleGroups
                hidden_animation_groups = $hiddenGroups
                screenshot = (Join-Path $OutputDir $fileName).Replace('\', '/')
                screenshot_sha256 = $capture.sha256
                screenshot_width = $capture.width
                screenshot_height = $capture.height
                sampled_color_count = $capture.sampled_color_count
            }
            $evidence.captured_state_count = [int] $evidence.captured_state_count + 1
        }

        $evidence.slides += [ordered]@{
            slide = $slideIndex
            slide_key = $slideKey
            click_count = $groupProperties.Count
            animation_groups_in_click_order = @($groupProperties | ForEach-Object { [string] $_.Name })
            states = $stateRows
        }
    }

    $evidence.status = "PASS_TARGET_POWERPOINT_DESKTOP_CAPTURED"
    $exitCode = 0
}
catch {
    $evidence.failure = $_.Exception.Message
    Write-Error $_.Exception.Message
}
finally {
    try {
        if ($null -ne $slideShowWindow) {
            $slideShowWindow.View.Exit()
        }
    }
    catch {}
    try {
        if ($null -ne $presentationObject) {
            $presentationObject.Close()
        }
    }
    catch {}
    try {
        if ($null -ne $ppt) {
            $ppt.Quit()
        }
    }
    catch {}

    $evidence | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $evidenceFullPath -Encoding UTF8
    Write-Host ($evidence | ConvertTo-Json -Depth 6)
}

exit $exitCode
