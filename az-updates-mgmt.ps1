# Import required Azure modules
Import-Module Az.OperationalInsights, Az.Automation, Az.Resources

# Azure subscription ID
$subId = "XXXX"

# Connect to Azure and set context
function Connect-ToAzure {
    Write-Host "Connecting to Azure and setting Az Context..." -ForegroundColor Green -BackgroundColor Black
    Connect-AzAccount -Subscription $subId
    Write-Host "Connected to Subscription: $subId" -ForegroundColor Green -BackgroundColor Black
}

# Main menu function
function Show-MainMenu {
    $title = "Azure Automation and Update Management Setup"
    $prompt = "Please select from these options:"
    $choices = @(
        "&E - Exit",
        "&1 - Check/Create Automation Account and List Log Analytics Workspaces",
        "&2 - Create new Log Analytics Workspace and deploy",
        "&3 - Enable Azure Update Management on existing LAW"
    )
    
    $choiceDesc = New-Object System.Collections.ObjectModel.Collection[System.Management.Automation.Host.ChoiceDescription]
    foreach ($choice in $choices) {
        $choiceDesc.Add((New-Object System.Management.Automation.Host.ChoiceDescription $choice))
    }
    
    $defaultChoice = 0
    $host.ui.PromptForChoice($title, $prompt, $choiceDesc, $defaultChoice)
}

# Function to check/create Automation Account and list Log Analytics Workspaces
function Invoke-Option1 {
    $ResourceGroup = "rrautomation"
    
    # Check and create Resource Group if needed
    try {
        Get-AzResourceGroup -Name $ResourceGroup -ErrorAction Stop
    } catch {
        Write-Host "Creating Resource Group: $ResourceGroup" -ForegroundColor Green
        New-AzResourceGroup -Name $ResourceGroup -Location "East US"
    }
    
    # Check and create Automation Account if needed
    try {
        Get-AzAutomationAccount -Name "rrautomation" -ResourceGroupName $ResourceGroup -ErrorAction Stop
    } catch {
        Write-Host "Creating Automation Account: rrautomation" -ForegroundColor Green
        New-AzAutomationAccount -Name "rrautomation" -ResourceGroupName $ResourceGroup -Location "East US"
    }
    
    # List Log Analytics Workspaces
    try {
        $logNames = Get-AzOperationalInsightsWorkspace -ResourceGroupName $ResourceGroup
        if ($logNames) {
            $logNames
            Write-Host "-----------------------REPEAT AND SELECT #3-------------------------" -ForegroundColor Green -BackgroundColor Black
        } else {
            throw
        }
    } catch {
        Write-Host "No Log Analytics Workspaces found in $ResourceGroup. Listing all workspaces:" -ForegroundColor Yellow
        Get-AzOperationalInsightsWorkspace
        Write-Host "-----------------------REPEAT AND SELECT #2-----------------------" -ForegroundColor Green -BackgroundColor Black
    }
}

# Function to create new Log Analytics Workspace and deploy
function Invoke-Option2 {
    $ResourceGroup = "rrautomation"
    $WorkspaceName = "log-analytics-" + (Get-Random -Maximum 99999)
    $Location = "eastus2"
    
    # Create Log Analytics Workspace
    $lawName = New-AzOperationalInsightsWorkspace -Location $Location -Name $WorkspaceName -Sku PerGB2018 -ResourceGroupName $ResourceGroup
    $workspaceKey = (Get-AzOperationalInsightsWorkspaceSharedKeys -ResourceGroupName $lawName.ResourceGroupName -Name $lawName.Name).PrimarySharedKey
    $workspaceId = $lawName.CustomerID
    
    # Connect VMs to Log Analytics Workspace
    Connect-VMsToLAW -workspaceId $workspaceId -workspaceKey $workspaceKey -lawName $lawName.Name
    
    # Setup Azure Update Management
    Setup-AzureUpdateManagement -ResourceGroup $ResourceGroup
}

# Function to enable Azure Update Management on existing LAW
function Invoke-Option3 {
    $ResourceGroup = "rrautomation"
    $lawName = Read-Host -Prompt "Please enter existing Log Analytics Workspace Name"
    $logName = Get-AzOperationalInsightsWorkspace -Name $lawName -ResourceGroupName $ResourceGroup
    $workspaceKey = (Get-AzOperationalInsightsWorkspaceSharedKeys -ResourceGroupName $logName.ResourceGroupName -Name $logName.Name).PrimarySharedKey
    $workspaceId = $logName.CustomerID
    
    # Connect VMs to Log Analytics Workspace
    Connect-VMsToLAW -workspaceId $workspaceId -workspaceKey $workspaceKey -lawName $lawName
    
    # Setup Azure Update Management
    Setup-AzureUpdateManagement -ResourceGroup $ResourceGroup
}

