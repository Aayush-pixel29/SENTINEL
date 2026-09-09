const vscode = require("vscode");
const cp = require("child_process");
const fs = require("fs");
const path = require("path");

let currentReport = null;
let viewProvider = null;

function workspaceRoot() {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
}

function reportPath() {
  const root = workspaceRoot();
  return root ? path.join(root, ".sentinel", "report.json") : null;
}

function runCommand(command, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = cp.spawn(command, args, {
      cwd,
      shell: process.platform === "win32",
      windowsHide: true
    });

    let stdout = "";
    let stderr = "";
    child.stdout?.on("data", d => stdout += d.toString());
    child.stderr?.on("data", d => stderr += d.toString());

    child.on("error", reject);
    child.on("close", code => resolve({ code: code ?? 1, stdout, stderr }));
  });
}

async function verify() {
  const root = workspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage("Sentinel: Open a Git repository/workspace first.");
    return;
  }

  const configured = vscode.workspace.getConfiguration("sentinel").get("cliPath", "sentinel");
  const parts = configured.trim().split(/\s+/);
  const command = parts.shift() || "sentinel";

  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "Sentinel: verifying changes...",
      cancellable: false
    },
    async () => {
      try {
        let result = await runCommand(command, [...parts, "verify"], root);

        // Friendly fallback for developers using the source checkout.
        if (result.code !== 0 && (result.stderr.includes("not recognized") ||
            result.stderr.includes("ENOENT") || result.stderr.includes("not found"))) {
          result = await runCommand("python", ["-m", "sentinel.cli", "verify"], root);
        }

        if (result.code !== 0 && !fs.existsSync(reportPath())) {
          vscode.window.showErrorMessage(
            "Sentinel could not run. Install the Sentinel engine with Python, then try again.",
            "Setup"
          ).then(choice => {
            if (choice === "Setup") vscode.commands.executeCommand("sentinel.setup");
          });
          return;
        }

        if (fs.existsSync(reportPath())) {
          loadReport();
          const verdict = currentReport?.verdict || "UNKNOWN";
          const message =
            verdict === "VERIFIED" ? "Sentinel: VERIFIED ✓" :
            verdict === "BLOCKED" ? "Sentinel: BLOCKED" :
            verdict === "REVIEW" ? "Sentinel: REVIEW" :
            "Sentinel: INCOMPLETE";
          if (verdict === "VERIFIED") {
            vscode.window.showInformationMessage(message);
          } else {
            vscode.window.showWarningMessage(message);
          }
        } else {
          vscode.window.showErrorMessage("Sentinel finished without producing .sentinel/report.json.");
        }
      } catch (err) {
        vscode.window.showErrorMessage(
          "Sentinel CLI was not found. Install it with: python -m pip install -e <path-to-SENTINEL>"
        );
      }
    }
  );
}

function loadReport() {
  const file = reportPath();
  if (!file || !fs.existsSync(file)) return null;

  try {
    currentReport = JSON.parse(fs.readFileSync(file, "utf8"));
    updateDiagnostics();
    viewProvider?.refresh();
    return currentReport;
  } catch {
    vscode.window.showErrorMessage("Sentinel: report.json is invalid.");
    return null;
  }
}

function allFindings() {
  if (!currentReport) return [];
  return [
    ...(currentReport.confirmed_findings || []),
    ...(currentReport.unconfirmed_findings || [])
  ];
}

function updateDiagnostics() {
  const root = workspaceRoot();
  if (!root || !currentReport) return;

  const diagnostics = new Map();
  for (const finding of allFindings()) {
    if (!finding.file) continue;
    const uri = vscode.Uri.file(path.join(root, finding.file));
    const line = Math.max(0, (Number(finding.line) || 1) - 1);
    const range = new vscode.Range(line, 0, line, Number.MAX_SAFE_INTEGER);
    const severity =
      finding.classification === "CONFIRMED" && ["CRITICAL", "HIGH", "ERROR"].includes(finding.severity)
        ? vscode.DiagnosticSeverity.Error
        : vscode.DiagnosticSeverity.Warning;

    const prefix = finding.classification === "CONFIRMED" ? "CONFIRMED" : "UNCONFIRMED (AI)";
    const diagnostic = new vscode.Diagnostic(
      range,
      `Sentinel ${prefix}: ${finding.title}. ${finding.description || ""}`,
      severity
    );
    diagnostic.source = "Sentinel";
    diagnostics.set(uri.toString(), { uri, diagnostic });
  }

  const collection = vscode.languages.createDiagnosticCollection("sentinel");
  collection.clear();
  for (const { uri, diagnostic } of diagnostics.values()) {
    collection.set(uri, [diagnostic]);
  }
  viewProvider?.setDiagnosticCollection(collection);
}

