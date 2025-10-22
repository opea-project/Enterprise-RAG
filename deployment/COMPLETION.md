# Installer.sh Auto-Completion

This directory contains shell auto-completion scripts for `installer.sh` located in the `scripts/` subdirectory to provide tab completion for commands, options, and file paths.

## Available Scripts

- **`scripts/installer-completion.bash`** - Bash completion script
- **`scripts/_installer.sh`** - Zsh completion script (underscore prefix is zsh convention)

## Features

- ✅ **Proper completion flow**: component → action → flags (no premature flag suggestions)
- ✅ Complete component names (`setup`, `validate`, `cluster`, `application`, `stack`)
- ✅ Complete action names based on selected component
- ✅ Complete option flags **only after** component and action are specified
- ✅ Complete file paths for `--config` (YAML files) and `--inventory` (INI files)
- ✅ Suggest common values for `--tag` (latest, v1.5.0, v1.4.0, v1.3.0, custom, dev)
- ✅ Suggest common registries for `--registry` (docker.io/opea, localhost:5000, localhost:32000, ghcr.io, quay.io)
- ✅ Suggest common directory names for `setup config` (inventory/cluster, inventory/prod, inventory/dev, inventory/test)
- ✅ Auto-detect existing inventory directories and suggest them
- ✅ Support for both `--option value` and `--option=value` formats
- ✅ Flags only appear when typing `--` (prevents clutter)

## Installation

### For Bash

**Option 1: Source in current session (temporary)**
```bash
cd deployment
source scripts/installer-completion.bash
```

**Option 2: Add to your ~/.bashrc (permanent)**
```bash
echo "source $(pwd)/scripts/installer-completion.bash" >> ~/.bashrc
source ~/.bashrc
```

**Option 3: System-wide installation**
```bash
sudo cp scripts/installer-completion.bash /etc/bash_completion.d/installer
# Restart your shell or source it
```

### For Zsh

**Option 1: Source in current session (temporary - quick start)**
```bash
cd deployment
source scripts/_installer.sh
# Completion is now active for ./installer.sh and installer.sh
```

**Option 2: Add to fpath (recommended for permanent use)**
```bash
# Create completion directory if it doesn't exist
mkdir -p ~/.zsh/completion

# Copy the completion script
cp scripts/_installer.sh ~/.zsh/completion/

# Add to ~/.zshrc (if not already present)
echo 'fpath=(~/.zsh/completion $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc

# Reload zsh configuration
source ~/.zshrc
```

**Option 3: Add to ~/.zshrc for direct sourcing (alternative)**
```bash
echo "source $(pwd)/scripts/_installer.sh" >> ~/.zshrc
source ~/.zshrc
```

**Option 4: System-wide installation**
```bash
# Find your zsh completion directory
echo $fpath

# Copy to one of the directories (e.g., /usr/local/share/zsh/site-functions)
sudo cp scripts/_installer.sh /usr/local/share/zsh/site-functions/

# Reload completions
rm -f ~/.zcompdump
exec zsh
```

## Usage Examples

Once installed, you can use tab completion:

```bash
# Complete components
./installer.sh <TAB>
# Shows: setup  validate  cluster  application  stack  --config  --inventory  -h  --help

# Complete actions for a component
./installer.sh setup <TAB>
# Shows: python-env  configure  images  config  info

# Complete config files (dynamically detects available directories)
./installer.sh stack deploy-complete --config=<TAB>
# Shows: inventory/sample/config.yaml  inventory/cluster/config.yaml  inventory/prod/config.yaml ...

# Complete inventory files (dynamically detects available directories)
./installer.sh application install --inventory=<TAB>
# Shows: inventory/sample/inventory.ini  inventory/localhost/inventory.ini  inventory/cluster/inventory.ini ...

# Complete directory names for new configurations
./installer.sh setup config <TAB>
# Shows: inventory/cluster  inventory/prod  inventory/dev  inventory/test  (plus any directories)

# Complete tag values
./installer.sh setup images --tag=<TAB>
# Shows: latest  v1.5.0  v1.4.0  v1.3.0  custom  dev

# Complete registry URLs
./installer.sh setup images --registry=<TAB>
# Shows: docker.io/opea  localhost:5000  localhost:32000  ghcr.io  quay.io

# Complete options
./installer.sh application install --<TAB>
# Shows: --config  --inventory  --tag  --registry  --non-interactive  -v  -vv  -vvv
```