# Function to connect VMs to Log Analytics Workspace
function Connect-VMsToLAW {
    param($workspaceId, $workspaceKey, $lawName)
    
    $runningVMs = Get-AzVM -Status | Where-Object { $_.PowerState -eq "VM running" }
    
    foreach ($vm in $runningVMs) {
        try {
            Set-AzVMExtension -ResourceGroupName $vm.ResourceGroupName -VMName $vm.Name -Name 'MicrosoftMonitoringAgent' -Publisher 'Microsoft.EnterpriseCloud.Monitoring' -ExtensionType 'MicrosoftMonitoringAgent' -Location $vm.Location -SettingString "{'workspaceId': '$workspaceId'}" -ProtectedSettingString "{'workspaceKey': '$workspaceKey'}" -ErrorAction Stop | Out-Null
            Write-Host "Connected VM($($vm.Name)) to LAW: $lawName" -ForegroundColor Green
        } catch {
            Write-Host "Failed to connect VM($($vm.Name)) to LAW. Error: $_" -ForegroundColor Red
        }
    }
}

# Function to setup Azure Update Management
function Setup-AzureUpdateManagement {
    param($ResourceGroup)
    
    $AutomationAccountName = "rrautomation"
    $ScheduleTime = (Get-Date).AddMinutes(15)
    $Location = (Get-AzResourceGroup -Name $ResourceGroup).Location
    
    # Create Update Deployment Schedule
    $scheduleParams = @{
        ResourceGroupName     = $ResourceGroup
        AutomationAccountName = $AutomationAccountName
        Name                  = "Group 1 Deploy Updates"
        StartTime             = $ScheduleTime
        ExpiryTime            = (Get-Date).AddYears(5)
        MonthInterval         = 1
        DayOfWeekOccurrence   = 3
        DayOfWeek             = 4
    }
    $AutomationSchedule = New-AzAutomationSchedule @scheduleParams
    
    # Create Azure Query
    $queryParams = @{
        ResourceGroupName     = $ResourceGroup
        AutomationAccountName = $AutomationAccountName
        Scope                 = @("/subscriptions/$((Get-AzContext).Subscription.Id)")
        Location              = $Location
        Tag                   = @{"AzUpdates" = "Group 1" }
    }
    $AzQuery = New-AzAutomationUpdateManagementAzureQuery @queryParams
    
    # Create Update Configuration
    $updateParams = @{
        ResourceGroupName            = $ResourceGroup
        AutomationAccountName        = $AutomationAccountName
        Schedule                     = $AutomationSchedule
        Windows                      = $true
        Duration                     = New-TimeSpan -Hours 3
        RebootSetting                = "Always"
        IncludedUpdateClassification = "Security"
        AzureQuery                   = $AzQuery
    }
    New-AzAutomationSoftwareUpdateConfiguration @updateParams
    
    Write-Host "Azure Update Management setup completed" -ForegroundColor Green -BackgroundColor Black
}

# Main script execution
Connect-ToAzure

do {
    $action = Show-MainMenu
    switch ($action) {
        0 { Write-Host "Exiting..." -ForegroundColor Red; break }
        1 { Invoke-Option1 }
        2 { Invoke-Option2 }
        3 { Invoke-Option3 }
    }
    $repeat = Read-Host "Repeat? (Y/N)"
} while ($repeat -eq "Y")

# Update parameters.json and deploy workbook
Write-Host "Updating parameters.json file..." -ForegroundColor Cyan
$json = Get-Content "parameters.json" | ConvertFrom-Json
$json.parameters.workspaceName.value = $lawName
$json | ConvertTo-Json | Out-File "parameters.json"

Write-Host "Deploying Azure Updates Dashboard Workbook, Alerts, and linking automation account to LAW..." -ForegroundColor Cyan
New-AzResourceGroupDeployment -Name "Azure-Automation-Update-Management" -ResourceGroupName $ResourceGroup -TemplateUri "\workbook.json" -TemplateParameterFile "\parameters.json"

# Disconnect from Azure
Disconnect-AzAccount > $null
Write-Host "Disconnected from Azure" -ForegroundColor Red -BackgroundColor Black