function explain() {
  const report = currentReport || loadReport();
  if (!report) {
    vscode.window.showInformationMessage("Sentinel: Run Verify Changes first.");
    return;
  }

  const confirmed = report.confirmed_findings || [];
  const unconfirmed = report.unconfirmed_findings || [];
  const failed = (report.checks || []).filter(c => c.status === "FAILED").map(c => c.name);

  const lines = [];
  lines.push(`Sentinel verdict: ${report.verdict}`);
  lines.push("");
  if (confirmed.length) {
    lines.push("CONFIRMED EVIDENCE:");
    for (const f of confirmed) {
      lines.push(`• ${f.source}: ${f.title}${f.file ? ` (${f.file}:${f.line || "?"})` : ""}`);
    }
  }
  if (unconfirmed.length) {
    lines.push("");
    lines.push("UNCONFIRMED AI CONCERNS:");
    for (const f of unconfirmed) {
      lines.push(`• ${f.title}${f.file ? ` (${f.file}:${f.line || "?"})` : ""}`);
    }
  }
  if (failed.length) {
    lines.push("");
    lines.push(`FAILED CHECKS: ${failed.join(", ")}`);
  }
  lines.push("");
  lines.push(
    report.verdict === "VERIFIED"
      ? "Recommended action: human review is still recommended before merging."
      : "Recommended action: inspect the evidence, fix confirmed issues, and verify again."
  );

  vscode.window.showInformationMessage(lines.join("\n"), { modal: true });
}

function setup() {
  const root = workspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage("Open the project/repository you want Sentinel to verify.");
    return;
  }

  const terminal = vscode.window.createTerminal({ name: "Sentinel Setup", cwd: root });
  terminal.show();
  terminal.sendText(
    'python -m pip install -e "https://github.com/Aayush-pixel29/SENTINEL.git"'
  );
  vscode.window.showInformationMessage(
    "Sentinel setup command opened in the terminal. After installation, run Sentinel: Verify Changes."
  );
}

class SentinelViewProvider {
  constructor(extensionUri) {
    this.extensionUri = extensionUri;
    this.view = null;
    this.collection = null;
  }

  resolveWebviewView(webviewView) {
    this.view = webviewView;
    webviewView.webview.options = { enableScripts: true };
    webviewView.webview.onDidReceiveMessage(async message => {
      if (message.command === "verify") vscode.commands.executeCommand("sentinel.verify");
      if (message.command === "explain") vscode.commands.executeCommand("sentinel.explain");
      if (message.command === "setup") vscode.commands.executeCommand("sentinel.setup");
      if (message.command === "open") await openFinding(message.file, message.line);
    });
    this.refresh();
  }

  setDiagnosticCollection(collection) {
    this.collection = collection;
  }

  refresh() {
    if (!this.view) return;
    this.view.webview.html = this.html();
  }

