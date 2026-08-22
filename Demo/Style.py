import streamlit as st


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --sg-primary: #faff69;
    --sg-primary-active: #e6eb52;
    --sg-primary-soft: rgba(250, 255, 105, 0.10);
    --sg-primary-border: rgba(250, 255, 105, 0.42);
    --sg-ink: #ffffff;
    --sg-body: #cccccc;
    --sg-body-strong: #e6e6e6;
    --sg-muted: #888888;
    --sg-muted-soft: #5a5a5a;
    --sg-hairline: #2a2a2a;
    --sg-hairline-strong: #3a3a3a;
    --sg-canvas: #0a0a0a;
    --sg-surface-soft: #121212;
    --sg-surface-card: #1a1a1a;
    --sg-surface-elevated: #242424;
    --sg-success: #22c55e;
    --sg-warning: #f59e0b;
    --sg-error: #ef4444;
    --sg-radius-sm: 6px;
    --sg-radius-md: 8px;
    --sg-radius-lg: 12px;
}

html,
body,
[class*="css"] {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

html,
body,
[data-testid="stAppViewContainer"],
.stApp {
    background: var(--sg-canvas);
    color: var(--sg-ink);
}

#MainMenu,
footer,
[data-testid="stHeader"] {
    visibility: hidden;
}

.block-container {
    max-width: 1440px;
    padding: 0 2rem 7rem;
}

/* Application header */
.topbar {
    min-height: 78px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 20;
    margin: 0 -2rem;
    padding: 0 2rem;
    background: var(--sg-canvas);
    border-bottom: 1px solid var(--sg-hairline);
}

.eyebrow {
    color: var(--sg-muted);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
}

.topbar-title {
    margin-top: 3px;
    color: var(--sg-ink);
    font-size: 16px;
    font-weight: 600;
}

.topbar-actions {
    display: flex;
    align-items: center;
}

.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 6px 10px;
    color: var(--sg-body);
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: 9999px;
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.7px;
}

.mode-dot {
    width: 7px;
    height: 7px;
    display: inline-block;
    background: var(--sg-primary);
    border-radius: 9999px;
}

/* Intro and controlled variables */
.comparison-workspace {
    padding-top: 36px;
}

.comparison-intro {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 290px;
    gap: 48px;
    align-items: end;
    padding: 0 0 30px;
}

.hero-badge {
    display: inline-block;
    margin-bottom: 16px;
    padding: 5px 11px;
    color: var(--sg-canvas);
    background: var(--sg-primary);
    border-radius: 9999px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.3px;
}

.comparison-intro h1 {
    margin: 0;
    color: var(--sg-ink);
    font-size: clamp(34px, 4vw, 48px);
    font-weight: 700;
    line-height: 1.08;
    letter-spacing: -1.8px;
}

.comparison-intro h1 span {
    color: var(--sg-primary);
}

.comparison-intro p {
    max-width: 760px;
    margin: 16px 0 0;
    color: var(--sg-body);
    font-size: 14px;
    line-height: 1.6;
}

.run-summary {
    min-height: 88px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    align-items: center;
    padding: 16px;
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-lg);
}

.run-summary-dot {
    width: 9px;
    height: 9px;
    background: var(--sg-muted-soft);
    border-radius: 9999px;
}

.run-complete .run-summary-dot {
    background: var(--sg-success);
}

.run-waiting .run-summary-dot {
    background: var(--sg-warning);
}

.run-summary small,
.run-summary strong {
    display: block;
}

.run-summary small {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.8px;
}

.run-summary strong {
    margin-top: 4px;
    color: var(--sg-body-strong);
    font-size: 12px;
    font-weight: 600;
}

.run-count {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.7px;
}

.shared-controls {
    display: grid;
    grid-template-columns: minmax(220px, 1.35fr) repeat(4, minmax(130px, 1fr));
    overflow: hidden;
    background: var(--sg-surface-soft);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-lg);
}

.shared-controls > div {
    min-height: 70px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 13px 16px;
    border-right: 1px solid var(--sg-hairline);
}

.shared-controls > div:last-child {
    border-right: 0;
}

.shared-controls-title {
    background: var(--sg-surface-card);
}

.shared-controls span,
.shared-controls small {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.8px;
}

.shared-controls-title small {
    margin-top: 6px;
    color: var(--sg-muted-soft);
    letter-spacing: 0;
}

.shared-controls strong {
    margin-top: 5px;
    color: var(--sg-body-strong);
    font-size: 12px;
    font-weight: 600;
}

