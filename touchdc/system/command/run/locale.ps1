function Set-PowerShellLanguage {
    Param (
        [Parameter(Mandatory)] 
        [System.Globalization.CultureInfo] $CultureInfo
    )

    if ($CultureInfo -notin (Get-WinUserLanguageList | % {$_.LanguageTag})) {
        Write-Error "Language pack for $CultureInfo is not installed."
        return
    }

    [System.Reflection.Assembly]::Load('System.Management.Automation')
        .GetType('Microsoft.PowerShell.NativeCultureResolver')
        .GetField('m_Culture', 'NonPublic, Static').SetValue($null, $CultureInfo)
    [System.Reflection.Assembly]::Load('System.Management.Automation')
        .GetType('Microsoft.PowerShell.NativeCultureResolver')
        .GetField('m_uiCulture', 'NonPublic, Static').SetValue($null, $CultureInfo)
}

Set-PowerShellLanguage 'en-AU'