# Enterprise & Remote Splunk Setup Guide

Yes! The tool works with **any Splunk Enterprise environment** - on-premises, cloud, remote, clustered, or distributed deployments.

## 🌐 Supported Environments

### ✅ **Enterprise On-Premises**
- Standalone Splunk Enterprise
- Clustered Splunk deployments
- Distributed Splunk environments
- Corporate data centers

### ✅ **Splunk Cloud**
- Splunk Cloud Platform
- Splunk Cloud Services
- Multi-tenant cloud instances

### ✅ **Remote/Hosted**
- AWS/Azure/GCP hosted Splunk
- Third-party managed Splunk
- VPN-accessible Splunk instances

## 🔧 Configuration for Different Environments

I've added several enterprise environment templates to your config. Edit `config/environments.json`:

### **Enterprise On-Premises Example**
```json
{
    "enterprise_prod": {
        "name": "Enterprise Production",
        "hec_url": "https://splunk-prod.yourcompany.com:8089/services/search/jobs",
        "token": "YOUR-ENTERPRISE-PROD-TOKEN-HERE",
        "indices": ["main", "security", "network", "firewall", "proxy", "windows", "linux"],
        "default_time_range": "-7d@d",
        "verify_ssl": true,
        "description": "Enterprise production Splunk environment",
        "username": "your-username",
        "password": "your-password"
    }
}
```

### **Splunk Cloud Example**
```json
{
    "cloud_splunk": {
        "name": "Splunk Cloud",
        "hec_url": "https://yourinstance.splunkcloud.com:8089/services/search/jobs",
        "token": "YOUR-CLOUD-TOKEN-HERE",
        "indices": ["main", "security", "network"],
        "default_time_range": "-24h@h",
        "verify_ssl": true,
        "description": "Splunk Cloud instance"
    }
}
```

## 🔑 Authentication Methods

The tool supports multiple authentication approaches:

### **1. HEC Token (Recommended)**
```json
{
    "token": "B5A79AAD-D822-46CC-80D1-819F80D7BFB0",
    "hec_url": "https://your-splunk.com:8089/services/search/jobs"
}
```

### **2. Username/Password**
```json
{
    "username": "your-splunk-user",
    "password": "your-password",
    "hec_url": "https://your-splunk.com:8089/services/search/jobs"
}
```

### **3. Certificate-based (Enterprise)**
For environments requiring client certificates, you can extend the client configuration.

## 🛡️ Security Considerations

### **SSL/TLS Configuration**
```json
{
    "verify_ssl": true,          // For production environments
    "verify_ssl": false,         // For dev/test with self-signed certs
}
```

### **Network Access**
- **VPN**: Tool works through VPN connections
- **Firewall**: Ensure port 8089 (REST API) is accessible
- **Proxy**: Configure proxy settings if required

### **Permissions Required**
Your Splunk user/token needs:
- **Search capability** on target indices
- **REST API access** 
- **Index read permissions**

## 📊 Enterprise-Specific Features

### **Large-Scale Data Handling**
```json
{
    "query_settings": {
        "max_results": 50000,      // Increase for large datasets
        "page_size": 2000,         // Larger pages for enterprise
        "timeout_seconds": 600     // Longer timeout for complex queries
    }
}
```

### **Multiple Indices**
```json
{
    "indices": [
        "main", "security", "network", "firewall", 
        "proxy", "windows", "linux", "application",
        "web", "database", "cloud"
    ]
}
```

### **Custom Vendor Patterns**
Add your organization's specific vendors:
```json
{
    "custom_vendor_patterns": {
        "custom_security_vendor": ["pattern1", "pattern2"],
        "internal_tool": ["company_internal_*"],
        "legacy_system": ["old_system_identifier"]
    }
}
```

## 🚀 Setup Steps for Enterprise

### **1. Get Required Information**
From your Splunk admin, obtain:
- Splunk server URL and port
- HEC token OR username/password
- List of available indices
- SSL certificate requirements
- Network access details (VPN, proxy)

