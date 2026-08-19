# Upgrading Omni Icon Vault

## 4.0.x → 4.1.0

The 4.1 upgrade changes the browser and local API but keeps canonical icon IDs, the localhost port, the Figma manifest path and the project-manifest format compatible.

### From a release ZIP

1. Stop Omni if it is running:

   ```bash
   omni-icons stop
   ```

2. Extract the 4.1.0 release into a new folder (recommended), or replace the core files in the existing installation.
3. Run the platform installer again:

   Windows:

   ```text
   INSTALL_WINDOWS.cmd
   ```

   macOS:

   ```bash
   ./INSTALL_MAC.command
   ```

   Linux:

   ```bash
   ./INSTALL_LINUX.sh
   ```

4. Verify and open:

   ```bash
   omni-icons doctor
   omni-icons open
   ```

### From a Git checkout

```bash
git pull
python install.py
omni-icons doctor
omni-icons open
```

### Figma

The plugin manifest is still:

```text
figma-plugin/manifest.json
```

If Figma already has the development plugin imported, reopen it after Omni 4.1 is installed. If Figma still shows an older cached UI, remove and re-import the development plugin once.

### User data

Browser favorites/theme/density are stored in the browser profile. Custom SVGs and collected favicons live in the Omni installation data folders; back them up before replacing an installation directory if you have added local assets.