## Troubleshooting

### Bash: Completion not working

1. Check if bash-completion is installed:
   ```bash
   apt list --installed | grep bash-completion
   # If not installed: sudo apt install bash-completion
   ```

2. Verify the script is sourced:
   ```bash
   type _installer_completion
   # Should show: "_installer_completion is a function"
   ```

3. Re-source your shell configuration:
   ```bash
   source ~/.bashrc
   ```

### Zsh: Completion not working

1. Check if compinit is loaded:
   ```bash
   echo $fpath
   # Should show your completion directories
   ```

2. Rebuild completion cache:
   ```bash
   rm -f ~/.zcompdump
   autoload -Uz compinit && compinit
   ```

3. Verify the function is loaded:
   ```bash
   which _installer_sh
   # Should show the function location
   ```

4. Check for conflicts:
   ```bash
   # Remove any cached completions
   rm -f ~/.zcompdump*
   exec zsh
   ```

## Customization

You can modify the completion scripts to add:
- Additional custom tags in the `--tag` suggestions
- Your organization's registry URLs in the `--registry` suggestions
- Custom config/inventory file locations
- Additional directory names for `setup config`

Edit the respective completion file and update the completion arrays:

**Bash (`scripts/installer-completion.bash`):**
```bash
# Add your custom tags
COMPREPLY=( $(compgen -W "latest v1.5.0 v1.4.0 v1.3.0 custom dev my-custom-tag" -- "$cur") )

# Add your custom registries
COMPREPLY=( $(compgen -W "docker.io/opea localhost:5000 my-registry.company.com:5000" -- "$cur") )

# Add your custom directory suggestions (in the config section)
local dir_suggestions="inventory/cluster inventory/prod inventory/staging inventory/qa"
```

**Zsh (`scripts/_installer.sh`):**
```zsh
# Add your custom tags
'--tag=[Docker image tag]:tag:(latest v1.5.0 v1.4.0 v1.3.0 custom dev my-custom-tag)'

# Add your custom registries
'--registry=[Docker registry URL]:registry:(docker.io/opea localhost:5000 my-registry.company.com:5000)'

# Add your custom directory suggestions
'3:suggested directories:(inventory/cluster inventory/prod inventory/staging inventory/qa)'
```

### Recommended Directory Structure

The completion scripts now support and suggest these common directory patterns:

- `inventory/cluster` - Default production cluster configuration
- `inventory/prod` - Production environment
- `inventory/dev` - Development environment
- `inventory/test` - Test/staging environment
- `inventory/sample` - Sample configuration (reference)
- `inventory/localhost` - Localhost-only deployment

The completion will automatically detect any of these directories if they exist and suggest them.

## Important Notes

### Zsh File Naming Convention

The zsh completion file is named `_installer.sh` (with underscore prefix) following the zsh convention:
- **In the repository**: `scripts/_installer.sh` - Can be sourced directly
- **In fpath directories**: Must have underscore prefix to be auto-discovered by zsh

When you source the file directly (`source scripts/_installer.sh`), it automatically registers the completion. When placed in an fpath directory, zsh auto-loads it based on the underscore prefix.

### Quick Start vs Permanent Installation

**Quick Start** (Bash and Zsh):
- Source the script in your current session
- Completion works immediately
- Lost when you close the terminal

**Permanent** (Bash):
- Add source command to `~/.bashrc`
- Or copy to `/etc/bash_completion.d/`

**Permanent** (Zsh):
- Copy to fpath directory (e.g., `~/.zsh/completion/`)
- Update `~/.zshrc` to include the directory in fpath
- Zsh auto-loads completion files starting with underscore

## Contributing

If you add new commands or options to `installer.sh`, please update the completion scripts accordingly to maintain a consistent user experience.