### **2. Update Configuration**
```bash
# Edit the configuration file
nano config/environments.json

# Add your enterprise environment details
```

### **3. Test Connectivity**
```bash
# Test network connectivity
curl -k https://your-splunk.com:8089/services/server/info

# Test with credentials
curl -k https://your-splunk.com:8089/services/server/info \
  -u username:password
```

### **4. Launch and Connect**
```bash
uv run jupyter lab vendor-analysis.ipynb
```

## 📋 Example Enterprise Configurations

### **Large Corporation**
```json
{
    "corp_prod": {
        "name": "Corporate Production",
        "hec_url": "https://splunk.internal.corp.com:8089/services/search/jobs",
        "token": "ABCD1234-5678-90EF-GHIJ-KLMNOPQRSTUV",
        "indices": [
            "main", "security", "network", "firewall", "proxy",
            "windows", "linux", "application", "database", "web"
        ],
        "default_time_range": "-30d@d",
        "verify_ssl": true,
        "description": "Corporate production environment with comprehensive logging"
    }
}
```

### **Multi-Site Deployment**
```json
{
    "site_east": {
        "name": "East Coast Data Center",
        "hec_url": "https://splunk-east.company.com:8089/services/search/jobs",
        "token": "EAST-TOKEN-HERE",
        "indices": ["main", "security", "network"],
        "verify_ssl": true
    },
    "site_west": {
        "name": "West Coast Data Center", 
        "hec_url": "https://splunk-west.company.com:8089/services/search/jobs",
        "token": "WEST-TOKEN-HERE",
        "indices": ["main", "security", "network"],
        "verify_ssl": true
    }
}
```

### **Splunk Cloud**
```json
{
    "splunk_cloud": {
        "name": "Splunk Cloud Production",
        "hec_url": "https://mycompany.splunkcloud.com:8089/services/search/jobs",
        "token": "CLOUD-TOKEN-HERE",
        "indices": ["main", "security"],
        "verify_ssl": true,
        "description": "Splunk Cloud Platform instance"
    }
}
```

## 🔍 Troubleshooting Enterprise Issues

### **Common Network Issues**

#### **Connection Timeout**
```bash
# Check network connectivity
telnet your-splunk.com 8089

# Check DNS resolution
nslookup your-splunk.com
```

#### **SSL Certificate Issues**
- Set `"verify_ssl": false` for testing
- Contact admin for proper certificates
- Use corporate CA bundle if required

#### **Proxy Issues**
- Configure system proxy settings
- May need to modify Python requests configuration

### **Authentication Problems**

#### **Invalid Token**
- Verify token in Splunk Web UI: Settings > Data Inputs > HTTP Event Collector
- Ensure token is enabled and has proper permissions
- Check token expiration

#### **Permission Denied**
- Verify user has search permissions on target indices
- Check role-based access controls
- Ensure REST API access is enabled

### **Performance Optimization**

#### **Large Datasets**
- Reduce time range initially (`-1h@h`, `-6h@h`)
- Use specific indices instead of all indices
- Implement custom filters to narrow search scope

#### **Slow Queries**
- Increase timeout settings
- Use pagination with smaller page sizes
- Run during off-peak hours

## ✅ Success Indicators

Your enterprise setup is working when:

1. ✅ Connection test passes in Jupyter notebook
2. ✅ You can see data from your enterprise indices
3. ✅ Vendor detection finds your organization's security tools
4. ✅ Gap analysis shows realistic coverage assessment
5. ✅ Export functions create usable reports for stakeholders

## 📞 Getting Help

For enterprise deployments:
1. **Work with your Splunk admin** for proper credentials and access
2. **Test network connectivity** before running analysis
3. **Start with limited time ranges** for initial testing
4. **Use built-in troubleshooting** in the Jupyter notebook

The tool is designed to scale from single Docker instances to enterprise Splunk deployments with terabytes of data! 🚀