.comparison-section-heading {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 36px 0 16px;
}

.comparison-section-heading h2 {
    margin: 4px 0 0;
    color: var(--sg-ink);
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.5px;
}

.comparison-section-heading p {
    margin: 0;
    color: var(--sg-muted);
    font-size: 12px;
}

/* Four-way result matrix */
.comparison-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
}

.comparison-card {
    min-width: 0;
    min-height: 430px;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
    background: var(--sg-surface-soft);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-lg);
}

.featured-card {
    border-color: var(--sg-primary-border);
}

.card-accent {
    height: 3px;
    flex: 0 0 3px;
    background: var(--sg-hairline-strong);
}

.featured-card .card-accent {
    background: var(--sg-primary);
}

.card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 20px 0;
}

.card-title-row {
    min-width: 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}

.config-number {
    min-width: 30px;
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    line-height: 1.6;
}

.config-mode {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 0.8px;
}

.card-header h3 {
    margin: 4px 0 0;
    color: var(--sg-ink);
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.25px;
}

.card-status-group {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 6px;
}

.panel-status,
.thesis-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 8px;
    border-radius: 9999px;
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.7px;
    white-space: nowrap;
}

.panel-status {
    color: var(--sg-muted);
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
}

.panel-status i {
    width: 6px;
    height: 6px;
    background: var(--sg-muted-soft);
    border-radius: 9999px;
}

.status-complete {
    color: var(--sg-body-strong);
}

.status-complete i {
    background: var(--sg-success);
}

.status-waiting i {
    background: var(--sg-warning);
}

.thesis-badge {
    color: var(--sg-canvas);
    background: var(--sg-primary);
}

.config-tags {
    display: flex;
    gap: 8px;
    margin: 18px 20px 0 62px;
}

.config-tags span {
    padding: 5px 8px;
    color: var(--sg-muted);
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-sm);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    letter-spacing: 0.5px;
}

.config-tags b {
    margin-left: 4px;
    color: var(--sg-body-strong);
    font-weight: 500;
}

/* Waiting state */
.panel-empty-state {
    min-height: 215px;
    display: flex;
    flex: 1;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 18px 20px;
    padding: 28px;
    text-align: center;
    background: var(--sg-canvas);
    border: 1px dashed var(--sg-hairline-strong);
    border-radius: var(--sg-radius-md);
}

.empty-state-mark {
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 25px;
}

.panel-empty-state strong {
    margin-top: 12px;
    color: var(--sg-body-strong);
    font-size: 13px;
    font-weight: 600;
}

.panel-empty-state p {
    max-width: 340px;
    margin: 8px 0 0;
    color: var(--sg-muted);
    font-size: 11px;
    line-height: 1.55;
}

/* Per-panel chat */
.panel-chat {
    margin: 18px 20px 0;
    overflow: hidden;
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-md);
}

.chat-turn {
    padding: 14px;
}

.user-turn {
    background: var(--sg-surface-elevated);
    border-left: 3px solid var(--sg-primary);
}

.answer-turn {
    background: var(--sg-canvas);
    border-top: 1px solid var(--sg-hairline);
}

.turn-label,
.mock-label {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.8px;
}

.answer-label-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.mock-label {
    color: var(--sg-primary);
}

.chat-turn p {
    margin: 8px 0 0;
    color: var(--sg-body-strong);
    font-size: 12px;
    line-height: 1.55;
}

.answer-markdown {
    color: var(--sg-body);
    font-size: 12px;
    line-height: 1.55;
}

.answer-markdown p {
    margin: 0 0 8px;
}

.answer-markdown p:last-child {
    margin-bottom: 0;
}

.answer-markdown ul,
.answer-markdown ol {
    margin: 8px 0 0;
    padding-left: 18px;
}

.answer-markdown li {
    margin: 3px 0;
}

.answer-markdown strong {
    color: var(--sg-body-strong);
    font-weight: 600;
}

.answer-markdown code {
    padding: 2px 4px;
    color: var(--sg-primary);
    background: var(--sg-surface-card);
    border-radius: var(--sg-radius-sm);
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
}

.answer-markdown blockquote {
    margin: 8px 0 0;
    padding-left: 10px;
    color: var(--sg-muted);
    border-left: 2px solid var(--sg-primary);
}

/* Citations and trace */
.evidence-section {
    margin: 14px 20px 0;
}

