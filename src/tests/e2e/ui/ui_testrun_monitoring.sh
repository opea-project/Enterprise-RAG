#!/bin/bash
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# UI Test Monitoring Control Script
# Manages Xvfb, x11vnc, and noVNC services for UI test debugging

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DISPLAY_NUM=99
VNC_PORT=5900
NOVNC_PORT=6080
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
SCREEN_RESOLUTION="${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24"

show_usage() {
    echo "Usage: $0 {start|stop|status|restart} [options]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all UI monitoring services"
    echo "  stop      - Stop all UI monitoring services"
    echo "  status    - Check status of monitoring services"
    echo "  restart   - Restart all monitoring services"
    echo ""
    echo "Options:"
    echo "  --display N      - Use display :N (default: 99)"
    echo "  --vnc-port N     - Use VNC port N (default: 5900)"
    echo "  --novnc-port N   - Use noVNC port N (default: 6080)"
    echo "  --resolution WxH - Screen resolution WIDTHxHEIGHT (default: 1920x1080)"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 restart"
    echo "  $0 start --display 100 --novnc-port 6081"
    echo "  $0 start --resolution 1280x720"
    echo "  $0 start --resolution 2560x1440 --display 100"
}

check_service() {
    local service_pattern="$1"
    if pgrep -f "$service_pattern" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

show_status() {
    echo -e "${BLUE}UI Monitoring Services Status:${NC}"
    echo "================================"
    echo -e "Configuration:"
    echo "  - Display: :${DISPLAY_NUM}"
    echo "  - Resolution: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"
    echo "  - VNC Port: ${VNC_PORT}"
    echo "  - noVNC Port: ${NOVNC_PORT}"
    echo ""
    
    # Check Xvfb
    if check_service "Xvfb :${DISPLAY_NUM}"; then
        echo -e "Xvfb (display :${DISPLAY_NUM}): ${GREEN}RUNNING${NC}"
    else
        echo -e "Xvfb (display :${DISPLAY_NUM}): ${RED}STOPPED${NC}"
    fi
    
    # Check x11vnc
    if check_service "x11vnc.*:${DISPLAY_NUM}"; then
        echo -e "x11vnc (port ${VNC_PORT}):    ${GREEN}RUNNING${NC}"
    else
        echo -e "x11vnc (port ${VNC_PORT}):    ${RED}STOPPED${NC}"
    fi
    
    # Check noVNC
    if check_service "novnc"; then
        echo -e "noVNC (port ${NOVNC_PORT}):    ${GREEN}RUNNING${NC}"
        echo ""
        echo -e "${YELLOW}Access via:${NC}"
        echo "  - Browser: http://localhost:${NOVNC_PORT}/vnc.html"
        echo "  - SSH tunnel: ssh -L ${NOVNC_PORT}:localhost:${NOVNC_PORT} user@remote-host"
    else
        echo -e "noVNC (port ${NOVNC_PORT}):    ${RED}STOPPED${NC}"
    fi
    echo "================================"
}

start_services() {
    echo -e "${GREEN}Starting UI monitoring services...${NC}"
    echo "Configuration: Display :${DISPLAY_NUM}, Resolution: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"
    echo ""
    
    # Start Xvfb on display :99
    if check_service "Xvfb :${DISPLAY_NUM}"; then
        echo -e "${YELLOW}Xvfb already running on display :${DISPLAY_NUM}${NC}"
    else
        echo "Starting Xvfb on display :${DISPLAY_NUM}..."
        Xvfb :${DISPLAY_NUM} -screen 0 ${SCREEN_RESOLUTION} &
        sleep 2
        if check_service "Xvfb :${DISPLAY_NUM}"; then
            echo -e "${GREEN}✓ Xvfb started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start Xvfb${NC}"
            return 1
        fi
    fi
    
    # Start x11vnc
    if check_service "x11vnc.*:${DISPLAY_NUM}"; then
        echo -e "${YELLOW}x11vnc already running${NC}"
    else
        echo "Starting x11vnc on port ${VNC_PORT}..."
        x11vnc -display :${DISPLAY_NUM} -forever -shared -rfbport ${VNC_PORT} &
        sleep 2
        if check_service "x11vnc.*:${DISPLAY_NUM}"; then
            echo -e "${GREEN}✓ x11vnc started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start x11vnc${NC}"
            return 1
        fi
    fi
    
    # Start noVNC
    if check_service "novnc"; then
        echo -e "${YELLOW}noVNC already running${NC}"
    else
        echo "Starting noVNC on port ${NOVNC_PORT}..."
        /usr/share/novnc/utils/novnc_proxy --vnc localhost:${VNC_PORT} --listen ${NOVNC_PORT} &
        sleep 2
        if check_service "novnc"; then
            echo -e "${GREEN}✓ noVNC started successfully${NC}"
        else
            echo -e "${RED}✗ Failed to start noVNC${NC}"
            return 1
        fi
    fi
    
    echo ""
    echo -e "${GREEN}UI monitoring started successfully!${NC}"
    echo -e "${YELLOW}Access via browser:${NC} http://localhost:${NOVNC_PORT}/vnc.html"
    echo -e "${YELLOW}Or via SSH tunnel:${NC} ssh -L ${NOVNC_PORT}:localhost:${NOVNC_PORT} user@remote-host"
}

stop_services() {
    echo -e "${YELLOW}Stopping UI monitoring services...${NC}"
    
    local stopped_any=0
    
    # Stop noVNC (first, as it depends on x11vnc)
    if check_service "novnc"; then
        echo "Stopping noVNC..."
        pkill -f "novnc"
        sleep 1
        if ! check_service "novnc"; then
            echo -e "${GREEN}✓ noVNC stopped${NC}"
            stopped_any=1
        else
            echo -e "${RED}✗ Failed to stop noVNC${NC}"
        fi
    else
        echo "noVNC not running"
    fi
    
    # Stop x11vnc
    if check_service "x11vnc"; then
        echo "Stopping x11vnc..."
        pkill -f "x11vnc"
        sleep 1
        if ! check_service "x11vnc"; then
            echo -e "${GREEN}✓ x11vnc stopped${NC}"
            stopped_any=1
        else
            echo -e "${RED}✗ Failed to stop x11vnc${NC}"
        fi
    else
        echo "x11vnc not running"
    fi
    
    # Stop Xvfb (last, as others depend on it)
    if check_service "Xvfb :${DISPLAY_NUM}"; then
        echo "Stopping Xvfb..."
        pkill -f "Xvfb :${DISPLAY_NUM}"
        sleep 1
        if ! check_service "Xvfb :${DISPLAY_NUM}"; then
            echo -e "${GREEN}✓ Xvfb stopped${NC}"
            stopped_any=1
        else
            echo -e "${RED}✗ Failed to stop Xvfb${NC}"
        fi
    else
        echo "Xvfb not running"
    fi
    
    if [ $stopped_any -eq 1 ]; then
        echo -e "${GREEN}UI monitoring stopped successfully!${NC}"
    else
        echo -e "${YELLOW}No services were running${NC}"
    fi
}

restart_services() {
    echo -e "${BLUE}Restarting UI monitoring services...${NC}"
    stop_services
    sleep 2
    start_services
}

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --display)
            DISPLAY_NUM="$2"
            shift 2
            ;;
        --vnc-port)
            VNC_PORT="$2"
            shift 2
            ;;
        --novnc-port)
            NOVNC_PORT="$2"
            shift 2
            ;;
        --resolution)
            # Parse resolution in format WIDTHxHEIGHT (e.g., 1920x1080)
            if [[ "$2" =~ ^([0-9]+)x([0-9]+)$ ]]; then
                SCREEN_WIDTH="${BASH_REMATCH[1]}"
                SCREEN_HEIGHT="${BASH_REMATCH[2]}"
                SCREEN_RESOLUTION="${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24"
                shift 2
            else
                echo -e "${RED}Error: Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1920x1080)${NC}"
                exit 1
            fi
            ;;
        start|stop|status|restart)
            COMMAND="$1"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
if [ -z "$COMMAND" ]; then
    echo -e "${RED}Error: No command specified${NC}"
    echo ""
    show_usage
    exit 1
fi

case $COMMAND in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    restart)
        restart_services
        ;;
    *)
        echo -e "${RED}Error: Invalid command: $COMMAND${NC}"
        show_usage
        exit 1
        ;;
esac
