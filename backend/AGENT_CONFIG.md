# Agent Service Configuration Guide

This guide explains how to configure the Agent Service to connect to your Microsoft Foundry project.

## Prerequisites

1. **Microsoft Foundry Project**: You must have a Foundry project with a GPT-4o model deployed
2. **Azure Authentication**: Ensure you're logged in to Azure CLI or have DefaultAzureCredential configured
3. **Access Permissions**: Your Azure identity must have access to the Foundry project

## Configuration Steps

### Step 1: Locate Your Foundry Project Endpoint

Your Foundry project endpoint typically looks like:
```
https://your-project-name.eastus2.api.azureml.ms
```

To find your endpoint:
1. Go to [Azure AI Studio](https://ai.azure.com)
2. Navigate to your Foundry project
3. Go to Settings or Overview
4. Copy the "Project Endpoint" URL

### Step 2: Identify Your Model Deployment Name

Your model deployment name is typically:
- `gpt-4o` (default)
- Or a custom deployment name you specified

To find your deployment name:
1. In Azure AI Studio, go to your project
2. Navigate to "Deployments"
3. Find your GPT-4o deployment
4. Copy the deployment name

### Step 3: Update Environment Variables

Edit the `.env` file in the `backend/` directory:

```bash
# Foundry Configuration
FOUNDRY_PROJECT_ENDPOINT=https://your-project-name.eastus2.api.azureml.ms
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4o
```

Replace:
- `your-project-name` with your actual project name
- `gpt-4o` with your actual deployment name (if different)

### Step 4: Azure Authentication

The Agent Service uses `DefaultAzureCredential` which supports multiple authentication methods in this order:

1. **Environment Variables** (for production)
   ```bash
   AZURE_CLIENT_ID=your-client-id
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_SECRET=your-client-secret
   ```

2. **Azure CLI** (for local development - recommended)
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

3. **Managed Identity** (when running in Azure)

For local development, **Azure CLI login is the easiest method**.

## Testing the Connection

Once configured, test the connection:

```bash
cd backend
.\venv\Scripts\python.exe test_agent.py
```

Expected output:
```
============================================================
Testing Foundry Connection
============================================================
Foundry connection validated successfully
Connection test PASSED

============================================================
Testing Streaming Corrections
============================================================
[streaming correction output...]
Streaming completed
Streaming test PASSED
```

## Troubleshooting

### Error: "Could not find credentials"

**Solution**: Run `az login` to authenticate with Azure CLI

### Error: "Access denied" or "403 Forbidden"

**Solution**: Ensure your Azure identity has the following roles on the Foundry project:
- Azure AI Developer (or higher)
- Cognitive Services OpenAI User

To grant access:
1. Go to Azure AI Studio → Your Project → Settings → Access Control
2. Add your Azure identity with appropriate role

### Error: "Project endpoint not found" or "404"

**Solution**: Verify your `FOUNDRY_PROJECT_ENDPOINT` is correct:
- Check for typos
- Ensure it starts with `https://`
- Confirm the region matches your project (e.g., `eastus2`)

### Error: "Model deployment not found"

**Solution**: Verify your `FOUNDRY_MODEL_DEPLOYMENT_NAME`:
- Check the exact deployment name in Azure AI Studio
- Names are case-sensitive
- Ensure the model is deployed (not just created)

## Architecture

```
FastAPI Backend
    ↓
AgentService
    ↓
Microsoft Agent Framework SDK (AzureAIClient)
    ↓
Microsoft Foundry Project
    ↓
GPT-4o Model
```

## Security Notes

1. **Never commit `.env` file** - It contains sensitive endpoint URLs
2. **Use Managed Identity in production** - Don't use client secrets if possible
3. **Rotate credentials regularly** - If using client secrets
4. **Grant least privilege** - Only necessary roles on Foundry project

## Next Steps

After successful connection test:
1. Run the FastAPI server: `uvicorn main:app --reload`
2. Test the streaming endpoint at `/api/corrections/stream`
3. Integrate with React frontend