  html() {
    const r = currentReport;
    if (!r) {
      return `
      <!doctype html><html><body>
      <style>
        body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);padding:12px}
        button{width:100%;padding:8px;margin:5px 0;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:0;border-radius:4px;cursor:pointer;}
        .muted{opacity:.75;line-height:1.5;margin-bottom:12px}
        h2{margin:0 0 8px}
      </style>
      <h2>🛡 Sentinel</h2>
      <p class="muted">Verify the Git changes in the current workspace. Sentinel runs the existing verification engine and shows evidence here.</p>
      <button onclick="send('verify')">Verify Changes</button>
      <button onclick="send('setup')">Setup Engine</button>
      <script>
        const vscode = acquireVsCodeApi();
        function send(command){ vscode.postMessage({command}); }
      </script>
      </body></html>`;
    }

    const verdict = r.verdict || "UNKNOWN";
    const cls =
      verdict === "VERIFIED" ? "ok" :
      verdict === "BLOCKED" ? "bad" :
      verdict === "REVIEW" ? "warn" : "muted";

    const checks = (r.checks || []).map(c => {
      const icon = c.status === "PASSED" ? "✓" : c.status === "FAILED" ? "✗" : "•";
      return `<div class="row"><span>${icon} ${esc(c.name)}</span><span>${esc(c.status)}</span></div>`;
    }).join("");

    const findings = allFindings().map(f => {
      const color = f.classification === "CONFIRMED" ? "bad" : "warn";
      const loc = f.file ? `${f.file}:${f.line || "?"}` : "";
      return `<div class="finding ${color}" onclick='openFinding(${JSON.stringify(f.file || "")}, ${Number(f.line) || 1})'>
        <b>${esc(f.title)}</b><br><small>${esc(f.classification)} · ${esc(loc)}</small>
      </div>`;
    }).join("");

    return `<!doctype html><html><body>
    <style>
      body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);padding:10px}
      h2{margin:0 0 4px}.sub{opacity:.7;font-size:11px;margin-bottom:12px}
      .verdict{padding:12px;border-radius:6px;margin:10px 0;font-weight:700;font-size:18px}
      .ok{color:var(--vscode-testing-iconPassed);background:color-mix(in srgb,var(--vscode-testing-iconPassed) 12%,transparent)}
      .bad{color:var(--vscode-testing-iconFailed);background:color-mix(in srgb,var(--vscode-testing-iconFailed) 12%,transparent)}
      .warn{color:var(--vscode-editorWarning-foreground);background:color-mix(in srgb,var(--vscode-editorWarning-foreground) 10%,transparent)}
      .muted{opacity:.7}
      .section{margin-top:16px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
      .row{display:flex;justify-content:space-between;padding:4px 0;font-size:11px}
      .finding{padding:8px;margin:6px 0;border-radius:5px;cursor:pointer;border:1px solid transparent;background:var(--vscode-editor-background);}
      .finding.bad{border-left:4px solid var(--vscode-testing-iconFailed);}
      .finding.warn{border-left:4px solid var(--vscode-editorWarning-foreground);}
      .finding:hover{background:var(--vscode-list-hoverBackground);}
      button{width:100%;padding:7px;margin-top:6px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:0;border-radius:4px;cursor:pointer}
      button:hover{opacity:0.9}
      small{opacity:.75}
    </style>
    <h2>🛡 Sentinel</h2>
    <div class="sub">${esc(r.repository || "")} · ${esc(r.branch || "")}</div>
    <div class="verdict ${cls}">${esc(verdict)}</div>
    <div class="section">Verification checks</div>
    ${checks || '<div class="muted">No checks recorded.</div>'}
    <div class="section">Findings</div>
    ${findings || '<div class="muted" style="margin-top:8px">No findings.</div>'}
    <div style="margin-top:20px;">
      <button onclick="send('verify')">Verify Again</button>
      <button onclick="send('explain')">Explain Verdict</button>
    </div>
    <script>
      const vscode = acquireVsCodeApi();
      function send(command){vscode.postMessage({command});}
      function openFinding(file,line){vscode.postMessage({command:'open',file,line});}
    </script>
    </body></html>`;
  }
}

async function openFinding(file, line) {
  const root = workspaceRoot();
  if (!root || !file) return;
  const uri = vscode.Uri.file(path.join(root, file));
  const doc = await vscode.workspace.openTextDocument(uri);
  const editor = await vscode.window.showTextDocument(doc);
  const pos = new vscode.Position(Math.max(0, Number(line || 1) - 1), 0);
  editor.selection = new vscode.Selection(pos, pos);
  editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function activate(context) {
  viewProvider = new SentinelViewProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("sentinel.verificationView", viewProvider),
    vscode.commands.registerCommand("sentinel.verify", verify),
    vscode.commands.registerCommand("sentinel.openReport", async () => {
      const file = reportPath();
      if (!file || !fs.existsSync(file)) {
        vscode.window.showInformationMessage("Sentinel: No report found. Run Verify Changes first.");
        return;
      }
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(file));
      vscode.window.showTextDocument(doc);
    }),
    vscode.commands.registerCommand("sentinel.explain", explain),
    vscode.commands.registerCommand("sentinel.setup", setup)
  );

  loadReport();

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(() => {
      const enabled = vscode.workspace.getConfiguration("sentinel").get("autoVerifyOnSave", false);
      if (enabled) verify();
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
