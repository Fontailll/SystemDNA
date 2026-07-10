# Configuration

## Configuration File Format

SystemDNA reads configuration from `~/.config/SystemDNA/config.json`. The file is JSON with the following structure:

```json
{
  "storage_dir": "/home/user/.local/share/SystemDNA",
  "snapshots_dir": "/home/user/.local/share/SystemDNA/snapshots",
  "plugins_enabled": true,
  "plugin_dirs": [],
  "log_level": "WARNING",
  "max_snapshots": 100
}
```

If the file does not exist, default values are used and the file is created.

## Available Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `storage_dir` | string | `~/.local/share/SystemDNA` | Base directory for all SystemDNA data |
| `snapshots_dir` | string | `{storage_dir}/snapshots` | Directory where snapshot JSON files are stored |
| `plugins_enabled` | boolean | `true` | Whether to load plugins on startup |
| `plugin_dirs` | array of strings | `[]` | Directories to scan for plugin modules |
| `log_level` | string | `"WARNING"` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `max_snapshots` | integer | `100` | Maximum number of snapshots to retain (not enforced automatically yet) |

## CLI Commands

- `systemdna config show` — display current configuration
- `systemdna config set <key> <value>` — set a configuration value
- `systemdna config path` — show config file and storage directory paths
- `systemdna config reset` — reset configuration to defaults

## Storage Location

- **Configuration directory**: `$XDG_CONFIG_HOME/SystemDNA/` (defaults to `~/.config/SystemDNA/`)
- **Configuration file**: `$XDG_CONFIG_HOME/SystemDNA/config.json`
- **Storage directory**: `~/.local/share/SystemDNA/`
- **Snapshots directory**: `~/.local/share/SystemDNA/snapshots/`

## Environment Variables

SystemDNA does not use environment variables for configuration. All settings are read from the config file or set via CLI commands.