.section-label-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.section-label-row span,
.section-label-row small,
.trace-details summary span,
.trace-details summary small {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.8px;
}

.section-label-row small,
.trace-details summary small {
    color: var(--sg-muted-soft);
}

.citation-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 8px;
}

.citation-list > div {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 9px 10px;
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-sm);
}

.citation-list b {
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    font-weight: 500;
}

.citation-list span {
    overflow: hidden;
    color: var(--sg-muted);
    font-size: 9px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.trace-details {
    margin: 14px 20px 16px;
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-md);
}

.trace-details summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 12px;
    cursor: pointer;
    list-style: none;
}

.trace-details summary::-webkit-details-marker {
    display: none;
}

.trace-details summary::after {
    content: "+";
    margin-left: 10px;
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
}

.trace-details[open] summary::after {
    content: "−";
}

.trace-table {
    padding: 4px 12px 10px;
    border-top: 1px solid var(--sg-hairline);
}

.trace-row {
    display: grid;
    grid-template-columns: 24px 58px minmax(0, 1fr);
    gap: 8px;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--sg-hairline);
}

.trace-row:last-child {
    border-bottom: 0;
}

.trace-row span,
.trace-row b,
.trace-row code {
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 400;
}

.trace-row span {
    color: var(--sg-muted-soft);
}

.trace-row b {
    color: var(--sg-primary);
}

.trace-row code {
    overflow: hidden;
    color: var(--sg-muted);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.panel-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: auto;
    padding: 11px 20px;
    color: var(--sg-muted-soft);
    background: var(--sg-canvas);
    border-top: 1px solid var(--sg-hairline);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    letter-spacing: 0.5px;
}

.panel-footer-waiting {
    margin-top: 0;
}

.composer-hint {
    margin: 24px 0 0;
    color: var(--sg-muted-soft);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 1.1px;
    text-align: center;
}

/* Persistent shared-query composer */
[data-testid="stBottom"] {
    background: linear-gradient(180deg, transparent, var(--sg-canvas) 30%);
}

[data-testid="stBottom"] > div {
    background: transparent;
}

[data-testid="stChatInput"] {
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline-strong);
    border-radius: 0;
    box-shadow: none;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--sg-primary);
    box-shadow: none;
}

[data-testid="stChatInput"] textarea {
    color: var(--sg-ink);
    caret-color: var(--sg-primary);
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--sg-muted);
}

[data-testid="stChatInputSubmitButton"] {
    color: var(--sg-canvas);
    background: var(--sg-primary);
    border-radius: var(--sg-radius-md);
}

@media (max-width: 1050px) {
    .shared-controls {
        grid-template-columns: repeat(4, 1fr);
    }

    .shared-controls-title {
        grid-column: 1 / -1;
        min-height: 58px !important;
    }

    .comparison-card {
        min-height: 450px;
    }

    .card-header {
        flex-direction: column;
    }

    .card-status-group {
        justify-content: flex-start;
        margin-left: 42px;
    }
}

@media (max-width: 850px) {
    .comparison-intro {
        grid-template-columns: 1fr;
        gap: 22px;
    }

    .run-summary {
        max-width: 360px;
    }

    .comparison-grid {
        grid-template-columns: 1fr;
    }

    .comparison-card {
        min-height: 420px;
    }

    .card-header {
        flex-direction: row;
    }

    .card-status-group {
        justify-content: flex-end;
        margin-left: 0;
    }
}

@media (max-width: 620px) {
    .block-container {
        padding-right: 1rem;
        padding-left: 1rem;
    }

    .topbar {
        margin: 0 -1rem;
        padding: 0 1rem;
    }

    .mode-badge {
        display: none;
    }

    .comparison-workspace {
        padding-top: 28px;
    }

    .comparison-intro h1 {
        font-size: 34px;
    }

    .shared-controls {
        grid-template-columns: repeat(2, 1fr);
    }

    .shared-controls > div:nth-child(3) {
        border-right: 0;
    }

    .comparison-section-heading {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
    }

    .card-header {
        flex-direction: column;
    }

    .card-status-group {
        justify-content: flex-start;
        margin-left: 42px;
    }

    .config-tags {
        margin-left: 20px;
    }

    .citation-list {
        grid-template-columns: 1fr;
    }

    .panel-footer {
        align-items: flex-start;
        flex-direction: column;
    }
}
</style>
"""


def apply_custom_style():
    """Load the ClickHouse-inspired design tokens and component overrides."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
