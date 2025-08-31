# API Key Configuration Solution

## The Problem
Dora doesn't pass environment variables from the parent shell to spawned nodes. When using `api_key = "env:OPENAI_API_KEY"` in the config, the node process doesn't have access to your shell's environment variables.

## The Solution: Local Config File

Since environment variables don't work reliably with Dora, we use a local config file approach:

1. **Template Config** (`maas_mcp_browser_config.toml`) - Uses `env:OPENAI_API_KEY` placeholder
2. **Local Config** (`maas_browser_local.toml`) - Contains your actual API key (gitignored)
3. **Local YAML** (`voice-chat-browser-local.yml`) - Points to the local config

## Quick Setup

### Option 1: Automated Setup (Recommended)
```bash
# Run the setup script
./setup_local_config.sh

# Enter your API key when prompted
# This creates:
#   - maas_browser_local.toml (with your key)
#   - voice-chat-browser-local.yml (uses local config)

# Start the system
dora up
dora start voice-chat-browser-local.yml
```

### Option 2: Manual Setup
```bash
# 1. Copy the template
cp maas_mcp_browser_config.toml maas_browser_local.toml

# 2. Edit the local config
nano maas_browser_local.toml
# Replace: api_key = "env:OPENAI_API_KEY"
# With:    api_key = "sk-your-actual-key"

# 3. Update the YAML to use local config
# In voice-chat-with-browser.yml, change:
#   CONFIG: maas_mcp_browser_config.toml
# To:
#   CONFIG: maas_browser_local.toml

# 4. Start
dora up
dora start voice-chat-with-browser.yml
```

## Security

The local config approach is secure because:
- ✅ `*_local.toml` files are gitignored
- ✅ API keys stay on your local machine
- ✅ Easy to have different keys per environment
- ✅ No risk of accidental commits

## File Structure

```
mac-aec-chat/
├── maas_mcp_browser_config.toml    # Template (committed, uses env:)
├── maas_browser_local.toml         # Your config (gitignored, has real key)
├── voice-chat-with-browser.yml     # Original YAML (uses template)
├── voice-chat-browser-local.yml    # Local YAML (uses local config)
└── .gitignore                       # Ignores *_local.toml files
```

## Why Not Environment Variables?

Environment variables would be ideal, but Dora's architecture makes this challenging:
1. Dora daemon runs as a separate process
2. Nodes are spawned as child processes of the daemon
3. Environment variables from your shell don't propagate to the nodes

Future Dora versions may support environment variable passthrough, but for now, the local config approach is the most reliable solution.

## Troubleshooting

### Error: "Environment variable OPENAI_API_KEY not found"
You're using the template config. Run `./setup_local_config.sh` to create a local config.

### Error: "Invalid API key"
Check your key in `maas_browser_local.toml`

### Want to change your API key?
```bash
# Re-run setup
./setup_local_config.sh

# Or manually edit
nano maas_browser_local.toml
```

## Best Practices

1. **Never commit local configs**
   - Already handled by .gitignore
   
2. **Use different configs for different purposes**
   - `maas_browser_local.toml` - Browser automation
   - `maas_weather_local.toml` - Weather only
   - `maas_dev_local.toml` - Development testing

3. **Rotate keys regularly**
   - Create new keys periodically
   - Update local configs
   - Revoke old keys

## Summary

✅ Use `setup_local_config.sh` for easy setup
✅ Local configs are gitignored for security
✅ Works reliably with Dora's architecture
✅ API keys are secure and won't be committed