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

/* Keep the existing interface visible while Streamlit reconciles a rerun. */
[data-stale="true"] {
    opacity: 1 !important;
}

#MainMenu,
footer,
[data-testid="stHeader"] {
    visibility: hidden;
}

.block-container {
    max-width: 1680px;
    padding: 0 1.25rem 5rem;
}

/* Application header */
.topbar {
    min-height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 20;
    margin: 0 -1.25rem;
    padding: 0 1.25rem;
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
    padding-top: 12px;
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

.run-running .run-summary-dot {
    background: var(--sg-primary);
}

.run-waiting .run-summary-dot {
    background: var(--sg-warning);
}

.run-error .run-summary-dot {
    background: var(--sg-error);
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

/* Shared backend selector */
[data-testid="stSelectbox"] {
    max-width: 300px;
    margin: 8px 0 12px;
}

[data-testid="stSelectbox"] label {
    display: none;
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 44px;
    color: var(--sg-body-strong);
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline-strong);
    border-radius: 0;
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--sg-primary);
    box-shadow: none;
}

[data-testid="stSelectbox"] [data-baseweb="select"] svg {
    fill: var(--sg-primary);
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
    gap: 20px;
}

.comparison-card {
    min-width: 0;
    height: clamp(560px, calc(100vh - 170px), 720px);
    min-height: 0;
    display: flex;
    flex-direction: column;
    position: relative;
    box-sizing: border-box;
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
    width: calc(100% - 32px);
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-inline: auto;
    padding: 16px 12px 0;
    box-sizing: border-box;
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

.status-running i {
    background: var(--sg-primary);
}

.status-waiting i {
    background: var(--sg-warning);
}

.status-error i {
    background: var(--sg-error);
}

.thesis-badge {
    color: var(--sg-canvas);
    background: var(--sg-primary);
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

.thinking-state {
    width: 100%;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 0;
    padding: 20px;
    text-align: center;
    background: var(--sg-surface-card);
    border: 0;
    animation: thinking-enter 320ms ease-out both;
}

.thinking-heading {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    text-align: left;
}

.thinking-heading > div {
    display: flex;
    flex-direction: column;
}

.thinking-mark {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 32px;
}

.thinking-mark i {
    width: 5px;
    height: 5px;
    display: block;
    background: var(--sg-primary);
    border-radius: 9999px;
    animation: thinking-dot 1.1s ease-in-out infinite;
}

.thinking-mark i:nth-child(2) {
    animation-delay: 140ms;
}

.thinking-mark i:nth-child(3) {
    animation-delay: 280ms;
}

.thinking-state strong {
    color: var(--sg-body-strong);
    font-size: 14px;
    font-weight: 600;
}

.thinking-heading small,
.thinking-current > span,
.thinking-step-copy b {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.7px;
}

.thinking-current {
    width: 100%;
    margin-top: 18px;
    padding: 10px 12px;
    text-align: left;
    background: var(--sg-surface-elevated);
    border-left: 2px solid var(--sg-primary);
    animation: thinking-current-enter 260ms ease-out both;
}

.thinking-current p {
    margin: 5px 0 0;
    color: var(--sg-body-strong);
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    line-height: 1.55;
}

.thinking-trace {
    width: 100%;
    margin-top: 12px;
    text-align: left;
}

.trace-event-row {
    display: grid;
    grid-template-columns: 28px 8px minmax(0, 1fr);
    gap: 10px;
    align-items: start;
    padding: 12px 0;
    border-bottom: 1px solid var(--sg-hairline);
    animation: trace-row-enter 280ms ease-out both;
}

.trace-event-row:last-child {
    border-bottom: 0;
}

.trace-event-row:nth-child(2) {
    animation-delay: 60ms;
}

.trace-event-row:nth-child(3) {
    animation-delay: 120ms;
}

.trace-event-row:nth-child(4) {
    animation-delay: 180ms;
}

.trace-event-row:nth-child(5) {
    animation-delay: 240ms;
}

.trace-event-index {
    color: var(--sg-body-strong);
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    font-weight: 600;
}

.trace-event-dot {
    width: 8px;
    height: 8px;
    margin-top: 2px;
    background: var(--sg-success);
    border-radius: 9999px;
}

.trace-status-running .trace-event-dot {
    background: var(--sg-primary);
}

.trace-status-error .trace-event-dot {
    background: var(--sg-error);
}

.trace-status-skipped .trace-event-dot {
    background: var(--sg-muted-soft);
}

.trace-event-row.is-active .trace-event-dot {
    animation: trace-active-pulse 1.15s ease-in-out infinite;
}

.trace-event-row.is-active .trace-event-index,
.trace-event-row.is-active .trace-event-heading b {
    color: var(--sg-primary);
}

.trace-event-copy {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.trace-event-heading {
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.trace-event-heading b {
    min-width: 0;
    overflow: hidden;
    color: var(--sg-ink);
    font-size: 14px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.trace-event-meta {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 6px;
}

.trace-event-meta time,
.trace-status-pill {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.trace-event-meta time {
    color: var(--sg-muted);
}

.trace-status-pill {
    padding: 4px 8px;
    color: var(--sg-success);
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.24);
    border-radius: 3px;
}

.trace-status-running .trace-status-pill {
    color: var(--sg-primary);
    background: var(--sg-primary-soft);
    border-color: var(--sg-primary-border);
}

.trace-status-error .trace-status-pill {
    color: var(--sg-error);
    background: rgba(239, 68, 68, 0.08);
    border-color: rgba(239, 68, 68, 0.24);
}

.trace-status-skipped .trace-status-pill {
    color: var(--sg-muted);
    background: transparent;
    border-color: var(--sg-hairline-strong);
}

.trace-event-copy > p {
    margin: 0;
    overflow-wrap: anywhere;
    color: var(--sg-body-strong);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.6;
}

.thinking-caption {
    width: 100%;
    margin: 12px 0 0;
    color: var(--sg-muted);
    font-size: 12px;
    font-weight: 500;
    line-height: 1.6;
    text-align: left;
}

.thinking-state > p {
    max-width: 340px;
    margin: 8px 0 0;
    color: var(--sg-muted);
    font-size: 11px;
    line-height: 1.55;
}

/* Fixed result viewport */
.panel-result {
    min-height: 0;
    height: 0;
    display: flex;
    flex: 1;
    flex-direction: column;
    margin-top: 18px;
    overflow: hidden;
    background: var(--sg-canvas);
    border-top: 1px solid var(--sg-hairline);
}

.panel-result-running {
    animation: panel-enter 360ms ease-out both;
}

.result-toolbar {
    min-height: 34px;
    display: flex;
    flex: 0 0 34px;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    background: var(--sg-surface-card);
    border-bottom: 1px solid var(--sg-hairline);
}

.result-toolbar span,
.result-toolbar small {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 8px;
    font-weight: 500;
    letter-spacing: 0.8px;
}

.result-toolbar small {
    color: var(--sg-muted-soft);
}

.panel-scroll {
    min-width: 0;
    min-height: 0;
    height: 0;
    flex: 1;
    max-height: 100%;
    box-sizing: border-box;
    overflow-x: hidden;
    overflow-y: auto;
    border: 1px solid transparent;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
    scrollbar-color: var(--sg-hairline-strong) var(--sg-canvas);
    scrollbar-width: thin;
}

.chat-history {
    display: flex;
    flex-direction: column;
    gap: 0;
    padding: 8px 20px 20px;
    background: linear-gradient(
        180deg,
        rgba(255, 255, 255, 0.012),
        transparent 22%
    );
    scroll-behavior: smooth;
    overflow-anchor: auto;
}

.chat-exchange {
    display: flex;
    flex: 0 0 auto;
    flex-direction: column;
    gap: 12px;
    padding: 18px 0;
    border-top: 1px solid var(--sg-hairline);
}

.chat-exchange:last-child {
    border-top: 0;
}

.panel-result-running .current-exchange {
    animation: chat-exchange-enter 320ms ease-out both;
}

.chat-message-row {
    width: 100%;
    display: flex;
}

.user-message-row {
    justify-content: flex-end;
    box-sizing: border-box;
    padding-right: 8px;
}

.assistant-message-row {
    justify-content: flex-start;
}

.chat-message {
    min-width: 0;
    padding: 14px 16px;
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-md);
    transition:
        background-color 180ms ease,
        border-color 180ms ease;
}

.user-message {
    position: relative;
    width: fit-content;
    max-width: 78%;
    margin-right: 6px;
    background: linear-gradient(135deg, #252525, #202020);
    border-color: var(--sg-hairline-strong);
}

.user-message::after {
    content: "";
    position: absolute;
    top: 7px;
    right: -7px;
    bottom: 7px;
    width: 2px;
    background: var(--sg-primary);
    border-radius: 9999px;
}

.assistant-message {
    width: fit-content;
    max-width: 92%;
    background: linear-gradient(145deg, #1b1b1b, #171717);
    border-color: var(--sg-hairline);
}

.thinking-message {
    width: 92%;
    padding: 0;
    overflow: hidden;
    border-color: var(--sg-primary-border);
}

.panel-scroll:focus {
    outline: none;
    border-color: var(--sg-primary);
}

.panel-scroll::-webkit-scrollbar {
    width: 8px;
}

.panel-scroll::-webkit-scrollbar-track {
    background: var(--sg-canvas);
}

.panel-scroll::-webkit-scrollbar-thumb {
    background: var(--sg-hairline-strong);
    border: 2px solid var(--sg-canvas);
    border-radius: 9999px;
}

.chat-turn {
    padding: 16px 18px;
}

.user-turn {
    background: linear-gradient(135deg, #252525, #202020);
}

.answer-turn {
    background: linear-gradient(145deg, #1b1b1b, #171717);
}

.turn-label,
.live-label {
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

.live-label {
    color: var(--sg-primary);
    text-align: right;
}

.user-turn p {
    margin: 0;
    color: var(--sg-body-strong);
    font-size: 13px;
    line-height: 1.55;
}

.connection-notice {
    margin-top: 9px;
}

.connection-notice strong {
    color: var(--sg-body-strong);
    font-size: 12px;
    font-weight: 600;
}

.connection-notice p {
    margin: 6px 0 0;
    color: var(--sg-muted);
    font-size: 10px;
    line-height: 1.5;
}

.assistant-message .result-disclosure {
    margin-right: 0;
    margin-left: 0;
}

.answer-markdown {
    margin-top: 10px;
    color: var(--sg-body);
    font-size: 14px;
    line-height: 1.55;
    overflow-wrap: anywhere;
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

.answer-markdown h1,
.answer-markdown h2,
.answer-markdown h3 {
    margin: 16px 0 8px;
    color: var(--sg-ink);
    font-weight: 700;
    letter-spacing: -0.2px;
}

.answer-markdown h1 {
    font-size: 18px;
}

.answer-markdown h2 {
    font-size: 16px;
}

.answer-markdown h3 {
    font-size: 14px;
}

.answer-markdown a {
    color: var(--sg-primary);
    text-decoration: underline;
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

.answer-markdown pre {
    margin: 10px 0;
    overflow-x: auto;
    padding: 12px;
    color: var(--sg-body);
    background: var(--sg-surface-card);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-sm);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    white-space: pre;
}

.answer-markdown pre code {
    padding: 0;
    color: inherit;
    background: transparent;
    font-size: inherit;
}

.answer-markdown table {
    width: 100%;
    margin: 10px 0;
    border-collapse: collapse;
    font-size: 12px;
}

.answer-markdown th,
.answer-markdown td {
    padding: 7px 8px;
    border: 1px solid var(--sg-hairline);
    text-align: left;
}

.answer-markdown th {
    color: var(--sg-ink);
    background: var(--sg-surface-card);
    font-weight: 600;
}

.runner-error {
    margin-top: 14px;
    padding: 11px 12px;
    color: var(--sg-body);
    background: rgba(239, 68, 68, 0.08);
    border-left: 3px solid var(--sg-error);
}

.runner-error strong {
    color: var(--sg-error);
    font-size: 11px;
    font-weight: 600;
}

.runner-error p {
    margin: 5px 0 0;
    color: var(--sg-body);
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    line-height: 1.5;
    overflow-wrap: anywhere;
}

/* Citations and trace */
.result-disclosure {
    margin: 0 18px 12px;
    background: #202020;
    border: 1px solid var(--sg-hairline-strong);
    border-radius: var(--sg-radius-md);
}

.citation-details {
    margin-top: 14px;
}

.result-disclosure summary {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 8px;
    align-items: center;
    padding: 14px 14px;
    cursor: pointer;
    list-style: none;
}

.result-disclosure summary::-webkit-details-marker {
    display: none;
}

.result-disclosure summary span,
.result-disclosure summary small {
    color: var(--sg-body-strong);
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

.result-disclosure summary small {
    color: var(--sg-muted);
    font-size: 12px;
    font-weight: 600;
}

.result-disclosure summary::after {
    content: "+";
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 20px;
}

.result-disclosure[open] summary::after {
    content: "−";
}

.citation-list {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 0 14px 14px;
    border-top: 1px solid var(--sg-hairline);
}

.citation-item {
    min-width: 0;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-top: 10px;
    padding: 12px 12px;
    background: #2a2a2a;
    border: 1px solid #484848;
    border-radius: 4px;
}

.citation-list b {
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
    font-weight: 700;
}

.citation-list span {
    color: var(--sg-body-strong);
    font-size: 14px;
    font-weight: 600;
    line-height: 1.65;
    overflow-wrap: anywhere;
}

.trace-details {
    margin-bottom: 18px;
}

.trace-table {
    padding: 8px 14px 14px;
    border-top: 1px solid var(--sg-hairline);
}

.trace-detail-trigger {
    width: 100%;
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 7px;
    align-items: center;
    margin-top: 4px;
    padding: 10px 12px;
    cursor: pointer;
    color: var(--sg-body-strong);
    background: #1e1e1e;
    border: 1px solid #484848;
    border-radius: 6px;
    text-align: left;
    transition: border-color 160ms ease, background 160ms ease;
}

.trace-detail-trigger span,
.trace-detail-trigger small {
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.6px;
}

.trace-detail-trigger span {
    color: var(--sg-primary);
}

.trace-detail-trigger small {
    justify-self: end;
    color: var(--sg-muted);
    font-size: 11px;
    font-weight: 600;
}

.trace-detail-trigger::after {
    content: "↗";
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
}

.trace-detail-trigger:hover {
    background: #252525;
    border-color: var(--sg-primary-border);
}

.trace-detail-trigger:focus-visible,
.trace-modal-close:focus-visible {
    outline: 2px solid var(--sg-primary);
    outline-offset: 2px;
}

.trace-detail-modal {
    width: min(760px, calc(100vw - 32px));
    max-width: 760px;
    max-height: min(82vh, 760px);
    margin: auto;
    padding: 0;
    overflow: hidden;
    color: var(--sg-ink);
    background: #161616;
    border: 1px solid #4a4a4a;
    border-radius: 14px;
    box-shadow: 0 28px 90px rgba(0, 0, 0, 0.72);
}

.trace-detail-modal::backdrop {
    background: rgba(0, 0, 0, 0.72);
    backdrop-filter: blur(7px);
}

.trace-detail-modal:popover-open {
    display: flex;
    flex-direction: column;
    animation: trace-modal-enter 180ms ease-out both;
}

@keyframes trace-modal-enter {
    from {
        opacity: 0;
        transform: translateY(12px) scale(0.985);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.trace-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    padding: 20px 22px;
    background: #1d1d1d;
    border-bottom: 1px solid var(--sg-hairline-strong);
}

.trace-modal-title {
    min-width: 0;
}

.trace-modal-eyebrow {
    display: block;
    color: var(--sg-primary);
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
}

.trace-modal-title h3 {
    margin: 5px 0 0;
    color: var(--sg-ink);
    font-size: 20px;
    font-weight: 700;
    line-height: 1.25;
}

.trace-modal-meta {
    display: flex;
    align-items: center;
    gap: 10px;
}

.trace-modal-meta time,
.trace-modal-status {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.trace-modal-meta time {
    color: var(--sg-muted);
}

.trace-modal-status {
    padding: 5px 8px;
    color: var(--sg-body-strong);
    background: #282828;
    border: 1px solid var(--sg-hairline-strong);
    border-radius: 9999px;
}

.trace-modal-status.trace-status-running {
    color: var(--sg-primary);
}

.trace-modal-status.trace-status-error {
    color: #fca5a5;
}

.trace-modal-close {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    padding: 0;
    cursor: pointer;
    color: var(--sg-body-strong);
    background: #292929;
    border: 1px solid #484848;
    border-radius: 8px;
    font-size: 22px;
    line-height: 1;
}

.trace-modal-close:hover {
    color: var(--sg-primary);
    border-color: var(--sg-primary-border);
}

.trace-modal-body {
    min-height: 0;
    flex: 1;
    padding: 20px 22px;
    overflow-y: auto;
}

.trace-modal-summary {
    padding: 14px 15px;
    background: var(--sg-primary-soft);
    border: 1px solid var(--sg-primary-border);
    border-radius: 8px;
}

.trace-modal-summary span,
.trace-modal-section-title span,
.trace-modal-section-title small {
    font-family: "JetBrains Mono", monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
}

.trace-modal-summary span {
    color: var(--sg-primary);
}

.trace-modal-summary p {
    margin: 7px 0 0;
    color: var(--sg-body-strong);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.65;
}

.trace-modal-footer {
    flex: 0 0 auto;
    padding: 11px 22px;
    color: var(--sg-muted);
    background: #121212;
    border-top: 1px solid var(--sg-hairline);
    font-family: "JetBrains Mono", monospace;
    font-size: 9px;
    letter-spacing: 0.6px;
}

.trace-detail-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin: 10px 0;
}

.trace-detail-item {
    min-width: 0;
    padding: 10px 11px;
    background: var(--sg-canvas);
    border: 1px solid var(--sg-hairline-strong);
    border-left: 3px solid var(--sg-primary-border);
}

.trace-detail-item-wide {
    grid-column: 1 / -1;
}

.trace-triple-list {
    display: grid;
    gap: 6px;
    margin-top: 8px;
}

.trace-triple-row {
    display: grid;
    grid-template-columns: 28px minmax(0, 1fr) auto;
    gap: 8px;
    align-items: center;
    padding: 8px 9px;
    background: #181818;
    border: 1px solid var(--sg-hairline);
}

.trace-triple-index,
.trace-triple-similarity {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: 700;
}

.trace-triple-expression {
    min-width: 0;
    overflow-wrap: anywhere;
    color: var(--sg-body-strong);
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    line-height: 1.55;
}

.trace-triple-node {
    color: var(--sg-body-strong);
    font-weight: 700;
}

.trace-triple-relation,
.trace-triple-similarity {
    color: var(--sg-primary);
}

.trace-triple-empty {
    margin-top: 8px;
    color: var(--sg-muted);
    font-size: 12px;
    font-weight: 500;
}

.trace-detail-item dt,
.trace-detail-item dd {
    margin: 0;
    overflow-wrap: anywhere;
}

.trace-detail-item dt {
    color: var(--sg-muted);
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.trace-detail-item dd {
    margin-top: 5px;
    color: var(--sg-body-strong);
    font-size: 13px;
    font-weight: 600;
    line-height: 1.6;
    white-space: pre-line;
}

.trace-raw-json {
    margin-top: 18px;
}

.trace-modal-section-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.trace-modal-section-title span {
    color: var(--sg-body-strong);
}

.trace-modal-section-title small {
    color: var(--sg-muted);
}

.trace-raw-json pre {
    max-height: 260px;
    margin: 0;
    padding: 14px;
    overflow: auto;
    color: var(--sg-body-strong);
    background: var(--sg-canvas);
    border: 1px solid var(--sg-hairline);
    border-radius: 8px;
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    font-weight: 500;
    line-height: 1.7;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.panel-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex: 0 0 auto;
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

@keyframes panel-enter {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes chat-exchange-enter {
    from {
        opacity: 0;
        transform: translateY(5px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes thinking-enter {
    from {
        opacity: 0;
        transform: translateY(4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes thinking-current-enter {
    from {
        opacity: 0.35;
        transform: translateX(-4px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes thinking-dot {
    0%,
    60%,
    100% {
        opacity: 0.35;
        transform: translateY(0) scale(0.8);
    }
    30% {
        opacity: 1;
        transform: translateY(-3px) scale(1);
    }
}

@keyframes trace-row-enter {
    from {
        opacity: 0;
        transform: translateX(-4px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes trace-active-pulse {
    0%,
    100% {
        opacity: 0.55;
        transform: scale(0.8);
    }
    50% {
        opacity: 1;
        transform: scale(1.25);
    }
}

@media (prefers-reduced-motion: reduce) {
    .panel-result,
    .current-exchange,
    .thinking-state,
    .thinking-current,
    .trace-event-row,
    .trace-detail-modal,
    .thinking-mark i,
    .trace-event-row.is-active .trace-event-dot {
        animation: none !important;
    }
}

@media (max-width: 1050px) {
    .shared-controls {
        grid-template-columns: repeat(4, 1fr);
    }

    .shared-controls-title {
        grid-column: 1 / -1;
        min-height: 58px !important;
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
        padding-top: 8px;
    }

    .card-header {
        flex-direction: column;
    }

    .card-status-group {
        justify-content: flex-start;
        margin-left: 42px;
    }

    .chat-history {
        padding-right: 12px;
        padding-left: 12px;
    }

    .user-message {
        max-width: 88%;
    }

    .assistant-message,
    .thinking-message {
        max-width: 100%;
        width: 100%;
    }

    .citation-list {
        grid-template-columns: 1fr;
    }

    .trace-detail-grid {
        grid-template-columns: 1fr;
    }

    .trace-detail-modal {
        width: calc(100vw - 20px);
        max-height: calc(100vh - 20px);
        border-radius: 10px;
    }

    .trace-modal-header {
        align-items: flex-start;
        padding: 16px;
    }

    .trace-modal-meta {
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .trace-modal-body {
        padding: 16px;
    }

    .trace-modal-footer {
        padding: 10px 16px;
    }

}
</style>
"""


def apply_custom_style():
    """Load the ClickHouse-inspired design tokens and component overrides."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
