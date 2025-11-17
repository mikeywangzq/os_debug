/**
 * GDB Client - WebSocket communication for real-time GDB debugging
 */

class GDBClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.callbacks = {};
        this.outputElement = document.getElementById('realtimeOutput');
    }

    /**
     * Initialize WebSocket connection
     */
    connect() {
        if (this.socket && this.socket.connected) {
            console.log('Already connected');
            return;
        }

        // Initialize Socket.IO connection
        this.socket = io({
            transports: ['websocket', 'polling']
        });

        // Register event handlers
        this.setupEventHandlers();

        console.log('Connecting to WebSocket server...');
    }

    /**
     * Setup all WebSocket event handlers
     */
    setupEventHandlers() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.updateStatus('connecting', 'Connecting...');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.updateStatus('disconnected', 'Disconnected');
            this.toggleQuickActions(false);
            document.getElementById('connectGdbBtn').disabled = false;
            document.getElementById('disconnectGdbBtn').disabled = true;
        });

        this.socket.on('connected', (data) => {
            console.log('Session created:', data.session_id);
        });

        // GDB events
        this.socket.on('gdb_started', (data) => {
            if (data.success) {
                this.appendMessage('success', 'GDB started successfully');
            } else {
                this.appendMessage('error', `Failed to start GDB: ${data.error}`);
            }
        });

        this.socket.on('gdb_connect_result', (data) => {
            if (data.success) {
                this.connected = true;
                this.updateStatus('connected', 'Connected');
                this.appendMessage('success', `Connected to target: ${data.message || 'Success'}`);
                this.toggleQuickActions(true);
                document.getElementById('connectGdbBtn').disabled = true;
                document.getElementById('disconnectGdbBtn').disabled = false;
            } else {
                this.updateStatus('disconnected', 'Connection Failed');
                this.appendMessage('error', `Connection failed: ${data.error}`);
            }
        });

        this.socket.on('gdb_disconnected', (data) => {
            this.connected = false;
            this.updateStatus('disconnected', 'Disconnected');
            this.appendMessage('info', 'Disconnected from GDB');
            this.toggleQuickActions(false);
            document.getElementById('connectGdbBtn').disabled = false;
            document.getElementById('disconnectGdbBtn').disabled = true;
        });

        // Real-time events
        this.socket.on('gdb_crash_detected', (data) => {
            this.handleCrashEvent(data);
        });

        this.socket.on('gdb_breakpoint_hit', (data) => {
            this.handleBreakpointEvent(data);
        });

        this.socket.on('gdb_console_output', (data) => {
            this.appendMessage('info', data.text, true);
        });

        this.socket.on('gdb_running', (data) => {
            this.appendMessage('info', 'Program running...');
        });

        this.socket.on('gdb_program_exited', (data) => {
            this.appendMessage('info', `Program exited with code ${data.exit_code}`);
        });

        // Command results
        this.socket.on('command_result', (data) => {
            if (data.success) {
                this.appendCommandResult(data);
            } else {
                this.appendMessage('error', `Command failed: ${data.error}`);
            }
        });

        this.socket.on('backtrace_result', (data) => {
            if (data.success) {
                this.displayBacktrace(data.frames);
            } else {
                this.appendMessage('error', 'Failed to get backtrace');
            }
        });

        this.socket.on('registers_result', (data) => {
            if (data.success) {
                this.displayRegisters(data.registers);
            } else {
                this.appendMessage('error', 'Failed to get registers');
            }
        });

        this.socket.on('breakpoint_result', (data) => {
            if (data.success) {
                this.appendMessage('success', `Breakpoint ${data.number} set at ${data.location}`);
            } else {
                this.appendMessage('error', 'Failed to set breakpoint');
            }
        });

        this.socket.on('error', (data) => {
            this.appendMessage('error', data.message || 'Unknown error');
        });
    }

    /**
     * Connect to GDB target
     */
    connectToTarget(target) {
        if (!this.socket || !this.socket.connected) {
            this.connect();
            // Wait for connection then try again
            setTimeout(() => this.connectToTarget(target), 1000);
            return;
        }

        this.updateStatus('connecting', 'Connecting...');
        this.socket.emit('gdb_connect', {
            target: target,
            auto_monitor: true
        });
    }

    /**
     * Disconnect from GDB
     */
    disconnect() {
        if (this.socket) {
            this.socket.emit('gdb_disconnect');
        }
    }

    /**
     * Execute a GDB command
     */
    executeCommand(command, type = 'cli') {
        if (!this.connected) {
            this.appendMessage('error', 'Not connected to GDB');
            return;
        }

        this.socket.emit('gdb_command', {
            command: command,
            type: type
        });
    }

    /**
     * Control commands
     */
    continue() {
        this.socket.emit('gdb_continue');
        this.appendMessage('info', 'Continuing execution...');
    }

    stepOver() {
        this.socket.emit('gdb_step_over');
        this.appendMessage('info', 'Stepping over...');
    }

    stepInto() {
        this.socket.emit('gdb_step_into');
        this.appendMessage('info', 'Stepping into...');
    }

    /**
     * Info commands
     */
    getBacktrace() {
        this.socket.emit('gdb_get_backtrace');
    }

    getRegisters() {
        this.socket.emit('gdb_get_registers');
    }

    setBreakpoint(location) {
        if (!location) {
            this.appendMessage('error', 'Breakpoint location not specified');
            return;
        }

        this.socket.emit('gdb_breakpoint', {
            location: location
        });
    }

    /**
     * Event handlers
     */
    handleCrashEvent(data) {
        this.appendMessage('crash', '⚠️ CRASH DETECTED ⚠️');

        if (data.signal) {
            this.appendMessage('error', `Signal: ${data.signal.name} - ${data.signal.meaning}`);
        }

        if (data.backtrace) {
            this.displayBacktrace(data.backtrace);
        }

        if (data.registers) {
            this.displayRegisters(data.registers);
        }

        // Automatically trigger analysis
        this.triggerAutomaticAnalysis(data);
    }

    handleBreakpointEvent(data) {
        this.appendMessage('warning', `🔴 Breakpoint ${data.breakpoint_number || '?'} hit`);

        if (data.backtrace) {
            this.displayBacktrace(data.backtrace);
        }
    }

    /**
     * Display functions
     */
    displayBacktrace(frames) {
        if (!frames || frames.length === 0) {
            return;
        }

        let html = '<div class="event-message event-info">';
        html += '<div class="event-timestamp">' + new Date().toLocaleTimeString() + '</div>';
        html += '<strong>Call Stack:</strong>';
        html += '<div class="event-content"><pre>';

        frames.forEach((frame, idx) => {
            const level = frame.level || idx;
            const func = frame.func || frame.function || '??';
            const addr = frame.addr || frame.address || '??';
            const file = frame.file || '';
            const line = frame.line || '';

            let frameStr = `#${level}  ${func} at ${addr}`;
            if (file) {
                frameStr += ` (${file}`;
                if (line) {
                    frameStr += `:${line}`;
                }
                frameStr += ')';
            }
            html += frameStr + '\n';
        });

        html += '</pre></div></div>';
        this.appendHTML(html);
    }

    displayRegisters(registers) {
        if (!registers || Object.keys(registers).length === 0) {
            return;
        }

        let html = '<div class="event-message event-info">';
        html += '<div class="event-timestamp">' + new Date().toLocaleTimeString() + '</div>';
        html += '<strong>Registers:</strong>';
        html += '<div class="event-content"><pre>';

        for (const [name, value] of Object.entries(registers)) {
            html += `${name.padEnd(8)} = ${value}\n`;
        }

        html += '</pre></div></div>';
        this.appendHTML(html);
    }

    appendCommandResult(data) {
        if (data.output) {
            this.appendMessage('info', data.output, true);
        } else if (data.responses) {
            // MI responses
            let output = JSON.stringify(data.responses, null, 2);
            this.appendMessage('info', output, true);
        }
    }

    /**
     * Trigger automatic analysis using the existing analyzer
     */
    triggerAutomaticAnalysis(crashData) {
        // Build debug text from crash data
        let debugText = '';

        if (crashData.signal) {
            debugText += `Signal: ${crashData.signal.name} - ${crashData.signal.meaning}\n\n`;
        }

        if (crashData.backtrace) {
            debugText += 'Backtrace:\n';
            crashData.backtrace.forEach(frame => {
                debugText += `#${frame.level} ${frame.func || '??'} at ${frame.addr || '??'}\n`;
            });
            debugText += '\n';
        }

        if (crashData.registers) {
            debugText += 'Registers:\n';
            for (const [name, value] of Object.entries(crashData.registers)) {
                debugText += `${name} = ${value}\n`;
            }
        }

        // Call the analysis API
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: debugText })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.displayAnalysisResults(result);
            }
        })
        .catch(error => {
            console.error('Analysis failed:', error);
            this.appendMessage('error', 'Automatic analysis failed');
        });
    }

    displayAnalysisResults(result) {
        let html = '<div class="event-message event-warning">';
        html += '<div class="event-timestamp">' + new Date().toLocaleTimeString() + '</div>';
        html += '<strong>🔍 Automatic Analysis Results:</strong>';
        html += '<div class="event-content">';

        if (result.summary) {
            html += `<p><strong>Summary:</strong> ${result.summary}</p>`;
        }

        if (result.hypotheses && result.hypotheses.length > 0) {
            html += '<p><strong>Hypotheses:</strong></p><ul>';
            result.hypotheses.forEach(hyp => {
                html += `<li><strong>${hyp.scenario}:</strong> ${hyp.description}</li>`;
            });
            html += '</ul>';
        }

        html += '</div></div>';
        this.appendHTML(html);
    }

    /**
     * UI Helper functions
     */
    updateStatus(status, text) {
        const statusDot = document.querySelector('#gdbStatus .status-dot');
        const statusText = document.querySelector('#gdbStatus .status-text');

        statusDot.className = `status-dot ${status}`;
        statusText.textContent = text;
    }

    toggleQuickActions(show) {
        const quickActions = document.getElementById('quickActions');
        if (quickActions) {
            quickActions.style.display = show ? 'block' : 'none';
        }
    }

    appendMessage(type, message, isCode = false) {
        const html = `
            <div class="event-message event-${type}">
                <div class="event-timestamp">${new Date().toLocaleTimeString()}</div>
                <div class="event-content">${isCode ? '<pre>' + this.escapeHtml(message) + '</pre>' : this.escapeHtml(message)}</div>
            </div>
        `;
        this.appendHTML(html);
    }

    appendHTML(html) {
        // Remove placeholder if present
        const placeholder = this.outputElement.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        this.outputElement.insertAdjacentHTML('beforeend', html);
        this.outputElement.scrollTop = this.outputElement.scrollHeight;
    }

    clearOutput() {
        this.outputElement.innerHTML = `
            <div class="placeholder">
                <p>Output cleared</p>
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in app.js
window.GDBClient = GDBClient;
