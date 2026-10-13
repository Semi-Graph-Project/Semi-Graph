import streamlit as st


CUSTOM_CSS = """
<style>
:root {
    /* Match Ant Design's light, token-based visual language. */
    --color-bg: #f7f9fc;
    --color-surface: #ffffff;
    --color-raised: #fafafa;
    --color-text: #262626;
    --color-heading: #101c49;
    --color-muted: #62708f;
    --color-primary: #435bff;
    --color-primary-hover: #344bea;
    --color-on-primary: #ffffff;
    --color-primary-soft: #eef2ff;
    --color-primary-border: #cbd5ff;
    --color-success: #079b70;
    --color-warning: #ad6800;
    --color-error: #cf1322;
    --color-border: #e7ebf3;
    --color-control-border: #dce3ef;
    --rgb-primary: 67, 91, 255;
    --rgb-success: 7, 155, 112;
    --rgb-error: 255, 77, 79;
    --rgb-warning: 250, 173, 20;
    --font-display: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
    --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
    --font-mono: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --radius-control: 6px;
    --radius-card: 8px;
    --radius-feature: 12px;
    --duration-fast: 160ms;
    --duration-reveal: 240ms;
    --shadow-card: 0 1px 2px rgba(0, 0, 0, 0.03);
    --shadow-modal: 0 9px 28px 8px rgba(0, 0, 0, 0.05), 0 6px 16px rgba(0, 0, 0, 0.08);

    --sg-primary: var(--color-primary);
    --sg-primary-active: var(--color-primary-hover);
    --sg-primary-soft: var(--color-primary-soft);
    --sg-primary-border: var(--color-primary-border);
    --sg-ink: var(--color-heading);
    --sg-body: var(--color-text);
    --sg-body-strong: var(--color-heading);
    --sg-muted: var(--color-muted);
    --sg-muted-soft: var(--color-muted);
    --sg-hairline: var(--color-border);
    --sg-hairline-strong: var(--color-control-border);
    --sg-canvas: var(--color-bg);
    --sg-surface-soft: var(--color-surface);
    --sg-surface-card: var(--color-surface);
    --sg-surface-elevated: var(--color-raised);
    --sg-success: var(--color-success);
    --sg-warning: var(--color-warning);
    --sg-error: var(--color-error);
    --sg-radius-sm: var(--radius-control);
    --sg-radius-md: var(--radius-control);
    --sg-radius-lg: var(--radius-card);
}

html,
body,
[class*="css"] {
    font-family: var(--font-body);
}

h1,
h2,
h3,
h4,
h5,
h6 {
    font-family: var(--font-display);
}

html,
body,
[data-testid="stAppViewContainer"],
.stApp {
    background: var(--sg-canvas);
    color: var(--sg-ink);
}

:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
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
    padding: 0 1.25rem 3rem;
}

/* Application header */
.st-key-comparison-topbar {
    margin: 0 0 8px;
    padding: 4px 0 6px;
    border-bottom: 1px solid var(--sg-hairline);
}

.st-key-comparison-topbar [data-testid="stHorizontalBlock"] {
    align-items: center;
    gap: 12px;
}

.st-key-comparison-topbar [data-testid="stColumn"] {
    min-width: 0;
}

.topbar-brand {
    min-height: 34px;
    display: flex;
    align-items: center;
    gap: 10px;
    white-space: nowrap;
}

.topbar-kicker {
    color: #24345f;
    font-size: 12px;
    font-weight: 750;
    letter-spacing: 0.7px;
}

.topbar-divider {
    width: 1px;
    height: 22px;
    background: var(--sg-hairline-strong);
}

.topbar-brand h1 {
    margin: 0;
    color: var(--sg-ink);
    font-size: clamp(20px, 2vw, 28px);
    font-weight: 750;
    letter-spacing: -0.7px;
    line-height: 1.15;
}

.topbar-live-mode,
.topbar-query-live {
    min-height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 0 8px;
    color: var(--sg-primary);
    background: #f3f5ff;
    border: 1px solid #e1e6ff;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 650;
    white-space: nowrap;
}

.topbar-query-live {
    flex-direction: column;
    align-items: flex-start;
    justify-content: center;
    gap: 1px;
    color: var(--sg-ink);
}

.topbar-query-live small {
    color: var(--sg-muted);
    font-size: 9px;
    letter-spacing: 0.7px;
}

.topbar-query-live strong {
    font-size: 12px;
}

.topbar-live-mode .mode-dot {
    width: 7px;
    height: 7px;
    display: inline-block;
    background: var(--sg-success);
    border-radius: 50%;
}

.st-key-comparison-topbar [data-testid="stSelectbox"] {
    max-width: none;
    margin: 0;
}

.st-key-comparison-topbar [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 34px;
    padding-left: 9px;
    background: #f7f9fd;
    border-color: #e2e8f2;
    border-radius: 10px;
}

.st-key-comparison-topbar [data-testid="stSegmentedControl"] {
    width: 100%;
    min-height: 34px;
    padding: 3px;
    background: #f3f5fa;
    border: 1px solid #e4e8f0;
    border-radius: 11px;
}

.st-key-comparison-topbar [data-testid="stSegmentedControl"] button {
    min-height: 26px;
    border-radius: 8px;
    font-weight: 600;
}

/* Intro and controlled variables */
.comparison-workspace {
    padding-top: 0;
}

.question-banner {
    min-height: 0;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin: 0 0 8px;
    padding: 8px 16px;
    overflow: hidden;
    background: linear-gradient(105deg, #f2f5fb 0%, #f8faff 100%);
    border: 1px solid #e5eaf3;
    border-radius: 12px;
}

.question-banner > span:first-child {
    color: #586a92;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.1px;
}

.question-banner p {
    max-width: calc(100% - 130px);
    margin: 3px 0 0;
    color: var(--sg-ink);
    font-size: clamp(17px, 1.7vw, 23px);
    font-weight: 720;
    letter-spacing: -0.65px;
    line-height: 1.18;
    overflow-wrap: anywhere;
}

.question-banner.is-empty p {
    color: var(--sg-muted);
    font-weight: 600;
}

.question-query-id {
    position: absolute;
    top: 50%;
    right: 16px;
    transform: translateY(-50%);
    padding: 6px 9px;
    color: #314785;
    background: #fff;
    border: 1px solid #e1e7f2;
    border-radius: 9px;
    font-size: 12px;
    font-weight: 700;
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
    color: var(--sg-primary);
    background: var(--sg-primary-soft);
    border: 1px solid var(--sg-primary-border);
    border-radius: var(--radius-control);
    font-size: 12px;
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
    font-family: var(--font-body);
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
    font-family: var(--font-body);
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
    font-family: var(--font-body);
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
    border-radius: var(--radius-control);
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(var(--rgb-primary), 0.12);
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

/* Vector and Graph, with Agent off and on. */
.comparison-grid {
    display: grid;
    grid-template-columns: 100px repeat(2, minmax(0, 1fr));
    grid-template-rows: 30px repeat(2, minmax(0, 1fr));
    gap: 6px 8px;
}

.matrix-column-heading {
    display: grid;
    place-items: center;
    color: var(--sg-ink);
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
}

.vector-column {
    background: #eef2ff;
}

.graph-column {
    color: #087f79;
    background: #e8f7f5;
}

.matrix-row-heading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: var(--sg-ink);
    background: #f2f5fa;
    border: 1px solid #e5eaf3;
    border-radius: 11px;
    text-align: center;
}

.matrix-row-heading strong {
    font-size: 15px;
    font-weight: 700;
}

.agent-on-row {
    background: #f1f4ff;
}

.row-mode-icon {
    width: 29px;
    height: 29px;
    display: grid;
    place-items: center;
    position: relative;
    color: var(--sg-primary);
}

.row-mode-off::before {
    content: "◉";
    color: #8593b1;
    font-size: 26px;
}

.row-mode-off::after {
    content: "";
    position: absolute;
    width: 28px;
    height: 2px;
    background: #8593b1;
    transform: rotate(-45deg);
}

.row-mode-on::before {
    content: "";
    width: 20px;
    height: 15px;
    border: 2px solid currentColor;
    border-radius: 5px;
}

.row-mode-on::after {
    content: "••";
    position: absolute;
    top: 2px;
    color: currentColor;
    font-size: 13px;
    letter-spacing: 2px;
}

.comparison-card {
    min-width: 0;
    height: clamp(180px, calc((100vh - 350px) / 2), 310px);
    min-height: 0;
    display: flex;
    flex-direction: column;
    position: relative;
    box-sizing: border-box;
    overflow: hidden;
    background: var(--sg-surface-soft);
    border: 1px solid #e4e9f2;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(26, 48, 93, 0.04);
}

.featured-card {
    border: 2px solid #5e70ff;
    box-shadow: 0 2px 10px rgba(67, 91, 255, 0.08);
}

.card-header {
    min-height: 40px;
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 8px;
    padding: 5px 10px 1px;
}

.architecture-icons {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 3px;
    padding: 2px;
    background: #f7f9fd;
    border: 1px solid #e7ecf5;
    border-radius: 12px;
}

.architecture-icon {
    width: 27px;
    height: 27px;
    display: inline-block;
    position: relative;
    color: #4d6296;
    background: #f1f4fb;
    border-radius: 10px;
}

.vector-icon::before {
    content: "";
    position: absolute;
    top: 8px;
    left: 9px;
    width: 16px;
    height: 18px;
    border: 2px solid currentColor;
    border-radius: 50% / 20%;
}

.vector-icon::after {
    content: "";
    position: absolute;
    top: 14px;
    left: 11px;
    width: 12px;
    height: 6px;
    border-top: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
}

.graph-icon {
    color: #00a696;
    background: #effaf8;
}

.graph-icon::before {
    content: "";
    position: absolute;
    top: 9px;
    left: 9px;
    width: 15px;
    height: 13px;
    border-left: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: skew(-28deg);
}

.graph-icon::after {
    content: "";
    position: absolute;
    top: 6px;
    left: 13px;
    width: 6px;
    height: 6px;
    background: currentColor;
    border: 2px solid #effaf8;
    border-radius: 50%;
    box-shadow: -8px 15px 0 -1px #effaf8, -8px 15px 0 1px currentColor,
        9px 11px 0 -1px #effaf8, 9px 11px 0 1px currentColor;
}

.agent-icon {
    color: #304eff;
    background: #eef2ff;
}

.agent-icon::before {
    content: "";
    position: absolute;
    top: 12px;
    left: 8px;
    width: 18px;
    height: 13px;
    border: 2px solid currentColor;
    border-radius: 5px;
}

.agent-icon::after {
    content: "••";
    position: absolute;
    top: 9px;
    left: 12px;
    color: currentColor;
    font-size: 12px;
    letter-spacing: 2px;
}

.card-header h3 {
    min-width: 0;
    margin: 0;
    color: var(--sg-ink);
    font-size: clamp(15px, 1.2vw, 18px);
    font-weight: 730;
    letter-spacing: -0.45px;
    line-height: 1.2;
}

.card-overview-body {
    min-height: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 0 10px 6px;
}

.card-answer-preview {
    min-height: 0;
    flex: 1;
    overflow: hidden;
    color: #435170;
    font-size: 12px;
    line-height: 1.32;
}

.card-answer-preview p {
    display: -webkit-box;
    margin: 0 0 2px;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
}

.card-answer-preview ul,
.card-answer-preview ol {
    margin: 0;
    padding-left: 18px;
}

.card-answer-preview.is-empty,
.card-answer-preview.is-running {
    display: flex;
    align-items: center;
    color: var(--sg-muted);
}

.card-answer-preview.is-error {
    color: var(--sg-error);
}

.answer-loading-dot {
    width: 8px;
    height: 8px;
    flex: 0 0 auto;
    margin-right: 9px;
    background: var(--sg-primary);
    border-radius: 50%;
    animation: trace-active-pulse 1.15s ease-in-out infinite;
}

.card-metrics {
    min-height: 25px;
    display: flex;
    align-items: center;
    gap: 5px;
    flex-wrap: wrap;
}

.card-metric,
.card-status {
    min-height: 24px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 7px;
    color: #34466f;
    background: #f1f4fa;
    border-radius: 8px;
    font-size: 10px;
    font-weight: 600;
    white-space: nowrap;
}

.card-metric i {
    color: #4058a0;
    font-size: 14px;
    font-style: normal;
    line-height: 1;
}

.card-metric strong {
    color: #30446f;
    font-size: 11px;
}

.citation-metric i {
    color: var(--sg-primary);
    font-size: 21px;
    font-weight: 800;
}

.card-status {
    margin-left: auto;
    padding-inline: 12px;
    color: var(--sg-success);
    background: #eaf8f2;
}

.card-status i {
    width: 15px;
    height: 15px;
    display: grid;
    place-items: center;
    color: #fff;
    background: var(--sg-success);
    border-radius: 50%;
    font-size: 10px;
    font-style: normal;
}

.card-status.running {
    color: var(--sg-primary);
    background: var(--sg-primary-soft);
}

.card-status.running i {
    background: var(--sg-primary);
}

.card-status.error {
    color: var(--sg-error);
    background: #fff1f0;
}

.card-status.error i {
    background: var(--sg-error);
}

.card-status.waiting {
    color: var(--sg-muted);
    background: #f1f3f6;
}

.card-status.waiting i {
    background: #8995ad;
}

.card-stage-strip {
    min-height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border-top: 1px solid #e8edf5;
    color: #657696;
    font-size: 10px;
}

.stage-item {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}

.stage-item i {
    width: 7px;
    height: 7px;
    border: 2px solid #506593;
    border-radius: 50%;
}

.stage-connector {
    color: #a4b0c7;
}

.card-overview-body > .chat-modal-trigger {
    min-height: 29px;
    justify-content: center;
    padding: 4px 9px;
    color: #2149ff;
    background: linear-gradient(90deg, #f1f4ff, #f7f8ff);
    border: 1px solid #667cff;
    border-radius: 8px;
    font-size: 12px;
}

.card-overview-body > .chat-modal-trigger::before {
    content: "";
    width: 16px;
    height: 12px;
    margin-right: 7px;
    border: 2px solid currentColor;
    border-radius: 4px;
    box-shadow: -2px 4px 0 -1px #f1f4ff;
}

.card-overview-body > .chat-modal-trigger:hover {
    background: #e8edff;
    border-color: #4058ff;
}

.card-overview-body > .chat-modal-trigger span {
    font-weight: 700;
}

.card-overview-body > .chat-detail-modal {
    padding: 0;
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
    font-family: var(--font-mono);
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
    animation: thinking-enter var(--duration-reveal) ease-out both;
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
    animation-delay: var(--duration-reveal);
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
    font-family: var(--font-body);
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
    animation: thinking-current-enter var(--duration-reveal) ease-out both;
}

.thinking-current p {
    margin: 5px 0 0;
    color: var(--sg-body-strong);
    font-family: var(--font-mono);
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
    animation: trace-row-enter var(--duration-reveal) ease-out both;
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
    animation-delay: var(--duration-fast);
}

.trace-event-row:nth-child(5) {
    animation-delay: 240ms;
}

.trace-event-index {
    color: var(--sg-body-strong);
    font-family: var(--font-mono);
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
    font-family: var(--font-body);
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
    background: rgba(var(--rgb-success), 0.1);
    border: 1px solid rgba(var(--rgb-success), 0.28);
    border-radius: var(--radius-control);
}

.trace-status-running .trace-status-pill {
    color: var(--sg-primary);
    background: var(--sg-primary-soft);
    border-color: var(--sg-primary-border);
}

.trace-status-error .trace-status-pill {
    color: var(--sg-error);
    background: rgba(var(--rgb-error), 0.08);
    border-color: rgba(var(--rgb-error), 0.24);
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
    margin-top: 12px;
    overflow: hidden;
    background: var(--sg-surface-card);
    border-top: 1px solid var(--sg-hairline);
}

.panel-result-running {
    animation: panel-enter var(--duration-reveal) ease-out both;
}

.compact-result {
    background: var(--sg-surface-card);
}

.compact-trace-list {
    min-height: 0;
    flex: 1;
    padding: 6px 12px;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-color: var(--sg-hairline-strong) var(--sg-surface-card);
    scrollbar-width: thin;
}

.compact-trace-row {
    display: grid;
    grid-template-columns: 24px 7px minmax(0, 1fr);
    gap: 7px;
    align-items: start;
    padding: 10px 0;
    border-bottom: 1px solid var(--sg-hairline);
}

.compact-trace-row:last-child {
    border-bottom: 0;
}

.compact-trace-index {
    color: var(--sg-muted);
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
}

.compact-trace-dot {
    width: 7px;
    height: 7px;
    margin-top: 2px;
    background: var(--sg-success);
    border-radius: 9999px;
}

.compact-trace-row.trace-status-running .compact-trace-dot {
    background: var(--sg-primary);
}

.compact-trace-row.trace-status-error .compact-trace-dot {
    background: var(--sg-error);
}

.compact-trace-row.trace-status-skipped .compact-trace-dot {
    background: var(--sg-muted-soft);
}

.compact-trace-row.is-active .compact-trace-dot {
    animation: trace-active-pulse 1.15s ease-in-out infinite;
}

.compact-trace-copy {
    min-width: 0;
}

.compact-trace-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
}

.compact-trace-heading b {
    min-width: 0;
    overflow: hidden;
    color: var(--sg-body-strong);
    font-size: 12px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.compact-trace-heading span {
    display: inline-flex;
    flex: 0 0 auto;
    gap: 5px;
    color: var(--sg-muted);
    font-family: var(--font-body);
    font-size: 10px;
    font-weight: 600;
}

.compact-trace-copy p {
    display: -webkit-box;
    margin: 4px 0 0;
    overflow: hidden;
    color: var(--sg-muted);
    font-size: 11px;
    line-height: 1.5;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
}

.panel-action-bar {
    flex: 0 0 auto;
    padding: 10px 12px;
    background: var(--sg-surface-card);
    border-top: 1px solid var(--sg-hairline);
}

.chat-modal-trigger {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-height: 44px;
    padding: 12px 14px;
    cursor: pointer;
    color: var(--color-on-primary);
    background: var(--sg-primary);
    border: 1px solid var(--sg-primary);
    border-radius: var(--radius-control);
    font-family: var(--font-body);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0;
}

.chat-modal-trigger small {
    color: var(--color-on-primary);
    font-family: var(--font-body);
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0;
}

.chat-modal-trigger:hover {
    color: var(--color-on-primary);
    background: var(--sg-primary-active);
    border-color: var(--sg-primary-active);
}

.chat-modal-trigger:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
}

.chat-detail-modal {
    width: min(1080px, calc(100vw - 48px));
    max-width: 1080px;
    height: min(88vh, 820px);
    max-height: calc(100vh - 40px);
    margin: auto;
    padding: 0;
    overflow: hidden;
    color: var(--sg-ink);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-modal);
}

.chat-detail-modal::backdrop {
    background: rgba(0, 0, 0, 0.35);
}

.chat-detail-modal:popover-open {
    display: flex;
    flex-direction: column;
    animation: trace-modal-enter var(--duration-fast) ease-out both;
}

.chat-modal-body {
    min-height: 0;
    flex: 1;
    position: relative;
    overflow: hidden;
}

.chat-modal-history {
    position: absolute;
    inset: 0;
    width: auto;
    min-width: 0;
    min-height: 0;
    height: auto;
    box-sizing: border-box;
    padding: 12px 28px 32px;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-color: var(--sg-hairline-strong) var(--sg-surface-card);
    scrollbar-width: thin;
}

.chat-modal-history:focus {
    outline: none;
}

.chat-detail-modal .chat-message {
    max-width: 88%;
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
    font-family: var(--font-body);
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
    background: var(--color-raised);
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
    animation: chat-exchange-enter var(--duration-reveal) ease-out both;
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
        background-color var(--duration-fast) ease,
        border-color var(--duration-fast) ease;
}

.user-message {
    position: relative;
    width: fit-content;
    max-width: 78%;
    margin-right: 6px;
    background: var(--color-primary-soft);
    border-color: var(--color-primary-border);
}

.assistant-message {
    width: fit-content;
    max-width: 92%;
    background: var(--color-surface);
    border-color: var(--sg-hairline);
    box-shadow: var(--shadow-card);
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
    background: var(--color-primary-soft);
}

.answer-turn {
    background: var(--color-surface);
}

.turn-label,
.live-label {
    color: var(--sg-muted);
    font-family: var(--font-body);
    font-size: 12px;
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
    font-size: 16px;
    line-height: 1.65;
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
    font-size: 16px;
    line-height: 1.65;
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
    font-family: var(--font-mono);
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
    font-family: var(--font-mono);
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
    background: rgba(var(--rgb-error), 0.08);
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
    font-family: var(--font-mono);
    font-size: 10px;
    line-height: 1.5;
    overflow-wrap: anywhere;
}

/* Citations and trace */
.result-disclosure {
    margin: 0 18px 12px;
    background: var(--color-surface);
    border: 1px solid var(--sg-hairline-strong);
    border-radius: var(--sg-radius-md);
}

.citation-details {
    margin-top: 14px;
}

.synthesis-chunks-details {
    margin-bottom: 12px;
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
    font-family: var(--font-body);
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
    font-family: var(--font-mono);
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
    background: var(--color-raised);
    border: 1px solid var(--color-control-border);
    border-radius: var(--radius-control);
}

.citation-list b {
    color: var(--sg-primary);
    font-family: var(--font-mono);
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

.synthesis-chunk-list {
    display: grid;
    gap: 8px;
    padding: 10px 14px 14px;
    border-top: 1px solid var(--sg-hairline);
}

.synthesis-chunk {
    min-width: 0;
    overflow: hidden;
    background: var(--color-surface);
    border: 1px solid var(--sg-hairline-strong);
    border-radius: var(--sg-radius-sm);
}

.synthesis-chunk summary {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto auto;
    gap: 10px;
    align-items: center;
    padding: 10px 12px;
    cursor: pointer;
    list-style: none;
}

.synthesis-chunk summary::-webkit-details-marker {
    display: none;
}

.synthesis-chunk summary::after {
    content: "+";
    color: var(--sg-primary);
    font-family: var(--font-mono);
    font-size: 14px;
}

.synthesis-chunk[open] summary::after {
    content: "−";
}

.synthesis-chunk-number {
    color: var(--sg-muted);
    font-family: var(--font-mono);
    font-size: 10px;
}

.synthesis-chunk summary code {
    min-width: 0;
    color: var(--sg-body-strong);
    font-family: var(--font-mono);
    font-size: 11px;
    overflow-wrap: anywhere;
}

.synthesis-chunk-status {
    padding: 4px 7px;
    border: 1px solid transparent;
    border-radius: var(--radius-control);
    font-family: var(--font-mono);
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.4px;
    white-space: nowrap;
}

.synthesis-chunk-status.chunk-cited {
    color: var(--sg-success);
    background: rgba(var(--rgb-success), 0.1);
    border-color: rgba(var(--rgb-success), 0.28);
}

.synthesis-chunk-status.chunk-not-cited {
    color: var(--sg-warning);
    background: rgba(var(--rgb-warning), 0.10);
    border-color: rgba(var(--rgb-warning), 0.24);
}

.synthesis-chunk-content {
    padding: 0 12px 12px;
    border-top: 1px solid var(--sg-hairline);
}

.synthesis-chunk-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 10px 0;
}

.synthesis-chunk-meta-item {
    padding: 4px 7px;
    color: var(--sg-muted);
    background: var(--color-raised);
    border-radius: var(--radius-control);
    font-size: 10px;
}

.synthesis-chunk-text {
    max-height: 320px;
    margin: 0;
    padding: 12px;
    overflow: auto;
    color: var(--sg-body);
    background: var(--color-bg);
    border: 1px solid var(--sg-hairline);
    border-radius: var(--sg-radius-sm);
    font-family: var(--font-mono);
    font-size: 10px;
    line-height: 1.6;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.synthesis-chunk-unavailable,
.synthesis-chunk-empty {
    margin: 8px 0 0;
    padding: 11px 12px;
    color: var(--sg-muted);
    background: var(--color-bg);
    border-radius: var(--sg-radius-sm);
    font-size: 11px;
    line-height: 1.55;
}

.synthesis-chunk-empty {
    margin: 0;
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
    background: var(--color-raised);
    border: 1px solid var(--color-control-border);
    border-radius: var(--radius-control);
    text-align: left;
    transition: border-color var(--duration-fast) ease, background var(--duration-fast) ease;
}

.trace-detail-trigger span,
.trace-detail-trigger small {
    font-family: var(--font-body);
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
    font-family: var(--font-mono);
    font-size: 14px;
}

.trace-detail-trigger:hover {
    background: var(--color-primary-soft);
    border-color: var(--sg-primary-border);
}

.trace-detail-trigger:focus-visible,
.trace-modal-close:focus-visible {
    outline: 2px solid var(--color-primary);
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
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-modal);
}

.trace-detail-modal::backdrop {
    background: rgba(0, 0, 0, 0.35);
}

.trace-detail-modal:popover-open {
    display: flex;
    flex-direction: column;
    animation: trace-modal-enter var(--duration-fast) ease-out both;
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
    background: var(--color-surface);
    border-bottom: 1px solid var(--sg-hairline-strong);
}

.trace-modal-title {
    min-width: 0;
}

.trace-modal-eyebrow {
    display: block;
    color: var(--sg-primary);
    font-family: var(--font-body);
    font-size: 12px;
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
    font-family: var(--font-body);
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
    background: var(--color-raised);
    border: 1px solid var(--sg-hairline-strong);
    border-radius: var(--radius-control);
}

.trace-modal-status.trace-status-running {
    color: var(--sg-primary);
}

.trace-modal-status.trace-status-error {
    color: var(--sg-error);
}

.trace-modal-close {
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    padding: 0;
    cursor: pointer;
    color: var(--sg-body-strong);
    background: var(--color-raised);
    border: 1px solid var(--color-control-border);
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
    font-family: var(--font-body);
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
    background: var(--color-raised);
    border-top: 1px solid var(--sg-hairline);
    font-family: var(--font-body);
    font-size: 12px;
    letter-spacing: 0;
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
    background: var(--color-surface);
    border: 1px solid var(--sg-hairline);
}

.trace-triple-index,
.trace-triple-similarity {
    color: var(--sg-muted);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
}

.trace-triple-expression {
    min-width: 0;
    overflow-wrap: anywhere;
    color: var(--sg-body-strong);
    font-family: var(--font-mono);
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
    font-family: var(--font-mono);
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
    font-family: var(--font-body);
    font-size: 8px;
    letter-spacing: 0.5px;
}

.panel-footer-waiting {
    margin-top: 0;
}

.composer-hint {
    margin: 24px 0 0;
    color: var(--sg-muted-soft);
    font-family: var(--font-body);
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
    border-radius: var(--radius-control);
    box-shadow: none;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgba(var(--rgb-primary), 0.12);
}

[data-testid="stChatInput"] textarea {
    color: var(--sg-ink);
    caret-color: var(--sg-primary);
}

[data-testid="stChatInput"] textarea:focus-visible {
    outline: none;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--sg-muted);
}

[data-testid="stChatInputSubmitButton"] {
    color: var(--color-on-primary);
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

/* Full Chat: keep the answer prominent and the evidence secondary. */
.chat-detail-modal {
    --chat-accent: #4f46e5;
    --chat-accent-soft: #eef2ff;
    --chat-text: #0f172a;
    --chat-muted: #64748b;
    --chat-border: #e2e8f0;
    color: var(--chat-text);
    background: #f8fafc;
    border-color: var(--chat-border);
    border-radius: 14px;
}

.chat-detail-modal .trace-modal-header {
    padding: 16px 22px;
    border-color: var(--chat-border);
}

.chat-detail-modal .trace-modal-close {
    width: 38px;
    height: 38px;
    font-size: 19px;
}

.chat-detail-modal .trace-modal-eyebrow,
.chat-detail-modal .turn-label,
.chat-evidence > h4 {
    color: var(--chat-accent);
    font-weight: 700;
    letter-spacing: 1.3px;
}

.chat-detail-modal .trace-modal-eyebrow,
.chat-detail-modal .turn-label,
.chat-evidence > h4 {
    display: inline-flex;
    align-items: center;
    gap: 9px;
}

.chat-icon {
    position: relative;
    display: inline-block;
    flex: 0 0 18px;
    width: 18px;
    height: 18px;
    color: inherit;
}

.chat-icon::before,
.chat-icon::after {
    content: "";
    position: absolute;
    box-sizing: border-box;
}

.chat-icon-bubble::before {
    top: 2px;
    left: 2px;
    width: 14px;
    height: 12px;
    border: 2px solid currentColor;
    border-radius: 5px;
}

.chat-icon-bubble::after {
    bottom: 1px;
    left: 5px;
    width: 5px;
    height: 5px;
    border-left: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: skewY(-20deg);
}

.chat-icon-answer::before {
    top: 1px;
    left: 1px;
    width: 16px;
    height: 15px;
    border: 2px solid currentColor;
    border-radius: 4px;
}

.chat-icon-answer::after,
.chat-icon-check::after {
    top: 2px;
    left: 7px;
    width: 5px;
    height: 9px;
    border-right: 2px solid currentColor;
    border-bottom: 2px solid currentColor;
    transform: rotate(45deg);
}

.chat-icon-document::before {
    top: 0;
    left: 2px;
    width: 14px;
    height: 18px;
    border: 2px solid currentColor;
    border-radius: 3px;
}

.chat-icon-document::after {
    top: 7px;
    left: 6px;
    width: 6px;
    height: 2px;
    background: currentColor;
    box-shadow: 0 4px 0 currentColor;
}

.chat-icon-stack::before,
.chat-icon-stack::after {
    left: 2px;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    transform: rotate(45deg) scale(0.65);
}

.chat-icon-stack::before {
    top: -1px;
}

.chat-icon-stack::after {
    top: 4px;
}

.chat-icon-gear::before {
    content: "⚙";
    inset: -3px 0 0;
    font-size: 21px;
    line-height: 20px;
}

.chat-detail-modal .trace-modal-eyebrow .chat-icon {
    flex-basis: 24px;
    width: 24px;
    height: 24px;
    color: var(--chat-accent);
    background: var(--chat-accent-soft);
    border-radius: 50%;
}

.chat-detail-modal .trace-modal-eyebrow .chat-icon::before {
    top: 6px;
    left: 6px;
}

.chat-detail-modal .trace-modal-eyebrow .chat-icon::after {
    bottom: 4px;
    left: 9px;
}

.chat-detail-modal .trace-modal-title h3 {
    margin-top: 6px;
    color: var(--chat-text);
    font-size: 25px;
    letter-spacing: -0.5px;
}

.chat-modal-subtitle {
    margin: 5px 0 0;
    color: var(--chat-muted);
    font-size: 14px;
}

.chat-detail-modal .trace-modal-status.trace-status-complete {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 7px 11px;
    color: #15803d;
    background: #ecfdf5;
    border-color: #d1fae5;
    border-radius: 10px;
    font-size: 13px;
}

.chat-detail-modal .trace-modal-status.trace-status-complete::before {
    content: "✓";
    display: grid;
    place-items: center;
    width: 18px;
    height: 18px;
    color: #fff;
    background: #16a34a;
    border-radius: 50%;
    font-size: 14px;
}

.chat-detail-modal .chat-modal-history {
    padding: 14px 24px 28px;
    background: #f8fafc;
}

.chat-detail-modal .chat-exchange {
    gap: 18px;
    border-color: var(--chat-border);
}

.chat-detail-modal .chat-message {
    max-width: 100%;
}

.chat-detail-modal .user-message {
    max-width: min(78%, 850px);
    color: var(--chat-text);
    background: var(--chat-accent-soft);
    border: 0;
    border-radius: 14px 14px 4px 14px;
    box-shadow: none;
}

.chat-detail-modal .assistant-message {
    width: 100%;
    padding: 24px;
    color: var(--chat-text);
    background: #fff;
    border: 1px solid var(--chat-border);
    border-radius: 12px;
    box-shadow: none;
}

.chat-detail-modal .answer-label-row {
    margin-bottom: 20px;
}

.chat-detail-modal .live-label {
    padding: 6px 10px;
    color: var(--chat-accent);
    background: var(--chat-accent-soft);
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
}

.chat-detail-modal .answer-markdown {
    max-width: 850px;
    margin: 0;
    color: var(--chat-text);
    font-size: 18px;
    line-height: 1.7;
}

.chat-detail-modal .answer-markdown p {
    margin-bottom: 14px;
}

.citation-chip {
    display: inline-flex;
    align-items: center;
    margin: 0 2px;
    padding: 2px 7px;
    cursor: pointer;
    color: var(--chat-accent);
    background: var(--chat-accent-soft);
    border: 0;
    border-radius: 7px;
    font: 600 13px var(--font-body);
    vertical-align: baseline;
}

.citation-chip:hover,
.citation-chip:focus-visible {
    background: #dfe4ff;
    outline: 2px solid var(--chat-accent);
    outline-offset: 1px;
}

.source-inspector {
    position: fixed;
    top: 50%;
    right: max(20px, calc((100vw - 1180px) / 2 + 20px));
    left: auto;
    width: min(420px, calc(100vw - 40px));
    max-height: min(72vh, 650px);
    margin: 0;
    padding: 20px;
    overflow: auto;
    color: #0f172a;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
    transform: translateY(-50%);
}

.source-inspector::backdrop {
    background: transparent;
}

.source-inspector-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    color: #4f46e5;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.source-inspector-heading button {
    width: 32px;
    height: 32px;
    cursor: pointer;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 20px;
}

.source-inspector b {
    display: block;
    overflow-wrap: anywhere;
    font-size: 15px;
}

.source-inspector p {
    margin: 14px 0 0;
    color: #334155;
    font-size: 14px;
    line-height: 1.7;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.chat-evidence > h4 {
    margin: 0 0 12px;
    font-size: 14px;
}

.retrieval-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 24px;
}

.retrieval-metrics > div {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 18px;
    background: #f8fafc;
    border: 1px solid var(--chat-border);
    border-radius: 10px;
}

.retrieval-metrics .metric-icon {
    display: grid;
    flex: 0 0 44px;
    place-items: center;
    width: 44px;
    height: 44px;
    color: var(--chat-accent);
    background: var(--chat-accent-soft);
    border-radius: 50%;
}

.retrieval-metrics .metric-icon-used {
    color: #16a34a;
    background: #e8f8ef;
}

.retrieval-metrics .metric-copy {
    display: flex;
    min-width: 0;
    flex-direction: column;
    gap: 3px;
}

.retrieval-metrics strong {
    color: var(--chat-text);
    font-size: 22px;
    line-height: 1.2;
}

.retrieval-metrics span {
    color: var(--chat-muted);
    font-size: 12px;
}

.chat-evidence {
    width: 100%;
    padding: 8px 2px 4px;
}

.chat-detail-modal .chat-evidence > h4 {
    color: var(--chat-accent);
}

.chat-evidence .result-disclosure {
    margin: 8px 0;
    background: #fff;
    border: 1px solid var(--chat-border);
    border-radius: 10px;
}

.chat-evidence .result-disclosure summary {
    grid-template-columns: 32px minmax(0, 1fr) auto auto;
    gap: 12px;
    padding: 15px 18px;
}

.chat-evidence .result-disclosure summary .evidence-row-icon {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    color: var(--chat-accent);
    background: var(--chat-accent-soft);
    border-radius: 50%;
}

.chat-evidence .result-disclosure summary span {
    color: var(--chat-text);
    font-size: 14px;
    letter-spacing: 0;
}

.chat-evidence .result-disclosure summary small {
    color: var(--chat-muted);
    letter-spacing: 0;
}

.chat-evidence .result-disclosure summary::after {
    color: var(--chat-muted);
}

.chat-evidence .citation-item,
.chat-evidence .synthesis-chunk {
    background: #f8fafc;
    border-color: var(--chat-border);
}

.chat-advanced {
    margin-top: 14px;
}

.chat-advanced > summary {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 10px 4px;
    cursor: pointer;
    color: var(--chat-muted);
    font-size: 13px;
    list-style: none;
}

.chat-advanced > summary::-webkit-details-marker {
    display: none;
}

.chat-advanced > summary small {
    font-size: 12px;
}

.chat-advanced > summary .chat-icon {
    margin-right: 2px;
}

.chat-advanced[open] > summary {
    color: var(--chat-accent);
}

.chat-advanced .trace-table {
    padding: 8px 0 14px;
    border-top: 1px solid var(--chat-border);
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
    html,
    html:focus-within,
    *,
    *::before,
    *::after {
        animation: none !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
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

    .comparison-grid {
        grid-template-columns: 92px repeat(2, minmax(0, 1fr));
    }

    .matrix-row-heading strong {
        font-size: 13px;
    }

    .card-header {
        gap: 8px;
    }
}

@media (max-width: 850px) {
    .st-key-comparison-topbar [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }

    .st-key-comparison-topbar [data-testid="stColumn"] {
        flex: 1 1 28% !important;
        width: auto !important;
    }

    .st-key-comparison-topbar [data-testid="stColumn"]:first-child {
        flex-basis: 100% !important;
    }

    .topbar-brand {
        white-space: normal;
    }

    .comparison-grid {
        grid-template-columns: 76px repeat(2, minmax(0, 1fr));
        gap: 8px;
    }

    .comparison-card {
        height: 340px;
    }

    .card-metrics {
        gap: 4px;
    }

    .card-metric,
    .card-status {
        gap: 5px;
        padding-inline: 7px;
        font-size: 11px;
    }

    .card-stage-strip {
        gap: 4px;
        font-size: 10px;
    }

    .stage-item {
        gap: 4px;
    }
}

@media (max-width: 620px) {
    .block-container {
        padding-right: 1rem;
        padding-left: 1rem;
    }

    .topbar-brand {
        gap: 8px;
    }

    .topbar-kicker {
        font-size: 10px;
    }

    .topbar-brand h1 {
        font-size: 20px;
    }

    .question-banner {
        align-items: flex-start;
        padding: 14px 16px;
    }

    .question-banner p {
        max-width: 100%;
        font-size: 19px;
    }

    .question-query-id {
        position: static;
        margin-top: 8px;
        transform: none;
    }

    .comparison-workspace {
        padding-top: 8px;
    }

    .comparison-grid {
        grid-template-columns: minmax(0, 1fr);
        grid-template-rows: none;
    }

    .matrix-corner,
    .matrix-column-heading,
    .matrix-row-heading {
        display: none;
    }

    .comparison-card {
        height: auto;
        min-height: 320px;
    }

    .card-overview-body {
        min-height: 255px;
    }

    .card-metrics {
        flex-wrap: wrap;
    }

    .card-status {
        margin-left: 0;
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

    .retrieval-metrics {
        grid-template-columns: 1fr;
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
        border-radius: var(--radius-card);
    }

    .chat-detail-modal {
        width: calc(100vw - 20px);
        height: calc(100vh - 20px);
        max-height: calc(100vh - 20px);
        border-radius: var(--radius-card);
    }

    .trace-modal-header {
        align-items: flex-start;
        padding: 16px;
    }

    .chat-detail-modal .trace-modal-header {
        padding: 12px 14px;
    }

    .trace-modal-meta {
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .trace-modal-body {
        padding: 16px;
    }

    .chat-modal-history {
        padding: 8px 16px 24px;
    }

    .trace-modal-footer {
        padding: 10px 16px;
    }

}

/* Keep the full comparison matrix visible on typical laptop-height screens. */
@media (max-height: 800px) and (min-width: 621px) {
    .block-container {
        padding-bottom: 3rem;
    }

    .st-key-comparison-topbar {
        margin-bottom: 8px;
        padding: 4px 0 6px;
    }

    .topbar-brand {
        min-height: 34px;
        gap: 10px;
    }

    .topbar-divider {
        height: 22px;
    }

    .topbar-brand h1 {
        font-size: clamp(19px, 1.7vw, 24px);
    }

    .topbar-live-mode,
    .topbar-query-live,
    .st-key-comparison-topbar [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        min-height: 34px;
    }

    .st-key-comparison-topbar [data-testid="stSegmentedControl"] {
        min-height: 34px;
    }

    .st-key-comparison-topbar [data-testid="stSegmentedControl"] button {
        min-height: 26px;
    }

    .question-banner {
        min-height: 0;
        margin-bottom: 8px;
        padding: 8px 16px;
    }

    .question-banner > span:first-child {
        font-size: 10px;
    }

    .question-banner p {
        margin-top: 3px;
        font-size: clamp(17px, 1.7vw, 23px);
        line-height: 1.18;
    }

    .question-query-id {
        right: 16px;
        padding: 6px 9px;
    }

    .comparison-grid {
        grid-template-columns: 100px repeat(2, minmax(0, 1fr));
        grid-template-rows: 30px repeat(2, minmax(0, 1fr));
        gap: 6px 8px;
    }

    .matrix-column-heading {
        font-size: 15px;
    }

    .matrix-row-heading {
        gap: 6px;
    }

    .comparison-card {
        height: clamp(180px, calc((100vh - 350px) / 2), 310px);
    }

    .card-header {
        min-height: 40px;
        gap: 8px;
        padding: 5px 10px 1px;
    }

    .architecture-icons {
        gap: 3px;
        padding: 2px;
        border-radius: 9px;
    }

    .architecture-icon {
        width: 27px;
        height: 27px;
        border-radius: 8px;
    }

    .card-header h3 {
        font-size: clamp(15px, 1.2vw, 18px);
    }

    .card-overview-body {
        gap: 5px;
        padding: 0 10px 6px;
    }

    .card-answer-preview {
        font-size: 12px;
        line-height: 1.32;
    }

    .card-answer-preview p {
        margin-bottom: 2px;
        -webkit-line-clamp: 3;
    }

    .card-metrics {
        min-height: 25px;
        gap: 5px;
    }

    .card-metric,
    .card-status {
        min-height: 24px;
        gap: 5px;
        padding: 3px 7px;
        font-size: 10px;
    }

    .card-metric i {
        font-size: 14px;
    }

    .card-metric strong {
        font-size: 11px;
    }

    .card-status i {
        width: 15px;
        height: 15px;
        font-size: 10px;
    }

    .card-stage-strip {
        min-height: 22px;
        gap: 7px;
        font-size: 10px;
    }

    .stage-item {
        gap: 4px;
    }

    .stage-item i {
        width: 7px;
        height: 7px;
    }

    .card-overview-body > .chat-modal-trigger {
        min-height: 29px;
        padding: 4px 9px;
        font-size: 12px;
    }
}


</style>
"""


def apply_custom_style():
    """Apply the Ant Design inspired theme to the comparison UI."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
