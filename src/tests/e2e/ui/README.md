# UI Automated Testing Guide

Please read main test [docummentation](../validation/README.md) first.

This project uses **Playwright** test framework for **UI** automated tests along with **Pytest**, **Tox** and integrated with **Allure** for report.

## Prerequisites

In addition to E2E test requirements and installation steps peovided [here](../validation/README.md) you need to install packages required to execute UI tests.

The following system packages must be installed for headless mode:

```bash
sudo apt-get update
sudo apt-get install -y \
    xvfb \
    python3-pip \
    firefox

# Install Playwright browser dependencies (required)
sudo playwright install-deps firefox
```

The following system packages must be installed additonally for non-headless mode:

```bash
sudo apt-get update
sudo apt-get install -y \
    x11vnc \
    novnc \
```

**Package Descriptions:**
- `xvfb`: is virtual framebuffer used for testing
- `firefox`: web browser used by Playwright
- `playwright install-deps`: system libraries required by Playwright (libgtk, libpango, etc.)
- `x11vnc`: VNC server for remote viewing
- `novnc`: Browser-based VNC client
---

## Running the UI Tests

### Dependencies installation

Navigate to the src/tests/ directory and install dependencie:
```bash
tox -e e2e-ui --notest
```

### Running the UI Tests

## UI Monitoring Setup

UI monitoring allows you to view browser actions in real-time during test execution. This is useful for debugging and demonstration purposes.

### Using the UI Monitoring Script

From the `/src/tests/e2e/ui` directory, use the unified monitoring script:

```bash
./ui_testrun_monitoring.sh {start|stop|status|restart} [options]
```

**Available Commands:**

- `start` - Start all UI monitoring services
- `stop` - Stop all UI monitoring services  
- `status` - Check status of monitoring services
- `restart` - Restart all monitoring services

**Available Options:**

- `--display N` - Use display :N (default: 99)
- `--vnc-port N` - Use VNC port N (default: 5900)
- `--novnc-port N` - Use noVNC port N (default: 6080)
- `--resolution WxH` - Screen resolution WIDTHxHEIGHT (default: 1920x1080)

### Starting UI Monitoring

**Basic start:**
```bash
./ui_testrun_monitoring.sh start
```

**Start with custom resolution:**
```bash
./ui_testrun_monitoring.sh start --resolution 1280x720
./ui_testrun_monitoring.sh start --resolution 2560x1440
```

**Start with custom configuration:**
```bash
./ui_testrun_monitoring.sh start --display 100 --novnc-port 6081
./ui_testrun_monitoring.sh start --resolution 2560x1440 --display 100
```

The script will:

1. Start Xvfb on display `:99` (virtual display) with specified resolution
2. Start x11vnc VNC server on port `5900`
3. Start noVNC web interface on port `6080`

**Expected Output:**

```text
Starting UI monitoring services...
Configuration: Display :99, Resolution: 1920x1080

Starting Xvfb on display :99...
✓ Xvfb started successfully
Starting x11vnc on port 5900...
✓ x11vnc started successfully
Starting noVNC on port 6080...
✓ noVNC started successfully

UI monitoring started successfully!
Access via browser: http://localhost:6080/vnc.html
```

### Checking Status

To verify services are running and view current configuration:

```bash
./ui_testrun_monitoring.sh status
```

**Expected Output:**

```text
UI Monitoring Services Status:
================================
Configuration:
  - Display: :99
  - Resolution: 1920x1080
  - VNC Port: 5900
  - noVNC Port: 6080

Xvfb (display :99): RUNNING
x11vnc (port 5900):    RUNNING
noVNC (port 6080):    RUNNING
================================
```

### Stopping UI Monitoring

When you're done with testing:

```bash
./ui_testrun_monitoring.sh stop
```

This will stop all monitoring services (noVNC, x11vnc, and Xvfb).

### Restarting UI Monitoring

To restart services (useful when changing configuration):

```bash
./ui_testrun_monitoring.sh restart
./ui_testrun_monitoring.sh restart --resolution 1280x720
```

## Running Tests

### Headless Mode (Default)

Run tests without a visible browser window (fastest):

```bash
cd /src/tests
tox -e e2e-ui -- e2e/ui/ -v
```

**Run specific test:**
```bash
tox -e e2e-ui -- e2e/ui/test_admin_login.py -v
tox -e e2e-ui -- e2e/ui/test_user_login.py -v
```


**Run all UI tests:**
```bash
cd src/tests
tox -e e2e-ui -- e2e/ui/ -v
```

**Run a specific test file:**
```bash
tox -e e2e-ui -- e2e/ui/test_admin_login.py -v
```

**Run a specific test function:**
```bash
tox -e e2e-ui -- e2e/ui/test_chat_prompting.py::test_single_prompt_response -v
```

**Run tests matching a pattern (using -k flag):**
```bash
# Run all tests with "admin" in the name
tox -e e2e-ui -- e2e/ui/ -k admin -v

# Run all tests with "chat" in the name
tox -e e2e-ui -- e2e/ui/ -k chat -v

# Run all tests with "quality" in the name
tox -e e2e-ui -- e2e/ui/ -k quality -v
```

### Non-Headless Mode (Visual)

Run tests with a visible browser (requires UI monitoring to be running):

**Step 1: Start UI monitoring first**
```bash
cd /src/tests/e2e/ui
./start_ui_monitoring.sh
```

**Step 2: Run tests with DISPLAY and HEADLESS=false**
```bash
cd /src/tests
HEADLESS=false DISPLAY=:99 tox -e e2e-ui -- e2e/ui/ -v
```

**Run specific test in non-headless mode:**
```bash
HEADLESS=false DISPLAY=:99 tox -e e2e-ui -- e2e/ui/test_admin_login.py -v
HEADLESS=false DISPLAY=:99 tox -e e2e-ui -- e2e/ui/test_user_login.py -v
```

## Remote Viewing via VNC

When running tests in non-headless mode, you can view the browser in real-time using VNC.

### Local Access (on the test machine)

Open a web browser and navigate to:
```
http://localhost:6080/vnc.html
```

Click "Connect" to view the virtual display where Firefox is running.

### Remote Access (via SSH Tunnel)

If you're accessing a remote test server, create an SSH tunnel:

**From your local machine:**
```bash
ssh -L 6080:localhost:6080 user@remote-test-server
```

Replace:
- `user`: Your username on the remote server
- `remote-test-server`: IP address or hostname of the test server

**Example:**
```bash
ssh -L 6080:localhost:6080 root@192.168.1.100
```

Then open your local browser to:
```
http://localhost:6080/vnc.html
```

### VNC Tips

- **Full screen**: Click the VNC toolbar icon in the top-left
- **Clipboard**: Use the clipboard icon to copy/paste text
- **Quality**: Adjust in the VNC settings if needed
- **Disconnect**: Simply close the browser tab

---

## Configuration

### Environment Variables

The following environment variables control test behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run browser in headless mode |
| `DISPLAY` | `:99` | X display for browser (when HEADLESS=false) |

## Project Structure & Best Practices
### Test Location
All UI tests are stored in the src/tests/e2e/ui directory. Each module should be named according to the component being tested. Example:

```
test_admin_login.py
test_chat_prompting.py
test_chat_response_quality.py
```

This naming convention helps with clarity and maintainability.

### UI Helpers and Fixtures
UI specyfic fixtures are defined in `src/tests/ui/conftest.py`, and UI utilities are organized in `src/tests/helpers/ui_helper.py`.
