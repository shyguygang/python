# 🤖 Azure Automation and Update Management Setup

![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![PowerShell](https://img.shields.io/badge/PowerShell-%235391FE.svg?style=for-the-badge&logo=powershell&logoColor=white)

This repository contains ARM templates and PowerShell scripts to automate the setup of Azure Automation and Update Management for your Azure environment.

## 📋 Table of Contents

- [Overview](#clipboard-overview)
- [Features](#sparkles-features)
- [Prerequisites](#checkered_flag-prerequisites)
- [Files in this Repository](#file_folder-files-in-this-repository)
- [Installation](#floppy_disk-installation)
- [Usage](#rocket-usage)
- [Functions](#wrench-functions)
- [Resources Created](#package-resources-created)
- [Troubleshooting](#sos-troubleshooting)
- [Contributing](#handshake-contributing)
- [License](#page_with_curl-license)

## :clipboard: Overview

This project provides tools to set up Azure Automation Update Management for Windows machines, including a workbook for monitoring update status, action groups for alerts, and metric alerts for update cycles.

## :sparkles: Features

- Create and manage Azure Automation accounts
- Set up Log Analytics Workspaces
- Connect VMs to Log Analytics Workspaces
- Configure Azure Update Management
- Deploy Azure Updates Dashboard Workbook and Alerts

## :checkered_flag: Prerequisites

- An active Azure subscription
- Azure CLI or Azure PowerShell installed
- Permissions to create resources in your Azure subscription
- PowerShell 5.1 or later
- Azure PowerShell modules (`Az.OperationalInsights`, `Az.Automation`, `Az.Resources`)

## :file_folder: Files in this Repository

- `template.json`: Main ARM template
- `parameters.json`: Parameters file for the ARM template
- `AzureAutomationSetup.ps1`: PowerShell script for setup

## :floppy_disk: Installation

1. Clone the repository:
   - ``` git clone https://github.com/your-repo/azure-automation-update-management.git ```
   - ``` cd azure-automation-update-management ```

3. Modify `parameters.json` with your environment-specific values.

## :rocket: Usage

### Using ARM Templates:

1. Deploy the template:

Using Azure CLI:
az deployment group create --resource-group <your-resource-group> --template-file template.json --parameters @parameters.json

Using Azure PowerShell:
```powershell
New-AzResourceGroupDeployment -ResourceGroupName <your-resource-group> -TemplateFile template.json -TemplateParameterFile parameters.json
```

2. Verify deployment in the Azure portal.

Using PowerShell Script:
``` .\AzureAutomationSetup.ps1 ```

3. Follow the on-screen prompts to set up your Azure environment.

## :wrench: Functions

- Connect-ToAzure: Connects to Azure and sets the context
- Show-MainMenu: Displays the main menu options
- Invoke-Option1: Checks/creates Automation Account and lists Log Analytics Workspaces
- Invoke-Option2: Creates new Log Analytics Workspace and deploys
- Invoke-Option3: Enables Azure Update Management on existing LAW
- Connect-VMsToLAW: Connects VMs to Log Analytics Workspace
- Setup-AzureUpdateManagement: Sets up Azure Update Management

## :package: Resources Created

:book: Azure Workbook for Windows Update Summary
:bell: Action Group for alerts
:warning: Metric Alerts for update cycles
:link: Linked service connecting Automation account to Log Analytics workspace

## :sos: Troubleshooting
If you encounter any issues during deployment:

1. Check the deployment logs in the Azure portal
2. Ensure all parameter values are correct
3. Verify you have the necessary permissions in your Azure subscription

## :handshake: Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
## :page_with_curl: License
This project is licensed under the GNU License - see the LICENSE file for details.

:information_source: For more information, please refer to the Azure Automation documentation.

## 👤 Author
(c) g0hst 2022
