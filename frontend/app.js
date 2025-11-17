/**
 * OS Debugging Assistant - Frontend JavaScript
 */

// API endpoint
const API_URL = window.location.origin + '/api/analyze';

// DOM elements - Static Analysis
const debugInput = document.getElementById('debugInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const exampleBtn = document.getElementById('exampleBtn');
const copyBtn = document.getElementById('copyBtn');
const outputArea = document.getElementById('outputArea');

// DOM elements - Real-time GDB
const connectGdbBtn = document.getElementById('connectGdbBtn');
const disconnectGdbBtn = document.getElementById('disconnectGdbBtn');
const gdbTarget = document.getElementById('gdbTarget');
const clearOutputBtn = document.getElementById('clearOutputBtn');
const continueBtn = document.getElementById('continueBtn');
const stepOverBtn = document.getElementById('stepOverBtn');
const stepIntoBtn = document.getElementById('stepIntoBtn');
const getBacktraceBtn = document.getElementById('getBacktraceBtn');
const getRegistersBtn = document.getElementById('getRegistersBtn');
const setBreakpointBtn = document.getElementById('setBreakpointBtn');
const breakpointLocation = document.getElementById('breakpointLocation');

// Initialize GDB Client
let gdbClient = null;

// Example debugging output
const EXAMPLE_INPUT = `#0  0x0000000080002a9e in panic () at kernel/printf.c:127
#1  0x0000000080001c3a in usertrap () at kernel/trap.c:67
#2  0x0000000000000000 in ?? ()

scause 0x000000000000000d
stval 0x0000000000000000
sepc=0x0000000000000bb4 ra=0x0000000000000b48
sp=0x0000000000003f50 gp=0x0000000000000000 tp=0x0000000000000000
t0=0x0000000000000000 t1=0x0000000000000000 t2=0x0000000000000000
s0=0x0000000000003fb0 s1=0x0000000000000000 a0=0x0000000000000000
a1=0x0000000000000000 a2=0x0000000000000000 a3=0x0000000000000000
a4=0x0000000000000000 a5=0x0000000000000bb4 a6=0x0000000000000000
a7=0x0000000000000007 s2=0x0000000000000000 s3=0x0000000000000000
s4=0x0000000000000000 s5=0x0000000000000000 s6=0x0000000000000000
s7=0x0000000000000000 s8=0x0000000000000000 s9=0x0000000000000000
s10=0x0000000000000000 s11=0x0000000000000000 t3=0x0000000000000000
t4=0x0000000000000000 t5=0x0000000000000000 t6=0x0000000000000000`;

// Event Listeners
analyzeBtn.addEventListener('click', handleAnalyze);
clearBtn.addEventListener('click', handleClear);
exampleBtn.addEventListener('click', handleLoadExample);
copyBtn.addEventListener('click', handleCopy);

// Handle analyze button click
async function handleAnalyze() {
    const inputText = debugInput.value.trim();

    if (!inputText) {
        showError('Please enter some debugging information to analyze.');
        return;
    }

    // Show loading state
    setLoading(true);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: inputText })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            displayResults(result);
            copyBtn.style.display = 'inline-flex';
        } else {
            showError(result.error || 'Analysis failed');
        }

    } catch (error) {
        console.error('Analysis error:', error);
        showError(`Failed to analyze: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// Handle clear button
function handleClear() {
    debugInput.value = '';
    outputArea.innerHTML = `
        <div class="placeholder">
            <p>👈 Enter debugging information and click "Analyze" to see results</p>
            <p class="placeholder-hint">The assistant will:</p>
            <ul>
                <li>Analyze GDB backtraces and register values</li>
                <li>Decode trapframe/exception information</li>
                <li>Check page table configurations</li>
                <li>Generate hypotheses about the root cause</li>
            </ul>
        </div>
    `;
    copyBtn.style.display = 'none';
}

// Handle load example button
function handleLoadExample() {
    debugInput.value = EXAMPLE_INPUT;
}

// Handle copy button
function handleCopy() {
    const text = outputArea.innerText;
    navigator.clipboard.writeText(text).then(() => {
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    });
}

// Set loading state
function setLoading(isLoading) {
    const btnText = analyzeBtn.querySelector('.btn-text');
    const spinner = analyzeBtn.querySelector('.spinner');

    if (isLoading) {
        analyzeBtn.disabled = true;
        btnText.textContent = 'Analyzing...';
        spinner.style.display = 'inline-block';
    } else {
        analyzeBtn.disabled = false;
        btnText.textContent = 'Analyze';
        spinner.style.display = 'none';
    }
}

// Display error message
function showError(message) {
    outputArea.innerHTML = `
        <div class="error-box">
            <h4>Error</h4>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    copyBtn.style.display = 'none';
}

// Display analysis results
function displayResults(result) {
    let html = '';

    // Summary
    if (result.summary) {
        html += `
            <div class="summary-box">
                <h3>摘要</h3>
                <p>${escapeHtml(result.summary)}</p>
            </div>
        `;
    }

    // AI Insights (if enabled)
    if (result.ai_enabled && result.ai_insights) {
        html += `
            <div class="ai-insights-box" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: white; margin-bottom: 15px;">🤖 AI 深度分析</h3>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 6px; white-space: pre-wrap; font-size: 0.95rem; line-height: 1.6;">
                    ${escapeHtml(result.ai_insights.explanation)}
                </div>
                <p style="margin-top: 10px; font-size: 0.85rem; opacity: 0.9;">
                    由 ${result.ai_insights.model} 提供支持
                </p>
            </div>
        `;
    }

    // Hypotheses
    if (result.hypotheses && result.hypotheses.length > 0) {
        html += '<h3 style="margin-top: 20px; margin-bottom: 15px;">Hypotheses</h3>';

        result.hypotheses.forEach((hyp, index) => {
            html += `
                <div class="hypothesis-card">
                    <div class="hypothesis-header">
                        <span class="priority-badge priority-${hyp.priority}">
                            ${hyp.priority} priority
                        </span>
                        <h4>${escapeHtml(hyp.scenario)}</h4>
                    </div>

                    <p><strong>Explanation:</strong> ${escapeHtml(hyp.explanation)}</p>

                    ${hyp.evidence && hyp.evidence.length > 0 ? `
                        <div class="evidence-list">
                            <h5>Evidence:</h5>
                            <ul>
                                ${hyp.evidence.map(e => `<li>${escapeHtml(e)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    ${hyp.suggestions && hyp.suggestions.length > 0 ? `
                        <div class="suggestions-list">
                            <h5>Suggestions:</h5>
                            <ol>
                                ${hyp.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }

    // GDB Analysis
    if (result.gdb_analysis) {
        html += renderGDBAnalysis(result.gdb_analysis);
    }

    // Trapframe Analysis
    if (result.trapframe_analysis) {
        html += renderTrapframeAnalysis(result.trapframe_analysis);
    }

    // Page Table Analysis
    if (result.pagetable_analysis) {
        html += renderPageTableAnalysis(result.pagetable_analysis);
    }

    // All Findings
    if (result.all_findings && result.all_findings.length > 0 && !result.hypotheses) {
        html += renderFindings(result.all_findings);
    }

    outputArea.innerHTML = html || '<p>No significant findings detected.</p>';
}

// Render GDB analysis
function renderGDBAnalysis(analysis) {
    let html = '<div class="analysis-section"><h4>GDB Analysis</h4>';

    if (analysis.backtrace_analysis && analysis.backtrace_analysis.frames) {
        html += '<h5 style="margin-top: 15px;">Backtrace:</h5>';
        analysis.backtrace_analysis.frames.forEach(frame => {
            html += `<div class="backtrace-frame">${escapeHtml(frame.description)}</div>`;
        });
    }

    if (analysis.register_analysis && analysis.register_analysis.registers) {
        html += '<h5 style="margin-top: 15px;">Registers:</h5>';
        html += '<div class="register-info">';
        Object.entries(analysis.register_analysis.registers).forEach(([name, info]) => {
            html += `<div class="register-item">${escapeHtml(info.description)}</div>`;
        });
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// Render trapframe analysis
function renderTrapframeAnalysis(analysis) {
    let html = '<div class="analysis-section"><h4>Exception/Trapframe Analysis</h4>';

    if (analysis.exception_info) {
        const info = analysis.exception_info;
        html += `<p><strong>Exception Type:</strong> ${escapeHtml(info.trap_name || info.description)}</p>`;

        if (info.trap_number !== undefined) {
            html += `<p><strong>Trap Number:</strong> ${info.trap_number}</p>`;
        }
        if (info.code !== undefined) {
            html += `<p><strong>Exception Code:</strong> ${info.code}</p>`;
        }
    }

    if (analysis.error_code_analysis) {
        html += '<h5 style="margin-top: 15px;">Error Code Details:</h5>';
        html += `<div class="code-block">${escapeHtml(analysis.error_code_analysis.description)}</div>`;
    }

    html += '</div>';
    return html;
}

// Render page table analysis
function renderPageTableAnalysis(analysis) {
    let html = '<div class="analysis-section"><h4>Page Table Analysis</h4>';

    if (analysis.visualization) {
        html += `<div class="code-block">${escapeHtml(analysis.visualization)}</div>`;
    }

    if (analysis.mappings && analysis.mappings.length > 0) {
        html += `<p style="margin-top: 10px;"><strong>Total Mappings:</strong> ${analysis.mappings.length}</p>`;
    }

    html += '</div>';
    return html;
}

// Render findings
function renderFindings(findings) {
    let html = '<div class="findings-section"><h4>Detailed Findings</h4>';

    findings.forEach(finding => {
        const severityClass = `finding-${finding.severity}`;
        html += `
            <div class="finding-item ${severityClass}">
                <span class="finding-severity">${finding.severity}</span>
                <span>${escapeHtml(finding.message)}</span>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Tab Switching
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Setup tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;

            // Update tab buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update tab contents
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabName}-tab`) {
                    content.classList.add('active');
                }
            });

            // Initialize GDB client when switching to real-time tab
            if (tabName === 'realtime' && !gdbClient) {
                initializeGDBClient();
            }
        });
    });
});

// ============================================
// Real-time GDB Event Handlers
// ============================================
function initializeGDBClient() {
    if (typeof GDBClient === 'undefined') {
        console.error('GDBClient not loaded. Make sure gdb_client.js is included.');
        return;
    }

    gdbClient = new GDBClient();
    console.log('GDB Client initialized');
}

// GDB Connection
if (connectGdbBtn) {
    connectGdbBtn.addEventListener('click', () => {
        if (!gdbClient) {
            initializeGDBClient();
        }

        const target = gdbTarget.value.trim();
        if (!target) {
            alert('Please enter a target (e.g., localhost:1234 or /path/to/program)');
            return;
        }

        gdbClient.connectToTarget(target);
    });
}

if (disconnectGdbBtn) {
    disconnectGdbBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.disconnect();
        }
    });
}

// Clear output
if (clearOutputBtn) {
    clearOutputBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.clearOutput();
        }
    });
}

// Control buttons
if (continueBtn) {
    continueBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.continue();
        }
    });
}

if (stepOverBtn) {
    stepOverBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.stepOver();
        }
    });
}

if (stepIntoBtn) {
    stepIntoBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.stepInto();
        }
    });
}

// Info buttons
if (getBacktraceBtn) {
    getBacktraceBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.getBacktrace();
        }
    });
}

if (getRegistersBtn) {
    getRegistersBtn.addEventListener('click', () => {
        if (gdbClient) {
            gdbClient.getRegisters();
        }
    });
}

// Breakpoint
if (setBreakpointBtn) {
    setBreakpointBtn.addEventListener('click', () => {
        if (gdbClient) {
            const location = breakpointLocation.value.trim();
            gdbClient.setBreakpoint(location);
        }
    });
}

// Allow Enter key for breakpoint location
if (breakpointLocation) {
    breakpointLocation.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            setBreakpointBtn.click();
        }
    });
}

// Initial state
console.log('OS Debugging Assistant loaded');
