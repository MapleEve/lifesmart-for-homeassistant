# LifeSmart Integration Troubleshooting Guide

This guide helps you resolve common issues with the LifeSmart Home Assistant integration.

## 🚨 Quick Issue Resolution

### Step 1: Generate Diagnostics Data
Before reporting any issue, please generate diagnostics data:

1. Go to **Settings** → **Devices & Services** → **LifeSmart**
2. Click **"Download diagnostics"** button
3. Save the generated `.json` file
4. For device-specific issues: Go to specific device page → Click **"Download diagnostics"**

### Step 2: Check Common Issues Below
Review the common problems and solutions below before creating an issue report.

---

## 🔌 Connection Issues

### Cloud Connection Problems
**Symptoms:** Integration fails to connect, shows "Authentication failed" or "API error"

**Solutions:**
1. **Check credentials:** Verify your AppKey, AppToken, and UserToken are correct
2. **Region settings:** Ensure the correct region is selected (China, North America, Europe, etc.)
3. **Token expiry:** Tokens may expire - try re-authentication
4. **Network access:** Confirm Home Assistant can reach LifeSmart cloud servers

### Local Connection Problems  
**Symptoms:** Local mode connection timeouts, "Unable to connect to gateway"

**Solutions:**
1. **Network connectivity:** Verify Home Assistant and LifeSmart gateway are on same network
2. **IP/Port settings:** Confirm gateway IP address and port (usually 8888)
3. **Gateway status:** Check if gateway is powered on and functioning
4. **Firewall:** Ensure no firewall blocking connections

---

## ⚙️ Device Issues

### Devices Show as "Unavailable"
**Symptoms:** Devices appear in HA but show "Unavailable" status

**Common Causes:**
- Device is powered off or disconnected from gateway
- Network connectivity issues between device and gateway
- Device firmware problems
- Gateway connection problems

**Solutions:**
1. Check device power and network status
2. Restart the LifeSmart gateway
3. Re-add the device in LifeSmart app first
4. Reload the integration in Home Assistant

### Device State Not Updating
**Symptoms:** Device status in HA doesn't match actual device state

**Solutions:**
1. **Check WebSocket connection:** In diagnostics data, verify `client_status.connected: true`
2. **Manual refresh:** Use "Reload Integration" in HA
3. **Device exclusion:** Check if device is in exclusion list (integration options)
4. **Gateway communication:** Verify device communicates properly with gateway

### Missing Devices
**Symptoms:** Some devices don't appear in Home Assistant

**Solutions:**
1. **Exclusion filters:** Check integration options for excluded devices/hubs
2. **Device compatibility:** Verify device is supported (check device specs documentation)
3. **Gateway registration:** Ensure device is properly registered in LifeSmart app
4. **Integration reload:** Reload the integration to rediscover devices

---

## 🚀 Performance Issues

### Slow Response Times
**Symptoms:** Device commands take long time to execute

**Diagnostics Check:**
- Review `concurrency_stats` in diagnostics data
- High queue counts indicate system overload

**Solutions:**
1. **Reduce device count:** Consider excluding unnecessary devices
2. **Network optimization:** Improve network connection quality
3. **Resource allocation:** Ensure adequate system resources for Home Assistant

### High Memory Usage
**Symptoms:** Home Assistant consuming excessive memory

**Diagnostics Check:**
- Look for `problematic_devices` in diagnostics data
- High device counts with errors

**Solutions:**
1. **Clean problematic devices:** Remove or fix devices causing errors
2. **Device limit:** Consider reducing total device count
3. **Integration restart:** Restart Home Assistant to clear memory leaks

---

## 🔧 Advanced Diagnostics

### Understanding Diagnostics Data

Key fields to check in your diagnostics file:

```json
{
  "hub_info": {
    "device_count": 150,        // Total managed devices
    "hub_count": 2,            // Number of LifeSmart gateways
    "connected": true          // Connection status
  },
  "client_status": {
    "client_type": "LifeSmartOpenAPIClient",  // Connection type
    "connected": true                         // Current connection state
  },
  "concurrency_stats": {
    "active_operations": 2,    // Current operations
    "queue_size": 0           // Pending operations
  },
  "problematic_devices": {     // Devices with issues
    "SL_SW_DM1": {
      "count": 5,             // Error count
      "last_seen": "2024-08-10 10:30:15"
    }
  }
}
```

### Performance Monitoring
- **Normal operation:** `active_operations` < 10, `queue_size` < 5
- **Performance issues:** High queue sizes, many active operations
- **Problem devices:** Any entries in `problematic_devices` indicate devices needing attention

---

## 📋 Before Reporting Issues

When creating a GitHub issue, please:

1. ✅ **Attach diagnostics data** (integration-level and device-level if applicable)
2. ✅ **Check this troubleshooting guide** first
3. ✅ **Search existing issues** for similar problems
4. ✅ **Provide specific details:**
   - Device model and type
   - Expected vs actual behavior  
   - Steps to reproduce
   - Home Assistant version
   - Integration version

---

## 🆘 Getting Help

- **GitHub Issues:** [Create new issue](https://github.com/MapleEve/lifesmart-HACS-for-hass/issues/new/choose)
- **Documentation:** Check device specifications in `/docs/` folder
- **Community:** Home Assistant Community forums

Remember: Diagnostics data is crucial for quick problem resolution! 📊