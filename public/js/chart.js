/**
 * Candlify v2 — Core Interactive Chart Controller (KLineCharts v9)
 * ================================================================
 * Hardened Frontend & PWA Features:
 * - P0 #2: AbortController + Sequence RequestId (Zero Race Condition)
 * - P1 #7: Correct Day Change Calculation & Null-safe formatting
 * - P1 #8: Explicit Timezone 'Asia/Jakarta' (WIB)
 * - P1 #9: Encoded URI parameters (Zero Injection)
 * - P2: Non-intrusive Toast Notifications
 * - Point 1: Direct In-Place Editable Ticker
 * - Point 2: Contextual Floating Action Popup upon Clicking an Object
 * - Point 3: Logo-Enabled Watchlist Chips
 * - Single Timeframe Dropdown Pill & Clean Control Bar
 */

// Helper: Hex Color to RGBA
function hexToRgba(hex, alpha = 0.15) {
    let c = hex.replace('#', '');
    if (c.length === 3) c = c.split('').map(x => x + x).join('');
    const num = parseInt(c, 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Helper: HTML Escaper (Anti-XSS Sanitizer)
function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ── 0. Registrasi Custom Overlays KLineCharts v9 ────────────────────────────
if (window.klinecharts && typeof window.klinecharts.registerOverlay === 'function') {
    // 1. Area SnR / Demand & Supply Box
    window.klinecharts.registerOverlay({
        name: 'rectZone',
        totalStep: 3,
        needDefaultPointFigure: true,
        needDefaultXAxisFigure: false,
        needDefaultYAxisFigure: true,
        createPointFigures: ({ overlay, coordinates }) => {
            if (!coordinates || coordinates.length < 2) return [];

            const p1 = coordinates[0];
            const p2 = coordinates[1];
            const minX = Math.min(p1.x, p2.x);
            const maxX = Math.max(p1.x, p2.x);
            const minY = Math.min(p1.y, p2.y);
            const maxY = Math.max(p1.y, p2.y);
            const width = Math.max(maxX - minX, 6);
            const height = Math.max(maxY - minY, 6);

            const primaryColor = overlay.styles?.rect?.borderColor || '#3b82f6';
            const fillColor = hexToRgba(primaryColor, 0.22);

            return [
                {
                    type: 'rect',
                    attrs: { x: minX, y: minY, width, height },
                    styles: {
                        style: 'stroke_fill',
                        color: fillColor,
                        borderColor: primaryColor,
                        borderSize: 1.5,
                        borderRadius: 3
                    }
                },
                {
                    type: 'text',
                    attrs: {
                        x: minX + 8,
                        y: minY + 6,
                        text: 'AREA SNR',
                        align: 'left',
                        baseline: 'top'
                    },
                    styles: {
                        color: primaryColor,
                        size: 10,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                }
            ];
        }
    });

    // 2. Long Position (Risk:Reward Tool khas Stockbit / TradingView)
    window.klinecharts.registerOverlay({
        name: 'priceProjection',
        totalStep: 4,
        needDefaultPointFigure: true,
        needDefaultXAxisFigure: false,
        needDefaultYAxisFigure: true,
        createPointFigures: ({ overlay, coordinates, precision }) => {
            if (!coordinates || coordinates.length < 2) return [];

            const c0 = coordinates[0]; // Point 0: Entry Level
            const c1 = coordinates[1]; // Point 1: Target TP & Right Edge

            // Level Harga dari overlay points
            const entryPrice = overlay.points[0]?.value || 0;
            const targetPrice = overlay.points[1]?.value || entryPrice;
            
            // Point 2: Stop Loss Level
            let c2;
            let stopPrice;
            if (coordinates.length >= 3 && coordinates[2]) {
                c2 = coordinates[2];
                stopPrice = overlay.points[2]?.value ?? (entryPrice - Math.abs(targetPrice - entryPrice) * 0.5);
            } else {
                // Preview dinamis sebelum klik ke-3: Default R:R 1:2
                const deltaY = Math.abs(c0.y - c1.y);
                c2 = { x: c1.x, y: c0.y + (deltaY > 0 ? deltaY * 0.5 : 25) };
                const deltaPrice = Math.abs(targetPrice - entryPrice);
                stopPrice = entryPrice - (deltaPrice > 0 ? deltaPrice * 0.5 : entryPrice * 0.02);
            }

            // Batas Horizontal Box
            const startX = Math.min(c0.x, c1.x);
            let endX = Math.max(c0.x, c1.x);
            if (endX - startX < 60) {
                endX = startX + 90; // Default lebar minimum visual yang nyaman
            }
            const boxWidth = endX - startX;

            // Batas Vertikal TP (Hijau)
            const tpTopY = Math.min(c0.y, c1.y);
            const tpBottomY = Math.max(c0.y, c1.y);
            const tpHeight = Math.max(tpBottomY - tpTopY, 4);

            // Batas Vertikal SL (Merah)
            const slTopY = Math.min(c0.y, c2.y);
            const slBottomY = Math.max(c0.y, c2.y);
            const slHeight = Math.max(slBottomY - slTopY, 4);

            // Perhitungan Matang: Rasio R:R & Persentase Gain/Loss
            const reward = Math.abs(targetPrice - entryPrice);
            const risk = Math.abs(entryPrice - stopPrice);
            const rrRatio = risk > 0 ? (reward / risk).toFixed(2) : '1.00';
            const tpPct = entryPrice > 0 ? ((targetPrice - entryPrice) / entryPrice * 100).toFixed(2) : '0.00';
            const slPct = entryPrice > 0 ? ((stopPrice - entryPrice) / entryPrice * 100).toFixed(2) : '0.00';

            const priceDecimals = precision?.price ?? 0;
            const fmtPrice = (val) => Number(val).toLocaleString('id-ID', { maximumFractionDigits: priceDecimals });

            return [
                // 1. Kotak Take Profit (Hijau Transparan)
                {
                    type: 'rect',
                    attrs: { x: startX, y: tpTopY, width: boxWidth, height: tpHeight },
                    styles: {
                        style: 'stroke_fill',
                        color: 'rgba(8, 153, 129, 0.22)',
                        borderColor: '#089981',
                        borderSize: 1.5,
                        borderRadius: 2
                    }
                },
                // 2. Kotak Stop Loss (Merah Transparan)
                {
                    type: 'rect',
                    attrs: { x: startX, y: slTopY, width: boxWidth, height: slHeight },
                    styles: {
                        style: 'stroke_fill',
                        color: 'rgba(242, 54, 69, 0.22)',
                        borderColor: '#f23645',
                        borderSize: 1.5,
                        borderRadius: 2
                    }
                },
                // 3. Garis Horizontal Level Entry
                {
                    type: 'line',
                    attrs: {
                        coordinates: [
                            { x: startX, y: c0.y },
                            { x: endX, y: c0.y }
                        ]
                    },
                    styles: {
                        color: '#ffffff',
                        size: 1.5,
                        style: 'dashed',
                        dashedValue: [3, 3]
                    }
                },
                // 4. Pill Badge TP di Atas (Hijau Stockbit)
                {
                    type: 'text',
                    attrs: {
                        x: startX + boxWidth / 2,
                        y: tpTopY - 8,
                        text: `Target: ${fmtPrice(targetPrice)} (${Number(tpPct) >= 0 ? '+' : ''}${tpPct}%)`,
                        align: 'center',
                        baseline: 'bottom'
                    },
                    styles: {
                        color: '#ffffff',
                        backgroundColor: '#089981',
                        borderColor: '#057a55',
                        borderSize: 1,
                        borderRadius: 4,
                        paddingLeft: 8,
                        paddingRight: 8,
                        paddingTop: 3,
                        paddingBottom: 3,
                        size: 11,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                },
                // 5. Pill Badge Stop Loss di Bawah (Merah Stockbit)
                {
                    type: 'text',
                    attrs: {
                        x: startX + boxWidth / 2,
                        y: slBottomY + 8,
                        text: `Stop: ${fmtPrice(stopPrice)} (${slPct}%)`,
                        align: 'center',
                        baseline: 'top'
                    },
                    styles: {
                        color: '#ffffff',
                        backgroundColor: '#f23645',
                        borderColor: '#b91c1c',
                        borderSize: 1,
                        borderRadius: 4,
                        paddingLeft: 8,
                        paddingRight: 8,
                        paddingTop: 3,
                        paddingBottom: 3,
                        size: 11,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                },
                // 6. Center Badge: Risk / Reward Ratio & Nilai Poin
                {
                    type: 'text',
                    attrs: {
                        x: startX + boxWidth / 2,
                        y: c0.y,
                        text: `R:R ${rrRatio}  |  TP +${fmtPrice(reward)}  SL -${fmtPrice(risk)}`,
                        align: 'center',
                        baseline: 'middle'
                    },
                    styles: {
                        color: '#ffffff',
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        borderColor: '#475569',
                        borderSize: 1,
                        borderRadius: 4,
                        paddingLeft: 8,
                        paddingRight: 8,
                        paddingTop: 4,
                        paddingBottom: 4,
                        size: 11,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                }
            ];
        }
    });

    // 3. Level SnR Otomatis (Classic Pivot: R2, R1, PP, S1, S2)
    window.klinecharts.registerOverlay({
        name: 'autoSnR',
        totalStep: 1,
        needDefaultPointFigure: false,
        needDefaultXAxisFigure: false,
        needDefaultYAxisFigure: true,
        createPointFigures: ({ overlay, coordinates, bounding, precision }) => {
            if (!coordinates || coordinates.length < 5) return [];

            const width = bounding.width;
            const isFib = overlay.extendData?.formula === 'fibonacci';
            const isWeekly = overlay.extendData?.period === 'weekly';
            const prefix = isWeekly ? 'W-' : '';

            const levels = [
                { name: `${prefix}R2${isFib ? ' (61.8%)' : ''}`, color: '#ef4444', textColor: '#fca5a5', coord: coordinates[0], val: overlay.points[0]?.value, baseline: 'bottom' },
                { name: `${prefix}R1${isFib ? ' (38.2%)' : ''}`, color: '#f87171', textColor: '#fca5a5', coord: coordinates[1], val: overlay.points[1]?.value, baseline: 'bottom' },
                { name: `${prefix}PP`, color: '#eab308', textColor: '#fde047', coord: coordinates[2], val: overlay.points[2]?.value, baseline: 'bottom' },
                { name: `${prefix}S1${isFib ? ' (38.2%)' : ''}`, color: '#34d399', textColor: '#86efac', coord: coordinates[3], val: overlay.points[3]?.value, baseline: 'top' },
                { name: `${prefix}S2${isFib ? ' (61.8%)' : ''}`, color: '#10b981', textColor: '#86efac', coord: coordinates[4], val: overlay.points[4]?.value, baseline: 'top' }
            ];

            const figures = [];
            const priceDecimals = precision?.price ?? 0;
            const fmtPrice = (val) => Number(val).toLocaleString('id-ID', { maximumFractionDigits: priceDecimals });

            levels.forEach(lvl => {
                if (!lvl.coord || typeof lvl.coord.y !== 'number' || isNaN(lvl.coord.y)) return;
                const y = lvl.coord.y;

                // 1. Garis Horizontal Dashed Elegan
                figures.push({
                    type: 'line',
                    attrs: {
                        coordinates: [
                            { x: 0, y },
                            { x: width, y }
                        ]
                    },
                    styles: {
                        color: lvl.color,
                        size: 1,
                        style: 'dashed',
                        dashedValue: [4, 4]
                    }
                });

                // 2. Pill Tag Label di Kanan Chart
                figures.push({
                    type: 'text',
                    attrs: {
                        x: width - 6,
                        y: lvl.baseline === 'bottom' ? y - 3 : y + 3,
                        text: `${lvl.name} ${fmtPrice(lvl.val)}`,
                        align: 'right',
                        baseline: lvl.baseline
                    },
                    styles: {
                        color: lvl.textColor,
                        backgroundColor: 'rgba(15, 23, 42, 0.90)',
                        borderColor: lvl.color,
                        borderSize: 1,
                        borderRadius: 3,
                        paddingLeft: 4,
                        paddingRight: 4,
                        paddingTop: 1,
                        paddingBottom: 1,
                        size: 9,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                });
            });

            return figures;
        }
    });

    // 4. Garis Harga Modal Bandar (HMB)
    window.klinecharts.registerOverlay({
        name: 'hmbLine',
        totalStep: 1,
        needDefaultPointFigure: false,
        needDefaultXAxisFigure: false,
        needDefaultYAxisFigure: true,
        createPointFigures: ({ overlay, coordinates, bounding, precision }) => {
            if (!coordinates || coordinates.length === 0) return [];
            const width = bounding.width;
            const y = coordinates[0]?.y;
            if (typeof y !== 'number' || isNaN(y)) return [];
            const val = overlay.points[0]?.value;
            const priceDecimals = precision?.price ?? 0;
            const fmtPrice = Number(val).toLocaleString('id-ID', { maximumFractionDigits: priceDecimals });
            
            return [
                {
                    type: 'line',
                    attrs: {
                        coordinates: [
                            { x: 0, y },
                            { x: width, y }
                        ]
                    },
                    styles: {
                        color: '#f59e0b',
                        size: 2,
                        style: 'solid'
                    }
                },
                {
                    type: 'text',
                    attrs: {
                        x: width - 6,
                        y: y - 4,
                        text: `HMB Rp ${fmtPrice}`,
                        align: 'right',
                        baseline: 'bottom'
                    },
                    styles: {
                        color: '#fbbf24',
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        borderColor: '#f59e0b',
                        borderSize: 1.5,
                        borderRadius: 4,
                        paddingLeft: 6,
                        paddingRight: 6,
                        paddingTop: 2,
                        paddingBottom: 2,
                        size: 10,
                        weight: 'bold'
                    },
                    ignoreEvent: true
                }
            ];
        }
    });
}

// ── 0b. Registrasi Custom Sub-Pane Indicator NET_FLOW ───────────────────────
if (window.klinecharts && typeof window.klinecharts.registerIndicator === 'function') {
    window.klinecharts.registerIndicator({
        name: 'NET_FLOW',
        shortName: 'NET FLOW (B)',
        figures: [
            {
                key: 'net_flow',
                title: 'Net (Miliar): ',
                type: 'bar',
                baseValue: 0,
                styles: (data) => {
                    const val = data?.current?.net_flow ?? 0;
                    return {
                        color: val >= 0 ? '#10b981' : '#ef4444'
                    };
                }
            }
        ],
        calc: (dataList) => {
            return dataList.map(k => ({ net_flow: typeof k.net_flow === 'number' ? k.net_flow : 0 }));
        }
    });
}

class CandlifyChart {
    constructor() {
        this.chart = null;
        this.currentSymbol = 'BBRI';
        this.currentInterval = '4h';
        
        // Screener & Rapid Navigation State
        this.currentView = 'screener'; // 'screener' | 'chart'
        this.previousView = 'screener';
        this._navigatedToChartFromApp = false;
        this.screenerStocks = [];
        this.currentFilteredStocks = [];
        this.activeNavigationList = ['BBRI'];
        this.currentNavigationIndex = 0;
        this.currentPreset = 'all';
        this.currentSort = 'change_desc';
        this.searchQuery = '';
        this._searchDebounceTimer = null;
        this.currentPage = 1;
        this.pageSize = 20;

        // P0 #2: Race Condition Guards
        this.reqId = 0;
        this.abortController = null;

        // Contextual Overlay State
        this.selectedOverlay = null;
        this._lastOverlayInteraction = 0;
        this.manualOverlayIds = new Set();

        // Auto SnR Configuration (Persistent in localStorage)
        this.snrConfig = this.loadSnrConfig();

        // State Indikator Aktif
        this.indicatorState = {
            EMA: false,
            BOLL: false,
            MACD: false,
            RSI: false,
            SNR: false,
            HMB: false,
            NET_FLOW: false
        };

        // Watchlist & Risk Management State
        this.watchlistItems = [];
        this.watchlistCategories = ['Breakout'];
        this.activeWatchlistCategory = 'all';
        this.selectedWlCategories = new Set();
        this.allWatchlistSymbols = new Set();
        this._needChartRefresh = false;
        this.riskSettings = {
            total_capital: 100000000,
            risk_pct: 1.0,
            default_category: 'Breakout',
            risk_nominal: 1000000
        };

        // Trading Plan & Journal State
        this.tradingPlans = [];
        this.activePlanFilter = 'ALL';
        this.journalStats = {
            holding_count: 0,
            holding_invested: 0,
            unrealized_pnl: 0,
            tp_signals_count: 0,
            antri_count: 0,
            closed_win_count: 0,
            closed_loss_count: 0,
            closed_total: 0,
            win_rate: 0,
            realized_pnl: 0
        };

        // Cache Data Bandarmologi
        this.bandarData = null;

        // Navigation History State
        this.previousView = 'screener';
        this._skipNextHashChange = false;
        
        this.dom = {
            container: document.getElementById('chart-container'),
            loading: document.getElementById('loading-overlay'),

            // ── Screener View & Filter Modal Elements ──
            screenerView: document.getElementById('screener-view'),
            chartView: document.getElementById('chart-view'),
            screenerMarketStatus: document.getElementById('screener-market-status'),
            screenerSearchInput: document.getElementById('screener-search-input'),
            screenerSearchClear: document.getElementById('screener-search-clear'),
            screenerPresetsContainer: document.getElementById('screener-presets-container'),
            screenerPresetChips: document.querySelectorAll('.screener-preset-chip, .preset-card'),
            btnToggleFilters: document.getElementById('btn-toggle-filters'),
            filterActiveDot: document.getElementById('filter-active-dot'),
            screenerActiveFilterBadge: document.getElementById('screener-active-filter-badge'),
            activePresetName: document.getElementById('active-preset-name'),
            btnClearActivePreset: document.getElementById('btn-clear-active-preset'),
            screenerSortSelect: document.getElementById('screener-sort-select'),
            screenerCountBadge: document.getElementById('screener-count-badge'),
            screenerList: document.getElementById('screener-list'),
            screenerPagination: document.getElementById('screener-pagination'),
            filterModal: document.getElementById('filter-modal'),
            filterModalBackdrop: document.getElementById('filter-modal-backdrop'),
            closeFilterModal: document.getElementById('close-filter-modal'),
            btnResetFilters: document.getElementById('btn-reset-filters'),
            btnApplyFilters: document.getElementById('btn-apply-filters'),

            // ── Watchlist View Elements ──
            watchlistView: document.getElementById('watchlist-view'),
            watchlistCountBadge: document.getElementById('watchlist-count-badge'),
            btnRiskSettings: document.getElementById('btn-risk-settings'),
            btnOpenAddWatchlist: document.getElementById('btn-open-add-watchlist'),
            btnEmptyAddWatchlist: document.getElementById('btn-empty-add-watchlist'),
            watchlistCategories: document.getElementById('watchlist-categories'),
            btnWlCatAll: document.getElementById('btn-wl-cat-all'),
            watchlistList: document.getElementById('watchlist-list'),
            watchlistEmpty: document.getElementById('watchlist-empty'),
            btnStarWatchlist: document.getElementById('btn-star-watchlist'),
            starIcon: document.getElementById('star-icon'),
            btnManageCategories: document.getElementById('btn-manage-categories'),

            // ── Watchlist Add/Edit Modal Elements ──
            watchlistModal: document.getElementById('watchlist-modal'),
            watchlistModalBackdrop: document.getElementById('watchlist-modal-backdrop'),
            wlModalTitle: document.getElementById('wl-modal-title'),
            closeWlModal: document.getElementById('close-wl-modal'),
            btnCancelWl: document.getElementById('btn-cancel-wl'),
            btnSubmitWl: document.getElementById('btn-submit-wl'),
            wlModalItemId: document.getElementById('wl-modal-item-id'),
            wlInputSymbol: document.getElementById('wl-input-symbol'),
            wlCategoryButtons: document.getElementById('wl-category-buttons'),
            wlSelectedCatCount: document.getElementById('wl-selected-cat-count'),
            wlInputCategory: document.getElementById('wl-input-category'),
            wlInputTargetEntry: document.getElementById('wl-input-target-entry'),
            wlInputNotes: document.getElementById('wl-input-notes'),

            // ── Watchlist Category Management Modal (CRUD) ──
            categoryMgmtModal: document.getElementById('category-mgmt-modal'),
            categoryMgmtBackdrop: document.getElementById('category-mgmt-backdrop'),
            closeCategoryMgmtModal: document.getElementById('close-category-mgmt-modal'),
            btnCloseCategoryMgmt: document.getElementById('btn-close-category-mgmt'),
            inputNewCategory: document.getElementById('input-new-category'),
            btnSubmitAddCat: document.getElementById('btn-submit-add-cat'),
            categoryMgmtItems: document.getElementById('category-mgmt-items'),

            // ── Database / Dashboard View Elements ──
            databaseView: document.getElementById('database-view') || document.getElementById('home-view'),
            homeView: document.getElementById('database-view') || document.getElementById('home-view'),
            dbStatTotalEmiten: document.getElementById('db-stat-total-emiten'),
            dbStatActivePrice: document.getElementById('db-stat-active-price'),
            dbStatActiveBroksum: document.getElementById('db-stat-active-broksum'),
            dbStatDateRange: document.getElementById('db-stat-date-range'),
            dbStatWlCount: document.getElementById('db-stat-wl-count'),
            dbStatRiskNominal: document.getElementById('db-stat-risk-nominal'),
            dbStatCapitalSub: document.getElementById('db-stat-capital-sub'),
            dbStatFeedSource: document.getElementById('db-stat-feed-source'),
            btnDbGoScreener: document.getElementById('btn-db-go-screener') || document.getElementById('btn-home-go-screener'),
            btnDbGoWatchlist: document.getElementById('btn-db-go-watchlist') || document.getElementById('btn-home-go-watchlist'),
            btnDbGoSettingsRisk: document.getElementById('btn-db-go-settings-risk'),
            btnDbGoSettingsFeed: document.getElementById('btn-db-go-settings-feed'),
            homeWatchlistCount: document.getElementById('db-stat-wl-count') || document.getElementById('home-watchlist-count'),
            calendarGrid: document.getElementById('calendar-grid'),
            calendarMonthTitle: document.getElementById('calendar-month-title'),
            dbCalendarCard: document.getElementById('db-calendar-card'),
            btnCalPrev: document.getElementById('btn-cal-prev'),
            btnCalNext: document.getElementById('btn-cal-next'),
            btnActionSuspend: document.getElementById('btnActionSuspend'),
            btnActionLogs: document.getElementById('btnActionLogs'),
            btnActionUpload: document.getElementById('btnActionUpload'),
            badgeSuspendCount: document.getElementById('badgeSuspendCount'),
            badgeLogsCount: document.getElementById('badgeLogsCount'),
            uploadModal: document.getElementById('uploadModal'),
            suspendModal: document.getElementById('suspendModal'),
            logsModal: document.getElementById('logsModal'),
            closeUploadModal: document.querySelector('.close-upload-modal'),
            closeSuspendModal: document.querySelector('.close-suspend-modal'),
            closeLogsModal: document.querySelector('.close-logs-modal'),
            suspendModalContent: document.getElementById('suspendModalContent'),
            logsModalContent: document.getElementById('logsModalContent'),
            dbDropzone: document.getElementById('db-dropzone'),
            dbFileInput: document.getElementById('db-fileInput'),
            dbFileNameDisplay: document.getElementById('db-fileNameDisplay'),
            uploadForm: document.getElementById('uploadForm'),
            btnDbUploadSubmit: document.getElementById('btnDbUploadSubmit'),
            dbUploadStatus: document.getElementById('db-uploadStatus'),
            liveClock: document.getElementById('live-clock'),
            dbServerStatus: document.getElementById('db-server-status'),
            dbEngineStatus: document.getElementById('db-engine-status'),
            dbEngineDot: document.getElementById('db-engine-dot'),
            dbLastSyncBadge: document.getElementById('db-last-sync-badge'),

            // ── Settings View Elements ──
            settingsView: document.getElementById('settings-view'),
            radioSourceNeon: document.getElementById('radio-source-neon'),
            radioSourceYahoo: document.getElementById('radio-source-yahoo'),
            settingInputCapital: document.getElementById('setting-input-capital'),
            settingCapitalHint: document.getElementById('setting-capital-hint'),
            settingSliderPct: document.getElementById('setting-slider-pct'),
            settingPctBadge: document.getElementById('setting-pct-badge'),
            settingPreviewNominal: document.getElementById('setting-preview-nominal'),
            settingSelectCategory: document.getElementById('setting-select-category'),
            btnSaveAllSettings: document.getElementById('btn-save-all-settings'),

            // ── Floating Glass Bottom Navigation ──
            floatingBottomNav: document.getElementById('floating-bottom-nav'),
            navBtns: document.querySelectorAll('.nav-btn'),

            // ── Risk Settings Modal Elements (Quick Access) ──
            riskModal: document.getElementById('risk-modal'),
            riskModalBackdrop: document.getElementById('risk-modal-backdrop'),
            closeRiskModal: document.getElementById('close-risk-modal'),
            btnCancelRisk: document.getElementById('btn-cancel-risk'),
            btnSubmitRisk: document.getElementById('btn-submit-risk'),
            riskInputCapital: document.getElementById('risk-input-capital'),
            riskCapitalHint: document.getElementById('risk-capital-hint'),
            riskSliderPct: document.getElementById('risk-slider-pct'),
            riskPctBadge: document.getElementById('risk-pct-badge'),
            riskPreviewNominal: document.getElementById('risk-preview-nominal'),
            riskSelectCategory: document.getElementById('risk-select-category'),

            // ── Journal View Elements ──
            journalView: document.getElementById('journal-view'),
            journalCountBadge: document.getElementById('journal-count-badge'),
            btnOpenCreatePlan: document.getElementById('btn-open-create-plan'),
            btnEmptyCreatePlan: document.getElementById('btn-empty-create-plan'),
            journalList: document.getElementById('journal-list'),
            journalEmpty: document.getElementById('journal-empty'),
            journalFilterChips: document.querySelectorAll('.journal-status-chip'),
            statHoldingCount: document.getElementById('stat-holding-count'),
            statHoldingInvested: document.getElementById('stat-holding-invested'),
            statUnrealizedPnl: document.getElementById('stat-unrealized-pnl'),
            statTpSignals: document.getElementById('stat-tp-signals'),
            statAntriCount: document.getElementById('stat-antri-count'),
            statWinRate: document.getElementById('stat-win-rate'),
            statRealizedPnl: document.getElementById('stat-realized-pnl'),

            // ── Plan Modal Elements ──
            planModal: document.getElementById('plan-modal'),
            planModalBackdrop: document.getElementById('plan-modal-backdrop'),
            planModalTitle: document.getElementById('plan-modal-title'),
            closePlanModal: document.getElementById('close-plan-modal'),
            btnCancelPlan: document.getElementById('btn-cancel-plan'),
            btnSubmitPlan: document.getElementById('btn-submit-plan'),
            planModalId: document.getElementById('plan-modal-id'),
            planInputSymbol: document.getElementById('plan-input-symbol'),
            planSelectCategory: document.getElementById('plan-select-category'),
            planSelectStatus: document.getElementById('plan-select-status'),
            planSelectOrderType: document.getElementById('plan-select-order-type'),
            planInputEntry: document.getElementById('plan-input-entry'),
            planInputSl: document.getElementById('plan-input-sl'),
            planInputTp1: document.getElementById('plan-input-tp1'),
            planInputLot: document.getElementById('plan-input-lot'),
            planCalcSettingHint: document.getElementById('plan-calc-setting-hint'),
            planCalcInvested: document.getElementById('plan-calc-invested'),
            planCalcRr: document.getElementById('plan-calc-rr'),
            planCalcRiskRp: document.getElementById('plan-calc-risk-rp'),
            planCalcRewardRp: document.getElementById('plan-calc-reward-rp'),
            planInputNotes: document.getElementById('plan-input-notes'),

            // ── Trailing Modal Elements ──
            trailingModal: document.getElementById('trailing-modal'),
            trailingModalBackdrop: document.getElementById('trailing-modal-backdrop'),
            trailingModalTitle: document.getElementById('trailing-modal-title'),
            closeTrailingModal: document.getElementById('close-trailing-modal'),
            btnCancelTrailing: document.getElementById('btn-cancel-trailing'),
            btnSubmitTrailing: document.getElementById('btn-submit-trailing'),
            trailingModalId: document.getElementById('trailing-modal-id'),
            trailingInfoEntry: document.getElementById('trailing-info-entry'),
            trailingInfoCurrSl: document.getElementById('trailing-info-curr-sl'),
            trailingInfoLivePrice: document.getElementById('trailing-info-live-price'),
            trailingInputSl: document.getElementById('trailing-input-sl'),
            trailingSlHint: document.getElementById('trailing-sl-hint'),

            // ── Exit / Journal Post-Mortem Modal Elements ──
            exitModal: document.getElementById('exit-modal'),
            exitModalBackdrop: document.getElementById('exit-modal-backdrop'),
            exitModalTitle: document.getElementById('exit-modal-title'),
            closeExitModal: document.getElementById('close-exit-modal'),
            btnCancelExit: document.getElementById('btn-cancel-exit'),
            btnSubmitExit: document.getElementById('btn-submit-exit'),
            exitModalId: document.getElementById('exit-modal-id'),
            exitSelectStatus: document.getElementById('exit-select-status'),
            exitInputPrice: document.getElementById('exit-input-price'),
            exitPnlPreview: document.getElementById('exit-pnl-preview'),
            exitInputNotes: document.getElementById('exit-input-notes'),

            // ── Chart Rapid Navigation Controls ──
            btnBackScreener: document.getElementById('btn-back-screener'),
            backScreenerLabel: document.getElementById('back-screener-label'),
            
            // In-Place Ticker Input (Point 1)
            tickerInplaceInput: document.getElementById('ticker-inplace-input'),
            currentPrice: document.getElementById('current-price-label'),
            currentChange: document.getElementById('current-change-label'),
            sourceBadge: document.getElementById('source-badge-label'),
            bandarBadge: document.getElementById('bandar-badge-label'),
            quickChipsContainer: document.getElementById('quick-chips-container'),
            
            // Timeframe Dropdown
            btnTimeframe: document.getElementById('btn-timeframe'),
            activeTfLabel: document.getElementById('active-tf-label'),
            timeframeMenu: document.getElementById('timeframe-menu'),
            tfOptions: document.querySelectorAll('.tf-opt'),
            
            // Toolbar Actions
            btnDraw: document.getElementById('btn-draw'),
            btnIndicator: document.getElementById('btn-indicator'),
            btnResetOverlays: document.getElementById('btn-reset-overlays'),
            
            // Contextual Overlay Action Popup (Point 2)
            overlayActionPopup: document.getElementById('overlay-action-popup'),
            popupOverlayName: document.getElementById('popup-overlay-name'),
            popupBtnLock: document.getElementById('popup-btn-lock'),
            popupBtnDelete: document.getElementById('popup-btn-delete'),
            popupBtnDeleteAll: document.getElementById('popup-btn-delete-all'),
            popupBtnClose: document.getElementById('popup-btn-close'),
            colorDots: document.querySelectorAll('.color-dot'),
            
            // Bottom Sheets & Backdrop
            sheetBackdrop: document.getElementById('sheet-backdrop'),
            drawSheet: document.getElementById('draw-sheet'),
            indicatorSheet: document.getElementById('indicator-sheet'),
            closeDrawSheet: document.getElementById('close-draw-sheet'),
            closeIndSheet: document.getElementById('close-ind-sheet'),
            
            // Auto SnR Settings Panel
            btnSnrSettings: document.getElementById('btn-snr-settings'),
            snrSettingsPanel: document.getElementById('snr-settings-panel'),
            snrConfigDesc: document.getElementById('snr-config-desc'),
            snrPeriodChips: document.querySelectorAll('#snr-period-selector .snr-chip'),
            snrFormulaChips: document.querySelectorAll('#snr-formula-selector .snr-chip'),
            
            // Indicator Toggle Buttons
            toggleSnr: document.getElementById('toggle-snr'),
            toggleHmb: document.getElementById('toggle-hmb'),
            toggleNetFlow: document.getElementById('toggle-netflow'),
            toggleEma: document.getElementById('toggle-ema'),
            toggleBoll: document.getElementById('toggle-boll'),
            toggleMacd: document.getElementById('toggle-macd'),
            toggleRsi: document.getElementById('toggle-rsi'),

            // Broker Summary (Broksum) Bottom Sheet
            broksumSheet: document.getElementById('broksum-sheet'),
            closeBroksumSheet: document.getElementById('close-broksum-sheet'),
            broksumTitle: document.getElementById('broksum-title'),
            broksumNotasiPill: document.getElementById('broksum-notasi-pill'),
            broksumSubtitle: document.getElementById('broksum-subtitle'),
            broksumStatusPill: document.getElementById('broksum-status-pill'),
            broksumNetflow: document.getElementById('broksum-netflow'),
            broksumHmb: document.getElementById('broksum-hmb'),
            broksumRatio: document.getElementById('broksum-ratio'),
            broksumRatioBuy: document.getElementById('broksum-ratio-buy'),
            broksumRatioSell: document.getElementById('broksum-ratio-sell'),
            broksumTotalBuy: document.getElementById('broksum-total-buy'),
            broksumTotalSell: document.getElementById('broksum-total-sell'),
            broksumBuyersList: document.getElementById('broksum-buyers-list'),
            broksumSellersList: document.getElementById('broksum-sellers-list'),
            broksumPresetChips: document.querySelectorAll('.broksum-chip'),
            broksumDateFrom: document.getElementById('broksum-date-from'),
            broksumDateTo: document.getElementById('broksum-date-to'),

            // Market Intelligence elements
            intelForeignStatus: document.getElementById('intel-foreign-status'),
            intelForeign1d: document.getElementById('intel-foreign-1d'),
            intelForeign5d: document.getElementById('intel-foreign-5d'),
            intelForeign20d: document.getElementById('intel-foreign-20d'),
            intelForeignSubtext: document.getElementById('intel-foreign-subtext'),
            intelWhaleStatus: document.getElementById('intel-whale-status'),
            intelWhaleToday: document.getElementById('intel-whale-today'),
            intelWhaleAvg: document.getElementById('intel-whale-avg'),
            intelNegoVal: document.getElementById('intel-nego-val'),
            intelNegoSubtext: document.getElementById('intel-nego-subtext'),

            // Order Flow & Intelligence Sub-Tabs
            broksumTabBtns: document.querySelectorAll('.broksum-tab-btn'),
            tabPaneSummary: document.getElementById('tab-pane-summary'),
            tabPaneHistory: document.getElementById('tab-pane-history'),
            tabPaneFlow: document.getElementById('tab-pane-flow'),
            tabPaneActivity: document.getElementById('tab-pane-activity'),

            // Tab 2: Historical Data Table
            historyTfPills: document.querySelectorAll('.history-tf-pill'),
            historyRowCount: document.getElementById('history-row-count'),
            historyTableBody: document.getElementById('history-table-body'),

            // Tab 3: Broker Flow Visualizer
            flowMeterStatus: document.getElementById('flow-meter-status'),
            flowMeterFill: document.getElementById('flow-meter-fill'),
            flowMetricBtns: document.querySelectorAll('.flow-metric-toggle .flow-btn'),
            flowTfPills: document.querySelectorAll('.flow-tf-pill'),
            flowCanvas: document.getElementById('broker-flow-canvas'),
            flowTooltip: document.getElementById('flow-tooltip'),
            flowBrokerChips: document.getElementById('flow-broker-chips'),

            // Tab 4: Broker Daily Activity
            activityBrokerSelect: document.getElementById('activity-broker-select'),
            activityBrokerChips: document.getElementById('activity-broker-chips'),
            activityActiveBrokerBadge: document.getElementById('activity-active-broker-badge'),
            activityPrevMonthBtn: document.getElementById('btn-activity-prev-month'),
            activityNextMonthBtn: document.getElementById('btn-activity-next-month'),
            activityMonthLabel: document.getElementById('activity-month-label'),
            actSumVal: document.getElementById('act-sum-val'),
            actSumVol: document.getElementById('act-sum-vol'),
            actSumDays: document.getElementById('act-sum-days'),
            activityCalendarGrid: document.getElementById('activity-calendar-grid'),

            // Header Board Badge
            tickerBoardBadge: document.getElementById('ticker-board-badge')
        };

        // State for Order Flow sub-views
        this.activeBroksumTab = 'summary';
        this.activeHistoryTf = 'daily';
        this.activeFlowDays = 30;
        this.activeFlowMetric = 'val';
        this.activeFlowBrokers = new Set();
        this.currentFlowData = null;
        this.hoverFlowDateIdx = null;
        this.activeActivityBroker = 'XL';
        this.activeActivityMonth = null;
        
        this.init();
    }
    
    init() {
        if (!window.klinecharts) {
            console.error('KLineCharts library not loaded!');
            return;
        }
        
        // 1. Inisialisasi Chart Canvas KLineCharts v9
        this.chart = window.klinecharts.init('chart-container', {
            styles: this.getChartStyles()
        });
        
        // P1 #8: Set Timezone ke Asia/Jakarta (WIB)
        if (typeof this.chart.setTimezone === 'function') {
            this.chart.setTimezone('Asia/Jakarta');
        }
        
        // 2. Tambahkan Sub-Pane Volume (VOL) secara default (Tinggi responsif untuk mobile PWA)
        const isMobile = window.innerWidth <= 768;
        const defaultVolHeight = isMobile ? 110 : 85;
        this.chart.createIndicator('VOL', false, { id: 'pane_vol', height: defaultVolHeight });
        
        // 3. Pasang Event Listeners, Mobile Gestures, & Sinkronkan UI SnR
        this.setupEvents();
        this.setupMobileChartGestures();
        this.setupToolEvents();
        this.setupScreenerEvents();
        this.setupWatchlistEvents();
        this.setupSettingsEvents();
        this.setupJournalEvents();
        this.setupDatabaseEvents();
        this.updateSnrUi();
        
        // 4. Periksa apakah user membuka langsung emiten spesifik via URL Hash (misal: #BBRI)
        const hash = (window.location.hash || '').replace('#', '').trim().toUpperCase();
        if (hash === 'HOME' || hash === 'DATABASE') {
            this.switchView('database');
        } else if (hash === 'WATCHLIST') {
            this.switchView('watchlist');
            this.loadData(this.currentSymbol, this.currentInterval);
        } else if (hash === 'JOURNAL' || hash === 'PLAN') {
            this.switchView('journal');
        } else if (hash === 'SETTINGS') {
            this.switchView('settings');
        } else if (hash && hash.length >= 4 && hash !== 'SCREENER') {
            this.currentSymbol = hash;
            this.activeNavigationList = [hash];
            this.currentNavigationIndex = 0;
            this.renderQuickChipsFromList(this.activeNavigationList, hash);
            this.updateNavIndex();
            this.switchView('chart', false, hash);
            this.loadData(this.currentSymbol, this.currentInterval);
        } else {
            // Default: Tampilkan Screener View sebagai layar utama
            this.switchView('screener');
            // Preload candlestick emiten default di background agar instan saat dibuka
            this.loadData(this.currentSymbol, this.currentInterval);
        }

        // 5. Muat data screener 880+ saham BEI, kategori watchlist, settings risiko, watchlist, dan trading plan
        this.fetchScreenerData();
        this.fetchWatchlistCategories();
        this.fetchRiskSettings();
        this.fetchWatchlist();
        this.fetchTradingPlans();
    }
    
    getChartStyles() {
        return {
            grid: {
                show: true,
                horizontal: {
                    show: true,
                    size: 1,
                    color: 'rgba(255, 255, 255, 0.04)',
                    style: 'dash',
                    dashedValue: [2, 2]
                },
                vertical: {
                    show: true,
                    size: 1,
                    color: 'rgba(255, 255, 255, 0.04)',
                    style: 'dash',
                    dashedValue: [2, 2]
                }
            },
            candle: {
                type: 'candle_solid',
                bar: {
                    upColor: '#089981',
                    downColor: '#f23645',
                    noChangeColor: '#888888',
                    upBorderColor: '#089981',
                    downBorderColor: '#f23645',
                    noChangeBorderColor: '#888888',
                    upWickColor: '#089981',
                    downWickColor: '#f23645',
                    noChangeWickColor: '#888888'
                },
                priceMark: {
                    show: true,
                    high: { show: true, color: '#f1f5f9', textSize: 10 },
                    low: { show: true, color: '#f1f5f9', textSize: 10 },
                    last: {
                        show: true,
                        upColor: '#089981',
                        downColor: '#f23645',
                        noChangeColor: '#888888',
                        line: { show: true, style: 'dash', dashedValue: [4, 4], size: 1 },
                        text: { show: true, size: 11, paddingLeft: 4, paddingTop: 4, paddingRight: 4, paddingBottom: 4, color: '#ffffff' }
                    }
                },
                tooltip: {
                    showRule: 'always',
                    showType: 'standard',
                    custom: [
                        { title: 'Waktu: ', value: '{time}' },
                        { title: 'O: ', value: '{open}' },
                        { title: 'H: ', value: '{high}' },
                        { title: 'L: ', value: '{low}' },
                        { title: 'C: ', value: '{close}' },
                        { title: 'V: ', value: '{volume}' }
                    ],
                    text: {
                        size: 11,
                        color: '#94a3b8'
                    }
                }
            },
            indicator: {
                bars: [
                    {
                        style: 'fill',
                        borderStyle: 'solid',
                        borderSize: 1,
                        upColor: 'rgba(8, 153, 129, 0.65)',
                        downColor: 'rgba(242, 54, 69, 0.65)',
                        noChangeColor: '#888888'
                    }
                ],
                lines: [
                    { style: 'solid', size: 1.5, color: '#06b6d4' },
                    { style: 'solid', size: 1.5, color: '#f59e0b' },
                    { style: 'solid', size: 1.5, color: '#a855f7' },
                    { style: 'solid', size: 1.5, color: '#3b82f6' }
                ]
            },
            xAxis: {
                show: true,
                axisLine: { show: true, color: 'rgba(255, 255, 255, 0.08)', size: 1 },
                tickText: { color: '#64748b', size: 10 },
                tickLine: { show: false }
            },
            yAxis: {
                show: true,
                axisLine: { show: true, color: 'rgba(255, 255, 255, 0.08)', size: 1 },
                tickText: { color: '#64748b', size: 10 },
                tickLine: { show: false }
            },
            crosshair: {
                show: true,
                horizontal: {
                    show: true,
                    line: { style: 'dash', dashedValue: [4, 2], size: 1, color: '#475569' },
                    text: { color: '#ffffff', backgroundColor: '#334155' }
                },
                vertical: {
                    show: true,
                    line: { style: 'dash', dashedValue: [4, 2], size: 1, color: '#475569' },
                    text: { color: '#ffffff', backgroundColor: '#334155' }
                }
            },
            separator: {
                size: 2,
                color: 'rgba(255, 255, 255, 0.16)',
                fill: true,
                activeBackgroundColor: 'rgba(59, 130, 246, 0.4)'
            },
            overlay: {
                point: {
                    color: '#10b981',
                    borderColor: '#ffffff',
                    borderSize: 1,
                    radius: 5,
                    activeRadius: 7
                },
                line: {
                    style: 'solid',
                    color: '#3b82f6',
                    size: 2
                }
            }
        };
    }
    
    setupMobileChartGestures() {
        const container = document.getElementById('chart-container');
        if (!container || !this.chart) return;

        let activeGesture = null; // 'pane_resize' | 'yaxis_scale'
        let activeResizePaneId = null;
        let activeYAxisComponent = null;
        let activeYAxisPane = null;
        let startTouchY = 0;
        let startPaneHeight = 80;
        let startExtremum = null;
        let lastYAxisTapTime = 0;

        // Subtle floating button "Auto Skala" when vertical price/indicator axis is manually zoomed/scaled
        let autoScaleBtn = document.getElementById('btn-auto-scale-y');
        if (!autoScaleBtn) {
            autoScaleBtn = document.createElement('button');
            autoScaleBtn.id = 'btn-auto-scale-y';
            autoScaleBtn.className = 'auto-scale-btn hidden';
            autoScaleBtn.innerHTML = '<span>⟲ Auto Skala</span>';
            autoScaleBtn.title = 'Kembalikan skala vertikal ke otomatis';
            if (container.parentElement) {
                container.parentElement.appendChild(autoScaleBtn);
            }

            autoScaleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.resetPriceAxisScale();
            });
        }

        const resetScale = (specificAxis = null) => {
            if (specificAxis && typeof specificAxis.setAutoCalcTickFlag === 'function') {
                specificAxis.setAutoCalcTickFlag(true);
                this.chart.adjustPaneViewport(false, true, true, true);
                if (autoScaleBtn) autoScaleBtn.classList.add('hidden');
                return;
            }

            // Reset semua pane (candle + sub-pane indikator)
            const candlePane = this.chart.getCandlePane ? this.chart.getCandlePane() : null;
            if (candlePane) {
                const a = candlePane.getAxisComponent ? candlePane.getAxisComponent() : null;
                if (a && typeof a.setAutoCalcTickFlag === 'function') a.setAutoCalcTickFlag(true);
            }
            const candidatePaneIds = ['pane_vol', 'pane_macd', 'pane_rsi', 'pane_net_flow'];
            for (const pid of candidatePaneIds) {
                const p = this.chart.getDrawPaneById ? this.chart.getDrawPaneById(pid) : null;
                if (p) {
                    const a = p.getAxisComponent ? p.getAxisComponent() : null;
                    if (a && typeof a.setAutoCalcTickFlag === 'function') a.setAutoCalcTickFlag(true);
                }
            }
            this.chart.adjustPaneViewport(false, true, true, true);
            if (autoScaleBtn) autoScaleBtn.classList.add('hidden');
        };
        this.resetPriceAxisScale = resetScale;

        // Helper untuk mencari pane mana yang berada di koordinat vertikal Y tertentu
        const getPaneAtY = (coordY) => {
            const candlePane = this.chart.getCandlePane ? this.chart.getCandlePane() : null;
            const candidatePaneIds = ['pane_vol', 'pane_macd', 'pane_rsi', 'pane_net_flow'];
            const allPanes = [];
            if (candlePane) allPanes.push(candlePane);
            for (const pid of candidatePaneIds) {
                const p = this.chart.getDrawPaneById ? this.chart.getDrawPaneById(pid) : null;
                if (p) allPanes.push(p);
            }

            for (const p of allPanes) {
                if (p && p.getBounding) {
                    const b = p.getBounding();
                    if (b && coordY >= b.top && coordY <= (b.top + b.height)) {
                        return p;
                    }
                }
            }
            return candlePane;
        };

        // Double-click on price or indicator scale resets auto-scale
        container.addEventListener('dblclick', (e) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            if (x >= rect.width - 70) {
                const targetPane = getPaneAtY(y);
                const axis = targetPane && targetPane.getAxisComponent ? targetPane.getAxisComponent() : null;
                resetScale(axis);
            }
        });

        // Touch gestures for mobile PWA
        container.addEventListener('touchstart', (e) => {
            if (e.touches.length !== 1) return;
            const touch = e.touches[0];
            const rect = container.getBoundingClientRect();
            const x = touch.clientX - rect.left;
            const y = touch.clientY - rect.top;

            // 1. Right side Price / Indicator Y-Axis (Width ~65px)
            if (x >= rect.width - 65) {
                const targetPane = getPaneAtY(y);
                const axis = targetPane && targetPane.getAxisComponent ? targetPane.getAxisComponent() : null;
                activeYAxisComponent = axis;
                activeYAxisPane = targetPane;

                const now = Date.now();
                if (now - lastYAxisTapTime < 350) {
                    // Double tap on scale -> reset auto-scale untuk pane yang disentuh!
                    resetScale(axis);
                    lastYAxisTapTime = 0;
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                lastYAxisTapTime = now;

                if (axis) {
                    activeGesture = 'yaxis_scale';
                    startTouchY = touch.clientY;
                    const ext = axis.getExtremum ? axis.getExtremum() : null;
                    startExtremum = ext ? { ...ext } : null;
                    e.stopPropagation();
                }
                return;
            }

            // 2. Near Indicator Sub-Pane Divider lines (Touch tolerance +/- 28px)
            // Mendukung fleksibel untuk semua indikator: Volume, RSI, MACD, Net Flow, dsb.
            const candidatePaneIds = ['pane_vol', 'pane_macd', 'pane_rsi', 'pane_net_flow'];
            let matchedPane = null;
            let closestDist = 28;

            for (const pid of candidatePaneIds) {
                const pane = this.chart.getDrawPaneById ? this.chart.getDrawPaneById(pid) : null;
                if (pane && pane.getBounding) {
                    const bound = pane.getBounding();
                    if (bound && bound.height > 0) {
                        const dividerY = bound.top;
                        const dist = Math.abs(y - dividerY);
                        if (dist <= 28 && dist < closestDist) {
                            closestDist = dist;
                            matchedPane = {
                                id: pid,
                                height: bound.height
                            };
                        }
                    }
                }
            }

            if (matchedPane) {
                activeGesture = 'pane_resize';
                activeResizePaneId = matchedPane.id;
                startTouchY = touch.clientY;
                startPaneHeight = matchedPane.height || 80;
                e.preventDefault();
                e.stopPropagation();
                return;
            }
        }, { capture: true, passive: false });

        container.addEventListener('touchmove', (e) => {
            if (!activeGesture || e.touches.length !== 1) return;
            const touch = e.touches[0];
            const rect = container.getBoundingClientRect();

            if (activeGesture === 'pane_resize' && activeResizePaneId) {
                e.preventDefault();
                e.stopPropagation();
                const deltaY = startTouchY - touch.clientY; // drag up -> increase height
                const maxH = Math.floor(rect.height * 0.55);
                const minH = 40;
                const newH = Math.max(minH, Math.min(maxH, Math.round(startPaneHeight + deltaY)));
                this.chart.setPaneOptions({ id: activeResizePaneId, height: newH });
            } else if (activeGesture === 'yaxis_scale' && startExtremum && startExtremum.range && activeYAxisComponent) {
                e.preventDefault();
                e.stopPropagation();
                const deltaY = touch.clientY - startTouchY;
                // Move down -> compress (larger range), Move up -> expand (smaller range)
                const factor = Math.exp(deltaY / 160);
                const newRange = startExtremum.range * factor;
                const diff = (newRange - startExtremum.range) / 2;
                const newMin = startExtremum.min - diff;
                const newMax = startExtremum.max + diff;

                const axis = activeYAxisComponent;
                if (axis) {
                    const rMin = typeof axis.convertToRealValue === 'function' ? axis.convertToRealValue(newMin) : newMin;
                    const rMax = typeof axis.convertToRealValue === 'function' ? axis.convertToRealValue(newMax) : newMax;
                    axis.setExtremum({
                        min: newMin,
                        max: newMax,
                        range: newRange,
                        realMin: rMin,
                        realMax: rMax,
                        realRange: rMax - rMin
                    });
                    this.chart.adjustPaneViewport(false, true, true, true);
                    if (autoScaleBtn) autoScaleBtn.classList.remove('hidden');
                }
            }
        }, { capture: true, passive: false });

        const endGesture = () => {
            activeGesture = null;
            activeResizePaneId = null;
            activeYAxisComponent = null;
            activeYAxisPane = null;
            startExtremum = null;
        };
        container.addEventListener('touchend', endGesture, { capture: true });
        container.addEventListener('touchcancel', endGesture, { capture: true });
    }

    setupEvents() {
        // Resize Window
        window.addEventListener('resize', () => {
            if (this.chart) this.chart.resize();
        });

        // Handle Browser / Mobile Hardware Back & Forward Buttons
        window.addEventListener('hashchange', () => {
            if (this._skipNextHashChange) {
                this._skipNextHashChange = false;
                return;
            }
            this.handleRouteFromHash();
        });

        window.addEventListener('popstate', () => {
            if (this._skipNextHashChange) {
                this._skipNextHashChange = false;
                return;
            }
            this.handleRouteFromHash();
        });
        
        // ── Point 1: Direct In-Place Editable Ticker ──
        if (this.dom.tickerInplaceInput) {
            // Auto size input based on content
            const updateInputWidth = () => {
                const len = this.dom.tickerInplaceInput.value.length || 4;
                this.dom.tickerInplaceInput.style.width = Math.max(len * 12, 54) + 'px';
            };

            this.dom.tickerInplaceInput.addEventListener('focus', () => {
                this.dom.tickerInplaceInput.select();
            });

            this.dom.tickerInplaceInput.addEventListener('input', () => {
                updateInputWidth();
            });

            this.dom.tickerInplaceInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const val = this.dom.tickerInplaceInput.value.trim().toUpperCase();
                    if (val && val !== this.currentSymbol) {
                        this.setSymbol(val);
                    }
                    this.dom.tickerInplaceInput.blur();
                } else if (e.key === 'Escape') {
                    this.dom.tickerInplaceInput.value = this.currentSymbol;
                    updateInputWidth();
                    this.dom.tickerInplaceInput.blur();
                }
            });

            this.dom.tickerInplaceInput.addEventListener('blur', () => {
                const val = this.dom.tickerInplaceInput.value.trim().toUpperCase();
                if (val && val !== this.currentSymbol) {
                    this.setSymbol(val);
                } else {
                    this.dom.tickerInplaceInput.value = this.currentSymbol;
                }
                updateInputWidth();
            });
        }

        // ── Single Timeframe Dropdown ──
        if (this.dom.btnTimeframe && this.dom.timeframeMenu) {
            this.dom.btnTimeframe.addEventListener('click', (e) => {
                e.stopPropagation();
                this.dom.timeframeMenu.classList.toggle('hidden');
            });

            this.dom.tfOptions.forEach(opt => {
                opt.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const tf = opt.dataset.tf;
                    if (tf) {
                        this.dom.tfOptions.forEach(b => b.classList.remove('active'));
                        opt.classList.add('active');
                        this.dom.activeTfLabel.textContent = tf.toUpperCase();
                        this.currentInterval = tf;
                        this.dom.timeframeMenu.classList.add('hidden');
                        this.loadData(this.currentSymbol, this.currentInterval);
                    }
                });
            });

            // Close timeframe dropdown on outside click
            document.addEventListener('click', () => {
                this.dom.timeframeMenu.classList.add('hidden');
            });
        }

        // ── Point 3: Logo-Enabled Watchlist Chips ──
        if (this.dom.quickChipsContainer) {
            this.dom.quickChipsContainer.addEventListener('click', (e) => {
                const btn = e.target.closest('.chip-btn');
                if (btn && btn.dataset.symbol) {
                    this.setSymbol(btn.dataset.symbol);
                }
            });
        }

        // Keyboard Shortcut: Delete / Backspace to delete selected overlay
        window.addEventListener('keydown', (e) => {
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedOverlay) {
                if (document.activeElement && document.activeElement.tagName === 'INPUT') return;
                this.deleteSelectedOverlay();
            }
        });

        // Auto-Deselect Overlay saat tap/klik di tempat kosong chart atau luar elemen
        document.addEventListener('pointerup', (e) => {
            // Jika baru saja berinteraksi/klik overlay (< 180ms), jangan deselect
            if (Date.now() - this._lastOverlayInteraction < 180) return;

            // Jika klik terjadi di dalam popup atau kontrol yang relevan, abaikan
            if (e.target.closest('#overlay-action-popup') || 
                e.target.closest('.action-pill') || 
                e.target.closest('.tf-menu') || 
                e.target.closest('.bottom-sheet') || 
                e.target.closest('.quick-chips-bar') ||
                e.target.closest('.ticker-badge')) {
                return;
            }

            // Jika ada overlay yang aktif dipilih, batalkan seleksi dan sembunyikan popup!
            if (this.selectedOverlay) {
                this.deselectOverlay();
            }
        });

        // Cegah event bubbling dari dalam popup aksi agar klik tombol popup tidak mendeselect
        if (this.dom.overlayActionPopup) {
            ['pointerdown', 'pointerup', 'click'].forEach(evt => {
                this.dom.overlayActionPopup.addEventListener(evt, (e) => e.stopPropagation());
            });
        }

        // PWA Lifecycle: Auto-save coretan saat tab/app ditutup atau backgrounded di HP
        window.addEventListener('beforeunload', () => {
            this.saveOverlaysForSymbol();
        });
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.saveOverlaysForSymbol();
            }
        });
    }

    setupToolEvents() {
        // 1. Open Drawing Tools Sheet
        if (this.dom.btnDraw) {
            this.dom.btnDraw.addEventListener('click', () => {
                this.openSheet('draw');
            });
        }

        // 2. Open Indicator Sheet
        if (this.dom.btnIndicator) {
            this.dom.btnIndicator.addEventListener('click', () => {
                this.openSheet('indicator');
            });
        }

        // 3. Reset All Overlays Button (Control Bar)
        if (this.dom.btnResetOverlays) {
            this.dom.btnResetOverlays.addEventListener('click', () => {
                this.clearAllOverlays();
            });
        }

        // ── Point 2: Contextual Floating Overlay Popup Events ──
        if (this.dom.popupBtnDelete) {
            this.dom.popupBtnDelete.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSelectedOverlay();
            });
        }

        if (this.dom.popupBtnDeleteAll) {
            this.dom.popupBtnDeleteAll.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clearAllOverlays();
            });
        }

        if (this.dom.popupBtnClose) {
            this.dom.popupBtnClose.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deselectOverlay();
            });
        }

        if (this.dom.popupBtnLock) {
            this.dom.popupBtnLock.addEventListener('click', () => {
                if (!this.selectedOverlay || !this.chart) return;
                const isLocked = !this.selectedOverlay.lock;
                this.selectedOverlay.lock = isLocked;
                this.chart.overrideOverlay({
                    id: this.selectedOverlay.id,
                    lock: isLocked
                });
                this.dom.popupBtnLock.textContent = isLocked ? '🔒' : '🔓';
                this.showToast(isLocked ? 'Garis dikunci' : 'Kunci garis dibuka', 'info');
                this.saveOverlaysForSymbol();
            });
        }

        // Color Picker Dots
        this.dom.colorDots.forEach(dot => {
            dot.addEventListener('click', () => {
                if (!this.selectedOverlay || !this.chart) return;
                const color = dot.dataset.color;
                if (!color) return;

                this.dom.colorDots.forEach(d => d.classList.remove('active'));
                dot.classList.add('active');

                // Update overlay styles
                this.chart.overrideOverlay({
                    id: this.selectedOverlay.id,
                    styles: {
                        line: { color: color },
                        point: { color: color },
                        rect: { borderColor: color, color: hexToRgba(color, 0.15) }
                    }
                });
                this.showToast(`Warna garis diubah`, 'info');
                this.saveOverlaysForSymbol();
            });
        });

        // Close Sheets via Backdrop & Close Buttons
        if (this.dom.sheetBackdrop) {
            this.dom.sheetBackdrop.addEventListener('click', () => this.closeSheets());
        }
        if (this.dom.closeDrawSheet) {
            this.dom.closeDrawSheet.addEventListener('click', () => this.closeSheets());
        }
        if (this.dom.closeIndSheet) {
            this.dom.closeIndSheet.addEventListener('click', () => this.closeSheets());
        }
        if (this.dom.closeBroksumSheet) {
            this.dom.closeBroksumSheet.addEventListener('click', () => this.closeSheets());
        }

        // Tap Bandar Badge (Kanan Bawah) to open Broker Summary Sheet
        if (this.dom.bandarBadge) {
            this.dom.bandarBadge.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openBroksumSheet();
            });
        }

        // Tool Selection from Bottom Sheet
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const toolType = btn.dataset.tool;
                const toolName = btn.dataset.name;
                this.closeSheets();
                this.startDrawing(toolType, toolName);
            });
        });

        // Technical Indicator Toggles
        if (this.dom.toggleSnr) {
            this.dom.toggleSnr.addEventListener('click', () => this.toggleAutoSnR());
        }
        if (this.dom.toggleHmb) {
            this.dom.toggleHmb.addEventListener('click', () => this.toggleHmbLine());
        }
        if (this.dom.toggleNetFlow) {
            this.dom.toggleNetFlow.addEventListener('click', () => this.toggleNetFlow());
        }

        // Auto SnR Settings Panel Toggle & Chips
        if (this.dom.btnSnrSettings && this.dom.snrSettingsPanel) {
            this.dom.btnSnrSettings.addEventListener('click', (e) => {
                e.stopPropagation();
                this.dom.snrSettingsPanel.classList.toggle('hidden');
                this.dom.btnSnrSettings.classList.toggle('active');
            });
        }

        if (this.dom.snrPeriodChips) {
            this.dom.snrPeriodChips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const period = chip.dataset.period;
                    if (period && period !== this.snrConfig.period) {
                        this.saveSnrConfig({ period });
                    }
                });
            });
        }

        if (this.dom.snrFormulaChips) {
            this.dom.snrFormulaChips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const formula = chip.dataset.formula;
                    if (formula && formula !== this.snrConfig.formula) {
                        this.saveSnrConfig({ formula });
                    }
                });
            });
        }

        if (this.dom.toggleEma) {
            this.dom.toggleEma.addEventListener('click', () => this.toggleIndicator('EMA', 'candle_pane', this.dom.toggleEma));
        }
        if (this.dom.toggleBoll) {
            this.dom.toggleBoll.addEventListener('click', () => this.toggleIndicator('BOLL', 'candle_pane', this.dom.toggleBoll));
        }
        if (this.dom.toggleMacd) {
            this.dom.toggleMacd.addEventListener('click', () => this.toggleIndicator('MACD', 'pane_macd', this.dom.toggleMacd, { height: 90 }));
        }
        if (this.dom.toggleRsi) {
            this.dom.toggleRsi.addEventListener('click', () => this.toggleIndicator('RSI', 'pane_rsi', this.dom.toggleRsi, { height: 80 }));
        }

        // Setup Filter Rentang Tanggal Broksum
        this.setupBroksumFilterEvents();
        this.setupBroksumSubTabEvents();
    }

    openSheet(type) {
        if (!this.dom.sheetBackdrop) return;
        this.dom.sheetBackdrop.classList.remove('hidden');
        if (type === 'draw' && this.dom.drawSheet) {
            this.dom.drawSheet.classList.remove('hidden');
            if (this.dom.indicatorSheet) this.dom.indicatorSheet.classList.add('hidden');
            if (this.dom.broksumSheet) this.dom.broksumSheet.classList.add('hidden');
        } else if (type === 'indicator' && this.dom.indicatorSheet) {
            this.dom.indicatorSheet.classList.remove('hidden');
            if (this.dom.drawSheet) this.dom.drawSheet.classList.add('hidden');
            if (this.dom.broksumSheet) this.dom.broksumSheet.classList.add('hidden');
        } else if (type === 'broksum' && this.dom.broksumSheet) {
            this.dom.broksumSheet.classList.remove('hidden');
            if (this.dom.drawSheet) this.dom.drawSheet.classList.add('hidden');
            if (this.dom.indicatorSheet) this.dom.indicatorSheet.classList.add('hidden');
        }
    }

    closeSheets() {
        if (this.dom.sheetBackdrop) this.dom.sheetBackdrop.classList.add('hidden');
        if (this.dom.drawSheet) this.dom.drawSheet.classList.add('hidden');
        if (this.dom.indicatorSheet) this.dom.indicatorSheet.classList.add('hidden');
        if (this.dom.broksumSheet) this.dom.broksumSheet.classList.add('hidden');
    }

    // ── Point 2: Mode Gambar Bersih Tanpa Banner Mengganggu ──
    startDrawing(toolType, toolName) {
        if (!this.chart) return;
        try {
            this.deselectOverlay();
            
            // Pasang overlay dengan callback lifecycle lengkap untuk auto-save
            const overlayId = this.chart.createOverlay({
                name: toolType,
                onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
                onSelected: ({ overlay }) => this.handleOverlaySelect(overlay),
                onDrawing: () => { this._lastOverlayInteraction = Date.now(); },
                onDrawEnd: ({ overlay }) => {
                    if (overlay && overlay.id) {
                        this.manualOverlayIds.add(overlay.id);
                    }
                    this.saveOverlaysForSymbol();
                },
                onPressedMoveEnd: () => {
                    this.saveOverlaysForSymbol();
                },
                onRemoved: ({ overlay }) => {
                    if (overlay && overlay.id) {
                        this.manualOverlayIds.delete(overlay.id);
                    }
                    this.saveOverlaysForSymbol();
                },
                onDeselected: () => this.deselectOverlay()
            });

            if (overlayId) {
                this.manualOverlayIds.add(overlayId);
            }

            // Toast instruksi spesifik yang membantu pengguna
            let guideText = `${toolName} aktif: tap titik di chart`;
            if (toolType === 'priceProjection') {
                guideText = 'Long Position: Tap 1: Entry, Tap 2: Target TP, Tap 3: Stop Loss';
            } else if (toolType === 'rectZone') {
                guideText = 'Area Box: Tap sudut awal lalu tap sudut akhir';
            }
            this.showToast(guideText, 'info');
        } catch (e) {
            console.error('Error creating overlay:', e);
            this.showToast(`Gagal memulai tool ${toolName}: ${e.message}`, 'error');
        }
    }

    // ── Point 2: Contextual Floating Action Popup upon Clicking an Object ──
    handleOverlaySelect(overlay) {
        if (!overlay) return;
        this._lastOverlayInteraction = Date.now();
        this.selectedOverlay = overlay;
        const nameMap = {
            'segment': 'Garis Tren',
            'horizontalStraightLine': 'Horizontal SnR',
            'rayLine': 'Garis Sinar',
            'fibonacciLine': 'Fibonacci',
            'priceChannelLine': 'Channel',
            'rectZone': 'Area Box',
            'priceProjection': 'Long (R:R)',
            'autoSnR': 'Auto SnR Pivots',
            'hmbLine': 'Harga Modal Bandar (HMB)'
        };
        let displayName = nameMap[overlay.name] || overlay.name || 'Garis';
        if (overlay.name === 'autoSnR' && overlay.extendData) {
            const f = overlay.extendData.formula === 'fibonacci' ? 'Fib' : 'Classic';
            const p = overlay.extendData.period === 'weekly' ? 'Weekly' : 'Daily';
            displayName = `Auto SnR (${f} ${p})`;
        }
        
        if (this.dom.overlayActionPopup && this.dom.popupOverlayName) {
            this.dom.popupOverlayName.textContent = displayName;
            if (this.dom.popupBtnLock) {
                this.dom.popupBtnLock.textContent = overlay.lock ? '🔒' : '🔓';
            }
            this.dom.overlayActionPopup.classList.remove('hidden');
        }
    }

    // Hapus satu garis spesifik yang sedang aktif dipilih
    deleteSelectedOverlay() {
        if (!this.selectedOverlay || !this.chart) return;
        const id = this.selectedOverlay.id;
        try {
            if (id === 'overlay_auto_snr') {
                this.toggleAutoSnR();
                return;
            }
            if (id === 'overlay_hmb') {
                this.toggleHmbLine();
                return;
            }
            this.chart.removeOverlay(id);
            this.manualOverlayIds.delete(id);
            this.saveOverlaysForSymbol();
            this.showToast('Garis berhasil dihapus', 'info');
        } catch (err) {
            console.error('Failed to remove overlay:', err);
        } finally {
            this.deselectOverlay();
        }
    }

    // Hapus semua garis & coretan manual yang ada di chart
    clearAllOverlays() {
        if (!this.chart) return;
        try {
            // Hapus semua manual overlay dari chart
            for (const id of this.manualOverlayIds) {
                try {
                    this.chart.removeOverlay(id);
                } catch (e) {}
            }
            this.manualOverlayIds.clear();
            this.saveOverlaysForSymbol();

            this.showToast('Semua coretan di chart dibersihkan', 'info');
            // Jika indikator Auto SnR atau HMB sedang aktif, pasang kembali overlay-nya
            if (this.indicatorState.SNR) {
                this.refreshAutoSnR();
            }
            if (this.indicatorState.HMB) {
                this.refreshHmbLine();
            }
        } catch (err) {
            console.error('Failed to remove all overlays:', err);
        } finally {
            this.deselectOverlay();
        }
    }

    // Batalkan seleksi garis & sembunyikan popup aksi
    deselectOverlay() {
        this.selectedOverlay = null;
        if (this.dom.overlayActionPopup) {
            this.dom.overlayActionPopup.classList.add('hidden');
        }
    }

    // ── Drawing Persistence: Auto-Save & Auto-Load per Emiten (localStorage) ──
    getStorageKeyForSymbol(symbol = this.currentSymbol) {
        return `candlify_drawings_${symbol.toUpperCase()}`;
    }

    saveOverlaysForSymbol(symbol = this.currentSymbol) {
        if (!this.chart || !symbol) return;
        try {
            const manualOverlays = [];

            // Tambahkan ID dari OverlayStore chart jika ada instance manual yang belum terdaftar
            const allInstances = this.chart._chartStore?.getOverlayStore()?.getInstances() || [];
            allInstances.forEach(inst => {
                if (inst && inst.id && !this.manualOverlayIds.has(inst.id)) {
                    if (inst.id !== 'overlay_auto_snr' && inst.id !== 'overlay_hmb' && 
                        inst.name !== 'autoSnR' && inst.name !== 'hmbLine') {
                        this.manualOverlayIds.add(inst.id);
                    }
                }
            });

            for (const id of this.manualOverlayIds) {
                const overlay = this.chart.getOverlayById(id);
                if (!overlay) continue;

                // Abaikan jika sistem overlay (Auto SnR atau HMB)
                if (overlay.id === 'overlay_auto_snr' || overlay.id === 'overlay_hmb' ||
                    overlay.name === 'autoSnR' || overlay.name === 'hmbLine') {
                    continue;
                }

                // Jangan simpan gambar yang belum selesai proses drawing-nya
                if (typeof overlay.isDrawing === 'function' && overlay.isDrawing()) {
                    continue;
                }

                // Jangan simpan jika points tidak valid
                if (!Array.isArray(overlay.points) || overlay.points.length === 0) {
                    continue;
                }

                // Bersihkan points agar formatnya serializable dan presisi
                const cleanPoints = overlay.points.map(pt => {
                    const p = {};
                    if (typeof pt.timestamp === 'number') p.timestamp = pt.timestamp;
                    if (typeof pt.dataIndex === 'number') p.dataIndex = pt.dataIndex;
                    if (typeof pt.value === 'number') p.value = pt.value;
                    return p;
                }).filter(p => typeof p.value === 'number');

                if (cleanPoints.length === 0) continue;

                manualOverlays.push({
                    id: overlay.id,
                    name: overlay.name,
                    points: cleanPoints,
                    styles: overlay.styles,
                    lock: !!overlay.lock,
                    visible: overlay.visible !== false,
                    extendData: overlay.extendData
                });
            }

            const storageKey = this.getStorageKeyForSymbol(symbol);
            localStorage.setItem(storageKey, JSON.stringify(manualOverlays));
        } catch (e) {
            console.warn(`[Candlify] Gagal menyimpan coretan ${symbol}:`, e);
        }
    }

    loadOverlaysForSymbol(symbol = this.currentSymbol) {
        if (!this.chart || !symbol) return;
        try {
            const storageKey = this.getStorageKeyForSymbol(symbol);
            const savedStr = localStorage.getItem(storageKey);
            if (!savedStr) return;

            const savedList = JSON.parse(savedStr);
            if (!Array.isArray(savedList) || savedList.length === 0) return;

            savedList.forEach(item => {
                if (!item || !item.name || !Array.isArray(item.points) || item.points.length === 0) return;

                // Hindari re-create jika overlay dengan ID tersebut sudah ada
                const existing = this.chart.getOverlayById(item.id);
                if (existing) {
                    this.manualOverlayIds.add(item.id);
                    return;
                }

                const createdId = this.chart.createOverlay({
                    id: item.id,
                    name: item.name,
                    points: item.points,
                    styles: item.styles,
                    lock: !!item.lock,
                    visible: item.visible !== false,
                    extendData: item.extendData,
                    onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
                    onSelected: ({ overlay }) => this.handleOverlaySelect(overlay),
                    onDrawing: () => { this._lastOverlayInteraction = Date.now(); },
                    onDrawEnd: ({ overlay }) => {
                        if (overlay && overlay.id) this.manualOverlayIds.add(overlay.id);
                        this.saveOverlaysForSymbol();
                    },
                    onPressedMoveEnd: () => {
                        this.saveOverlaysForSymbol();
                    },
                    onRemoved: ({ overlay }) => {
                        if (overlay && overlay.id) this.manualOverlayIds.delete(overlay.id);
                        this.saveOverlaysForSymbol();
                    },
                    onDeselected: () => this.deselectOverlay()
                });

                if (createdId) {
                    this.manualOverlayIds.add(createdId);
                } else if (item.id) {
                    this.manualOverlayIds.add(item.id);
                }
            });
        } catch (e) {
            console.warn(`[Candlify] Gagal memuat coretan ${symbol}:`, e);
        }
    }

    clearManualOverlaysFromChart() {
        if (!this.chart) return;
        this.deselectOverlay();
        for (const id of this.manualOverlayIds) {
            try {
                this.chart.removeOverlay(id);
            } catch (err) {
                // ignore
            }
        }
        this.manualOverlayIds.clear();
    }

    // ── Auto SnR: Configuration & Persistence ──
    loadSnrConfig() {
        try {
            const saved = localStorage.getItem('candlify_snr_config');
            if (saved) {
                const parsed = JSON.parse(saved);
                return {
                    period: parsed.period === 'weekly' ? 'weekly' : 'daily',
                    formula: parsed.formula === 'fibonacci' ? 'fibonacci' : 'classic'
                };
            }
        } catch (e) {
            console.warn('Failed to parse snrConfig from localStorage', e);
        }
        return {
            period: 'daily',
            formula: 'classic'
        };
    }

    saveSnrConfig(config) {
        this.snrConfig = { ...this.snrConfig, ...config };
        try {
            localStorage.setItem('candlify_snr_config', JSON.stringify(this.snrConfig));
        } catch (e) {
            console.warn('Failed to save snrConfig to localStorage', e);
        }
        this.updateSnrUi();
        if (this.indicatorState.SNR) {
            this.refreshAutoSnR();
            const periodTxt = this.snrConfig.period === 'weekly' ? 'Weekly' : 'Daily';
            const formulaTxt = this.snrConfig.formula === 'fibonacci' ? 'Fibonacci' : 'Classic';
            this.showToast(`SnR diperbarui: ${formulaTxt} (${periodTxt})`, 'info');
        }
    }

    updateSnrUi() {
        const periodTxt = this.snrConfig?.period === 'weekly' ? 'Weekly' : 'Daily';
        const formulaTxt = this.snrConfig?.formula === 'fibonacci' ? 'Fibonacci' : 'Classic';

        if (this.dom.snrConfigDesc) {
            this.dom.snrConfigDesc.textContent = `Level kunci ${formulaTxt} Pivot (${periodTxt})`;
        }

        if (this.dom.snrPeriodChips) {
            this.dom.snrPeriodChips.forEach(chip => {
                if (chip.dataset.period === this.snrConfig?.period) {
                    chip.classList.add('active');
                } else {
                    chip.classList.remove('active');
                }
            });
        }

        if (this.dom.snrFormulaChips) {
            this.dom.snrFormulaChips.forEach(chip => {
                if (chip.dataset.formula === this.snrConfig?.formula) {
                    chip.classList.add('active');
                } else {
                    chip.classList.remove('active');
                }
            });
        }
    }

    // ── Auto SnR: Pivot Point Calculation (Classic & Fibonacci, Daily & Weekly) ──
    calculatePivots() {
        if (!this.chart) return null;
        const data = this.chart.getDataList();
        if (!data || data.length === 0) return null;

        const period = this.snrConfig?.period || 'daily';
        const formula = this.snrConfig?.formula || 'classic';
        let H, L, C, refTimestamp;

        if (period === 'weekly') {
            // Helper: Group by Monday date of the week in WIB (UTC+7)
            const getMondayKey = (ts) => {
                const d = new Date(ts + 7 * 3600000);
                const day = d.getUTCDay(); // 0 is Sunday, 1 is Monday
                const diff = d.getUTCDate() - (day === 0 ? 6 : day - 1);
                d.setUTCDate(diff);
                return d.toISOString().split('T')[0];
            };

            const weekMap = new Map();
            for (const c of data) {
                const wKey = getMondayKey(c.timestamp);
                if (!weekMap.has(wKey)) weekMap.set(wKey, []);
                weekMap.get(wKey).push(c);
            }
            const weeks = Array.from(weekMap.keys());
            let targetCandles = [];
            if (weeks.length > 1) {
                // Gunakan pekan sebelumnya yang sudah tuntas (closed week)
                targetCandles = weekMap.get(weeks[weeks.length - 2]);
            } else {
                targetCandles = weekMap.get(weeks[0]);
            }

            if (!targetCandles || targetCandles.length === 0) return null;
            H = Math.max(...targetCandles.map(c => Number(c.high)));
            L = Math.min(...targetCandles.map(c => Number(c.low)));
            C = Number(targetCandles[targetCandles.length - 1].close);
            refTimestamp = data[data.length - 1].timestamp;
        } else {
            // Daily Period
            if (this.currentInterval === '1d' || this.currentInterval === '1w') {
                const refCandle = data.length > 1 ? data[data.length - 2] : data[data.length - 1];
                H = Number(refCandle.high);
                L = Number(refCandle.low);
                C = Number(refCandle.close);
                refTimestamp = data[data.length - 1].timestamp;
            } else {
                // Intraday (5m, 15m, 1h, 4h): kelompokkan berdasarkan tanggal kalender WIB
                const dateMap = new Map();
                for (const c of data) {
                    const dStr = new Date(c.timestamp + 7 * 3600000).toISOString().split('T')[0];
                    if (!dateMap.has(dStr)) dateMap.set(dStr, []);
                    dateMap.get(dStr).push(c);
                }
                const dates = Array.from(dateMap.keys());
                let targetCandles = [];
                if (dates.length > 1) {
                    targetCandles = dateMap.get(dates[dates.length - 2]); // Hari bursa sebelumnya
                } else {
                    targetCandles = dateMap.get(dates[0]); // Hari berjalan jika data cuma 1 hari
                }

                if (!targetCandles || targetCandles.length === 0) return null;
                H = Math.max(...targetCandles.map(c => Number(c.high)));
                L = Math.min(...targetCandles.map(c => Number(c.low)));
                C = Number(targetCandles[targetCandles.length - 1].close);
                refTimestamp = data[data.length - 1].timestamp;
            }
        }

        if (H <= 0 || L <= 0 || C <= 0 || isNaN(H) || isNaN(L) || isNaN(C)) return null;

        let pp, r1, s1, r2, s2;

        if (formula === 'fibonacci') {
            const range = H - L;
            pp = Math.round((H + L + C) / 3);
            r1 = Math.round(pp + (0.382 * range));
            r2 = Math.round(pp + (0.618 * range));
            s1 = Math.round(pp - (0.382 * range));
            s2 = Math.round(pp - (0.618 * range));
        } else {
            // Classic (Floor)
            pp = Math.round((H + L + C) / 3);
            r1 = Math.round((2 * pp) - L);
            s1 = Math.round((2 * pp) - H);
            r2 = Math.round(pp + (H - L));
            s2 = Math.round(pp - (H - L));
        }

        return { r2, r1, pp, s1, s2, timestamp: refTimestamp, formula, period };
    }

    toggleAutoSnR() {
        if (!this.chart) return;
        const currentActive = this.indicatorState.SNR || false;

        if (currentActive) {
            this.chart.removeOverlay('overlay_auto_snr');
            this.indicatorState.SNR = false;
            if (this.dom.toggleSnr) {
                this.dom.toggleSnr.textContent = 'OFF';
                this.dom.toggleSnr.classList.remove('active');
            }
            this.showToast('Auto SnR Pivots dinonaktifkan', 'info');
        } else {
            const pivots = this.calculatePivots();
            if (!pivots) {
                this.showToast('Data candlestick belum cukup untuk hitung SnR', 'warning');
                return;
            }
            this.chart.createOverlay({
                id: 'overlay_auto_snr',
                name: 'autoSnR',
                lock: true,
                extendData: {
                    formula: pivots.formula,
                    period: pivots.period
                },
                points: [
                    { timestamp: pivots.timestamp, value: pivots.r2 },
                    { timestamp: pivots.timestamp, value: pivots.r1 },
                    { timestamp: pivots.timestamp, value: pivots.pp },
                    { timestamp: pivots.timestamp, value: pivots.s1 },
                    { timestamp: pivots.timestamp, value: pivots.s2 }
                ],
                onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
                onSelected: ({ overlay }) => this.handleOverlaySelect(overlay)
            });
            this.indicatorState.SNR = true;
            if (this.dom.toggleSnr) {
                this.dom.toggleSnr.textContent = 'AKTIF';
                this.dom.toggleSnr.classList.add('active');
            }
            const periodTxt = pivots.period === 'weekly' ? 'Weekly' : 'Daily';
            const formulaTxt = pivots.formula === 'fibonacci' ? 'Fibonacci' : 'Classic';
            this.showToast(`Auto SnR aktif (${formulaTxt} ${periodTxt} - PP: ${pivots.pp.toLocaleString('id-ID')})`, 'info');
        }
    }

    refreshAutoSnR() {
        if (!this.chart || !this.indicatorState.SNR) return;
        this.chart.removeOverlay('overlay_auto_snr');
        const pivots = this.calculatePivots();
        if (pivots) {
            this.chart.createOverlay({
                id: 'overlay_auto_snr',
                name: 'autoSnR',
                lock: true,
                extendData: {
                    formula: pivots.formula,
                    period: pivots.period
                },
                points: [
                    { timestamp: pivots.timestamp, value: pivots.r2 },
                    { timestamp: pivots.timestamp, value: pivots.r1 },
                    { timestamp: pivots.timestamp, value: pivots.pp },
                    { timestamp: pivots.timestamp, value: pivots.s1 },
                    { timestamp: pivots.timestamp, value: pivots.s2 }
                ],
                onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
                onSelected: ({ overlay }) => this.handleOverlaySelect(overlay)
            });
        }
    }

    // ── Bandarmologi: Harga Modal Bandar (HMB) & Net Flow ──
    toggleHmbLine() {
        if (!this.chart) return;
        const currentActive = this.indicatorState.HMB || false;

        if (currentActive) {
            this.chart.removeOverlay('overlay_hmb');
            this.indicatorState.HMB = false;
            if (this.dom.toggleHmb) {
                this.dom.toggleHmb.textContent = 'OFF';
                this.dom.toggleHmb.classList.remove('active');
            }
            this.showToast('Garis HMB dinonaktifkan', 'info');
        } else {
            const latestHmb = this.bandarData?.summary?.latest_hmb;
            if (!latestHmb || latestHmb <= 0) {
                this.showToast('Data HMB belum tersedia untuk saham ini', 'warning');
                return;
            }
            const data = this.chart.getDataList();
            const refTimestamp = data && data.length > 0 ? data[data.length - 1].timestamp : Date.now();

            this.chart.createOverlay({
                id: 'overlay_hmb',
                name: 'hmbLine',
                lock: true,
                points: [
                    { timestamp: refTimestamp, value: latestHmb }
                ],
                onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
                onSelected: ({ overlay }) => this.handleOverlaySelect(overlay)
            });
            this.indicatorState.HMB = true;
            if (this.dom.toggleHmb) {
                this.dom.toggleHmb.textContent = 'AKTIF';
                this.dom.toggleHmb.classList.add('active');
            }
            this.showToast(`Garis HMB aktif (Rp ${latestHmb.toLocaleString('id-ID')})`, 'info');
        }
    }

    refreshHmbLine() {
        if (!this.chart || !this.indicatorState.HMB) return;
        this.chart.removeOverlay('overlay_hmb');
        const latestHmb = this.bandarData?.summary?.latest_hmb;
        if (!latestHmb || latestHmb <= 0) return;
        const data = this.chart.getDataList();
        const refTimestamp = data && data.length > 0 ? data[data.length - 1].timestamp : Date.now();

        this.chart.createOverlay({
            id: 'overlay_hmb',
            name: 'hmbLine',
            lock: true,
            points: [
                { timestamp: refTimestamp, value: latestHmb }
            ],
            onClick: ({ overlay }) => this.handleOverlaySelect(overlay),
            onSelected: ({ overlay }) => this.handleOverlaySelect(overlay)
        });
    }

    toggleNetFlow() {
        if (!this.chart) return;
        const currentActive = this.indicatorState.NET_FLOW || false;

        if (currentActive) {
            this.chart.removeIndicator('pane_net_flow');
            this.indicatorState.NET_FLOW = false;
            if (this.dom.toggleNetFlow) {
                this.dom.toggleNetFlow.textContent = 'OFF';
                this.dom.toggleNetFlow.classList.remove('active');
            }
            this.showToast('Net Flow sub-pane dinonaktifkan', 'info');
        } else {
            this.chart.createIndicator('NET_FLOW', false, { id: 'pane_net_flow', height: 80 });
            this.indicatorState.NET_FLOW = true;
            if (this.dom.toggleNetFlow) {
                this.dom.toggleNetFlow.textContent = 'AKTIF';
                this.dom.toggleNetFlow.classList.add('active');
            }
            this.showToast('Bandar Net Flow sub-pane diaktifkan', 'info');
        }
    }

    updateBandarBadge(summary) {
        if (!this.dom.bandarBadge) return;
        if (!summary || !summary.latest_hmb) {
            this.dom.bandarBadge.classList.add('hidden');
            return;
        }
        const isAccum = summary.latest_status === 'ACCUM';
        const flowMiliar = (summary.latest_net_flow / 1e9).toFixed(1);
        const sign = summary.latest_net_flow > 0 ? '+' : '';
        const statusIcon = isAccum ? '🟢' : '🔴';

        // Foreign Flow token (Official IDX Data)
        let foreignToken = '';
        let foreignTitle = '';
        const foreign = summary.foreign_flow || summary.market_intelligence?.foreign_flow;
        if (foreign && foreign.today_net_val !== undefined && foreign.today_net_val !== 0) {
            const fVal = foreign.today_net_val;
            const fAbs = Math.abs(fVal);
            const fSign = fVal > 0 ? '+' : '-';
            let fDisp = '';
            if (fAbs >= 1e12) fDisp = `${(fAbs / 1e12).toFixed(1)}T`;
            else if (fAbs >= 1e9) fDisp = `${(fAbs / 1e9).toFixed(1)}B`;
            else if (fAbs >= 1e6) fDisp = `${(fAbs / 1e6).toFixed(0)}M`;
            else fDisp = `${(fAbs / 1e3).toFixed(0)}K`;

            foreignToken = ` • 🌐 ${fSign}${fDisp}`;
            foreignTitle = ` | Asing: ${fSign}${fDisp} (${(foreign.today_net_lots || 0).toLocaleString('id-ID')} Lot)`;
        }

        this.dom.bandarBadge.className = `bandar-badge ${isAccum ? 'accum' : 'distrib'}`;
        // Tanpa icon 📊 agar tetap muat satu baris rapi di layar HP!
        this.dom.bandarBadge.innerHTML = `${statusIcon} ${sign}${flowMiliar}B${foreignToken} • HMB ${summary.latest_hmb.toLocaleString('id-ID')}`;
        this.dom.bandarBadge.title = `Order Flow ${summary.latest_date || ''}: Top 3 Net ${sign}${flowMiliar}B${foreignTitle} | HMB Rp ${summary.latest_hmb.toLocaleString('id-ID')} (Klik untuk detail Broksum & Intelligence)`;
    }

    setupBroksumFilterEvents() {
        if (this.dom.broksumPresetChips) {
            this.dom.broksumPresetChips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const preset = chip.dataset.preset;
                    this.applyBroksumPreset(preset);
                });
            });
        }

        const onDateChange = () => {
            const fromVal = this.dom.broksumDateFrom?.value;
            const toVal = this.dom.broksumDateTo?.value;
            if (fromVal && toVal) {
                // Matikan highlight preset chip karena menggunakan custom date
                if (this.dom.broksumPresetChips) {
                    this.dom.broksumPresetChips.forEach(c => c.classList.remove('active'));
                }
                this.fetchBroksumRange(this.currentSymbol, fromVal, toVal);
            }
        };

        if (this.dom.broksumDateFrom) {
            this.dom.broksumDateFrom.addEventListener('change', onDateChange);
        }
        if (this.dom.broksumDateTo) {
            this.dom.broksumDateTo.addEventListener('change', onDateChange);
        }
    }

    applyBroksumPreset(preset) {
        const dataList = this.bandarData?.data || [];
        if (dataList.length === 0) return;

        const dates = dataList.map(d => d.date);
        const toDate = dates[dates.length - 1];
        let fromDate = toDate;

        if (preset === '1d') {
            fromDate = toDate;
        } else if (preset === '1w') {
            const idx = Math.max(0, dates.length - 5);
            fromDate = dates[idx];
        } else if (preset === '2w') {
            const idx = Math.max(0, dates.length - 10);
            fromDate = dates[idx];
        } else if (preset === '1m') {
            const idx = Math.max(0, dates.length - 20);
            fromDate = dates[idx];
        } else if (preset === '3m') {
            const idx = Math.max(0, dates.length - 60);
            fromDate = dates[idx];
        } else if (preset === '6m') {
            fromDate = dates[0];
        }

        if (this.dom.broksumPresetChips) {
            this.dom.broksumPresetChips.forEach(c => {
                if (c.dataset.preset === preset) c.classList.add('active');
                else c.classList.remove('active');
            });
        }

        if (this.dom.broksumDateFrom) this.dom.broksumDateFrom.value = fromDate;
        if (this.dom.broksumDateTo) this.dom.broksumDateTo.value = toDate;

        this.fetchBroksumRange(this.currentSymbol, fromDate, toDate);
    }

    async fetchBroksumRange(symbol, fromDate, toDate) {
        if (!symbol || !fromDate || !toDate) return;
        
        // Visual feedback: redam opasitas tabel selagi data baru ditarik
        if (this.dom.broksumBuyersList) this.dom.broksumBuyersList.style.opacity = '0.5';
        if (this.dom.broksumSellersList) this.dom.broksumSellersList.style.opacity = '0.5';

        try {
            const symEnc = encodeURIComponent(symbol);
            const fromEnc = encodeURIComponent(fromDate);
            const toEnc = encodeURIComponent(toDate);
            const resp = await fetch(`/api/bandarmologi/broksum?symbol=${symEnc}&from_date=${fromEnc}&to_date=${toEnc}`);
            const json = await resp.json();

            if (resp.ok && json.success) {
                this.renderBroksumData(json);
            } else {
                this.showToast(json.detail || json.error || 'Gagal memuat rentang Broksum', 'warning');
            }
        } catch (err) {
            console.error('Fetch broksum range error:', err);
            this.showToast(`Gagal menarik data: ${err.message}`, 'error');
        } finally {
            if (this.dom.broksumBuyersList) this.dom.broksumBuyersList.style.opacity = '1';
            if (this.dom.broksumSellersList) this.dom.broksumSellersList.style.opacity = '1';
        }
    }

    renderBroksumData(payload) {
        const summary = payload.summary;
        if (!summary) return;

        const isAccum = summary.latest_status === 'ACCUM';
        const flowMiliar = (summary.latest_net_flow / 1e9).toFixed(1);
        const sign = summary.latest_net_flow > 0 ? '+' : '';

        if (this.dom.broksumTitle) {
            this.dom.broksumTitle.textContent = `Broker Summary ${payload.symbol || this.currentSymbol}`;
        }
        if (this.dom.broksumNotasiPill) {
            const notasi = summary.notasi_khusus || summary.market_intelligence?.emiten_info?.notasi_khusus || '';
            if (notasi) {
                this.dom.broksumNotasiPill.textContent = `[${notasi}]`;
                this.dom.broksumNotasiPill.title = `Notasi Khusus BEI: ${notasi}`;
                this.dom.broksumNotasiPill.classList.remove('hidden');
            } else {
                this.dom.broksumNotasiPill.classList.add('hidden');
            }
        }
        if (this.dom.broksumSubtitle) {
            const fromStr = payload.from_date || summary.latest_date;
            const toStr = payload.to_date || summary.latest_date;
            const days = payload.trading_days ? ` • ${payload.trading_days} Hari Bursa` : '';
            if (fromStr === toStr) {
                this.dom.broksumSubtitle.textContent = `Tanggal: ${toStr} • End of Day (EOD)`;
            } else {
                this.dom.broksumSubtitle.textContent = `Periode: ${fromStr} s/d ${toStr}${days}`;
            }
        }
        if (this.dom.broksumStatusPill) {
            this.dom.broksumStatusPill.className = `bandar-badge ${isAccum ? 'accum' : 'distrib'}`;
            this.dom.broksumStatusPill.textContent = isAccum ? '🟢 Akumulasi' : '🔴 Distribusi';
        }
        if (this.dom.broksumNetflow) {
            this.dom.broksumNetflow.textContent = `${sign}Rp ${Math.abs(flowMiliar)} B`;
            this.dom.broksumNetflow.style.color = isAccum ? '#34d399' : '#f87171';
        }
        if (this.dom.broksumHmb) {
            this.dom.broksumHmb.textContent = `Rp ${Number(summary.latest_hmb || 0).toLocaleString('id-ID')}`;
        }

        // Ratio Calculation
        const buyVal = Number(summary.total_buy_val) || 1;
        const sellVal = Number(summary.total_sell_val) || 1;
        const totalVal = buyVal + sellVal;
        const buyPct = Math.round((buyVal / totalVal) * 100);
        const sellPct = 100 - buyPct;

        if (this.dom.broksumRatio) {
            this.dom.broksumRatio.textContent = `${buyPct}% / ${sellPct}%`;
        }
        if (this.dom.broksumRatioBuy) {
            this.dom.broksumRatioBuy.style.width = `${buyPct}%`;
        }
        if (this.dom.broksumRatioSell) {
            this.dom.broksumRatioSell.style.width = `${sellPct}%`;
        }
        if (this.dom.broksumTotalBuy) {
            this.dom.broksumTotalBuy.textContent = `Total: Rp ${(buyVal / 1e9).toFixed(1)} B`;
        }
        if (this.dom.broksumTotalSell) {
            this.dom.broksumTotalSell.textContent = `Total: Rp ${(sellVal / 1e9).toFixed(1)} B`;
        }

        const fmtLot = (vol) => {
            const v = Math.abs(vol);
            if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
            if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K';
            return v.toLocaleString('id-ID');
        };

        const fmtVal = (val) => {
            const absVal = Math.abs(val);
            if (absVal >= 1e9) return (absVal / 1e9).toFixed(1) + 'B';
            if (absVal >= 1e6) return (absVal / 1e6).toFixed(0) + 'M';
            return (absVal / 1e3).toFixed(0) + 'K';
        };

        // Populate Market Intelligence Cards (Foreign Flow, Whale Trade Size, Pasar Nego)
        const foreign = summary.foreign_flow || summary.market_intelligence?.foreign_flow || {};
        if (this.dom.intelForeign1d) {
            const isRange = foreign.range_net_val !== undefined;
            const netVal1d = isRange ? foreign.range_net_val : (foreign.today_net_val || 0);
            const netLots1d = isRange ? (foreign.range_net_lots || 0) : (foreign.today_net_lots || 0);
            const sign1d = netVal1d > 0 ? '+' : (netVal1d < 0 ? '-' : '');
            const lotSign1d = netLots1d > 0 ? '+' : '';
            const cls1d = netVal1d > 0 ? 'up' : (netVal1d < 0 ? 'down' : '');

            this.dom.intelForeign1d.textContent = `${sign1d}${fmtVal(netVal1d)}`;
            this.dom.intelForeign1d.className = `intel-val ${cls1d}`;
            this.dom.intelForeign1d.title = `${lotSign1d}${netLots1d.toLocaleString('id-ID')} Lot`;

            const netVal5d = foreign.flow_5d_val || 0;
            const sign5d = netVal5d > 0 ? '+' : (netVal5d < 0 ? '-' : '');
            const cls5d = netVal5d > 0 ? 'up' : (netVal5d < 0 ? 'down' : '');
            if (this.dom.intelForeign5d) {
                this.dom.intelForeign5d.textContent = `${sign5d}${fmtVal(netVal5d)}`;
                this.dom.intelForeign5d.className = `intel-val ${cls5d}`;
            }

            const netVal20d = foreign.flow_20d_val || 0;
            const sign20d = netVal20d > 0 ? '+' : (netVal20d < 0 ? '-' : '');
            const cls20d = netVal20d > 0 ? 'up' : (netVal20d < 0 ? 'down' : '');
            if (this.dom.intelForeign20d) {
                this.dom.intelForeign20d.textContent = `${sign20d}${fmtVal(netVal20d)}`;
                this.dom.intelForeign20d.className = `intel-val ${cls20d}`;
            }

            if (this.dom.intelForeignStatus) {
                const isNetBuy = netVal1d > 0;
                this.dom.intelForeignStatus.className = `intel-card-badge ${isNetBuy ? 'accum' : (netVal1d < 0 ? 'distrib' : '')}`;
                this.dom.intelForeignStatus.textContent = isNetBuy ? '🟢 Inflow' : (netVal1d < 0 ? '🔴 Outflow' : 'Netral');
            }

            if (this.dom.intelForeignSubtext) {
                const buyLot = isRange ? Math.round((foreign.range_buy_shares || 0) / 100) : (foreign.today_buy_lots || 0);
                const sellLot = isRange ? Math.round((foreign.range_sell_shares || 0) / 100) : (foreign.today_sell_lots || 0);
                this.dom.intelForeignSubtext.textContent = `B: ${fmtLot(buyLot)}L • S: ${fmtLot(sellLot)}L`;
            }
        }

        const tradeSize = summary.trade_size || summary.market_intelligence?.trade_size || {};
        const nego = summary.pasar_nego || summary.market_intelligence?.pasar_nego || {};

        if (this.dom.intelWhaleToday) {
            this.dom.intelWhaleToday.textContent = `${tradeSize.today_lot_per_trade || 0}`;
            if (this.dom.intelWhaleAvg) {
                this.dom.intelWhaleAvg.textContent = `${tradeSize.avg_lot_per_trade_20d || 0}`;
            }
            if (this.dom.intelWhaleStatus) {
                const ratio = tradeSize.whale_ratio || 1.0;
                if (ratio >= 1.5) {
                    this.dom.intelWhaleStatus.className = 'intel-card-badge whale';
                    this.dom.intelWhaleStatus.textContent = `🐳 Whale (${ratio.toFixed(1)}x)`;
                } else if (ratio <= 0.75) {
                    this.dom.intelWhaleStatus.className = 'intel-card-badge';
                    this.dom.intelWhaleStatus.textContent = `🦐 Ritel (${ratio.toFixed(1)}x)`;
                } else {
                    this.dom.intelWhaleStatus.className = 'intel-card-badge';
                    this.dom.intelWhaleStatus.textContent = `Normal (${ratio.toFixed(1)}x)`;
                }
            }
        }

        if (this.dom.intelNegoVal) {
            const nVal = nego.value || 0;
            this.dom.intelNegoVal.textContent = nVal > 0 ? fmtVal(nVal) : 'Rp 0';
            if (this.dom.intelNegoSubtext) {
                if (nego.has_crossing) {
                    this.dom.intelNegoSubtext.innerHTML = `⚠️ <strong style="color: #fbbf24;">Crossing:</strong> ${escapeHtml(nego.crossing_reason || 'Signifikan')}`;
                } else {
                    const nLot = nego.volume_lots || 0;
                    this.dom.intelNegoSubtext.textContent = nVal > 0 ? `Nego: ${fmtLot(nLot)} Lot` : 'Pasar Nego: Normal';
                }
            }
        }

        if (this.dom.broksumBuyersList) {
            const buyers = summary.top_buyers || [];
            if (buyers.length === 0) {
                this.dom.broksumBuyersList.innerHTML = '<div style="padding: 10px; text-align: center; color: var(--text-muted); font-size: 11px;">Tidak ada data pembeli</div>';
            } else {
                this.dom.broksumBuyersList.innerHTML = buyers.map(b => `
                    <div class="broksum-row">
                        <span class="broker-code-tag">${b.broker}</span>
                        <span class="cell-vol">${fmtLot(b.net_vol)}</span>
                        <span class="cell-val">${fmtVal(b.net_val)}</span>
                        <span class="cell-avg">${Number(b.avg_price || 0).toLocaleString('id-ID')}</span>
                    </div>
                `).join('');
            }
        }

        if (this.dom.broksumSellersList) {
            const sellers = summary.top_sellers || [];
            if (sellers.length === 0) {
                this.dom.broksumSellersList.innerHTML = '<div style="padding: 10px; text-align: center; color: var(--text-muted); font-size: 11px;">Tidak ada data penjual</div>';
            } else {
                this.dom.broksumSellersList.innerHTML = sellers.map(s => `
                    <div class="broksum-row">
                        <span class="broker-code-tag">${s.broker}</span>
                        <span class="cell-vol">${fmtLot(s.net_vol)}</span>
                        <span class="cell-val">${fmtVal(s.net_val)}</span>
                        <span class="cell-avg">${Number(s.avg_price || 0).toLocaleString('id-ID')}</span>
                    </div>
                `).join('');
            }
        }
    }

    openBroksumSheet() {
        const summary = this.bandarData?.summary;
        if (!summary || !summary.top_buyers) {
            this.showToast('Data Broker Summary belum tersedia untuk saham ini', 'warning');
            return;
        }

        // Inisialisasi batas min/max kalender & nilai default
        const dataList = this.bandarData?.data || [];
        if (dataList.length > 0) {
            const minDate = dataList[0].date;
            const maxDate = dataList[dataList.length - 1].date;
            if (this.dom.broksumDateFrom) {
                this.dom.broksumDateFrom.min = minDate;
                this.dom.broksumDateFrom.max = maxDate;
                this.dom.broksumDateFrom.value = maxDate;
            }
            if (this.dom.broksumDateTo) {
                this.dom.broksumDateTo.min = minDate;
                this.dom.broksumDateTo.max = maxDate;
                this.dom.broksumDateTo.value = maxDate;
            }
        }

        // Aktifkan chip 1D secara default
        if (this.dom.broksumPresetChips) {
            this.dom.broksumPresetChips.forEach(c => {
                if (c.dataset.preset === '1d') c.classList.add('active');
                else c.classList.remove('active');
            });
        }

        this.renderBroksumData({
            symbol: this.currentSymbol,
            from_date: summary.latest_date,
            to_date: summary.latest_date,
            trading_days: 1,
            summary: summary
        });

        // Sinkronisasi data ke sub-tab aktif
        if (this.activeBroksumTab === 'summary') {
            this.switchBroksumTab('summary');
        } else if (this.activeBroksumTab === 'history') {
            this.loadHistoryTable(this.currentSymbol, this.activeHistoryTf || 'daily');
        } else if (this.activeBroksumTab === 'flow') {
            this.loadBrokerFlow(this.currentSymbol, this.activeFlowDays || 30, this.activeFlowMetric || 'val');
        } else if (this.activeBroksumTab === 'activity') {
            this.loadBrokerActivity(this.currentSymbol, this.activeActivityBroker || 'XL', this.activeActivityMonth);
        }

        this.openSheet('broksum');
    }

    setupBroksumSubTabEvents() {
        if (this.dom.broksumTabBtns) {
            this.dom.broksumTabBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const tab = btn.dataset.tab;
                    this.switchBroksumTab(tab);
                });
            });
        }

        // Tab 2 History controls
        if (this.dom.historyTfPills) {
            this.dom.historyTfPills.forEach(pill => {
                pill.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const tf = pill.dataset.tf;
                    this.dom.historyTfPills.forEach(p => p.classList.toggle('active', p === pill));
                    this.activeHistoryTf = tf;
                    this.loadHistoryTable(this.currentSymbol, tf);
                });
            });
        }

        // Tab 3 Flow controls
        if (this.dom.flowMetricBtns) {
            this.dom.flowMetricBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const metric = btn.dataset.metric;
                    this.dom.flowMetricBtns.forEach(b => b.classList.toggle('active', b === btn));
                    this.activeFlowMetric = metric;
                    this.loadBrokerFlow(this.currentSymbol, this.activeFlowDays, metric);
                });
            });
        }

        if (this.dom.flowTfPills) {
            this.dom.flowTfPills.forEach(pill => {
                pill.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const days = parseInt(pill.dataset.days, 10);
                    this.dom.flowTfPills.forEach(p => p.classList.toggle('active', p === pill));
                    this.activeFlowDays = days;
                    this.loadBrokerFlow(this.currentSymbol, days, this.activeFlowMetric);
                });
            });
        }

        // Tab 3 Flow Canvas Hover / Crosshair Interactions
        if (this.dom.flowCanvas) {
            const handleFlowHover = (e) => {
                if (!this.currentFlowData || !this.currentFlowData.dates || this.currentFlowData.dates.length < 2) return;
                const rect = this.dom.flowCanvas.getBoundingClientRect();
                const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                const mouseX = clientX - rect.left;
                const mouseY = clientY - rect.top;

                const padLeft = 48;
                const padRight = 62;
                const chartW = rect.width - padLeft - padRight;
                if (chartW <= 0) return;

                const dates = this.currentFlowData.dates;
                const ratio = Math.max(0, Math.min(1, (mouseX - padLeft) / chartW));
                const dateIdx = Math.round(ratio * (dates.length - 1));

                this.hoverFlowDateIdx = dateIdx;
                this.renderBrokerFlowCanvas();

                // Update Tooltip
                if (this.dom.flowTooltip) {
                    const dateStr = dates[dateIdx];
                    const series = this.currentFlowData.series || {};
                    const colors = ['#34d399', '#60a5fa', '#f87171', '#fbbf24', '#a855f7', '#38bdf8', '#f472b6', '#fb923c', '#4ade80', '#e879f9'];
                    const topBrokers = this.currentFlowData.top_brokers || [];
                    const isVal = this.activeFlowMetric === 'val';
                    const unit = isVal ? 'B' : 'K';
                    const divisor = isVal ? 1e9 : 1000;

                    let rowsHtml = '';
                    topBrokers.forEach((brk, idx) => {
                        if (!this.activeFlowBrokers.has(brk)) return;
                        const pts = series[brk] || [];
                        const val = pts[dateIdx] !== undefined ? pts[dateIdx] : 0;
                        const color = colors[idx % colors.length];
                        const valFormatted = `${val >= 0 ? '+' : ''}${(val / divisor).toFixed(1)} ${unit}`;
                        const valColor = val >= 0 ? '#34d399' : '#f87171';
                        rowsHtml += `
                            <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; line-height:1.4;">
                                <span style="color:${color}; font-weight:700;">${brk}</span>
                                <span style="color:${valColor}; font-weight:600; font-family:var(--font-mono, monospace);">${valFormatted}</span>
                            </div>
                        `;
                    });

                    this.dom.flowTooltip.innerHTML = `
                        <div style="font-weight:700; color:#94a3b8; font-size:9.5px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:3px; margin-bottom:4px;">${dateStr}</div>
                        ${rowsHtml || '<div style="color:#64748b;">Tidak ada broker aktif</div>'}
                    `;
                    this.dom.flowTooltip.classList.remove('hidden');

                    const tooltipW = this.dom.flowTooltip.offsetWidth || 110;
                    let tipX = mouseX + 12;
                    if (tipX + tooltipW > rect.width) {
                        tipX = mouseX - tooltipW - 12;
                    }
                    let tipY = Math.max(8, Math.min(rect.height - 60, mouseY - 20));
                    this.dom.flowTooltip.style.left = `${tipX}px`;
                    this.dom.flowTooltip.style.top = `${tipY}px`;
                }
            };

            const clearFlowHover = () => {
                this.hoverFlowDateIdx = null;
                if (this.dom.flowTooltip) {
                    this.dom.flowTooltip.classList.add('hidden');
                }
                this.renderBrokerFlowCanvas();
            };

            this.dom.flowCanvas.addEventListener('mousemove', handleFlowHover);
            this.dom.flowCanvas.addEventListener('mouseleave', clearFlowHover);
            this.dom.flowCanvas.addEventListener('touchmove', handleFlowHover, { passive: true });
            this.dom.flowCanvas.addEventListener('touchend', clearFlowHover);
        }

        // Tab 4 Activity controls
        if (this.dom.activityBrokerSelect) {
            this.dom.activityBrokerSelect.addEventListener('change', () => {
                const broker = this.dom.activityBrokerSelect.value;
                this.activeActivityBroker = broker;
                this.loadBrokerActivity(this.currentSymbol, broker, this.activeActivityMonth);
            });
        }

        if (this.dom.activityPrevMonthBtn) {
            this.dom.activityPrevMonthBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.navigateActivityMonth(-1);
            });
        }

        if (this.dom.activityNextMonthBtn) {
            this.dom.activityNextMonthBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.navigateActivityMonth(1);
            });
        }

        // Tab 4 Activity Chips mousewheel horizontal scroll
        if (this.dom.activityBrokerChips) {
            this.dom.activityBrokerChips.addEventListener('wheel', (e) => {
                if (e.deltaY !== 0) {
                    e.preventDefault();
                    this.dom.activityBrokerChips.scrollLeft += e.deltaY;
                }
            }, { passive: false });
        }
    }

    switchBroksumTab(tabId) {
        this.activeBroksumTab = tabId;
        if (this.dom.broksumTabBtns) {
            this.dom.broksumTabBtns.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === tabId);
            });
        }

        if (this.dom.tabPaneSummary) this.dom.tabPaneSummary.classList.toggle('hidden', tabId !== 'summary');
        if (this.dom.tabPaneHistory) this.dom.tabPaneHistory.classList.toggle('hidden', tabId !== 'history');
        if (this.dom.tabPaneFlow) this.dom.tabPaneFlow.classList.toggle('hidden', tabId !== 'flow');
        if (this.dom.tabPaneActivity) this.dom.tabPaneActivity.classList.toggle('hidden', tabId !== 'activity');

        if (tabId === 'history') {
            this.loadHistoryTable(this.currentSymbol, this.activeHistoryTf || 'daily');
        } else if (tabId === 'flow') {
            this.loadBrokerFlow(this.currentSymbol, this.activeFlowDays || 30, this.activeFlowMetric || 'val');
        } else if (tabId === 'activity') {
            this.loadBrokerActivity(this.currentSymbol, this.activeActivityBroker || 'XL', this.activeActivityMonth);
        }
    }

    async loadHistoryTable(symbol, timeframe = 'daily') {
        if (!symbol || !this.dom.historyTableBody) return;
        if (this.dom.historyRowCount) {
            this.dom.historyRowCount.textContent = 'Memuat riwayat harga...';
        }

        try {
            const symEnc = encodeURIComponent(symbol);
            const tfEnc = encodeURIComponent(timeframe);
            const resp = await fetch(`/api/stock/historical-data?symbol=${symEnc}&timeframe=${tfEnc}&limit=60`);
            const json = await resp.json();

            if (resp.ok && json.success) {
                const rows = json.data || [];
                if (rows.length === 0) {
                    this.dom.historyTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: var(--text-muted);">Tidak ada riwayat harga</td></tr>';
                    if (this.dom.historyRowCount) this.dom.historyRowCount.textContent = '0 baris data';
                    return;
                }

                if (this.dom.historyRowCount) {
                    this.dom.historyRowCount.textContent = `${rows.length} baris data • ${timeframe.toUpperCase()}`;
                }

                this.dom.historyTableBody.innerHTML = rows.map(r => {
                    const isUp = r.change_pct > 0;
                    const isDown = r.change_pct < 0;
                    const sign = isUp ? '+' : '';
                    const cls = isUp ? 'val-up' : (isDown ? 'val-down' : 'val-neutral');
                    const chgText = (r.change_pct !== null && !isNaN(r.change_pct)) ? `${sign}${r.change_pct.toFixed(2)}%` : '-';
                    let valText = '-';
                    if (r.value) {
                        const valNum = Number(r.value);
                        if (valNum >= 1e9) valText = `${(valNum / 1e9).toFixed(1)} B`;
                        else if (valNum >= 1e6) valText = `${(valNum / 1e6).toFixed(0)} M`;
                        else valText = `${(valNum / 1e3).toFixed(0)} K`;
                    }
                    return `
                        <tr>
                            <td>${r.date}</td>
                            <td style="font-weight: 700;">${Number(r.close).toLocaleString('id-ID')}</td>
                            <td class="${cls}">${chgText}</td>
                            <td style="color: #cbd5e1;">${valText}</td>
                        </tr>
                    `;
                }).join('');
            } else {
                if (this.dom.historyTableBody) {
                    this.dom.historyTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 20px; color: #f87171;">${json.detail || 'Gagal memuat data'}</td></tr>`;
                }
            }
        } catch (err) {
            console.error('loadHistoryTable error:', err);
            if (this.dom.historyTableBody) {
                this.dom.historyTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 20px; color: #f87171;">Error: ${err.message}</td></tr>`;
            }
        }
    }

    async loadBrokerFlow(symbol, days = 30, metric = 'val') {
        if (!symbol || !this.dom.flowCanvas) return;
        try {
            const symEnc = encodeURIComponent(symbol);
            const resp = await fetch(`/api/bandarmologi/broker-flow?symbol=${symEnc}&days=${days}&metric=${metric}`);
            const json = await resp.json();

            if (resp.ok && json.success) {
                this.currentFlowData = json;
                const flowSummary = json.summary || {};
                const topBrokers = json.top_brokers || [];
                const topBuyers = json.top_buyers || [];
                const topSellers = json.top_sellers || [];
                
                // Initialize default selected brokers: Top 3 Buyers + Top 2 Sellers
                if (!this.activeFlowBrokers || this.activeFlowBrokers.size === 0) {
                    const defaultSelection = [...topBuyers.slice(0, 3), ...topSellers.slice(0, 2)];
                    this.activeFlowBrokers = new Set(defaultSelection.length > 0 ? defaultSelection : topBrokers.slice(0, 5));
                }

                // Update Gauge Meter
                const netFlow = flowSummary.net_flow || 0;
                const totalBuy = flowSummary.total_buy || 1;
                const totalSell = flowSummary.total_sell || 1;
                const isAcc = netFlow >= 0;
                const isVal = metric === 'val';
                const unit = isVal ? 'B' : 'K Lot';
                const divisor = isVal ? 1e9 : 1000;
                const netFlowFormatted = `${isAcc ? '+' : ''}${(netFlow / divisor).toFixed(1)} ${unit}`;

                if (this.dom.flowMeterStatus) {
                    this.dom.flowMeterStatus.innerHTML = `Net ${isAcc ? 'Acc' : 'Dist'}: <strong style="color: ${isAcc ? '#34d399' : '#f87171'}">${netFlowFormatted}</strong>`;
                }

                if (this.dom.flowMeterFill) {
                    const ratio = totalBuy / (totalBuy + totalSell); // 0.0 to 1.0
                    const leftPct = Math.max(5, Math.min(95, ratio * 100));
                    this.dom.flowMeterFill.style.left = `${leftPct}%`;
                    this.dom.flowMeterFill.style.background = isAcc ? '#34d399' : '#f87171';
                    this.dom.flowMeterFill.style.boxShadow = isAcc ? '0 0 10px rgba(52, 211, 153, 0.8)' : '0 0 10px rgba(248, 113, 113, 0.8)';
                }

                // Render broker toggle chips
                this.renderFlowBrokerChips(topBrokers);

                // Render canvas chart
                this.renderBrokerFlowCanvas();
            }
        } catch (err) {
            console.error('loadBrokerFlow error:', err);
        }
    }

    renderFlowBrokerChips(topBrokers) {
        if (!this.dom.flowBrokerChips) return;
        const colors = ['#34d399', '#60a5fa', '#f87171', '#fbbf24', '#a855f7', '#38bdf8', '#f472b6', '#fb923c', '#4ade80', '#e879f9'];

        this.dom.flowBrokerChips.innerHTML = topBrokers.map((brk, idx) => {
            const color = colors[idx % colors.length];
            const isActive = this.activeFlowBrokers.has(brk);
            return `
                <div class="flow-chip ${isActive ? 'active' : ''}" data-broker="${brk}" style="${isActive ? `border-color: ${color}; background: ${color}22; color: #fff;` : ''}">
                    <span class="flow-chip-dot" style="background: ${color};"></span>
                    <span>${brk}</span>
                </div>
            `;
        }).join('');

        // Attach click handlers to chips
        this.dom.flowBrokerChips.querySelectorAll('.flow-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                e.stopPropagation();
                const brk = chip.dataset.broker;
                if (this.activeFlowBrokers.has(brk)) {
                    if (this.activeFlowBrokers.size > 1) {
                        this.activeFlowBrokers.delete(brk);
                    }
                } else {
                    this.activeFlowBrokers.add(brk);
                }
                this.renderFlowBrokerChips(this.currentFlowData?.top_brokers || []);
                this.renderBrokerFlowCanvas();
            });
        });
    }

    renderBrokerFlowCanvas() {
        const canvas = this.dom.flowCanvas;
        if (!canvas || !this.currentFlowData) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = (rect.width || 360) * dpr;
        canvas.height = (rect.height || 200) * dpr;
        ctx.resetTransform();
        ctx.scale(dpr, dpr);

        const width = rect.width || 360;
        const height = rect.height || 200;
        ctx.clearRect(0, 0, width, height);

        const dates = this.currentFlowData.dates || [];
        const series = this.currentFlowData.series || {};
        const colors = ['#34d399', '#60a5fa', '#f87171', '#fbbf24', '#a855f7', '#38bdf8', '#f472b6', '#fb923c', '#4ade80', '#e879f9'];
        const topBrokers = this.currentFlowData.top_brokers || [];
        const isVal = this.activeFlowMetric === 'val';
        const unit = isVal ? 'B' : 'K';
        const divisor = isVal ? 1e9 : 1000;

        const formatFlowVal = (v) => {
            if (Math.abs(v) < 1) return '0';
            const num = v / divisor;
            return `${num >= 0 ? '+' : ''}${num.toFixed(1)}${unit}`;
        };

        if (dates.length < 2) {
            ctx.fillStyle = '#64748b';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Data flow belum mencukupi', width / 2, height / 2);
            return;
        }

        // Find min and max across selected series
        let minVal = 0;
        let maxVal = 0;
        let hasData = false;

        topBrokers.forEach(brk => {
            if (!this.activeFlowBrokers.has(brk)) return;
            const points = series[brk] || [];
            points.forEach(v => {
                hasData = true;
                if (v < minVal) minVal = v;
                if (v > maxVal) maxVal = v;
            });
        });

        if (!hasData) {
            minVal = -100;
            maxVal = 100;
        }

        // Add 14% padding
        const range = Math.max(1, maxVal - minVal);
        const pad = range * 0.14;
        const yMin = minVal - pad;
        const yMax = maxVal + pad;
        const yRange = yMax - yMin;

        const padLeft = 48;
        const padRight = 64;
        const padTop = 15;
        const padBottom = 22;
        const chartW = width - padLeft - padRight;
        const chartH = height - padTop - padBottom;

        const getY = (val) => padTop + chartH - ((val - yMin) / yRange) * chartH;
        const getX = (idx) => padLeft + (idx / (dates.length - 1)) * chartW;

        // Draw Zero Baseline
        const zeroY = getY(0);
        ctx.save();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padLeft, zeroY);
        ctx.lineTo(width - padRight, zeroY);
        ctx.stroke();
        ctx.restore();

        // Label 0
        ctx.fillStyle = '#94a3b8';
        ctx.font = '9px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('0', padLeft - 6, zeroY + 3);

        // Max Positive Guideline & Label
        if (maxVal > 0) {
            const topY = getY(maxVal);
            if (Math.abs(topY - zeroY) > 20) {
                ctx.save();
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, topY);
                ctx.lineTo(width - padRight, topY);
                ctx.stroke();
                ctx.restore();

                ctx.fillStyle = '#34d399';
                ctx.font = '9px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(formatFlowVal(maxVal), padLeft - 6, topY + 3);
            }
        }

        // Min Negative Guideline & Label
        if (minVal < 0) {
            const botY = getY(minVal);
            if (Math.abs(botY - zeroY) > 20) {
                ctx.save();
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padLeft, botY);
                ctx.lineTo(width - padRight, botY);
                ctx.stroke();
                ctx.restore();

                ctx.fillStyle = '#f87171';
                ctx.font = '9px monospace';
                ctx.textAlign = 'right';
                ctx.fillText(formatFlowVal(minVal), padLeft - 6, botY + 3);
            }
        }

        // Draw curves for each active broker
        topBrokers.forEach((brk, idx) => {
            if (!this.activeFlowBrokers.has(brk)) return;
            const points = series[brk] || [];
            if (points.length < 2) return;

            const color = colors[idx % colors.length];
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.beginPath();

            for (let i = 0; i < points.length; i++) {
                const x = getX(i);
                const y = getY(points[i]);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Draw endpoint marker with broker tag & final value
            const lastX = getX(points.length - 1);
            const lastY = getY(points[points.length - 1]);
            const finalVal = points[points.length - 1];
            const finalStr = formatFlowVal(finalVal);

            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(lastX, lastY, 3.5, 0, Math.PI * 2);
            ctx.fill();

            ctx.font = 'bold 9px sans-serif';
            ctx.textAlign = 'left';
            ctx.fillText(`${brk} ${finalStr}`, lastX + 6, lastY + 3);
        });

        // Draw Interactive Crosshair & Highlight Dots if Hovered
        if (this.hoverFlowDateIdx !== null && this.hoverFlowDateIdx !== undefined && this.hoverFlowDateIdx >= 0 && this.hoverFlowDateIdx < dates.length) {
            const hX = getX(this.hoverFlowDateIdx);
            ctx.save();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(hX, padTop);
            ctx.lineTo(hX, height - padBottom);
            ctx.stroke();
            ctx.restore();

            // Highlight dots on each active line
            topBrokers.forEach((brk, idx) => {
                if (!this.activeFlowBrokers.has(brk)) return;
                const pts = series[brk] || [];
                const val = pts[this.hoverFlowDateIdx];
                if (val === undefined) return;
                const color = colors[idx % colors.length];
                const ptY = getY(val);
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(hX, ptY, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 1.5;
                ctx.stroke();
            });
        }

        // Draw X-axis Dates (first, middle, last)
        ctx.fillStyle = '#64748b';
        ctx.font = '9px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(dates[0], padLeft, height - 6);
        ctx.textAlign = 'center';
        const midIdx = Math.floor(dates.length / 2);
        ctx.fillText(dates[midIdx], getX(midIdx), height - 6);
        ctx.textAlign = 'right';
        ctx.fillText(dates[dates.length - 1], width - padRight, height - 6);
    }

    async loadBrokerActivity(symbol, brokerCode = 'XL', monthStr = null) {
        if (!symbol) return;
        const brk = brokerCode.toUpperCase();
        this.activeActivityBroker = brk;

        try {
            const symEnc = encodeURIComponent(symbol);
            const brkEnc = encodeURIComponent(brk);
            const monthParam = monthStr ? `&month=${encodeURIComponent(monthStr)}` : '';
            const resp = await fetch(`/api/bandarmologi/broker-activity?symbol=${symEnc}&broker=${brkEnc}&broker_code=${brkEnc}${monthParam}`);
            const json = await resp.json();

            if (resp.ok && json.success) {
                this.activeActivityMonth = json.month;
                const currentSelected = json.broker || brk;
                this.activeActivityBroker = currentSelected;

                // Update Active Broker Badge
                if (this.dom.activityActiveBrokerBadge) {
                    const stats = (json.broker_stats && json.broker_stats[currentSelected]) || {};
                    const daysText = stats.accum_days ? ` • ${stats.accum_days} hari akum` : '';
                    this.dom.activityActiveBrokerBadge.innerHTML = `Broker: <strong>${currentSelected}</strong>${daysText}`;
                }

                // Render broker chips (hanya broker dengan transaksi nyata, urut akumulasi)
                this.renderActivityBrokerChips(json.available_brokers || [], currentSelected, json.broker_stats || {});
                
                // Populate/Update hidden broker selector for compatibility
                if (this.dom.activityBrokerSelect && Array.isArray(json.available_brokers) && json.available_brokers.length > 0) {
                    this.dom.activityBrokerSelect.innerHTML = json.available_brokers.map(b => `
                        <option value="${b}" ${b === currentSelected ? 'selected' : ''}>${b}</option>
                    `).join('');
                    this.dom.activityBrokerSelect.value = currentSelected;
                }

                // Format Month Title: "2026-10" -> "Oktober 2026"
                if (this.dom.activityMonthLabel) {
                    const [y, m] = json.month.split('-');
                    const dateObj = new Date(parseInt(y, 10), parseInt(m, 10) - 1, 1);
                    this.dom.activityMonthLabel.textContent = dateObj.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' });
                }

                // Summary Card
                const netVal = json.monthly_net_val || 0;
                const netVol = json.monthly_net_vol || 0;
                const isAcc = netVal >= 0;
                const sign = isAcc ? '+' : '';
                const valText = `${sign}Rp ${(Math.abs(netVal) / 1e9).toFixed(2)} B`;
                
                const absNetVol = Math.abs(netVol);
                const volSign = netVol > 0 ? '+' : (netVol < 0 ? '-' : '');
                const volText = absNetVol >= 1000 ? `${volSign}${(absNetVol / 1000).toFixed(1)}K Lot` : `${volSign}${absNetVol.toLocaleString('id-ID')} Lot`;

                if (this.dom.actSumVal) {
                    this.dom.actSumVal.textContent = valText;
                    this.dom.actSumVal.style.color = isAcc ? '#34d399' : '#f87171';
                }
                if (this.dom.actSumVol) {
                    this.dom.actSumVol.textContent = volText;
                    this.dom.actSumVol.style.color = isAcc ? '#34d399' : '#f87171';
                }
                if (this.dom.actSumDays) {
                    this.dom.actSumDays.textContent = `${json.accum_days || 0} / ${json.trading_days || 0} Hari`;
                }

                // Render Calendar
                this.renderActivityCalendar(json);
            }
        } catch (err) {
            console.error('loadBrokerActivity error:', err);
        }
    }

    renderActivityBrokerChips(availableBrokers, activeBroker, brokerStats = {}) {
        if (!this.dom.activityBrokerChips) return;
        const colors = ['#34d399', '#60a5fa', '#f87171', '#fbbf24', '#a855f7', '#38bdf8', '#f472b6', '#fb923c', '#4ade80', '#e879f9'];

        if (!availableBrokers || availableBrokers.length === 0) {
            this.dom.activityBrokerChips.innerHTML = `<span style="font-size: 10px; color: var(--text-muted); padding: 4px;">Tidak ada transaksi broker di bulan ini</span>`;
            return;
        }

        this.dom.activityBrokerChips.innerHTML = availableBrokers.map((brk, idx) => {
            const stats = brokerStats[brk] || {};
            const isBuyer = stats.is_buyer !== false;
            const accumDays = stats.accum_days || 0;
            const dotColor = isBuyer ? '#34d399' : '#f87171';
            const isActive = brk === activeBroker;
            return `
                <div class="flow-chip ${isActive ? 'active' : ''}" data-broker="${brk}" title="${brk} • ${accumDays} hari akumulasi">
                    <span class="flow-chip-dot" style="background: ${dotColor};"></span>
                    <span>${brk}</span>
                    ${accumDays > 0 ? `<span class="activity-chip-days">${accumDays}d</span>` : ''}
                </div>
            `;
        }).join('');

        // Attach click handlers to activity chips
        this.dom.activityBrokerChips.querySelectorAll('.flow-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                e.stopPropagation();
                const brk = chip.dataset.broker;
                if (brk && brk !== this.activeActivityBroker) {
                    this.activeActivityBroker = brk;
                    this.loadBrokerActivity(this.currentSymbol, brk, this.activeActivityMonth);
                }
            });
        });

        // Auto-scroll active chip into view (smooth centering)
        const activeChip = this.dom.activityBrokerChips.querySelector('.flow-chip.active');
        if (activeChip && typeof activeChip.scrollIntoView === 'function') {
            activeChip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    }

    navigateActivityMonth(delta) {
        if (!this.activeActivityMonth) return;
        const [yStr, mStr] = this.activeActivityMonth.split('-');
        let year = parseInt(yStr, 10);
        let month = parseInt(mStr, 10) + delta;
        if (month > 12) {
            year += 1;
            month = 1;
        } else if (month < 1) {
            year -= 1;
            month = 12;
        }
        const newMonthStr = `${year}-${String(month).padStart(2, '0')}`;
        this.loadBrokerActivity(this.currentSymbol, this.activeActivityBroker || 'XL', newMonthStr);
    }

    renderActivityCalendar(data) {
        if (!this.dom.activityCalendarGrid) return;
        const monthStr = data.month;
        const [yStr, mStr] = monthStr.split('-');
        const year = parseInt(yStr, 10);
        const month = parseInt(mStr, 10);

        const daysInMonth = new Date(year, month, 0).getDate();
        const activityMap = new Map();
        (data.daily_activity || []).forEach(act => {
            activityMap.set(act.date, act);
        });

        // 5-Column Grid (MON, TUE, WED, THU, FRI)
        const cells = [];

        // Hitung sel kosong untuk hari sebelum tanggal 1
        const firstDayDate = new Date(year, month - 1, 1);
        const firstDayOfWeek = firstDayDate.getDay(); // 0 = Sun, 1 = Mon, ..., 6 = Sat
        let emptyPaddingCount = 0;
        if (firstDayOfWeek >= 1 && firstDayOfWeek <= 5) {
            emptyPaddingCount = firstDayOfWeek - 1;
        }

        for (let i = 0; i < emptyPaddingCount; i++) {
            cells.push('<div class="activity-day-cell empty"></div>');
        }

        // Loop hari kerja dalam sebulan
        for (let d = 1; d <= daysInMonth; d++) {
            const dateObj = new Date(year, month - 1, d);
            const dow = dateObj.getDay();
            if (dow === 0 || dow === 6) continue; // Skip hari libur Sabtu & Minggu

            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            const act = activityMap.get(dateStr);

            if (act) {
                const isBuy = act.net_vol > 0;
                const isSell = act.net_vol < 0;
                const badgeClass = isBuy ? 'buy' : (isSell ? 'sell' : 'neutral');
                const badgeText = isBuy ? 'BUY' : (isSell ? 'SELL' : 'NET');
                const lotClass = isBuy ? 'buy' : (isSell ? 'sell' : '');
                
                const absLot = Math.abs(act.net_vol);
                const sign = act.net_vol > 0 ? '+' : (act.net_vol < 0 ? '-' : '');
                const lotFormatted = absLot >= 1000 ? `${sign}${(absLot / 1000).toFixed(1)}K` : `${sign}${absLot.toLocaleString('id-ID')}`;
                const avgPrice = act.avg_price ? `Rp ${Math.round(act.avg_price).toLocaleString('id-ID')}` : '-';

                cells.push(`
                    <div class="activity-day-cell ${isBuy ? 'buy-day' : (isSell ? 'sell-day' : '')}" title="${dateStr}: Net ${act.net_vol.toLocaleString('id-ID')} lot @ ${avgPrice}">
                        <div class="act-day-hdr">
                            <span class="act-day-num">${d}</span>
                            <span class="act-day-badge ${badgeClass}">${badgeText}</span>
                        </div>
                        <div class="act-day-body">
                            <span class="act-day-lot ${lotClass}">${lotFormatted}</span>
                            <span class="act-day-avg">${avgPrice}</span>
                        </div>
                    </div>
                `);
            } else {
                cells.push(`
                    <div class="activity-day-cell inactive-day" title="${dateStr}: Tidak ada transaksi broker ${data.broker || ''}">
                        <div class="act-day-hdr">
                            <span class="act-day-num">${d}</span>
                        </div>
                        <div class="act-day-body">
                            <span class="act-day-avg">-</span>
                        </div>
                    </div>
                `);
            }
        }

        // Lengkapi sel sisa di baris terakhir agar genap 5 kolom
        const remainder = cells.length % 5;
        if (remainder !== 0) {
            const trailingCount = 5 - remainder;
            for (let i = 0; i < trailingCount; i++) {
                cells.push('<div class="activity-day-cell empty"></div>');
            }
        }

        this.dom.activityCalendarGrid.innerHTML = cells.join('');
    }

    syncBandarDataToCandles(candles) {
        if (!candles || candles.length === 0) return;
        if (!this.bandarData || !Array.isArray(this.bandarData.data) || this.bandarData.data.length === 0) {
            candles.forEach(c => {
                c.net_flow = 0;
                c.hmb = 0;
            });
            return;
        }

        const bandarMap = new Map();
        this.bandarData.data.forEach(item => {
            bandarMap.set(item.date, item);
        });

        candles.forEach(c => {
            const dStr = new Date(c.timestamp + 7 * 3600000).toISOString().split('T')[0];
            const b = bandarMap.get(dStr);
            if (b) {
                c.net_flow = b.net_flow / 1e9;
                c.hmb = b.hmb;
            } else {
                c.net_flow = 0;
                c.hmb = 0;
            }
        });
    }

    toggleIndicator(name, paneId, buttonEl, paneOptions = {}) {
        if (!this.chart) return;
        const currentActive = this.indicatorState[name] || false;
        
        if (currentActive) {
            if (paneId === 'candle_pane') {
                this.chart.removeIndicator(paneId, name);
            } else {
                this.chart.removeIndicator(paneId);
            }
            this.indicatorState[name] = false;
            buttonEl.textContent = 'OFF';
            buttonEl.classList.remove('active');
            this.showToast(`Indikator ${name} dinonaktifkan`, 'info');
        } else {
            const opt = { id: paneId, ...paneOptions };
            this.chart.createIndicator(name, false, opt);
            this.indicatorState[name] = true;
            buttonEl.textContent = 'AKTIF';
            buttonEl.classList.add('active');
            this.showToast(`Indikator ${name} diaktifkan`, 'info');
        }
    }
    
    // ========================================================================
    // SCREENER VIEW & DYNAMIC SCREENER-TO-NAV WORKFLOW
    // ========================================================================

    setupScreenerEvents() {
        // 1. Search Input Debounced
        if (this.dom.screenerSearchInput) {
            this.dom.screenerSearchInput.addEventListener('input', (e) => {
                const val = e.target.value;
                if (this.dom.screenerSearchClear) {
                    if (val) this.dom.screenerSearchClear.classList.remove('hidden');
                    else this.dom.screenerSearchClear.classList.add('hidden');
                }
                clearTimeout(this._searchDebounceTimer);
                this._searchDebounceTimer = setTimeout(() => {
                    this.searchQuery = val.trim();
                    this.currentPage = 1;
                    this.filterAndRenderScreener();
                }, 180);
            });
        }

        // 2. Clear Search Button
        if (this.dom.screenerSearchClear) {
            this.dom.screenerSearchClear.addEventListener('click', () => {
                if (this.dom.screenerSearchInput) {
                    this.dom.screenerSearchInput.value = '';
                    this.dom.screenerSearchInput.focus();
                }
                this.dom.screenerSearchClear.classList.add('hidden');
                this.searchQuery = '';
                this.currentPage = 1;
                this.filterAndRenderScreener();
            });
        }

        // 3. Filter Modal Open Button
        if (this.dom.btnToggleFilters) {
            this.dom.btnToggleFilters.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openFilterModal();
            });
        }

        // 3b. Filter Modal Close Buttons & Backdrop Click
        if (this.dom.closeFilterModal) {
            this.dom.closeFilterModal.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeFilterModal();
            });
        }
        if (this.dom.filterModalBackdrop) {
            this.dom.filterModalBackdrop.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeFilterModal();
            });
        }
        if (this.dom.btnApplyFilters) {
            this.dom.btnApplyFilters.addEventListener('click', (e) => {
                e.stopPropagation();
                this.closeFilterModal();
            });
        }
        if (this.dom.btnResetFilters) {
            this.dom.btnResetFilters.addEventListener('click', (e) => {
                e.stopPropagation();
                this.applyPresetFilter('all');
            });
        }

        // 3c. Clear Active Filter Badge in Brand Row
        if (this.dom.btnClearActivePreset) {
            this.dom.btnClearActivePreset.addEventListener('click', (e) => {
                e.stopPropagation();
                this.applyPresetFilter('all');
            });
        }
        if (this.dom.screenerActiveFilterBadge) {
            this.dom.screenerActiveFilterBadge.addEventListener('click', () => {
                this.openFilterModal();
            });
        }

        // 4. Preset Strategy Cards/Chips Selection
        if (this.dom.screenerPresetChips) {
            this.dom.screenerPresetChips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const preset = chip.dataset.preset;
                    this.applyPresetFilter(preset);
                });
            });
        }

        // 5. Sort Select
        if (this.dom.screenerSortSelect) {
            this.dom.screenerSortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.currentPage = 1;
                this.fetchScreenerData(this.currentPreset, this.currentSort);
            });
        }

        // 6. Screener List Click Delegation (Open Chart with Smooth Flow)
        if (this.dom.screenerList) {
            this.dom.screenerList.addEventListener('click', (e) => {
                const card = e.target.closest('.stock-card');
                if (card && card.dataset.symbol) {
                    this.openChartFromScreener(card.dataset.symbol);
                }
            });
        }

        // 7. Navigation Controls: Back to Previous View (Screener, Watchlist, Journal, etc.)
        if (this.dom.btnBackScreener) {
            this.dom.btnBackScreener.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this._navigatedToChartFromApp && window.history.length > 1) {
                    this._navigatedToChartFromApp = false;
                    window.history.back();
                } else {
                    const target = this.previousView || 'screener';
                    this.switchView(target, true);
                }
            });
        }

        // 8. Floating Glass Bottom Navigation (5 Tabs)
        if (this.dom.navBtns) {
            this.dom.navBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const view = btn.dataset.view;
                    if (view) {
                        this.switchView(view);
                    }
                });
            });
        }

        // 9. Keyboard Shortcuts (Arrow Keys & Brackets for Quick Stock Flipping)
        window.addEventListener('keydown', (e) => {
            if (document.activeElement && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA')) return;

            if (e.key === 'Escape') {
                if (this.dom.filterModal && !this.dom.filterModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeFilterModal();
                    return;
                }
                if (this.dom.watchlistModal && !this.dom.watchlistModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeWatchlistModal();
                    return;
                }
                if (this.dom.riskModal && !this.dom.riskModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeRiskModal();
                    return;
                }
                if (this.dom.planModal && !this.dom.planModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closePlanModal();
                    return;
                }
                if (this.dom.trailingModal && !this.dom.trailingModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeTrailingModal();
                    return;
                }
                if (this.dom.exitModal && !this.dom.exitModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeExitModal();
                    return;
                }
                if (this.dom.uploadModal && !this.dom.uploadModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeUploadModal();
                    return;
                }
                if (this.dom.suspendModal && !this.dom.suspendModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeSuspendModal();
                    return;
                }
                if (this.dom.logsModal && !this.dom.logsModal.classList.contains('hidden')) {
                    e.preventDefault();
                    this.closeLogsModal();
                    return;
                }
            }

            if (this.currentView === 'chart') {
                if (e.key === 'ArrowLeft' || e.key === '[') {
                    e.preventDefault();
                    this.navigateFilteredStock(-1);
                } else if (e.key === 'ArrowRight' || e.key === ']') {
                    e.preventDefault();
                    this.navigateFilteredStock(1);
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    this.switchView('screener');
                }
            } else if (this.currentView === 'watchlist' || this.currentView === 'journal') {
                if (e.key === 'Escape') {
                    e.preventDefault();
                    this.switchView('screener');
                }
            }
        });
    }

    setupWatchlistEvents() {
        // 1. Star Button in Chart View Header: Opens Watchlist Modal
        if (this.dom.btnStarWatchlist) {
            this.dom.btnStarWatchlist.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleStarWatchlist();
            });
        }

        // 2. Risk Settings Button in Watchlist View
        if (this.dom.btnRiskSettings) {
            this.dom.btnRiskSettings.addEventListener('click', () => {
                this.openRiskModal();
            });
        }

        // 3. Add Watchlist Trigger Buttons
        if (this.dom.btnOpenAddWatchlist) {
            this.dom.btnOpenAddWatchlist.addEventListener('click', () => {
                this.openWatchlistModal();
            });
        }
        if (this.dom.btnEmptyAddWatchlist) {
            this.dom.btnEmptyAddWatchlist.addEventListener('click', () => {
                this.openWatchlistModal();
            });
        }

        // 4. Watchlist Modal Dialog Controls (Hanya Batal & Simpan)
        if (this.dom.closeWlModal) {
            this.dom.closeWlModal.addEventListener('click', () => this.closeWatchlistModal());
        }
        if (this.dom.btnCancelWl) {
            this.dom.btnCancelWl.addEventListener('click', () => this.closeWatchlistModal());
        }
        if (this.dom.watchlistModalBackdrop) {
            this.dom.watchlistModalBackdrop.addEventListener('click', () => this.closeWatchlistModal());
        }
        if (this.dom.btnSubmitWl) {
            this.dom.btnSubmitWl.addEventListener('click', () => this.submitWatchlistForm());
        }
        if (this.dom.wlInputSymbol) {
            this.dom.wlInputSymbol.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase();
            });
        }

        // 4B. Watchlist Category Management Controls (CRUD)
        if (this.dom.btnManageCategories) {
            this.dom.btnManageCategories.addEventListener('click', () => {
                this.openCategoryMgmtModal();
            });
        }
        if (this.dom.closeCategoryMgmtModal) {
            this.dom.closeCategoryMgmtModal.addEventListener('click', () => this.closeCategoryMgmtModal());
        }
        if (this.dom.btnCloseCategoryMgmt) {
            this.dom.btnCloseCategoryMgmt.addEventListener('click', () => this.closeCategoryMgmtModal());
        }
        if (this.dom.categoryMgmtBackdrop) {
            this.dom.categoryMgmtBackdrop.addEventListener('click', () => this.closeCategoryMgmtModal());
        }
        if (this.dom.btnSubmitAddCat) {
            this.dom.btnSubmitAddCat.addEventListener('click', () => this.handleAddNewCategory());
        }
        if (this.dom.inputNewCategory) {
            this.dom.inputNewCategory.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.handleAddNewCategory();
                }
            });
        }

        // 5. Risk Settings Modal Dialog Controls
        if (this.dom.closeRiskModal) {
            this.dom.closeRiskModal.addEventListener('click', () => this.closeRiskModal());
        }
        if (this.dom.btnCancelRisk) {
            this.dom.btnCancelRisk.addEventListener('click', () => this.closeRiskModal());
        }
        if (this.dom.riskModalBackdrop) {
            this.dom.riskModalBackdrop.addEventListener('click', () => this.closeRiskModal());
        }
        if (this.dom.btnSubmitRisk) {
            this.dom.btnSubmitRisk.addEventListener('click', () => this.submitRiskSettings());
        }

        // Live calculation on Risk Input / Slider change
        if (this.dom.riskSliderPct) {
            this.dom.riskSliderPct.addEventListener('input', (e) => {
                if (this.dom.riskPctBadge) this.dom.riskPctBadge.textContent = `${parseFloat(e.target.value).toFixed(2)}%`;
                this.updateRiskCalculations();
            });
        }
        if (this.dom.riskInputCapital) {
            this.dom.riskInputCapital.addEventListener('input', () => {
                this.updateRiskCalculations();
            });
        }

        // 6. Watchlist Category Filter Chips
        if (this.dom.watchlistCategories) {
            this.dom.watchlistCategories.addEventListener('click', (e) => {
                const chip = e.target.closest('.watchlist-cat-chip');
                if (!chip) return;
                const cat = chip.dataset.category || 'all';
                this.activeWatchlistCategory = cat;
                
                const allChips = this.dom.watchlistCategories.querySelectorAll('.watchlist-cat-chip');
                allChips.forEach(c => c.classList.remove('active'));
                if (this.dom.btnWlCatAll) this.dom.btnWlCatAll.classList.remove('active');
                chip.classList.add('active');

                this.fetchWatchlist(cat);
            });
        }

        // 6b. Watchlist 'Semua' Pinned Button
        if (this.dom.btnWlCatAll) {
            this.dom.btnWlCatAll.addEventListener('click', () => {
                this.activeWatchlistCategory = 'all';
                if (this.dom.watchlistCategories) {
                    const allChips = this.dom.watchlistCategories.querySelectorAll('.watchlist-cat-chip');
                    allChips.forEach(c => c.classList.remove('active'));
                }
                this.dom.btnWlCatAll.classList.add('active');
                this.fetchWatchlist('all');
            });
        }

        // 7. Watchlist List Card Click Delegation
        if (this.dom.watchlistList) {
            this.dom.watchlistList.addEventListener('click', (e) => {
                // Plan Button: directly convert watchlist item to trading plan!
                const btnPlan = e.target.closest('.btn-wl-plan');
                if (btnPlan) {
                    e.stopPropagation();
                    const sym = btnPlan.dataset.symbol;
                    const cat = btnPlan.dataset.category;
                    const entry = btnPlan.dataset.entry;
                    const notes = btnPlan.dataset.notes;
                    this.openPlanModal({ symbol: sym, category: cat, entry_price: entry, notes: notes });
                    return;
                }

                // Delete Button
                const btnDel = e.target.closest('.btn-wl-delete');
                if (btnDel) {
                    e.stopPropagation();
                    const itemId = parseInt(btnDel.dataset.id, 10);
                    const sym = btnDel.dataset.symbol;
                    this.deleteWatchlistItem(itemId, sym);
                    return;
                }

                // Edit Button
                const btnEdit = e.target.closest('.btn-wl-edit');
                if (btnEdit) {
                    e.stopPropagation();
                    const itemId = parseInt(btnEdit.dataset.id, 10);
                    const item = this.watchlistItems.find(i => i.id === itemId);
                    if (item) {
                        this.openWatchlistModal(item);
                    }
                    return;
                }

                // Note Popover Trigger
                const btnNote = e.target.closest('.btn-wl-note');
                if (btnNote) {
                    e.stopPropagation();
                    const itemId = btnNote.dataset.id;
                    const popover = document.getElementById(`wl-popover-${itemId}`);
                    document.querySelectorAll('.wl-note-popover').forEach(p => {
                        if (p !== popover) p.classList.add('hidden');
                    });
                    if (popover) {
                        popover.classList.toggle('hidden');
                    }
                    return;
                }

                // Open Chart from card body
                const card = e.target.closest('.watchlist-card');
                if (card && card.dataset.symbol) {
                    this.openChartFromWatchlist(card.dataset.symbol);
                }
            });
        }

        // Dismiss open note popovers when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.wl-note-wrap')) {
                document.querySelectorAll('.wl-note-popover').forEach(p => p.classList.add('hidden'));
            }
        });
    }

    setupSettingsEvents() {
        // 1. Data Source Radio Selection
        const cardNeon = document.getElementById('source-card-neon');
        const cardYahoo = document.getElementById('source-card-yahoo');
        if (cardNeon && this.dom.radioSourceNeon) {
            cardNeon.addEventListener('click', () => {
                this.dom.radioSourceNeon.checked = true;
            });
        }
        if (cardYahoo && this.dom.radioSourceYahoo) {
            cardYahoo.addEventListener('click', () => {
                this.dom.radioSourceYahoo.checked = true;
            });
        }

        // 2. Risk slider and capital live calculations in Settings View
        if (this.dom.settingSliderPct) {
            this.dom.settingSliderPct.addEventListener('input', (e) => {
                if (this.dom.settingPctBadge) this.dom.settingPctBadge.textContent = `${parseFloat(e.target.value).toFixed(2)}%`;
                this.updateSettingsCalculations();
            });
        }
        if (this.dom.settingInputCapital) {
            this.dom.settingInputCapital.addEventListener('input', () => {
                this.updateSettingsCalculations();
            });
        }

        // 3. Save All Settings button
        if (this.dom.btnSaveAllSettings) {
            this.dom.btnSaveAllSettings.addEventListener('click', () => {
                this.saveAllSettings();
            });
        }

        // 4. Kitab Pre-Breakout & Dynamic Docs Markdown Reader Modal
        const btnCloseDoc = document.getElementById('btn-close-doc-modal');
        const docModal = document.getElementById('doc-reader-modal');
        const initialBtnOpenDoc = document.getElementById('btn-open-doc-modal');

        if (initialBtnOpenDoc) {
            initialBtnOpenDoc.addEventListener('click', (e) => {
                const slug = e.currentTarget.dataset.slug || '01_panduan_candlify_pwa';
                this.openDocModal(slug);
            });
        }

        if (btnCloseDoc && docModal) {
            btnCloseDoc.addEventListener('click', () => {
                docModal.classList.add('hidden');
            });
            docModal.addEventListener('click', (e) => {
                if (e.target === docModal) {
                    docModal.classList.add('hidden');
                }
            });
        }

        // Fetch dan render daftar panduan dinamis dari folder docs/
        this.fetchAndRenderSettingsDocs();

        // 5. Database Overview Navigation Links
        if (this.dom.btnDbGoScreener) {
            this.dom.btnDbGoScreener.addEventListener('click', () => this.switchView('screener'));
        }
        if (this.dom.btnDbGoWatchlist) {
            this.dom.btnDbGoWatchlist.addEventListener('click', () => this.switchView('watchlist'));
        }
        if (this.dom.btnDbGoSettingsRisk) {
            this.dom.btnDbGoSettingsRisk.addEventListener('click', () => this.switchView('settings'));
        }
        if (this.dom.btnDbGoSettingsFeed) {
            this.dom.btnDbGoSettingsFeed.addEventListener('click', () => this.switchView('settings'));
        }
    }

    setupDatabaseEvents() {
        // 1. Live Clock WIB
        setInterval(() => {
            const now = new Date();
            if (this.dom.liveClock) {
                this.dom.liveClock.innerText = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            }
        }, 1000);

        // 2. Open Modal Actions
        if (this.dom.btnActionUpload) {
            this.dom.btnActionUpload.addEventListener('click', () => this.openUploadModal());
        }
        if (this.dom.btnActionSuspend) {
            this.dom.btnActionSuspend.addEventListener('click', () => this.openSuspendModal());
        }
        if (this.dom.btnActionLogs) {
            this.dom.btnActionLogs.addEventListener('click', () => this.openLogsModal());
        }

        // 3. Close Modal Handlers (Buttons & Backdrop)
        if (this.dom.closeUploadModal) {
            this.dom.closeUploadModal.addEventListener('click', () => this.closeUploadModal());
        }
        if (this.dom.uploadModal) {
            this.dom.uploadModal.addEventListener('click', (e) => {
                if (e.target === this.dom.uploadModal) this.closeUploadModal();
            });
        }

        if (this.dom.closeSuspendModal) {
            this.dom.closeSuspendModal.addEventListener('click', () => this.closeSuspendModal());
        }
        if (this.dom.suspendModal) {
            this.dom.suspendModal.addEventListener('click', (e) => {
                if (e.target === this.dom.suspendModal) this.closeSuspendModal();
            });
        }

        if (this.dom.closeLogsModal) {
            this.dom.closeLogsModal.addEventListener('click', () => this.closeLogsModal());
        }
        if (this.dom.logsModal) {
            this.dom.logsModal.addEventListener('click', (e) => {
                if (e.target === this.dom.logsModal) this.closeLogsModal();
            });
        }

        // 4. Dropzone & File Input Logic
        if (this.dom.dbDropzone && this.dom.dbFileInput) {
            this.dom.dbDropzone.addEventListener('click', () => this.dom.dbFileInput.click());
            this.dom.dbDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.dom.dbDropzone.classList.add('dragover');
            });
            this.dom.dbDropzone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                this.dom.dbDropzone.classList.remove('dragover');
            });
            this.dom.dbDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                this.dom.dbDropzone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    this.dom.dbFileInput.files = e.dataTransfer.files;
                    if (this.dom.dbFileNameDisplay) {
                        this.dom.dbFileNameDisplay.innerText = e.dataTransfer.files[0].name;
                    }
                }
            });
            this.dom.dbFileInput.addEventListener('change', () => {
                if (this.dom.dbFileInput.files.length && this.dom.dbFileNameDisplay) {
                    this.dom.dbFileNameDisplay.innerText = this.dom.dbFileInput.files[0].name;
                }
            });
        }

        // 5. Upload Master Form Submission
        if (this.dom.uploadForm) {
            this.dom.uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!this.dom.dbFileInput || !this.dom.dbFileInput.files.length) {
                    this.showToast('Silakan pilih file .xlsx terlebih dahulu', 'warning');
                    return;
                }

                const btnUpload = this.dom.btnDbUploadSubmit;
                const statusEl = this.dom.dbUploadStatus;

                if (btnUpload) {
                    btnUpload.disabled = true;
                    btnUpload.innerHTML = 'Mengunggah &amp; Memproses...';
                }
                if (statusEl) statusEl.innerHTML = '<span style="color: var(--accent-cyan);">Memproses data emiten ke database Neon...</span>';

                const formData = new FormData();
                formData.append('file', this.dom.dbFileInput.files[0]);

                try {
                    const res = await fetch('/api/database/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await res.json();
                    if (res.ok && result.status === 'success') {
                        if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-emerald);">✅ ${result.message}</span>`;
                        this.showToast(`✅ ${result.message}`, 'success');
                        this.updateDatabaseOverview();
                        setTimeout(() => {
                            this.closeUploadModal();
                            if (statusEl) statusEl.innerHTML = '';
                            if (this.dom.dbFileNameDisplay) this.dom.dbFileNameDisplay.innerText = 'Pilih File Excel (.xlsx)';
                            if (this.dom.dbFileInput) this.dom.dbFileInput.value = '';
                        }, 1800);
                    } else {
                        const msg = result.detail || result.error || result.message || 'Gagal memproses file';
                        if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-rose);">❌ ${msg}</span>`;
                        this.showToast(`❌ ${msg}`, 'error');
                    }
                } catch (err) {
                    if (statusEl) statusEl.innerHTML = `<span style="color: var(--accent-rose);">❌ Error: ${err.message}</span>`;
                    this.showToast(`❌ Error: ${err.message}`, 'error');
                } finally {
                    if (btnUpload) {
                        btnUpload.disabled = false;
                        btnUpload.innerHTML = 'Upload &amp; Sinkronkan';
                    }
                }
            });
        }

        // 6. Calendar Month Navigation (< and > buttons)
        if (this.dom.btnCalPrev) {
            this.dom.btnCalPrev.addEventListener('click', (e) => {
                e.stopPropagation();
                this.navigateCalendarMonth(-1);
            });
        }
        if (this.dom.btnCalNext) {
            this.dom.btnCalNext.addEventListener('click', (e) => {
                e.stopPropagation();
                this.navigateCalendarMonth(1);
            });
        }

        // 7. Calendar Touch Swipe Gestures (Mobile / PWA)
        const calContainer = this.dom.dbCalendarCard || this.dom.calendarGrid;
        if (calContainer) {
            let touchStartX = 0;
            let touchStartY = 0;
            let touchStartTime = 0;

            calContainer.addEventListener('touchstart', (e) => {
                if (!e.changedTouches || e.changedTouches.length === 0) return;
                touchStartX = e.changedTouches[0].screenX;
                touchStartY = e.changedTouches[0].screenY;
                touchStartTime = Date.now();
            }, { passive: true });

            calContainer.addEventListener('touchend', (e) => {
                if (!e.changedTouches || e.changedTouches.length === 0) return;
                const touchEndX = e.changedTouches[0].screenX;
                const touchEndY = e.changedTouches[0].screenY;
                const touchDuration = Date.now() - touchStartTime;

                const diffX = touchEndX - touchStartX;
                const diffY = touchEndY - touchStartY;

                // Gerakan horizontal jelas (> 35px), lebih besar dari vertikal, durasi gestur < 800ms
                if (Math.abs(diffX) > 35 && Math.abs(diffX) > Math.abs(diffY) * 1.3 && touchDuration < 800) {
                    if (diffX > 0) {
                        // Geser kanan (swipe right) -> Bulan sebelumnya
                        this.navigateCalendarMonth(-1);
                    } else {
                        // Geser kiri (swipe left) -> Bulan berikutnya
                        this.navigateCalendarMonth(1);
                    }
                }
            }, { passive: true });
        }
    }

    openUploadModal() {
        if (this.dom.uploadModal) this.dom.uploadModal.classList.remove('hidden');
    }

    closeUploadModal() {
        if (this.dom.uploadModal) this.dom.uploadModal.classList.add('hidden');
    }

    openSuspendModal() {
        if (this.dom.suspendModal) this.dom.suspendModal.classList.remove('hidden');
    }

    closeSuspendModal() {
        if (this.dom.suspendModal) this.dom.suspendModal.classList.add('hidden');
    }

    openLogsModal() {
        if (this.dom.logsModal) this.dom.logsModal.classList.remove('hidden');
    }

    closeLogsModal() {
        if (this.dom.logsModal) this.dom.logsModal.classList.add('hidden');
    }


    openFilterModal() {
        if (this.dom.filterModal && this.dom.filterModalBackdrop) {
            this.dom.filterModalBackdrop.classList.remove('hidden');
            this.dom.filterModal.classList.remove('hidden');
        }
    }

    closeFilterModal() {
        if (this.dom.filterModal && this.dom.filterModalBackdrop) {
            this.dom.filterModalBackdrop.classList.add('hidden');
            this.dom.filterModal.classList.add('hidden');
        }
    }

    applyPresetFilter(preset, showToastFeedback = true) {
        if (!preset) preset = 'all';
        this.currentPreset = preset;
        this.currentPage = 1;

        if (this.dom.screenerPresetChips) {
            this.dom.screenerPresetChips.forEach(c => {
                if (c.dataset.preset === preset) {
                    c.classList.add('active');
                } else {
                    c.classList.remove('active');
                }
            });
        }

        const presetNames = {
            'all': 'Semua Saham',
            'pre_breakout': '🎯 Pre-Breakout Base',
            'foreign_inflow': '🌐 Foreign Inflow',
            'whale_footprint': '🐳 Whale Footprint',
            'swing': '🚀 Swing Setup',
            'breakout': '💥 Breakout R1',
            'vol_bb': '💎 Akumulasi BB',
            'oversold': '⚡ Oversold RSI',
            'bigcap': '🏆 Big Cap Flow'
        };
        const pName = presetNames[preset] || preset;
        const isFiltered = preset !== 'all';

        if (preset === 'pre_breakout') {
            this.currentSort = 'score_desc';
            if (this.dom.screenerSortSelect) {
                this.dom.screenerSortSelect.value = 'score_desc';
            }
        } else if (preset === 'foreign_inflow') {
            this.currentSort = 'foreign_desc';
            if (this.dom.screenerSortSelect) {
                this.dom.screenerSortSelect.value = 'foreign_desc';
            }
        } else if (preset === 'whale_footprint') {
            this.currentSort = 'whale_desc';
            if (this.dom.screenerSortSelect) {
                this.dom.screenerSortSelect.value = 'whale_desc';
            }
        } else if (['score_desc', 'foreign_desc', 'whale_desc'].includes(this.currentSort)) {
            this.currentSort = 'change_desc';
            if (this.dom.screenerSortSelect) {
                this.dom.screenerSortSelect.value = 'change_desc';
            }
        }

        if (this.dom.filterActiveDot) {
            this.dom.filterActiveDot.classList.toggle('hidden', !isFiltered);
        }
        if (this.dom.btnToggleFilters) {
            this.dom.btnToggleFilters.classList.toggle('active', isFiltered);
        }
        if (this.dom.screenerActiveFilterBadge && this.dom.activePresetName) {
            if (isFiltered) {
                this.dom.activePresetName.textContent = pName;
                this.dom.screenerActiveFilterBadge.classList.remove('hidden');
            } else {
                this.dom.screenerActiveFilterBadge.classList.add('hidden');
            }
        }

        this.closeFilterModal();

        if (showToastFeedback && isFiltered) {
            this.showToast(`Filter aktif: ${pName}`, 'info');
        } else if (showToastFeedback && !isFiltered) {
            this.showToast('Filter direset ke Semua Saham', 'info');
        }

        this.fetchScreenerData(this.currentPreset, this.currentSort);
    }

    async fetchScreenerData(preset = this.currentPreset, sort = this.currentSort) {
        if (this.dom.screenerCountBadge) {
            this.dom.screenerCountBadge.textContent = 'Memindai...';
        }
        let stocksData = null;
        try {
            const pEnc = encodeURIComponent(preset);
            const sEnc = encodeURIComponent(sort);
            const resp = await fetch(`/api/screen?preset=${pEnc}&sort=${sEnc}`);
            const json = await resp.json();
            if (resp.ok && json.success && Array.isArray(json.stocks)) {
                stocksData = json.stocks;
            } else {
                if (this.dom.screenerCountBadge) {
                    this.dom.screenerCountBadge.textContent = 'Gagal';
                }
                this.showToast('Gagal memuat data screener', 'error');
                return;
            }
        } catch (err) {
            console.error('Screener fetch error:', err);
            if (this.dom.screenerCountBadge) {
                this.dom.screenerCountBadge.textContent = 'Koneksi terganggu';
            }
            return;
        }

        if (stocksData) {
            this.screenerStocks = stocksData;
            this.filterAndRenderScreener();
        }
    }

    filterAndRenderScreener() {
        let filtered = this.screenerStocks || [];
        if (this.searchQuery) {
            const q = this.searchQuery.toLowerCase();
            filtered = filtered.filter(s => 
                (s.symbol && s.symbol.toLowerCase().includes(q)) || 
                (s.name && s.name.toLowerCase().includes(q))
            );
        }
        this.currentFilteredStocks = filtered;

        const total = filtered.length;
        if (this.dom.screenerCountBadge) {
            this.dom.screenerCountBadge.textContent = `${total} Saham`;
        }

        if (!this.dom.screenerList) return;

        if (total === 0) {
            this.dom.screenerList.innerHTML = `
                <div class="screener-empty">
                    <div class="screener-empty-icon">🔍</div>
                    <p>Tidak ada saham yang cocok dengan filter atau pencarian Anda.</p>
                </div>
            `;
            if (this.dom.screenerPagination) this.dom.screenerPagination.innerHTML = '';
            return;
        }

        // Pagination calculation
        const totalPages = Math.ceil(total / this.pageSize) || 1;
        if (this.currentPage < 1) this.currentPage = 1;
        if (this.currentPage > totalPages) this.currentPage = totalPages;

        const startIdx = (this.currentPage - 1) * this.pageSize;
        const endIdx = Math.min(startIdx + this.pageSize, total);
        const pageStocks = filtered.slice(startIdx, endIdx);

        const fmtPrice = (val) => Number(val).toLocaleString('id-ID');
        const fmtVol = (v) => {
            if (v >= 1e9) return (v / 1e9).toFixed(1) + 'B';
            if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
            if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K';
            return (v || 0).toLocaleString('id-ID');
        };
        const fmtMcap = (m) => {
            if (m >= 1e12) return (m / 1e12).toFixed(1) + 'T';
            if (m >= 1e9) return (m / 1e9).toFixed(1) + 'B';
            return '-';
        };
        const fmtVal = (val) => {
            const absVal = Math.abs(val || 0);
            if (absVal >= 1e12) return (absVal / 1e12).toFixed(1) + 'T';
            if (absVal >= 1e9) return (absVal / 1e9).toFixed(1) + 'B';
            if (absVal >= 1e6) return (absVal / 1e6).toFixed(0) + 'M';
            if (absVal >= 1e3) return (absVal / 1e3).toFixed(0) + 'K';
            return absVal.toLocaleString('id-ID');
        };

        const getDynamicMetric = (s) => {
            if (this.currentSort.startsWith('foreign') || s.is_foreign_inflow) {
                const val = s.foreign_val ?? 0;
                const sign = val > 0 ? '+' : (val < 0 ? '-' : '');
                const cls = val >= 0 ? 'up' : 'down';
                const lotStr = s.foreign_net_lots ? ` (${s.foreign_net_lots > 0 ? '+' : ''}${s.foreign_net_lots.toLocaleString('id-ID')} Lot)` : '';
                return `<span class="metric-dynamic ${cls}">🌐 Asing ${sign}${fmtVal(val)}${lotStr}</span> • `;
            }
            if (this.currentSort.startsWith('whale') || s.is_whale) {
                const ratio = s.whale_ratio ?? 1.0;
                const lpt = s.lot_per_trade ? ` (${s.lot_per_trade.toFixed(0)} Lot/Trd)` : '';
                return `<span class="metric-dynamic highlight">🐳 Whale ${ratio.toFixed(1)}x${lpt}</span> • `;
            }
            if (this.currentSort.startsWith('score') || s.is_pre_breakout) {
                const val = s.score != null ? s.score : '--';
                const acc = s.top_accumulator ? ` • Acc ${escapeHtml(s.top_accumulator)}` : '';
                const domStr = s.dominance ? ` (${Number(s.dominance).toFixed(0)}% Dom)` : '';
                return `<span class="metric-dynamic up">🎯 Skor ${val}${acc}${domStr}</span> • `;
            }
            if (this.currentSort.startsWith('perf_3m')) {
                const val = s.perf_3m ?? 0;
                const sign = val >= 0 ? '+' : '';
                const cls = val >= 0 ? 'up' : 'down';
                return `<span class="metric-dynamic ${cls}">3M ${sign}${val.toFixed(1)}%</span> • `;
            }
            if (this.currentSort.startsWith('perf_1m')) {
                const val = s.perf_1m ?? 0;
                const sign = val >= 0 ? '+' : '';
                const cls = val >= 0 ? 'up' : 'down';
                return `<span class="metric-dynamic ${cls}">1M ${sign}${val.toFixed(1)}%</span> • `;
            }
            if (this.currentSort.startsWith('rsi')) {
                const val = s.rsi != null ? s.rsi.toFixed(1) : '--';
                const cls = (s.rsi && s.rsi <= 35) ? 'up' : (s.rsi && s.rsi >= 65 ? 'down' : '');
                return `<span class="metric-dynamic ${cls}">RSI ${val}</span> • `;
            }
            if (this.currentSort.startsWith('surge')) {
                const val = s.volume_surge != null ? s.volume_surge.toFixed(1) + 'x' : '--';
                return `<span class="metric-dynamic highlight">Surge ${val}</span> • `;
            }
            return '';
        };

        const fragment = document.createDocumentFragment();
        for (let i = 0; i < pageStocks.length; i++) {
            const s = pageStocks[i];
            const isUp = (s.change_pct ?? 0) >= 0;
            const changeSign = isUp ? '+' : '';
            const changeClass = isUp ? 'up' : 'down';
            const surgeBadge = s.volume_surge && s.volume_surge >= 1.5 
                ? `<span class="stock-badge-surge">⚡ ${s.volume_surge}x Vol</span>` 
                : '';
            const pbTooltip = s.is_pre_breakout
                ? `Dom: ${Number(s.dominance || 0).toFixed(1)}% | AAR: ${Number(s.aar || 0).toFixed(1)}% | CLV: ${Number(s.clv_3d || 0).toFixed(2)} | U/D Vol: ${Number(s.up_down_vol_ratio || 0).toFixed(2)}x`
                : '';
            const preBreakoutBadge = s.is_pre_breakout 
                ? `<span class="stock-badge-prebreakout" title="${escapeHtml(pbTooltip)}">🎯 Base ${escapeHtml(s.range_7)}%${s.is_pocket_pivot ? ' ⚡Pivot' : ''}</span>` 
                : '';
            const boardName = s.board || s.papan_pencatatan || '';
            const isFca = (boardName.includes('Pemantauan') || s.is_fca);
            
            // Papan bursa disingkat (UTM, PGM, AKS, EKB) agar hemat ruang; FCA diwakili notasi resmi [X]
            let boardBadge = '';
            if (boardName.includes('Akselerasi')) {
                boardBadge = `<span class="stock-badge-board badge-akselerasi" title="Papan Akselerasi">AKS</span>`;
            } else if (boardName.includes('Pengembangan')) {
                boardBadge = `<span class="stock-badge-board badge-pengembangan" title="Papan Pengembangan">PGM</span>`;
            } else if (boardName.includes('Ekonomi Baru')) {
                boardBadge = `<span class="stock-badge-board badge-utama" title="Papan Ekonomi Baru">EKB</span>`;
            } else if (boardName.includes('Utama')) {
                boardBadge = `<span class="stock-badge-board badge-utama" title="Papan Utama">UTM</span>`;
            }

            // Notasi Khusus Resmi BEI (X, E, M, dll.)
            let notasiText = (s.notasi_khusus || '').trim();
            if (isFca && !notasiText.includes('X')) {
                notasiText = notasiText ? `X, ${notasiText}` : 'X';
            }
            const notasiBadge = notasiText
                ? `<span class="stock-badge-board notasi-pill" title="Notasi Khusus BEI: ${escapeHtml(notasiText)}">[${escapeHtml(notasiText)}]</span>`
                : '';
            const dynamicMetricHtml = getDynamicMetric(s);

            const submetricsText = (s.is_pre_breakout && s.hmb)
                ? `${dynamicMetricHtml}HMB Rp ${fmtPrice(s.hmb)} • Dry ${escapeHtml(s.volume_dry_ratio)}x`
                : `${dynamicMetricHtml}Vol ${fmtVol(s.volume)} • Mcap ${fmtMcap(s.market_cap)}`;

            const card = document.createElement('div');
            card.className = 'stock-card';
            card.dataset.symbol = s.symbol;
            card.innerHTML = `
                <div class="stock-card-left">
                    <img src="https://assets.stockbit.com/logos/companies/${s.symbol}.png" 
                         alt="${s.symbol}" 
                         class="stock-logo" 
                         loading="lazy"
                         onerror="this.style.display='none'">
                    <div class="stock-info">
                        <div class="stock-symbol-row">
                            <span class="stock-symbol">${s.symbol}</span>
                            <span class="stock-change ${changeClass}">${changeSign}${(s.change_pct ?? 0).toFixed(2)}%</span>
                            ${surgeBadge}
                            ${preBreakoutBadge}
                            ${boardBadge}
                            ${notasiBadge}
                        </div>
                        <span class="stock-name" title="${s.name || s.symbol}">${s.name || s.symbol}</span>
                    </div>
                </div>
                <div class="stock-card-right">
                    <div class="stock-price">Rp ${fmtPrice(s.price)}</div>
                    <div class="stock-submetrics">${submetricsText}</div>
                </div>
            `;
            fragment.appendChild(card);
        }

        this.dom.screenerList.innerHTML = '';
        this.dom.screenerList.appendChild(fragment);

        this.renderPagination(total, totalPages, startIdx, endIdx);
    }

    renderPagination(total, totalPages, startIdx, endIdx) {
        if (!this.dom.screenerPagination) return;
        if (total <= this.pageSize) {
            this.dom.screenerPagination.innerHTML = '';
            return;
        }

        const fragment = document.createDocumentFragment();

        // Info range
        const info = document.createElement('span');
        info.className = 'pg-info';
        info.textContent = `${startIdx + 1}–${endIdx} dari ${total}`;
        fragment.appendChild(info);

        const createBtn = (label, targetPage, disabled = false, isActive = false) => {
            const btn = document.createElement('button');
            btn.className = `pg-btn ${isActive ? 'active' : ''}`;
            btn.textContent = label;
            if (disabled) {
                btn.disabled = true;
            } else {
                btn.addEventListener('click', () => {
                    this.currentPage = targetPage;
                    this.filterAndRenderScreener();
                    const content = document.querySelector('.screener-content');
                    if (content) content.scrollTop = 0;
                });
            }
            return btn;
        };

        // « (first)
        fragment.appendChild(createBtn('«', 1, this.currentPage <= 1));
        // ‹ (prev)
        fragment.appendChild(createBtn('‹', this.currentPage - 1, this.currentPage <= 1));

        // Number buttons (max 5)
        const startPg = Math.max(1, this.currentPage - 2);
        const endPg = Math.min(totalPages, startPg + 4);
        for (let p = startPg; p <= endPg; p++) {
            fragment.appendChild(createBtn(String(p), p, false, p === this.currentPage));
        }

        // › (next)
        fragment.appendChild(createBtn('›', this.currentPage + 1, this.currentPage >= totalPages));
        // » (last)
        fragment.appendChild(createBtn('»', totalPages, this.currentPage >= totalPages));

        this.dom.screenerPagination.innerHTML = '';
        this.dom.screenerPagination.appendChild(fragment);
    }

    openChartFromScreener(symbol) {
        this.updateChartBackButton('screener');
        const clean = symbol.replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        // Simpan daftar saham yang sedang aktif terfilter ke navigation flow
        if (this.currentFilteredStocks && this.currentFilteredStocks.length > 0) {
            this.activeNavigationList = this.currentFilteredStocks.map(s => s.symbol);
        } else {
            this.activeNavigationList = [clean];
        }

        const idx = this.activeNavigationList.indexOf(clean);
        this.currentNavigationIndex = idx >= 0 ? idx : 0;

        // Render dynamic quick chips sesuai daftar saham yang discreen
        this.renderQuickChipsFromList(this.activeNavigationList, clean);
        this.updateNavIndex();

        // Pindah ke Chart View dengan target symbol langsung agar hash history sinkron (tidak nyelip BBRI)
        this.switchView('chart', true, clean);

        // Buka saham terpilih
        this.setSymbol(clean, true);
    }

    renderQuickChipsFromList(symbols = [], activeSymbol = this.currentSymbol) {
        if (!this.dom.quickChipsContainer) return;
        this.dom.quickChipsContainer.innerHTML = '';

        // Tampilkan chips: jika list sangat panjang, ambil window di sekitar activeSymbol
        let displaySymbols = symbols;
        if (symbols.length > 50) {
            const activeIdx = Math.max(0, symbols.indexOf(activeSymbol));
            const start = Math.max(0, activeIdx - 15);
            const end = Math.min(symbols.length, start + 50);
            displaySymbols = symbols.slice(start, end);
        }

        const fragment = document.createDocumentFragment();
        displaySymbols.forEach(sym => {
            const btn = document.createElement('button');
            btn.className = `chip-btn ${sym === activeSymbol ? 'active' : ''}`;
            btn.dataset.symbol = sym;
            btn.innerHTML = `
                <img src="https://assets.stockbit.com/logos/companies/${sym}.png" 
                     alt="${sym}" 
                     class="chip-logo" 
                     loading="lazy"
                     onerror="this.style.display='none'">
                <span class="chip-text">${sym}</span>
            `;
            fragment.appendChild(btn);
        });

        this.dom.quickChipsContainer.appendChild(fragment);
        this.scrollActiveChipIntoView();
    }

    scrollActiveChipIntoView() {
        if (!this.dom.quickChipsContainer) return;
        const activeChip = this.dom.quickChipsContainer.querySelector('.chip-btn.active');
        if (activeChip) {
            activeChip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
        }
    }

    navigateFilteredStock(direction) {
        if (!this.activeNavigationList || this.activeNavigationList.length === 0) return;

        const len = this.activeNavigationList.length;
        this.currentNavigationIndex = (this.currentNavigationIndex + direction + len) % len;
        const nextSymbol = this.activeNavigationList[this.currentNavigationIndex];

        this.updateNavIndex();
        this.renderQuickChipsFromList(this.activeNavigationList, nextSymbol);
        this.setSymbol(nextSymbol);
    }

    updateNavIndex() {
        if (!this.dom.chartNavIndex) return;
        const total = this.activeNavigationList ? this.activeNavigationList.length : 1;
        const current = (this.currentNavigationIndex >= 0 ? this.currentNavigationIndex : 0) + 1;
        this.dom.chartNavIndex.textContent = `${current}/${total}`;
    }

    updateChartBackButton(fromView) {
        if (!this.dom.btnBackScreener) return;
        const view = fromView || this.previousView || 'screener';
        this.previousView = view;

        let label = 'Screener';
        if (view === 'watchlist') label = 'Watchlist';
        else if (view === 'journal') label = 'Journal';
        else if (view === 'database') label = 'Database';

        if (this.dom.backScreenerLabel) {
            this.dom.backScreenerLabel.textContent = label;
        } else {
            this.dom.btnBackScreener.innerHTML = `<span class="back-arrow">◀</span> <span id="back-screener-label">${label}</span>`;
            this.dom.backScreenerLabel = document.getElementById('back-screener-label');
        }
        this.dom.btnBackScreener.title = `Kembali ke ${label}`;
    }

    closeAnyOpenModal() {
        let closedSomething = false;
        const modalsToClose = [
            { el: this.dom.filterModal, close: () => this.closeFilterModal() },
            { el: this.dom.watchlistModal, close: () => this.closeWatchlistModal() },
            { el: this.dom.categoryMgmtModal, close: () => this.closeCategoryMgmtModal() },
            { el: this.dom.riskModal, close: () => this.closeRiskModal() },
            { el: this.dom.planModal, close: () => this.closePlanModal() },
            { el: this.dom.trailingModal, close: () => this.closeTrailingModal() },
            { el: this.dom.exitModal, close: () => this.closeExitModal() },
            { el: this.dom.uploadModal, close: () => this.closeUploadModal ? this.closeUploadModal() : this.dom.uploadModal.classList.add('hidden') },
            { el: this.dom.suspendModal, close: () => this.closeSuspendModal ? this.closeSuspendModal() : this.dom.suspendModal.classList.add('hidden') },
            { el: this.dom.logsModal, close: () => this.closeLogsModal ? this.closeLogsModal() : this.dom.logsModal.classList.add('hidden') },
            { el: this.dom.indicatorSheet, close: () => this.closeSheet ? this.closeSheet('indicator') : this.dom.indicatorSheet.classList.add('hidden') },
            { el: this.dom.drawSheet, close: () => this.closeSheet ? this.closeSheet('draw') : this.dom.drawSheet.classList.add('hidden') }
        ];

        for (const item of modalsToClose) {
            if (item.el && !item.el.classList.contains('hidden')) {
                try { item.close(); } catch (_) { item.el.classList.add('hidden'); }
                closedSomething = true;
            }
        }
        if (this.dom.sheetBackdrop && !this.dom.sheetBackdrop.classList.contains('hidden')) {
            this.dom.sheetBackdrop.classList.add('hidden');
        }
        return closedSomething;
    }

    handleRouteFromHash() {
        this.closeAnyOpenModal();

        const rawHash = (window.location.hash || '').replace('#', '').trim();
        const hash = rawHash.toUpperCase();

        if (!hash || hash === 'SCREENER') {
            if (this.currentView !== 'screener') {
                this.switchView('screener', false);
            }
        } else if (hash === 'DATABASE' || hash === 'HOME') {
            if (this.currentView !== 'database') {
                this.switchView('database', false);
            }
        } else if (hash === 'WATCHLIST') {
            if (this.currentView !== 'watchlist') {
                this.switchView('watchlist', false);
            }
        } else if (hash === 'JOURNAL' || hash === 'PLAN') {
            if (this.currentView !== 'journal') {
                this.switchView('journal', false);
            }
        } else if (hash === 'SETTINGS') {
            if (this.currentView !== 'settings') {
                this.switchView('settings', false);
            }
        } else if (hash.length >= 4) {
            if (this.currentView !== 'chart' || this.currentSymbol !== hash) {
                this.switchView('chart', false, hash);
                this.setSymbol(hash, false);
            }
        } else {
            if (this.currentView !== 'screener') {
                this.switchView('screener', false);
            }
        }
    }

    switchView(viewName, updateHistory = true, targetSymbol = null) {
        if (viewName === 'home') viewName = 'database';

        if (targetSymbol) {
            this.currentSymbol = targetSymbol.replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        }

        // Rekam previousView jika berpindah ke chart
        if (viewName === 'chart') {
            this._navigatedToChartFromApp = true;
            if (this.currentView && this.currentView !== 'chart') {
                this.updateChartBackButton(this.currentView);
            } else {
                this.updateChartBackButton(this.previousView || 'screener');
            }
        } else {
            this.previousView = viewName;
            this._navigatedToChartFromApp = false;
        }

        this.currentView = viewName;

        // Hide all views first
        if (this.dom.databaseView) this.dom.databaseView.classList.add('hidden');
        if (this.dom.homeView) this.dom.homeView.classList.add('hidden');
        if (this.dom.screenerView) this.dom.screenerView.classList.add('hidden');
        if (this.dom.watchlistView) this.dom.watchlistView.classList.add('hidden');
        if (this.dom.journalView) this.dom.journalView.classList.add('hidden');
        if (this.dom.settingsView) this.dom.settingsView.classList.add('hidden');
        if (this.dom.chartView) this.dom.chartView.classList.add('hidden');

        let targetHash = '#screener';

        if (viewName === 'database') {
            const dbView = this.dom.databaseView || this.dom.homeView;
            if (dbView) {
                dbView.classList.remove('hidden');
                dbView.classList.remove('view-enter');
                void dbView.offsetWidth;
                dbView.classList.add('view-enter');
            }
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.remove('nav-hidden');
            this.updateDatabaseOverview();
            this.saveOverlaysForSymbol(this.currentSymbol);
            targetHash = '#database';
        } else if (viewName === 'screener') {
            if (this.dom.screenerView) {
                this.dom.screenerView.classList.remove('hidden');
                this.dom.screenerView.classList.remove('view-enter');
                void this.dom.screenerView.offsetWidth; // trigger reflow
                this.dom.screenerView.classList.add('view-enter');
            }
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.remove('nav-hidden');
            this.saveOverlaysForSymbol(this.currentSymbol);
            targetHash = '#screener';
        } else if (viewName === 'watchlist') {
            if (this.dom.watchlistView) {
                this.dom.watchlistView.classList.remove('hidden');
                this.dom.watchlistView.classList.remove('view-enter');
                void this.dom.watchlistView.offsetWidth; // trigger reflow
                this.dom.watchlistView.classList.add('view-enter');
            }
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.remove('nav-hidden');
            this.saveOverlaysForSymbol(this.currentSymbol);
            this.fetchWatchlist(this.activeWatchlistCategory);
            targetHash = '#watchlist';
        } else if (viewName === 'journal') {
            if (this.dom.journalView) {
                this.dom.journalView.classList.remove('hidden');
                this.dom.journalView.classList.remove('view-enter');
                void this.dom.journalView.offsetWidth; // trigger reflow
                this.dom.journalView.classList.add('view-enter');
            }
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.remove('nav-hidden');
            this.saveOverlaysForSymbol(this.currentSymbol);
            this.fetchTradingPlans(this.activePlanFilter);
            targetHash = '#journal';
        } else if (viewName === 'settings') {
            if (this.dom.settingsView) {
                this.dom.settingsView.classList.remove('hidden');
                this.dom.settingsView.classList.remove('view-enter');
                void this.dom.settingsView.offsetWidth;
                this.dom.settingsView.classList.add('view-enter');
            }
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.remove('nav-hidden');
            this.populateSettingsFields();
            this.saveOverlaysForSymbol(this.currentSymbol);
            targetHash = '#settings';
        } else if (viewName === 'chart') {
            if (this.dom.chartView) {
                this.dom.chartView.classList.remove('hidden');
                this.dom.chartView.classList.remove('view-enter');
                void this.dom.chartView.offsetWidth; // trigger reflow
                this.dom.chartView.classList.add('view-enter');
            }
            // Hide floating bottom nav on chart view to give full screen for chart
            if (this.dom.floatingBottomNav) this.dom.floatingBottomNav.classList.add('nav-hidden');
            this.checkWatchlistStatus(this.currentSymbol);
            targetHash = '#' + (this.currentSymbol || 'BBRI');

            if (this._needChartRefresh) {
                this._needChartRefresh = false;
                this.loadData(this.currentSymbol, this.currentInterval);
            }

            setTimeout(() => {
                if (this.chart) this.chart.resize();
                this.scrollActiveChipIntoView();
            }, 60);
        }

        // Sinkronisasi status aktif di Floating Bottom Nav buttons
        if (this.dom.navBtns) {
            this.dom.navBtns.forEach(btn => {
                const target = btn.dataset.view;
                if (target === viewName || (viewName === 'database' && target === 'home')) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }

        // Sinkronisasi hash history browser jika updateHistory true
        if (updateHistory && window.location.hash !== targetHash) {
            this._skipNextHashChange = true;
            window.location.hash = targetHash;
        }
    }

    openChartFromWatchlist(symbol) {
        this.updateChartBackButton('watchlist');
        const clean = symbol.replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        // Set daftar navigasi dari watchlist agar user bisa next-next khusus saham watchlist
        if (this.watchlistItems && this.watchlistItems.length > 0) {
            this.activeNavigationList = this.watchlistItems.map(item => item.symbol);
        } else {
            this.activeNavigationList = [clean];
        }

        const idx = this.activeNavigationList.indexOf(clean);
        this.currentNavigationIndex = idx >= 0 ? idx : 0;

        this.renderQuickChipsFromList(this.activeNavigationList, clean);
        this.updateNavIndex();
        this.switchView('chart', true, clean);
        this.setSymbol(clean, true);
    }

    // ── Point 1 & 3: In-Place Ticker & Dynamic Logo Chips ──
    setSymbol(symbol, force = false) {
        const clean = symbol.replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        if (!clean || (!force && clean === this.currentSymbol)) return;

        // Auto-save coretan emiten sebelumnya sebelum berganti
        this.saveOverlaysForSymbol(this.currentSymbol);

        // Bersihkan coretan manual lama dari canvas chart agar tidak bentrok
        this.clearManualOverlaysFromChart();
        
        this.currentSymbol = clean;
        
        // Update navigation index jika clean ada di activeNavigationList
        if (this.activeNavigationList && this.activeNavigationList.length > 0) {
            const idx = this.activeNavigationList.indexOf(clean);
            if (idx >= 0) {
                this.currentNavigationIndex = idx;
            } else {
                this.activeNavigationList.push(clean);
                this.currentNavigationIndex = this.activeNavigationList.length - 1;
            }
            this.updateNavIndex();
        }

        // Update input in-place
        if (this.dom.tickerInplaceInput) {
            this.dom.tickerInplaceInput.value = clean;
            this.dom.tickerInplaceInput.style.width = Math.max(clean.length * 12, 54) + 'px';
        }
        
        // Update URL hash jika di chart view (gunakan replaceState agar flipping chip tidak menumpuk history)
        if (this.currentView === 'chart') {
            const targetHash = '#' + clean;
            if (window.location.hash !== targetHash) {
                this._skipNextHashChange = true;
                try {
                    history.replaceState(null, '', targetHash);
                } catch (_) {
                    window.location.hash = targetHash;
                }
            }
        }

        // Update chip active state jika ada di daftar chip
        if (this.dom.quickChipsContainer) {
            let matched = false;
            const chipButtons = this.dom.quickChipsContainer.querySelectorAll('.chip-btn');
            chipButtons.forEach(b => {
                if (b.dataset.symbol === clean) {
                    b.classList.add('active');
                    matched = true;
                } else {
                    b.classList.remove('active');
                }
            });

            if (!matched) {
                this.renderQuickChipsFromList(this.activeNavigationList, clean);
            } else {
                this.scrollActiveChipIntoView();
            }
        }
        
        this.loadData(this.currentSymbol, this.currentInterval);
        this.checkWatchlistStatus(clean);
    }

    // ========================================================
    // WATCHLIST & RISK MANAGEMENT METHODS (NEON CLOUD DB)
    // ========================================================

    async fetchWatchlist(category = null) {
        try {
            let url = '/api/watchlist';
            if (category && category.toLowerCase() !== 'all') {
                url += `?category=${encodeURIComponent(category)}`;
            }
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            if (json.success && Array.isArray(json.data)) {
                this.watchlistItems = json.data;
                if (!category || category.toLowerCase() === 'all') {
                    this.allWatchlistSymbols = new Set(json.data.map(i => i.symbol.toUpperCase().trim()));
                } else {
                    json.data.forEach(i => this.allWatchlistSymbols.add(i.symbol.toUpperCase().trim()));
                }
                this.renderWatchlist();
                this.checkWatchlistStatus(this.currentSymbol);
            }
        } catch (err) {
            console.error('Fetch watchlist error:', err);
        }
    }

    getHumanAge(createdAtStr) {
        if (!createdAtStr) return 'Baru';
        try {
            let s = String(createdAtStr).trim();
            let created;
            if (s.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(s)) {
                created = new Date(s);
            } else {
                created = new Date(s.replace(' ', 'T') + 'Z');
            }
            if (isNaN(created.getTime())) return 'Baru';

            const now = new Date();
            const diffMs = now - created;
            if (diffMs < 0) return 'Baru saja';
            
            const diffMins = Math.floor(diffMs / (1000 * 60));
            if (diffMins < 60) {
                return diffMins <= 5 ? 'Baru saja' : `${diffMins}m lalu`;
            }
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) {
                return `${diffHours}j lalu`;
            }
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays === 1) {
                return 'Kemarin';
            }
            if (diffDays < 7) {
                return `${diffDays}h lalu`;
            }
            const diffWeeks = Math.floor(diffDays / 7);
            if (diffWeeks < 4) {
                return `${diffWeeks}mgg lalu`;
            }
            return `${Math.floor(diffDays / 30)}bln lalu`;
        } catch (e) {
            return 'Baru';
        }
    }

    getWatchlistAgeDays(createdAtStr, fallbackDays = 0) {
        if (typeof fallbackDays === 'number' && !isNaN(fallbackDays) && !createdAtStr) {
            return Math.max(0, fallbackDays);
        }
        if (!createdAtStr) return 0;
        try {
            let s = String(createdAtStr).trim();
            let created;
            if (s.endsWith('Z') || /[+-]\d{2}:?\d{2}$/.test(s)) {
                created = new Date(s);
            } else {
                created = new Date(s.replace(' ', 'T') + 'Z');
            }
            if (isNaN(created.getTime())) return 0;
            const diffMs = new Date() - created;
            if (diffMs < 0) return 0;
            return Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
        } catch (e) {
            return 0;
        }
    }

    renderWatchlist() {
        if (!this.dom.watchlistList) return;

        const items = this.watchlistItems || [];

        // Update count badges
        if (this.dom.watchlistCountBadge) {
            this.dom.watchlistCountBadge.textContent = `${items.length} Saham`;
        }
        if (this.dom.homeWatchlistCount) {
            this.dom.homeWatchlistCount.textContent = items.length;
        }

        // Empty state vs List
        if (items.length === 0) {
            if (this.dom.watchlistEmpty) this.dom.watchlistEmpty.classList.remove('hidden');
            this.dom.watchlistList.innerHTML = '';
            return;
        }

        if (this.dom.watchlistEmpty) this.dom.watchlistEmpty.classList.add('hidden');

        const escapeHtml = (str) => {
            if (!str) return '';
            return String(str).replace(/[&<>"']/g, (m) => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            }[m]));
        };

        const showCategoryBadge = !this.activeWatchlistCategory || this.activeWatchlistCategory.toLowerCase() === 'all';

        const html = items.map(item => {
            const sym = item.symbol;
            const price = item.price ? Number(item.price).toLocaleString('id-ID') : '--';
            const changePct = typeof item.change_pct === 'number' ? item.change_pct : 0;
            const isUp = changePct >= 0;
            const changeSign = isUp ? '+' : '';
            const changeClass = isUp ? 'up' : 'down';
            const name = item.name && item.name !== sym ? item.name : 'Emiten IDX';
            const ageHuman = (item.created_at ? this.getHumanAge(item.created_at) : (item.age || 'Baru'));
            const ageDays = (typeof item.age_days === 'number')
                ? item.age_days
                : this.getWatchlistAgeDays(item.created_at, 0);
            const ageTierClass = ageDays <= 5 ? 'age-fresh' : (ageDays <= 13 ? 'age-warm' : 'age-stale');
            const ageStatusLabel = ageDays <= 5 ? 'Fresh Setup' : (ageDays <= 13 ? 'Maturing' : 'Stale / Evaluasi');

            const bName = item.board || '';
            const isFca = (item.is_fca || bName.includes('FCA') || bName.includes('Pemantauan'));

            let boardBadge = '';
            if (bName.includes('Akselerasi')) {
                boardBadge = `<span class="stock-badge-board badge-akselerasi" title="Papan Akselerasi">AKS</span>`;
            } else if (bName.includes('Pengembangan')) {
                boardBadge = `<span class="stock-badge-board badge-pengembangan" title="Papan Pengembangan">PGM</span>`;
            } else if (bName.includes('Ekonomi Baru')) {
                boardBadge = `<span class="stock-badge-board badge-utama" title="Papan Ekonomi Baru">EKB</span>`;
            } else if (bName.includes('Utama')) {
                boardBadge = `<span class="stock-badge-board badge-utama" title="Papan Utama">UTM</span>`;
            }

            let notasiText = (item.notasi_khusus || '').trim();
            if (isFca && !notasiText.includes('X')) {
                notasiText = notasiText ? `X, ${notasiText}` : 'X';
            }
            const notasiBadge = notasiText
                ? `<span class="stock-badge-board notasi-pill" title="Notasi Khusus BEI: ${escapeHtml(notasiText)}">[${escapeHtml(notasiText)}]</span>`
                : '';

            const categoryBadgeHtml = showCategoryBadge
                ? `<span class="wl-category-badge">${escapeHtml(item.category)}</span>`
                : '';

            const targetVal = Number(item.target_entry) || 0;
            const liveVal = Number(item.price) || 0;
            const diffTargetPct = (targetVal > 0 && liveVal > 0) ? ((liveVal - targetVal) / targetVal) * 100 : null;
            const isNearTarget = diffTargetPct !== null && Math.abs(diffTargetPct) <= 2.5;
            const targetInlineHtml = targetVal > 0
                ? `<span class="wl-target-inline ${isNearTarget ? 'near' : ''}" title="Target Entry: Rp ${targetVal.toLocaleString('id-ID')}${isNearTarget ? ' (Area Beli!)' : ''}">🎯 ${targetVal.toLocaleString('id-ID')}</span> • `
                : '';

            return `
                <div class="watchlist-card ${isNearTarget ? 'wl-near-target' : ''}" data-id="${item.id}" data-symbol="${sym}">
                    <div class="wl-card-left">
                        <img src="https://assets.stockbit.com/logos/companies/${sym}.png" 
                             alt="${sym}" 
                             class="wl-stock-logo" 
                             loading="lazy" 
                             onerror="this.style.display='none'">
                        <div class="wl-stock-info">
                            <div class="wl-symbol-row">
                                <span class="wl-symbol">${sym}</span>
                                ${boardBadge}
                                ${notasiBadge}
                                ${categoryBadgeHtml}
                            </div>
                            <div class="wl-name">${targetInlineHtml}${escapeHtml(name)}</div>
                        </div>
                    </div>

                    <div class="wl-card-center">
                        <span class="subtle-age-badge ${ageTierClass}" title="Umur pantauan: ${ageDays} hari (${ageHuman}) • Status: ${ageStatusLabel}">${ageDays}</span>
                        <div class="wl-price-col">
                            <span class="wl-price">${price}</span>
                            <span class="wl-change ${changeClass}">${changeSign}${changePct.toFixed(2)}%</span>
                        </div>
                        ${item.notes ? `
                        <div class="wl-note-wrap">
                            <button class="wl-note-trigger btn-wl-note" title="Lihat Catatan" data-id="${item.id}">
                                📝
                            </button>
                            <div class="wl-note-popover hidden" id="wl-popover-${item.id}">
                                <div class="popover-arrow"></div>
                                <div class="popover-title">📌 Catatan ${sym}</div>
                                <div class="popover-text">${escapeHtml(item.notes)}</div>
                            </div>
                        </div>` : ''}
                    </div>

                    <div class="wl-card-actions-right">
                        <button class="wl-icon-btn plan-btn btn-wl-plan" data-symbol="${sym}" data-category="${escapeHtml(item.category)}" data-entry="${item.target_entry || item.price || ''}" data-notes="${escapeHtml(item.notes || '')}" title="Buat Trading Plan (Money Management)">
                            🎯
                        </button>
                        <button class="wl-icon-btn btn-wl-edit" data-id="${item.id}" title="Edit Catatan & Kategori">
                            ✏️
                        </button>
                        <button class="wl-icon-btn danger btn-wl-delete" data-id="${item.id}" data-symbol="${sym}" title="Hapus dari Watchlist">
                            🗑️
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        this.dom.watchlistList.innerHTML = html;
    }

    checkWatchlistStatus(symbol) {
        if (!this.dom.btnStarWatchlist || !this.dom.starIcon) return;
        const clean = (symbol || '').toUpperCase().trim();
        const found = (this.allWatchlistSymbols && this.allWatchlistSymbols.has(clean)) || 
                      (this.watchlistItems || []).some(i => i.symbol === clean);

        if (found) {
            this.dom.btnStarWatchlist.classList.add('active');
            this.dom.starIcon.textContent = '⭐';
            this.dom.btnStarWatchlist.title = `Atur / Ubah Watchlist ${clean}`;
        } else {
            this.dom.btnStarWatchlist.classList.remove('active');
            this.dom.starIcon.textContent = '☆';
            this.dom.btnStarWatchlist.title = `Tambah ${clean} ke Watchlist`;
        }
    }

    toggleStarWatchlist() {
        const clean = this.currentSymbol;
        if (!clean) return;

        const existing = (this.watchlistItems || []).find(i => i.symbol === clean);
        if (existing) {
            // Already in watchlist: open in edit mode (includes multi-select options)
            this.openWatchlistModal(existing);
        } else {
            // Not in watchlist: open in add mode prefilled with current symbol
            this.openWatchlistModal({ symbol: clean, isNew: true });
        }
    }

    async openWatchlistModal(editItem = null) {
        if (!this.dom.watchlistModal || !this.dom.watchlistModalBackdrop) return;

        const sym = editItem?.symbol || (this.currentView === 'chart' ? this.currentSymbol : '');
        const cleanSym = (sym || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();

        if (this.dom.wlInputSymbol) {
            this.dom.wlInputSymbol.value = cleanSym;
            this.dom.wlInputSymbol.disabled = !!cleanSym;
        }

        // Inisialisasi kategori terpilih
        this.selectedWlCategories = new Set();
        let targetEntry = editItem?.target_entry || '';
        let notes = editItem?.notes || '';

        // Ambil dari cache lokal watchlistItems jika ada
        const localMatches = (this.watchlistItems || []).filter(i => i.symbol === cleanSym);
        localMatches.forEach(m => {
            if (m.category) this.selectedWlCategories.add(m.category);
            if (!targetEntry && m.target_entry) targetEntry = m.target_entry;
            if (!notes && m.notes) notes = m.notes;
        });

        if (editItem?.category) {
            this.selectedWlCategories.add(editItem.category);
        }

        // Tandai apakah saham sudah tersimpan di watchlist sebelumnya
        this.isExistingWatchlistStock = (this.selectedWlCategories.size > 0);

        if (this.dom.wlInputTargetEntry) this.dom.wlInputTargetEntry.value = targetEntry || '';
        if (this.dom.wlInputNotes) this.dom.wlInputNotes.value = notes || '';

        if (this.dom.wlModalTitle) {
            this.dom.wlModalTitle.textContent = `⭐ Watchlist ${cleanSym || 'Saham'}`;
        }

        this.renderWatchlistModalCategoryButtons();
        this.updateWatchlistModalSubmitBtn();

        this.dom.watchlistModalBackdrop.classList.remove('hidden');
        this.dom.watchlistModal.classList.remove('hidden');

        // Sinkronisasi kategori live dari database Neon
        if (cleanSym) {
            try {
                const res = await fetch(`/api/watchlist/stock/${encodeURIComponent(cleanSym)}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.success && Array.isArray(data.categories)) {
                        this.selectedWlCategories = new Set(data.categories);
                        if (data.categories.length > 0) {
                            this.isExistingWatchlistStock = true;
                        }
                        if (data.target_entry !== null && data.target_entry !== undefined && !this.dom.wlInputTargetEntry.value) {
                            this.dom.wlInputTargetEntry.value = data.target_entry;
                        }
                        if (data.notes && !this.dom.wlInputNotes.value) {
                            this.dom.wlInputNotes.value = data.notes;
                        }
                        this.renderWatchlistModalCategoryButtons();
                        this.updateWatchlistModalSubmitBtn();
                    }
                }
            } catch (e) {
                console.warn('Gagal sync status kategori stock:', e);
            }
        }

        if (!cleanSym && this.dom.wlInputSymbol) {
            setTimeout(() => this.dom.wlInputSymbol.focus(), 100);
        } else if (this.dom.wlInputTargetEntry) {
            setTimeout(() => this.dom.wlInputTargetEntry.focus(), 100);
        }
    }

    renderWatchlistModalCategoryButtons() {
        if (!this.dom.wlCategoryButtons) return;
        this.dom.wlCategoryButtons.innerHTML = '';

        const cats = this.watchlistCategories && this.watchlistCategories.length > 0 
            ? this.watchlistCategories 
            : ['Breakout'];

        cats.forEach(cat => {
            const isSelected = this.selectedWlCategories.has(cat);
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `wl-cat-btn ${isSelected ? 'active' : ''}`;
            btn.dataset.cat = cat;
            btn.innerHTML = `
                <span class="wl-cat-icon">${isSelected ? '✓' : '+'}</span>
                <span class="wl-cat-name">${cat}</span>
            `;

            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (this.selectedWlCategories.has(cat)) {
                    this.selectedWlCategories.delete(cat);
                } else {
                    this.selectedWlCategories.add(cat);
                }
                this.renderWatchlistModalCategoryButtons();
                this.updateWatchlistModalSubmitBtn();
            });

            this.dom.wlCategoryButtons.appendChild(btn);
        });

        // Update keterangan jumlah pilihan
        if (this.dom.wlSelectedCatCount) {
            const count = this.selectedWlCategories.size;
            if (count === 0) {
                if (this.isExistingWatchlistStock) {
                    this.dom.wlSelectedCatCount.textContent = '0 dipilih (akan dihapus)';
                    this.dom.wlSelectedCatCount.style.color = '#f87171';
                } else {
                    this.dom.wlSelectedCatCount.textContent = 'Pilih watchlist tujuan';
                    this.dom.wlSelectedCatCount.style.color = 'var(--text-muted)';
                }
            } else {
                this.dom.wlSelectedCatCount.textContent = `${count} dipilih`;
                this.dom.wlSelectedCatCount.style.color = 'var(--text-muted)';
            }
        }
    }

    updateWatchlistModalSubmitBtn() {
        if (!this.dom.btnSubmitWl) return;
        const count = this.selectedWlCategories.size;
        if (count === 0) {
            if (this.isExistingWatchlistStock) {
                this.dom.btnSubmitWl.textContent = '🗑️ Hapus dari Semua Watchlist';
                this.dom.btnSubmitWl.className = 'filter-btn-danger';
                this.dom.btnSubmitWl.disabled = false;
            } else {
                this.dom.btnSubmitWl.textContent = 'Pilih Minimal 1 Watchlist';
                this.dom.btnSubmitWl.className = 'filter-btn-secondary';
                this.dom.btnSubmitWl.disabled = true;
            }
        } else if (count === 1) {
            const catName = Array.from(this.selectedWlCategories)[0];
            this.dom.btnSubmitWl.textContent = `Simpan ke ${catName}`;
            this.dom.btnSubmitWl.className = 'filter-btn-primary';
            this.dom.btnSubmitWl.disabled = false;
        } else {
            this.dom.btnSubmitWl.textContent = `Simpan ke ${count} Watchlist`;
            this.dom.btnSubmitWl.className = 'filter-btn-primary';
            this.dom.btnSubmitWl.disabled = false;
        }
    }

    closeWatchlistModal() {
        if (this.dom.watchlistModal) this.dom.watchlistModal.classList.add('hidden');
        if (this.dom.watchlistModalBackdrop) this.dom.watchlistModalBackdrop.classList.add('hidden');
    }

    async submitWatchlistForm() {
        const symbol = this.dom.wlInputSymbol ? this.dom.wlInputSymbol.value.trim().toUpperCase() : '';
        const rawTarget = this.dom.wlInputTargetEntry ? this.dom.wlInputTargetEntry.value.trim() : '';
        const targetEntry = rawTarget ? parseFloat(rawTarget) : null;
        const notes = this.dom.wlInputNotes ? this.dom.wlInputNotes.value.trim() : '';

        if (!symbol) {
            this.showToast('Kode saham tidak boleh kosong!', 'warning');
            return;
        }

        const categories = Array.from(this.selectedWlCategories);
        if (categories.length === 0 && !this.isExistingWatchlistStock) {
            this.showToast('Pilih minimal satu kategori watchlist!', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/watchlist/sync-stock', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    categories: categories,
                    target_entry: targetEntry,
                    notes: notes
                })
            });
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Gagal menyimpan watchlist');

            if (categories.length > 0) {
                this.allWatchlistSymbols.add(symbol);
                this.showToast(`⭐ ${symbol} disimpan ke: ${categories.join(', ')}`, 'info');
            } else {
                this.allWatchlistSymbols.delete(symbol);
                this.showToast(`🗑️ ${symbol} dihapus dari semua watchlist`, 'info');
            }

            this.closeWatchlistModal();
            await this.fetchWatchlist(this.activeWatchlistCategory);
            this.checkWatchlistStatus(this.currentSymbol);
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    // ── Watchlist Categories Methods (CRUD) ──

    async fetchWatchlistCategories() {
        try {
            const res = await fetch('/api/watchlist/categories');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            if (json.success && Array.isArray(json.categories)) {
                this.watchlistCategories = json.categories;
                this.renderWatchlistCategoryChips();
                this.populateCategoryDropdowns();
            }
        } catch (err) {
            console.warn('Gagal memuat kategori watchlist:', err);
        }
    }

    renderWatchlistCategoryChips() {
        if (!this.dom.watchlistCategories) return;
        const cats = this.watchlistCategories || ['Breakout'];
        
        let html = '';
        cats.forEach(c => {
            const isActive = this.activeWatchlistCategory === c;
            const label = c === 'Breakout' ? '💥 Breakout' : escapeHtml(c);
            html += `<button class="watchlist-cat-chip ${isActive ? 'active' : ''}" data-category="${escapeHtml(c)}">${label}</button>`;
        });
        
        this.dom.watchlistCategories.innerHTML = html;

        // Update active state pada tombol 'Semua' di pinned actions
        if (this.dom.btnWlCatAll) {
            const isAllActive = this.activeWatchlistCategory === 'all';
            if (isAllActive) {
                this.dom.btnWlCatAll.classList.add('active');
            } else {
                this.dom.btnWlCatAll.classList.remove('active');
            }
        }

        // Pasang event listener ke setiap chip
        this.dom.watchlistCategories.querySelectorAll('.watchlist-cat-chip').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const cat = e.currentTarget.dataset.category;
                this.dom.watchlistCategories.querySelectorAll('.watchlist-cat-chip').forEach(b => b.classList.remove('active'));
                if (this.dom.btnWlCatAll) this.dom.btnWlCatAll.classList.remove('active');
                e.currentTarget.classList.add('active');
                this.activeWatchlistCategory = cat;
                this.fetchWatchlist(cat);
            });
        });
    }

    populateCategoryDropdowns() {
        const cats = this.watchlistCategories || ['Breakout'];
        
        // 1. Dropdown di Watchlist Add/Edit Modal
        if (this.dom.wlInputCategory) {
            const currentVal = this.dom.wlInputCategory.value;
            this.dom.wlInputCategory.innerHTML = cats.map(c => 
                `<option value="${escapeHtml(c)}">${c === 'Breakout' ? '💥 Breakout' : escapeHtml(c)}</option>`
            ).join('');
            if (cats.includes(currentVal)) {
                this.dom.wlInputCategory.value = currentVal;
            }
        }

        // 2. Dropdown di Settings View
        if (this.dom.settingSelectCategory) {
            const currentVal = this.dom.settingSelectCategory.value;
            this.dom.settingSelectCategory.innerHTML = cats.map(c => 
                `<option value="${escapeHtml(c)}">${c === 'Breakout' ? '💥 Breakout' : escapeHtml(c)}</option>`
            ).join('');
            if (cats.includes(currentVal)) {
                this.dom.settingSelectCategory.value = currentVal;
            }
        }

        // 3. Dropdown di Quick Risk Modal
        if (this.dom.riskSelectCategory) {
            const currentVal = this.dom.riskSelectCategory.value;
            this.dom.riskSelectCategory.innerHTML = cats.map(c => 
                `<option value="${escapeHtml(c)}">${c === 'Breakout' ? '💥 Breakout' : escapeHtml(c)}</option>`
            ).join('');
            if (cats.includes(currentVal)) {
                this.dom.riskSelectCategory.value = currentVal;
            }
        }

        // 4. Dropdown di Trading Plan Modal
        if (this.dom.planSelectCategory) {
            const currentVal = this.dom.planSelectCategory.value;
            this.dom.planSelectCategory.innerHTML = cats.map(c => 
                `<option value="${escapeHtml(c)}">${c === 'Breakout' ? '💥 Breakout' : escapeHtml(c)}</option>`
            ).join('');
            if (cats.includes(currentVal)) {
                this.dom.planSelectCategory.value = currentVal;
            }
        }
    }

    openCategoryMgmtModal() {
        if (!this.dom.categoryMgmtModal || !this.dom.categoryMgmtBackdrop) return;
        this.dom.categoryMgmtBackdrop.classList.remove('hidden');
        this.dom.categoryMgmtModal.classList.remove('hidden');
        this.renderCategoryMgmtList();
        if (this.dom.inputNewCategory) {
            this.dom.inputNewCategory.value = '';
            setTimeout(() => this.dom.inputNewCategory.focus(), 80);
        }
    }

    closeCategoryMgmtModal() {
        if (this.dom.categoryMgmtModal) this.dom.categoryMgmtModal.classList.add('hidden');
        if (this.dom.categoryMgmtBackdrop) this.dom.categoryMgmtBackdrop.classList.add('hidden');
    }

    renderCategoryMgmtList() {
        if (!this.dom.categoryMgmtItems) return;
        const cats = this.watchlistCategories || ['Breakout'];
        
        let html = '';
        cats.forEach(c => {
            const isDefault = c.toLowerCase() === 'breakout';
            if (isDefault) {
                html += `
                    <div class="cat-item-row default">
                        <div class="cat-item-left">
                            <span class="cat-item-name">💥 Breakout</span>
                            <span class="cat-item-badge">Default</span>
                        </div>
                        <div class="cat-item-actions">
                            <span class="cat-locked-hint" title="Kategori utama sistem">🔒 Tetap</span>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div class="cat-item-row" data-name="${escapeHtml(c)}" id="cat-row-${encodeURIComponent(c)}">
                        <div class="cat-item-left">
                            <span class="cat-item-name">${escapeHtml(c)}</span>
                        </div>
                        <div class="cat-item-actions">
                            <button class="cat-action-btn btn-rename-cat" data-name="${escapeHtml(c)}" title="Ubah Nama">✏️</button>
                            <button class="cat-action-btn btn-delete-cat" data-name="${escapeHtml(c)}" title="Hapus Kategori">🗑️</button>
                        </div>
                    </div>
                `;
            }
        });
        
        this.dom.categoryMgmtItems.innerHTML = html;

        // Pasang event listener untuk rename dan delete
        this.dom.categoryMgmtItems.querySelectorAll('.btn-rename-cat').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.currentTarget.dataset.name;
                this.promptRenameCategory(name);
            });
        });

        this.dom.categoryMgmtItems.querySelectorAll('.btn-delete-cat').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.currentTarget.dataset.name;
                this.confirmDeleteCategory(name);
            });
        });
    }

    async handleAddNewCategory() {
        const input = this.dom.inputNewCategory;
        if (!input) return;
        const name = input.value.trim();
        if (!name) {
            this.showToast('Nama kategori tidak boleh kosong!', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/watchlist/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Gagal menambah kategori');

            this.watchlistCategories = json.categories;
            this.renderWatchlistCategoryChips();
            this.populateCategoryDropdowns();
            this.renderCategoryMgmtList();
            input.value = '';
            this.showToast(`✅ Watchlist '${name}' berhasil ditambahkan!`, 'info');
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    promptRenameCategory(oldName) {
        const row = document.getElementById(`cat-row-${encodeURIComponent(oldName)}`);
        if (!row) return;

        row.innerHTML = `
            <div class="cat-item-left" style="width: 100%;">
                <input type="text" class="cat-rename-input" id="input-rename-${encodeURIComponent(oldName)}" value="${escapeHtml(oldName)}" maxlength="40">
            </div>
            <div class="cat-item-actions">
                <button class="cat-action-btn btn-save-rename" title="Simpan">💾</button>
                <button class="cat-action-btn btn-cancel-rename" title="Batal">✕</button>
            </div>
        `;

        const input = row.querySelector('.cat-rename-input');
        if (input) {
            input.focus();
            input.select();
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') row.querySelector('.btn-save-rename')?.click();
                if (e.key === 'Escape') this.renderCategoryMgmtList();
            });
        }

        row.querySelector('.btn-cancel-rename')?.addEventListener('click', () => {
            this.renderCategoryMgmtList();
        });

        row.querySelector('.btn-save-rename')?.addEventListener('click', async () => {
            const newName = input.value.trim();
            if (!newName || newName === oldName) {
                this.renderCategoryMgmtList();
                return;
            }

            try {
                const res = await fetch(`/api/watchlist/categories/${encodeURIComponent(oldName)}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ new_name: newName })
                });
                const json = await res.json();
                if (!res.ok) throw new Error(json.detail || 'Gagal mengubah kategori');

                this.watchlistCategories = json.categories;
                if (this.activeWatchlistCategory === oldName) {
                    this.activeWatchlistCategory = newName;
                }
                this.renderWatchlistCategoryChips();
                this.populateCategoryDropdowns();
                this.renderCategoryMgmtList();
                this.fetchWatchlist(this.activeWatchlistCategory);
                this.showToast(`✅ Watchlist '${newName}' berhasil diperbarui!`, 'info');
            } catch (err) {
                this.showToast(`Error: ${err.message}`, 'error');
            }
        });
    }

    async confirmDeleteCategory(name) {
        if (!confirm(`Hapus watchlist '${name}'? Saham di dalamnya akan otomatis dipindahkan ke 'Breakout'.`)) {
            return;
        }

        try {
            const res = await fetch(`/api/watchlist/categories/${encodeURIComponent(name)}`, {
                method: 'DELETE'
            });
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Gagal menghapus kategori');

            this.watchlistCategories = json.categories;
            if (this.activeWatchlistCategory === name) {
                this.activeWatchlistCategory = 'all';
            }
            this.renderWatchlistCategoryChips();
            this.populateCategoryDropdowns();
            this.renderCategoryMgmtList();
            this.fetchWatchlist(this.activeWatchlistCategory);
            this.showToast(`🗑️ Watchlist '${name}' dihapus (saham dipindahkan ke Breakout)`, 'info');
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    async updateDatabaseOverview() {
        const capital = this.riskSettings?.total_capital || 100000000;
        const riskPct = this.riskSettings?.risk_pct || 1.0;
        const nominal = this.riskSettings?.risk_nominal || Math.round(capital * (riskPct / 100.0));
        const source = this.riskSettings?.daily_source || 'neon_db';

        if (this.dom.dbStatWlCount) {
            this.dom.dbStatWlCount.textContent = `${(this.watchlistItems || []).length} Saham`;
        }
        if (this.dom.dbStatRiskNominal) {
            this.dom.dbStatRiskNominal.textContent = `Rp ${Number(nominal).toLocaleString('id-ID')} (${riskPct.toFixed(1)}%)`;
        }
        if (this.dom.dbStatCapitalSub) {
            this.dom.dbStatCapitalSub.textContent = `Modal: Rp ${Number(capital).toLocaleString('id-ID')}`;
        }
        if (this.dom.dbStatFeedSource) {
            this.dom.dbStatFeedSource.textContent = source === 'yahoo' ? 'Yahoo Finance (Direct Live)' : 'Neon DB (Glory Engine)';
        }

        try {
            const res = await fetch('/api/database/health');
            const json = await res.json();
            if (res.ok && json.status === 'success') {
                const d = json.data;
                const master = d.saham || { total: 0, last_update: 'N/A' };
                const stats = d.archive?.stats || { total_harga: 0, total_broksum: 0, min_date: 'N/A', max_date: 'N/A' };

                if (this.dom.dbLastSyncBadge) {
                    this.dom.dbLastSyncBadge.textContent = `Last Synced: ${master.last_update || '-'}`;
                    this.dom.dbLastSyncBadge.title = `Master Emiten IDX: ${master.last_update || '-'}`;
                }
                if (this.dom.dbEngineStatus) {
                    this.dom.dbEngineStatus.textContent = 'Neon DB Aktif';
                }
                if (this.dom.dbServerStatus) {
                    this.dom.dbServerStatus.textContent = 'Neon DB Online';
                }
                if (this.dom.dbEngineDot) {
                    this.dom.dbEngineDot.style.background = '#10b981';
                }

                if (this.dom.dbStatTotalEmiten) {
                    this.dom.dbStatTotalEmiten.textContent = master.total ? `${master.total}` : '0';
                }
                if (this.dom.dbStatActivePrice) {
                    this.dom.dbStatActivePrice.textContent = (stats.total_harga || 0).toLocaleString('id-ID');
                }
                if (this.dom.dbStatActiveBroksum) {
                    this.dom.dbStatActiveBroksum.textContent = (stats.total_broksum || 0).toLocaleString('id-ID');
                }
                if (this.dom.dbStatDateRange) {
                    this.dom.dbStatDateRange.textContent = `${stats.min_date || '-'} s.d. ${stats.max_date || '-'}`;
                }

                // Badges for Actions
                const gaps = d.gaps || [];
                if (this.dom.badgeSuspendCount) {
                    if (gaps.length > 0) {
                        this.dom.badgeSuspendCount.textContent = gaps.length;
                        this.dom.badgeSuspendCount.style.display = 'flex';
                    } else {
                        this.dom.badgeSuspendCount.style.display = 'none';
                    }
                }

                const errors = d.errors || [];
                if (this.dom.badgeLogsCount) {
                    if (errors.length > 0) {
                        this.dom.badgeLogsCount.textContent = errors.length;
                        this.dom.badgeLogsCount.style.display = 'flex';
                    } else {
                        this.dom.badgeLogsCount.style.display = 'none';
                    }
                }

                // Modal: Suspend List
                if (this.dom.suspendModalContent) {
                    if (gaps.length === 0) {
                        this.dom.suspendModalContent.innerHTML = `<div style="text-align: center; color: var(--accent-emerald); padding: 1.5rem 0; font-size: 0.85rem;">Normal 🟢 (0 saham suspensi / gap anomali tercatat)</div>`;
                    } else {
                        this.dom.suspendModalContent.innerHTML = gaps.map(g => `
                            <div class="gap-item">
                                <div class="gap-meta">
                                    <span class="gap-ticker">${g.ticker}</span>
                                    <span class="gap-date">Tanggal: ${g.date} • ${g.attempts}x dicoba (${g.last_attempt || '-'})</span>
                                </div>
                                <span class="gap-badge">${g.reason || 'Data Kosong'}</span>
                            </div>
                        `).join('');
                    }
                }

                // Modal: Logs List
                if (this.dom.logsModalContent) {
                    if (errors.length === 0) {
                        this.dom.logsModalContent.innerHTML = `<div style="text-align: center; color: var(--accent-emerald); padding: 1.5rem 0; font-size: 0.85rem;">Normal 🟢 (Tidak ada error dalam 48 jam)</div>`;
                    } else {
                        this.dom.logsModalContent.innerHTML = errors.map(e => {
                            const color = (e.level === 'CRITICAL' || e.level === 'ERROR') ? 'var(--accent-rose)' : 'var(--accent-yellow)';
                            return `
                                <div class="error-item" style="margin-bottom: 10px; padding: 10px; background: rgba(0,0,0,0.3); border-left: 3px solid ${color}; border-radius: 6px;">
                                    <div style="font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px;">[${e.bot_name || 'bot'}] ${e.time || '-'}</div>
                                    <div style="font-size: 0.82rem; color: var(--text-main);">${e.message}</div>
                                </div>
                            `;
                        }).join('');
                    }
                }

                // Simpan metadata kalender dan cache
                this.calendarAvailableMonths = d.available_months || ['2026-09', '2026-08', '2026-07', '2026-06', '2026-05', '2026-04', '2026-03'];
                const activeMonth = d.current_month || this.calendarAvailableMonths[0] || '2026-09';
                this.currentCalMonthStr = activeMonth;
                if (!this.calendarCache) this.calendarCache = {};
                this.calendarCache[activeMonth] = d.history || [];

                // Render Calendar Heatmap
                this.renderSyncCalendar(d.history || [], activeMonth);
            } else {
                throw new Error(json.detail || json.error || `HTTP ${res.status}`);
            }
        } catch (err) {
            console.warn('Gagal memuat status database health:', err);
            if (this.dom.dbEngineStatus) {
                this.dom.dbEngineStatus.textContent = 'DB Terputus';
                this.dom.dbEngineStatus.style.color = '#f87171';
            }
            if (this.dom.dbServerStatus) {
                this.dom.dbServerStatus.textContent = 'Offline';
                this.dom.dbServerStatus.style.color = '#f87171';
                this.dom.dbServerStatus.style.opacity = '1';
            }
            if (this.dom.dbEngineDot) {
                this.dom.dbEngineDot.style.background = '#ef4444';
                this.dom.dbEngineDot.style.boxShadow = '0 0 6px rgba(239, 68, 68, 0.6)';
            }
            if (this.dom.dbLastSyncBadge) {
                this.dom.dbLastSyncBadge.textContent = 'Gagal Konek DB';
                this.dom.dbLastSyncBadge.className = 'status-badge badge-red';
            }
            if (this.dom.dbStatTotalEmiten) this.dom.dbStatTotalEmiten.textContent = 'Error';
            if (this.dom.dbStatActivePrice) this.dom.dbStatActivePrice.textContent = 'Error';
            if (this.dom.dbStatActiveBroksum) this.dom.dbStatActiveBroksum.textContent = 'Error';
            if (this.dom.dbStatDateRange) this.dom.dbStatDateRange.textContent = 'Koneksi database gagal';
            if (this.dom.calendarGrid) {
                this.dom.calendarGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 24px 10px; color: #f87171; font-size: 11px;">
                        ⚠️ Gagal terhubung ke Database Neon.<br>
                        <span style="color: var(--text-muted); font-size: 10px;">${err.message || 'Cek konfigurasi DATABASE_URL di Vercel.'}</span>
                    </div>
                `;
            }
        }
    }

    async navigateCalendarMonth(direction) {
        // direction: -1 (mundur / bulan lampau), +1 (maju / bulan terbaru)
        if (!this.calendarAvailableMonths || this.calendarAvailableMonths.length === 0) return;

        const currentIdx = this.calendarAvailableMonths.indexOf(this.currentCalMonthStr);
        if (currentIdx === -1) return;

        // calendarAvailableMonths diurutkan DESC: index 0 paling baru, index length-1 paling lama
        // direction -1 (mundur ke masa lalu) -> index naik (+1)
        // direction +1 (maju ke masa kini) -> index turun (-1)
        const targetIdx = currentIdx - direction;
        if (targetIdx < 0 || targetIdx >= this.calendarAvailableMonths.length) {
            return; // Di luar jangkauan bulan
        }

        const targetMonth = this.calendarAvailableMonths[targetIdx];
        await this.loadAndRenderCalendarMonth(targetMonth, direction);
    }

    async loadAndRenderCalendarMonth(monthStr, animDirection = 0) {
        if (!monthStr) return;
        this.currentCalMonthStr = monthStr;

        // Update disabled buttons
        const currentIdx = this.calendarAvailableMonths.indexOf(monthStr);
        if (this.dom.btnCalPrev) {
            this.dom.btnCalPrev.disabled = (currentIdx >= this.calendarAvailableMonths.length - 1);
        }
        if (this.dom.btnCalNext) {
            this.dom.btnCalNext.disabled = (currentIdx <= 0);
        }

        // Trigger animasi CSS
        if (this.dom.calendarGrid && animDirection !== 0) {
            this.dom.calendarGrid.classList.remove('cal-anim-left', 'cal-anim-right');
            void this.dom.calendarGrid.offsetWidth; // Force reflow
            if (animDirection > 0) {
                this.dom.calendarGrid.classList.add('cal-anim-left');
            } else {
                this.dom.calendarGrid.classList.add('cal-anim-right');
            }
        }

        // Gunakan cache jika sudah pernah diload
        if (this.calendarCache && this.calendarCache[monthStr]) {
            this.renderSyncCalendar(this.calendarCache[monthStr], monthStr);
            return;
        }

        // Tampilkan indikator loading di grid kalender
        if (this.dom.calendarGrid) {
            this.dom.calendarGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 24px 10px; font-size: 11px; color: var(--text-muted);">
                    <span class="spinner" style="display:inline-block; width:12px; height:12px; margin-right:6px; border:2px solid var(--accent-emerald); border-top-color:transparent; border-radius:50%; animation:spin 0.6s linear infinite; vertical-align:middle;"></span>
                    Memuat riwayat sinkronisasi ${monthStr}...
                </div>
            `;
        }

        try {
            const res = await fetch(`/api/database/calendar?month=${encodeURIComponent(monthStr)}`);
            const json = await res.json();
            if (res.ok && json.status === 'success') {
                if (!this.calendarCache) this.calendarCache = {};
                this.calendarCache[monthStr] = json.history || [];
                this.renderSyncCalendar(json.history || [], monthStr);
            } else {
                throw new Error(json.detail || 'Gagal memuat kalender');
            }
        } catch (err) {
            console.warn(`Gagal memuat data kalender ${monthStr}:`, err);
            if (this.dom.calendarGrid) {
                this.dom.calendarGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 20px; font-size: 11px; color: var(--accent-rose);">
                        ⚠️ Gagal memuat data ${monthStr} (${err.message})
                    </div>
                `;
            }
        }
    }

    renderSyncCalendar(historyData, monthStr = null) {
        if (!this.dom.calendarGrid) return;

        let currentYear, currentMonth;
        if (monthStr && monthStr.includes('-')) {
            const parts = monthStr.split('-');
            currentYear = parseInt(parts[0], 10);
            currentMonth = parseInt(parts[1], 10) - 1; // 0-11
        } else {
            const today = new Date();
            currentYear = today.getFullYear();
            currentMonth = today.getMonth();
        }

        const monthNames = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];

        if (this.dom.calendarMonthTitle) {
            this.dom.calendarMonthTitle.innerText = `${monthNames[currentMonth]} ${currentYear}`;
        }

        // Update nav buttons disabled state
        if (this.calendarAvailableMonths && this.calendarAvailableMonths.length > 0) {
            const activeStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}`;
            const currentIdx = this.calendarAvailableMonths.indexOf(activeStr);
            if (this.dom.btnCalPrev) {
                this.dom.btnCalPrev.disabled = (currentIdx >= this.calendarAvailableMonths.length - 1);
            }
            if (this.dom.btnCalNext) {
                this.dom.btnCalNext.disabled = (currentIdx <= 0);
            }
        }

        const historyMap = {};
        if (historyData) {
            historyData.forEach(item => {
                historyMap[item.date] = item;
            });
        }

        const firstDayDate = new Date(currentYear, currentMonth, 1);
        let firstDayIndex = firstDayDate.getDay() - 1; // 0 = Senin, 6 = Minggu
        if (firstDayIndex === -1) firstDayIndex = 6;

        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        let html = '';

        for (let i = 0; i < firstDayIndex; i++) {
            html += `<div class="cal-box cal-box-empty"></div>`;
        }

        const today = new Date();
        const isCurrentRealMonth = (today.getFullYear() === currentYear && today.getMonth() === currentMonth);

        for (let day = 1; day <= daysInMonth; day++) {
            const monthPadded = String(currentMonth + 1).padStart(2, '0');
            const dayPadded = String(day).padStart(2, '0');
            const dateStr = `${currentYear}-${monthPadded}-${dayPadded}`;

            const hist = historyMap[dateStr];
            let boxClass = 'cal-box-empty';
            let contentHtml = `<div class="cal-stats" style="margin-top: 6px; opacity: 0.35;">-</div>`;

            let idxDotHtml = '';
            if (hist) {
                if (hist.broksum_synced >= hist.target_harvester && hist.broksum_synced > 0) {
                    boxClass = 'cal-box-green';
                } else if (hist.ohlcv_scraped > 0) {
                    boxClass = 'cal-box-red';
                }

                if (hist.idx_official_synced > 0) {
                    idxDotHtml = `<span class="cal-idx-dot" title="IDX Official Synced: ${hist.idx_official_synced} emiten">✓</span>`;
                }

                contentHtml = `
                    <div class="cal-stats">
                        <span>H: <strong>${hist.ohlcv_scraped}</strong></span>
                        <span>B: <strong>${hist.broksum_synced}</strong></span>
                    </div>
                `;
            }

            const isToday = (isCurrentRealMonth && day === today.getDate()) ? 'border: 1px solid var(--accent-emerald);' : '';

            html += `
                <div class="cal-box ${boxClass}" style="${isToday}">
                    ${idxDotHtml}
                    <div class="cal-date">${day}</div>
                    ${contentHtml}
                </div>
            `;
        }

        this.dom.calendarGrid.innerHTML = html;
    }

    async deleteWatchlistItem(itemId, symbol) {
        if (!confirm(`Hapus ${symbol} dari Watchlist?`)) return;

        try {
            const res = await fetch(`/api/watchlist/${itemId}`, { method: 'DELETE' });
            const json = await res.json();
            if (res.ok && json.success) {
                this.showToast(`🗑️ ${symbol} dihapus dari Watchlist`, 'info');
                this.watchlistItems = this.watchlistItems.filter(i => i.id !== itemId);
                const cleanSym = (symbol || '').toUpperCase().trim();
                const stillHasSymbol = this.watchlistItems.some(i => (i.symbol || '').toUpperCase().trim() === cleanSym);
                if (!stillHasSymbol && this.allWatchlistSymbols) {
                    this.allWatchlistSymbols.delete(cleanSym);
                }
                this.renderWatchlist();
                this.checkWatchlistStatus(this.currentSymbol);
            } else {
                throw new Error(json.detail || 'Gagal menghapus');
            }
        } catch (err) {
            this.showToast(`Gagal: ${err.message}`, 'error');
        }
    }

    // ── Risk & Settings Methods ──

    async fetchRiskSettings() {
        try {
            const res = await fetch('/api/settings/risk');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            if (json.success && json.data) {
                this.riskSettings = json.data;
                this.populateSettingsFields();
            }
        } catch (err) {
            console.warn('Gagal memuat risk settings:', err);
        }
    }

    populateSettingsFields() {
        const capital = this.riskSettings?.total_capital || 100000000;
        const riskPct = this.riskSettings?.risk_pct || 1.0;
        const defaultCat = this.riskSettings?.default_category || 'Breakout';
        const source = this.riskSettings?.daily_source || 'neon_db';

        // Settings View inputs
        if (this.dom.settingInputCapital) this.dom.settingInputCapital.value = capital;
        if (this.dom.settingSliderPct) this.dom.settingSliderPct.value = riskPct;
        if (this.dom.settingPctBadge) this.dom.settingPctBadge.textContent = `${riskPct.toFixed(2)}%`;
        if (this.dom.settingSelectCategory) this.dom.settingSelectCategory.value = defaultCat;
        if (source === 'yahoo') {
            if (this.dom.radioSourceYahoo) this.dom.radioSourceYahoo.checked = true;
        } else {
            if (this.dom.radioSourceNeon) this.dom.radioSourceNeon.checked = true;
        }
        this.updateSettingsCalculations();

        // Quick Risk Modal inputs
        if (this.dom.riskInputCapital) this.dom.riskInputCapital.value = capital;
        if (this.dom.riskSliderPct) this.dom.riskSliderPct.value = riskPct;
        if (this.dom.riskPctBadge) this.dom.riskPctBadge.textContent = `${riskPct.toFixed(2)}%`;
        if (this.dom.riskSelectCategory) this.dom.riskSelectCategory.value = defaultCat;
        this.updateRiskCalculations();
    }

    async saveAllSettings() {
        const rawCapital = this.dom.settingInputCapital ? this.dom.settingInputCapital.value : '100000000';
        const capital = parseFloat(String(rawCapital).replace(/[^0-9.]/g, '')) || 0;
        const pct = this.dom.settingSliderPct ? parseFloat(this.dom.settingSliderPct.value) || 1.0 : 1.0;
        const category = this.dom.settingSelectCategory?.value || this.riskSettings?.default_category || 'Breakout';
        const source = this.dom.radioSourceYahoo && this.dom.radioSourceYahoo.checked ? 'yahoo' : 'neon_db';

        if (capital <= 0) {
            this.showToast('Total modal harus lebih besar dari 0!', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/settings/risk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    total_capital: capital,
                    risk_pct: pct,
                    default_category: category,
                    daily_source: source
                })
            });
            const json = await res.json();
            if (res.ok && json.success) {
                this.riskSettings = json.data;
                this.populateSettingsFields();
                this.updateDatabaseOverview();
                this.showToast('Pengaturan feed & risiko berhasil disimpan! ⚙️', 'info');
                // Flag chart refresh for when user switches back to chart view
                this._needChartRefresh = true;
            } else {
                const errMsg = Array.isArray(json.detail) 
                    ? json.detail.map(d => d.msg || JSON.stringify(d)).join(', ') 
                    : (json.detail || 'Gagal menyimpan settings');
                throw new Error(errMsg);
            }
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    openRiskModal() {
        if (!this.dom.riskModal || !this.dom.riskModalBackdrop) return;
        this.populateSettingsFields();
        this.dom.riskModalBackdrop.classList.remove('hidden');
        this.dom.riskModal.classList.remove('hidden');
    }

    closeRiskModal() {
        if (this.dom.riskModal) this.dom.riskModal.classList.add('hidden');
        if (this.dom.riskModalBackdrop) this.dom.riskModalBackdrop.classList.add('hidden');
    }

    updateRiskCalculations() {
        const capital = this.dom.riskInputCapital ? parseFloat(this.dom.riskInputCapital.value) || 0 : 0;
        const pct = this.dom.riskSliderPct ? parseFloat(this.dom.riskSliderPct.value) || 1.0 : 1.0;
        const nominal = Math.round(capital * (pct / 100.0));

        if (this.dom.riskCapitalHint) {
            this.dom.riskCapitalHint.textContent = `Rp ${Number(capital).toLocaleString('id-ID')}`;
        }
        if (this.dom.riskPreviewNominal) {
            this.dom.riskPreviewNominal.textContent = `Rp ${Number(nominal).toLocaleString('id-ID')}`;
        }
    }

    updateSettingsCalculations() {
        const capital = this.dom.settingInputCapital ? parseFloat(this.dom.settingInputCapital.value) || 0 : 0;
        const pct = this.dom.settingSliderPct ? parseFloat(this.dom.settingSliderPct.value) || 1.0 : 1.0;
        const nominal = Math.round(capital * (pct / 100.0));

        if (this.dom.settingCapitalHint) {
            this.dom.settingCapitalHint.textContent = `Rp ${Number(capital).toLocaleString('id-ID')}`;
        }
        if (this.dom.settingPreviewNominal) {
            this.dom.settingPreviewNominal.textContent = `Rp ${Number(nominal).toLocaleString('id-ID')}`;
        }
    }

    async submitRiskSettings() {
        const rawCapital = this.dom.riskInputCapital ? this.dom.riskInputCapital.value : '100000000';
        const capital = parseFloat(String(rawCapital).replace(/[^0-9.]/g, '')) || 0;
        const pct = this.dom.riskSliderPct ? parseFloat(this.dom.riskSliderPct.value) || 1.0 : 1.0;
        const category = this.dom.riskSelectCategory?.value || this.riskSettings?.default_category || 'Breakout';
        const source = this.riskSettings?.daily_source || 'neon_db';

        if (capital <= 0) {
            this.showToast('Total modal harus lebih besar dari 0!', 'warning');
            return;
        }

        try {
            const res = await fetch('/api/settings/risk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    total_capital: capital,
                    risk_pct: pct,
                    default_category: category,
                    daily_source: source
                })
            });
            const json = await res.json();
            if (res.ok && json.success) {
                this.riskSettings = json.data;
                this.populateSettingsFields();
                this.updateDatabaseOverview();
                this.closeRiskModal();
                this.showToast('Pengaturan modal & risiko berhasil disimpan! ⚙️', 'info');
            } else {
                const errMsg = Array.isArray(json.detail) 
                    ? json.detail.map(d => d.msg || JSON.stringify(d)).join(', ') 
                    : (json.detail || 'Gagal menyimpan settings');
                throw new Error(errMsg);
            }
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    // ── Dynamic Documentation Methods ──

    async fetchAndRenderSettingsDocs() {
        const container = document.getElementById('settings-docs-list');
        if (!container) return;

        try {
            const res = await fetch('/api/docs');
            const data = await res.json();
            if (data.success && Array.isArray(data.docs) && data.docs.length > 0) {
                const html = data.docs.map((doc, idx) => `
                    <button class="settings-action-tile btn-doc-item" type="button" ${idx === 0 ? 'id="btn-open-doc-modal"' : ''} data-slug="${escapeHtml(doc.slug)}" data-title="${escapeHtml(doc.title)}" data-subtitle="${escapeHtml(doc.subtitle || '')}" data-icon="${escapeHtml(doc.icon || '📖')}" title="Buka ${escapeHtml(doc.title)}">
                        <div class="action-tile-left">
                            <span class="action-tile-icon">${escapeHtml(doc.icon || '📖')}</span>
                            <div class="action-tile-text">
                                <div class="action-tile-title">${escapeHtml(doc.title)}</div>
                                <div class="action-tile-sub">${escapeHtml(doc.subtitle || '')}</div>
                            </div>
                        </div>
                        <span class="action-tile-arrow">›</span>
                    </button>
                `).join('');
                container.innerHTML = html;

                container.querySelectorAll('.btn-doc-item').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const target = e.currentTarget;
                        const slug = target.dataset.slug;
                        const title = target.dataset.title;
                        const subtitle = target.dataset.subtitle;
                        const icon = target.dataset.icon;
                        this.openDocModal(slug, title, subtitle, icon);
                    });
                });
            }
        } catch (err) {
            console.warn('Gagal memuat daftar dokumen panduan:', err);
        }
    }

    async openDocModal(slug = 'bandarmology', title = 'Kitab Pre-Breakout & Bandarmology', subtitle = 'Dokumentasi Resmi Candlify', icon = '📖') {
        const docModal = document.getElementById('doc-reader-modal');
        const docContent = document.getElementById('doc-reader-content');
        const docModalTitle = document.getElementById('doc-modal-title');
        const docModalSub = document.getElementById('doc-modal-subtitle');
        const docModalIcon = document.getElementById('doc-modal-icon');

        if (!docModal || !docContent) return;

        docModal.classList.remove('hidden');
        if (docModalTitle) docModalTitle.textContent = title;
        if (docModalSub) docModalSub.textContent = subtitle;
        if (docModalIcon) docModalIcon.textContent = icon;

        docContent.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                <div style="font-size: 24px; margin-bottom: 10px;">⏳</div>
                Memuat dokumen panduan...
            </div>
        `;

        try {
            const url = (slug === 'bandarmology' || slug === 'bandarmology_pre_breakout') ? '/api/docs/bandarmology' : `/api/docs/${encodeURIComponent(slug)}`;
            const res = await fetch(url);
            const data = await res.json();
            if (data.success && data.markdown) {
                if (data.title && docModalTitle) docModalTitle.textContent = data.title;
                if (data.icon && docModalIcon) docModalIcon.textContent = data.icon;
                if (window.marked && typeof window.marked.parse === 'function') {
                    docContent.innerHTML = window.marked.parse(data.markdown);
                } else {
                    docContent.innerHTML = `<pre style="white-space: pre-wrap; color:#e2e8f0;">${escapeHtml(data.markdown)}</pre>`;
                }
                docContent.scrollTop = 0;
            } else {
                docContent.innerHTML = '<div style="color:#f87171; padding:20px;">Gagal memuat dokumen panduan.</div>';
            }
        } catch (e) {
            docContent.innerHTML = `<div style="color:#f87171; padding:20px;">Gagal mengambil dokumen: ${e.message}</div>`;
        }
    }

    // ── Journal & Trading Plan Methods ──

    setupJournalEvents() {
        // 1. Open Plan Modal Buttons (from header and empty state)
        if (this.dom.btnOpenCreatePlan) {
            this.dom.btnOpenCreatePlan.addEventListener('click', () => {
                this.openPlanModal();
            });
        }
        if (this.dom.btnEmptyCreatePlan) {
            this.dom.btnEmptyCreatePlan.addEventListener('click', () => {
                this.openPlanModal();
            });
        }

        // 2. Status Filter Chips
        if (this.dom.journalFilterChips) {
            this.dom.journalFilterChips.forEach(chip => {
                chip.addEventListener('click', (e) => {
                    this.dom.journalFilterChips.forEach(c => c.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                    this.activePlanFilter = e.currentTarget.dataset.status || 'ALL';
                    this.renderTradingPlans();
                });
            });
        }

        // 3. Plan Modal Dialog Controls
        if (this.dom.closePlanModal) {
            this.dom.closePlanModal.addEventListener('click', () => this.closePlanModal());
        }
        if (this.dom.btnCancelPlan) {
            this.dom.btnCancelPlan.addEventListener('click', () => this.closePlanModal());
        }
        if (this.dom.planModalBackdrop) {
            this.dom.planModalBackdrop.addEventListener('click', () => this.closePlanModal());
        }
        if (this.dom.btnSubmitPlan) {
            this.dom.btnSubmitPlan.addEventListener('click', () => this.submitPlanForm());
        }

        if (this.dom.planInputSymbol) {
            this.dom.planInputSymbol.addEventListener('input', (e) => {
                e.target.value = e.target.value.toUpperCase();
            });
        }

        // Live Position Sizing Calculation on Price / Lot inputs
        ['planInputEntry', 'planInputSl', 'planInputTp1'].forEach(key => {
            if (this.dom[key]) {
                this.dom[key].addEventListener('input', () => {
                    this.calculatePositionSizing(!this._userEditedLot);
                });
            }
        });

        if (this.dom.planInputLot) {
            this.dom.planInputLot.addEventListener('input', () => {
                this._userEditedLot = true;
                this.calculatePositionSizing(false);
            });
        }

        if (this.dom.planCalcSettingHint) {
            this.dom.planCalcSettingHint.addEventListener('click', (e) => {
                const btnApply = e.target.closest('#btn-apply-rec-lot');
                if (btnApply && this._recommendedLot && this._recommendedLot > 0) {
                    if (this.dom.planInputLot) this.dom.planInputLot.value = this._recommendedLot;
                    this._userEditedLot = true;
                    this.calculatePositionSizing(false);
                }
            });
        }

        // 4. Trailing Stop Modal Dialog Controls
        if (this.dom.closeTrailingModal) {
            this.dom.closeTrailingModal.addEventListener('click', () => this.closeTrailingModal());
        }
        if (this.dom.btnCancelTrailing) {
            this.dom.btnCancelTrailing.addEventListener('click', () => this.closeTrailingModal());
        }
        if (this.dom.trailingModalBackdrop) {
            this.dom.trailingModalBackdrop.addEventListener('click', () => this.closeTrailingModal());
        }
        if (this.dom.btnSubmitTrailing) {
            this.dom.btnSubmitTrailing.addEventListener('click', () => this.submitTrailingStop());
        }

        // 5. Exit / Close Position Modal Dialog Controls
        if (this.dom.closeExitModal) {
            this.dom.closeExitModal.addEventListener('click', () => this.closeExitModal());
        }
        if (this.dom.btnCancelExit) {
            this.dom.btnCancelExit.addEventListener('click', () => this.closeExitModal());
        }
        if (this.dom.exitModalBackdrop) {
            this.dom.exitModalBackdrop.addEventListener('click', () => this.closeExitModal());
        }
        if (this.dom.btnSubmitExit) {
            this.dom.btnSubmitExit.addEventListener('click', () => this.submitExitPosition());
        }
        if (this.dom.exitInputPrice) {
            this.dom.exitInputPrice.addEventListener('input', () => this.updateExitPnlPreview());
        }
        if (this.dom.exitSelectStatus) {
            this.dom.exitSelectStatus.addEventListener('change', () => this.updateExitPnlPreview());
        }

        // 6. Journal List Card Click Delegation
        if (this.dom.journalList) {
            this.dom.journalList.addEventListener('click', (e) => {
                // One-click Match to Holding
                const btnMatch = e.target.closest('.btn-plan-match');
                if (btnMatch) {
                    e.stopPropagation();
                    const planId = parseInt(btnMatch.dataset.id, 10);
                    this.quickMatchPlan(planId);
                    return;
                }

                // Trailing Stop button
                const btnTrailing = e.target.closest('.btn-plan-trailing');
                if (btnTrailing) {
                    e.stopPropagation();
                    const planId = parseInt(btnTrailing.dataset.id, 10);
                    const plan = (this.tradingPlans || []).find(p => p.id === planId);
                    if (plan) this.openTrailingModal(plan);
                    return;
                }

                // Exit / Bukukan button
                const btnExit = e.target.closest('.btn-plan-exit');
                if (btnExit) {
                    e.stopPropagation();
                    const planId = parseInt(btnExit.dataset.id, 10);
                    const plan = (this.tradingPlans || []).find(p => p.id === planId);
                    if (plan) this.openExitModal(plan);
                    return;
                }

                // Edit Plan button
                const btnEdit = e.target.closest('.btn-plan-edit');
                if (btnEdit) {
                    e.stopPropagation();
                    const planId = parseInt(btnEdit.dataset.id, 10);
                    const plan = (this.tradingPlans || []).find(p => p.id === planId);
                    if (plan) this.openPlanModal(plan);
                    return;
                }

                // Delete Plan button
                const btnDelete = e.target.closest('.btn-plan-delete');
                if (btnDelete) {
                    e.stopPropagation();
                    const planId = parseInt(btnDelete.dataset.id, 10);
                    const sym = btnDelete.dataset.symbol || '';
                    this.confirmDeletePlan(planId, sym);
                    return;
                }

                // Chart Jump button
                const btnChart = e.target.closest('.btn-plan-chart');
                if (btnChart) {
                    e.stopPropagation();
                    const sym = btnChart.dataset.symbol;
                    if (sym) this.openChartFromPlan(sym);
                    return;
                }

                // Clicking anywhere on card opens chart
                const card = e.target.closest('.plan-card');
                if (card && card.dataset.symbol) {
                    this.openChartFromPlan(card.dataset.symbol);
                }
            });
        }
    }

    getStockInfo(symbol) {
        if (!symbol) return null;
        const clean = symbol.toUpperCase().trim();
        return (this.screenerStocks || []).find(s => s.symbol === clean) || null;
    }

    formatPlanDate(dateStr) {
        if (!dateStr) return '--';
        try {
            const d = new Date(dateStr);
            if (isNaN(d.getTime())) return String(dateStr);
            return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
        } catch (e) {
            return String(dateStr);
        }
    }

    async fetchTradingPlans(filterStatus = null) {
        try {
            const url = filterStatus && filterStatus !== 'ALL' && filterStatus !== 'TP_HIT' && filterStatus !== 'CLOSED'
                ? `/api/trading-plans?status=${encodeURIComponent(filterStatus)}`
                : '/api/trading-plans';

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            if (json.success && Array.isArray(json.data)) {
                this.tradingPlans = json.data;
                this.updateJournalStatsUI();
                this.renderTradingPlans();
            }
        } catch (err) {
            console.warn('Gagal memuat trading plans:', err);
        }
    }

    updateJournalStatsUI() {
        const plans = this.tradingPlans || [];
        const holdingPlans = plans.filter(p => p.status === 'HOLDING');
        const antriPlans = plans.filter(p => p.status === 'ANTRI');
        const closedWins = plans.filter(p => p.status === 'CLOSED_WIN');
        const closedLosses = plans.filter(p => p.status === 'CLOSED_LOSS');
        const closedTotal = closedWins.length + closedLosses.length;

        // Holding Count & Invested
        const holdingCount = holdingPlans.length;
        let holdingInvested = 0;
        let totalUnrealized = 0;
        let tpSignalsCount = 0;

        holdingPlans.forEach(p => {
            const entry = Number(p.entry_price) || 0;
            const lots = Number(p.lot_size) || 0;
            const invested = entry * lots * 100;
            holdingInvested += invested;

            const stock = this.getStockInfo(p.symbol);
            const livePrice = stock && stock.price ? Number(stock.price) : entry;
            const pnl = (livePrice - entry) * lots * 100;
            totalUnrealized += pnl;

            if (p.tp1_price && livePrice >= Number(p.tp1_price)) {
                tpSignalsCount++;
            }
        });

        // Realized PnL
        let totalRealized = 0;
        plans.filter(p => p.status === 'CLOSED_WIN' || p.status === 'CLOSED_LOSS').forEach(p => {
            if (typeof p.realized_pnl === 'number') {
                totalRealized += p.realized_pnl;
            } else if (p.exit_price && p.entry_price && p.lot_size) {
                totalRealized += (p.exit_price - p.entry_price) * p.lot_size * 100;
            }
        });

        const winRate = closedTotal > 0 ? (closedWins.length / closedTotal) * 100 : 0;

        // Update DOM elements
        if (this.dom.statHoldingCount) this.dom.statHoldingCount.textContent = holdingCount;
        if (this.dom.statHoldingInvested) this.dom.statHoldingInvested.textContent = `Rp ${Math.round(holdingInvested).toLocaleString('id-ID')}`;

        if (this.dom.statUnrealizedPnl) {
            const sign = totalUnrealized >= 0 ? '+' : '';
            this.dom.statUnrealizedPnl.textContent = `${sign}Rp ${Math.abs(Math.round(totalUnrealized)).toLocaleString('id-ID')}`;
            this.dom.statUnrealizedPnl.className = `j-stat-val ${totalUnrealized >= 0 ? 'green' : 'red'}`;
        }
        if (this.dom.statTpSignals) {
            this.dom.statTpSignals.textContent = `${tpSignalsCount} Hit`;
            this.dom.statTpSignals.className = tpSignalsCount > 0 ? 'green font-bold' : '';
        }

        if (this.dom.statAntriCount) this.dom.statAntriCount.textContent = antriPlans.length;

        if (this.dom.statWinRate) {
            this.dom.statWinRate.textContent = `${winRate.toFixed(0)}%`;
            if (closedTotal > 0) {
                this.dom.statWinRate.title = `${closedWins.length} Win / ${closedLosses.length} Loss (${closedTotal} Selesai)`;
            }
        }
        if (this.dom.statRealizedPnl) {
            const sign = totalRealized >= 0 ? '+' : '';
            this.dom.statRealizedPnl.textContent = `${sign}Rp ${Math.abs(Math.round(totalRealized)).toLocaleString('id-ID')}`;
            this.dom.statRealizedPnl.className = totalRealized >= 0 ? 'green' : 'red';
        }

        if (this.dom.journalCountBadge) {
            this.dom.journalCountBadge.textContent = `${plans.length} Posisi`;
        }
    }

    renderTradingPlans() {
        if (!this.dom.journalList) return;

        const allPlans = this.tradingPlans || [];
        let filtered = allPlans;

        if (this.activePlanFilter === 'HOLDING') {
            filtered = allPlans.filter(p => p.status === 'HOLDING');
        } else if (this.activePlanFilter === 'ANTRI') {
            filtered = allPlans.filter(p => p.status === 'ANTRI');
        } else if (this.activePlanFilter === 'TP_HIT') {
            filtered = allPlans.filter(p => {
                if (p.status !== 'HOLDING') return false;
                const stock = this.getStockInfo(p.symbol);
                const livePrice = stock && stock.price ? stock.price : p.entry_price;
                return p.tp1_price && livePrice >= p.tp1_price;
            });
        } else if (this.activePlanFilter === 'CLOSED') {
            filtered = allPlans.filter(p => p.status === 'CLOSED_WIN' || p.status === 'CLOSED_LOSS');
        }

        if (filtered.length === 0) {
            if (this.dom.journalEmpty) this.dom.journalEmpty.classList.remove('hidden');
            this.dom.journalList.innerHTML = '';
            return;
        }

        if (this.dom.journalEmpty) this.dom.journalEmpty.classList.add('hidden');

        const escapeHtml = (str) => {
            if (!str) return '';
            return String(str).replace(/[&<>"']/g, (m) => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            }[m]));
        };

        const html = filtered.map(plan => {
            const sym = plan.symbol;
            const stock = this.getStockInfo(sym);
            const livePrice = stock && stock.price ? Number(stock.price) : Number(plan.entry_price);
            const entry = Number(plan.entry_price) || 0;
            const sl = Number(plan.sl_price) || 0;
            const tp1 = Number(plan.tp1_price) || 0;
            const lots = Number(plan.lot_size) || 1;
            const invested = entry * lots * 100;

            const isHolding = plan.status === 'HOLDING';
            const isAntri = plan.status === 'ANTRI';
            const isClosedWin = plan.status === 'CLOSED_WIN';
            const isClosedLoss = plan.status === 'CLOSED_LOSS';
            const isClosed = isClosedWin || isClosedLoss;

            // Signals for holding
            const isTpHit = isHolding && tp1 > 0 && livePrice >= tp1;
            const isSlHit = isHolding && sl > 0 && livePrice <= sl;
            const isNearSl = isHolding && sl > 0 && !isSlHit && livePrice <= sl * 1.02;

            // PnL calculation
            let pnlRp = 0;
            let pnlPct = 0;
            if (isHolding) {
                pnlRp = (livePrice - entry) * lots * 100;
                pnlPct = entry > 0 ? ((livePrice - entry) / entry) * 100 : 0;
            } else if (isClosed) {
                if (typeof plan.realized_pnl === 'number') {
                    pnlRp = plan.realized_pnl;
                    pnlPct = plan.realized_pnl_pct || (entry > 0 ? (pnlRp / invested) * 100 : 0);
                } else {
                    const exit = Number(plan.exit_price) || entry;
                    pnlRp = (exit - entry) * lots * 100;
                    pnlPct = entry > 0 ? ((exit - entry) / entry) * 100 : 0;
                }
            }

            const pnlSign = pnlRp >= 0 ? '+' : '';
            const pnlColorClass = pnlRp >= 0 ? 'green' : 'red';

            // Progress Bar between SL and TP1
            let progressPct = 50;
            let progressColor = 'green';
            if (tp1 > sl) {
                progressPct = Math.min(100, Math.max(0, ((livePrice - sl) / (tp1 - sl)) * 100));
                progressColor = livePrice >= entry ? 'green' : 'red';
            }

            // Status Badge
            let statusBadgeHtml = '';
            if (isHolding) {
                statusBadgeHtml = `<span class="plan-status-badge holding">🚀 Holding</span>`;
            } else if (isAntri) {
                statusBadgeHtml = `<span class="plan-status-badge antri">📋 Antri Limit</span>`;
            } else if (isClosedWin) {
                statusBadgeHtml = `<span class="plan-status-badge closed_win">🎯 TP Win</span>`;
            } else if (isClosedLoss) {
                statusBadgeHtml = `<span class="plan-status-badge closed_loss">🛑 Cut Loss</span>`;
            }

            const dateStr = plan.entry_date ? this.formatPlanDate(plan.entry_date) : this.formatPlanDate(plan.created_at);

            return `
                <div class="plan-card ${isTpHit ? 'tp-hit' : ''} ${isNearSl ? 'near-sl' : ''}" data-id="${plan.id}" data-symbol="${sym}">
                    <!-- Card Top Header -->
                    <div class="plan-card-hdr">
                        <div class="plan-hdr-left">
                            <img src="https://assets.stockbit.com/logos/companies/${sym}.png" 
                                 alt="${sym}" 
                                 class="plan-logo" 
                                 loading="lazy" 
                                 onerror="this.style.display='none'">
                            <div class="plan-sym-box">
                                <span class="plan-sym">${sym}</span>
                                <span class="plan-cat-badge">${escapeHtml(plan.category || 'Breakout')}</span>
                            </div>
                        </div>
                        <div class="plan-hdr-right">
                            <span class="subtle-age-badge" title="Tanggal Posisi">${dateStr}</span>
                            ${statusBadgeHtml}
                        </div>
                    </div>

                    ${isTpHit ? `
                    <div class="plan-tpHit-banner">
                        <span>🎯 TP1 HIT! Level Rp ${tp1.toLocaleString('id-ID')} Tercapai</span>
                        <span class="action-hint">Amankan profit atau naikkan SL</span>
                    </div>` : ''}

                    ${isSlHit ? `
                    <div class="plan-tpHit-banner" style="background: rgba(239, 68, 68, 0.22); border-color: #ef4444; color: #f87171;">
                        <span>🛑 STOP LOSS HIT! Level Rp ${sl.toLocaleString('id-ID')} Tertembus</span>
                        <span class="action-hint">Disiplin cut loss sesuai plan</span>
                    </div>` : ''}

                    ${isNearSl ? `
                    <div class="plan-tpHit-banner" style="background: rgba(245, 158, 11, 0.18); border-color: rgba(245, 158, 11, 0.45); color: #fbbf24;">
                        <span>⚠️ Waspada Dekat Stop Loss (Rp ${sl.toLocaleString('id-ID')})</span>
                        <span class="action-hint">Ketat pantau harga</span>
                    </div>` : ''}

                    <!-- PnL & Lot Strip -->
                    <div class="plan-pnl-row">
                        <div class="plan-pnl-left">
                            <span class="plan-pnl-label">${isClosed ? 'Realized PnL:' : 'Floating PnL:'}</span>
                            <span class="plan-pnl-val ${pnlColorClass}">
                                ${isAntri ? 'Siap Antri Order' : `${pnlSign}Rp ${Math.abs(Math.round(pnlRp)).toLocaleString('id-ID')} (${pnlSign}${pnlPct.toFixed(2)}%)`}
                            </span>
                        </div>
                        <div class="plan-lot-info">
                            <strong>${lots} Lot</strong> (Rp ${Math.round(invested).toLocaleString('id-ID')})
                        </div>
                    </div>

                    ${!isClosed && tp1 > sl ? `
                    <!-- Visual Progress Bar between SL and TP1 -->
                    <div class="plan-progress-track" title="Posisi Harga Saat Ini terhadap SL dan TP1">
                        <div class="plan-progress-bar ${progressColor}" style="width: ${progressPct.toFixed(1)}%;"></div>
                    </div>` : ''}

                    <!-- Metrics Levels Grid -->
                    <div class="plan-metrics-grid">
                        <div class="plan-metric-col">
                            <span class="plan-m-label">Entry Price</span>
                            <span class="plan-m-val entry">Rp ${entry.toLocaleString('id-ID')}</span>
                        </div>
                        <div class="plan-metric-col">
                            <span class="plan-m-label">${isClosed ? 'Harga Exit' : 'Realtime'}</span>
                            <span class="plan-m-val ${isClosed ? 'gold' : 'live'}">
                                Rp ${Number(isClosed ? (plan.exit_price || livePrice) : livePrice).toLocaleString('id-ID')}
                            </span>
                        </div>
                        <div class="plan-metric-col">
                            <span class="plan-m-label">Stop Loss</span>
                            <span class="plan-m-val sl">Rp ${sl.toLocaleString('id-ID')}</span>
                        </div>
                        <div class="plan-metric-col">
                            <span class="plan-m-label">Target TP1</span>
                            <span class="plan-m-val tp">Rp ${tp1.toLocaleString('id-ID')}</span>
                        </div>
                    </div>

                    ${plan.notes ? `
                    <div class="plan-notes-box">
                        ${escapeHtml(plan.notes)}
                    </div>` : ''}

                    <!-- Actions Footer -->
                    <div class="plan-actions-footer">
                        ${isHolding ? `
                            <button class="plan-action-btn trailing-btn btn-plan-trailing" data-id="${plan.id}" title="Naikkan Stop Loss untuk kunci profit">
                                🛡️ Trailing SL
                            </button>
                            <button class="plan-action-btn exit-btn btn-plan-exit" data-id="${plan.id}" title="Bukukan posisi ke Jurnal Trading">
                                🏁 Bukukan / Exit
                            </button>
                            <button class="plan-action-btn btn-plan-edit" data-id="${plan.id}" title="Edit Plan">
                                ✏️ Edit
                            </button>
                            <button class="plan-action-btn danger btn-plan-delete" data-id="${plan.id}" data-symbol="${sym}" title="Hapus Plan">
                                🗑️ Hapus
                            </button>
                        ` : ''}

                        ${isAntri ? `
                            <button class="plan-action-btn match-btn btn-plan-match" data-id="${plan.id}" title="Tandai order sudah match di broker">
                                ✅ Match (Jadi Holding)
                            </button>
                            <button class="plan-action-btn btn-plan-edit" data-id="${plan.id}" title="Edit Plan">
                                ✏️ Edit
                            </button>
                            <button class="plan-action-btn danger btn-plan-delete" data-id="${plan.id}" data-symbol="${sym}" title="Hapus Plan">
                                🗑️ Hapus
                            </button>
                        ` : ''}

                        ${isClosed ? `
                            <button class="plan-action-btn danger btn-plan-delete" data-id="${plan.id}" data-symbol="${sym}" title="Hapus dari Jurnal">
                                🗑️ Hapus
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.dom.journalList.innerHTML = html;
    }

    openPlanModal(prefill = null) {
        if (!this.dom.planModal || !this.dom.planModalBackdrop) return;

        const isEdit = Boolean(prefill && prefill.id);
        if (this.dom.planModalId) this.dom.planModalId.value = isEdit ? prefill.id : '';

        if (this.dom.planModalTitle) {
            this.dom.planModalTitle.textContent = isEdit ? `✏️ Edit Trading Plan — ${prefill.symbol}` : '🎯 Buat Trading Plan Baru';
        }
        if (this.dom.btnSubmitPlan) {
            this.dom.btnSubmitPlan.textContent = isEdit ? 'Simpan Perubahan' : 'Simpan Trading Plan';
        }

        const sym = prefill?.symbol || (this.currentView === 'chart' ? this.currentSymbol : '');
        if (this.dom.planInputSymbol) {
            this.dom.planInputSymbol.value = (sym || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
            this.dom.planInputSymbol.readOnly = isEdit;
        }

        if (this.dom.planSelectCategory) {
            this.dom.planSelectCategory.value = prefill?.category || this.riskSettings.default_category || 'Breakout';
        }

        if (this.dom.planSelectStatus) {
            this.dom.planSelectStatus.value = prefill?.status || 'ANTRI';
        }

        if (this.dom.planSelectOrderType) {
            this.dom.planSelectOrderType.value = prefill?.order_type || 'LIMIT';
        }

        // Live stock price lookup as default entry
        const stock = this.getStockInfo(sym);
        const livePrice = stock ? stock.price : null;

        const entryVal = prefill?.entry_price || livePrice || '';
        if (this.dom.planInputEntry) this.dom.planInputEntry.value = entryVal;

        // Auto default SL & TP1 if not provided
        if (this.dom.planInputSl) {
            if (prefill?.sl_price) {
                this.dom.planInputSl.value = prefill.sl_price;
            } else if (entryVal) {
                // Default SL: 3% below entry
                this.dom.planInputSl.value = Math.round(Number(entryVal) * 0.97);
            } else {
                this.dom.planInputSl.value = '';
            }
        }

        if (this.dom.planInputTp1) {
            if (prefill?.tp1_price) {
                this.dom.planInputTp1.value = prefill.tp1_price;
            } else if (entryVal) {
                // Default TP1: 6% above entry (R:R 1:2)
                this.dom.planInputTp1.value = Math.round(Number(entryVal) * 1.06);
            } else {
                this.dom.planInputTp1.value = '';
            }
        }

        if (isEdit || (prefill && prefill.lot_size)) {
            this._userEditedLot = true;
            if (this.dom.planInputLot) {
                this.dom.planInputLot.value = prefill?.lot_size || 1;
            }
        } else {
            this._userEditedLot = false;
            if (this.dom.planInputLot) {
                this.dom.planInputLot.value = '';
            }
        }

        if (this.dom.planInputNotes) {
            this.dom.planInputNotes.value = prefill?.notes || '';
        }

        this.calculatePositionSizing(!this._userEditedLot);

        this.dom.planModalBackdrop.classList.remove('hidden');
        this.dom.planModal.classList.remove('hidden');

        if (!isEdit && !sym && this.dom.planInputSymbol) {
            setTimeout(() => this.dom.planInputSymbol.focus(), 80);
        }
    }

    closePlanModal() {
        if (this.dom.planModal) this.dom.planModal.classList.add('hidden');
        if (this.dom.planModalBackdrop) this.dom.planModalBackdrop.classList.add('hidden');
    }

    calculatePositionSizing(autoRecalcLot = true) {
        const capital = Number(this.riskSettings?.total_capital) || 100000000;
        const riskPct = Number(this.riskSettings?.risk_pct) || 1.0;
        const maxRiskRp = Number(this.riskSettings?.risk_nominal) || Math.round(capital * (riskPct / 100.0));
        const capFmt = (capital / 1000000).toFixed(0) + 'jt';

        const entry = parseFloat(this.dom.planInputEntry?.value) || 0;
        const sl = parseFloat(this.dom.planInputSl?.value) || 0;
        const tp1 = parseFloat(this.dom.planInputTp1?.value) || 0;

        if (entry <= 0 || sl <= 0 || sl >= entry) {
            if (this.dom.planCalcSettingHint) {
                this.dom.planCalcSettingHint.textContent = `Modal Rp ${capFmt} (Max Risk ${riskPct.toFixed(1)}% = Rp ${Number(maxRiskRp).toLocaleString('id-ID')})`;
            }
            if (this.dom.planCalcInvested) this.dom.planCalcInvested.textContent = 'Rp --';
            if (this.dom.planCalcRr) this.dom.planCalcRr.textContent = '--';
            if (this.dom.planCalcRiskRp) this.dom.planCalcRiskRp.textContent = 'SL harus < Entry';
            if (this.dom.planCalcRewardRp) this.dom.planCalcRewardRp.textContent = 'TP1 harus > Entry';
            return;
        }

        const riskPerShare = entry - sl;
        const riskPerLot = riskPerShare * 100;
        const recLots = riskPerLot > 0 ? Math.max(1, Math.floor(maxRiskRp / riskPerLot)) : 1;
        this._recommendedLot = recLots;

        if (this.dom.planCalcSettingHint) {
            const symInput = (this.dom.planInputSymbol?.value || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
            const activeSym = (this.currentSymbol || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
            const hmbVal = (symInput && symInput === activeSym) ? Number(this.bandarData?.summary?.latest_hmb || 0) : 0;
            const hmbHint = hmbVal > 0 ? ` • HMB: <strong>Rp ${Math.round(hmbVal).toLocaleString('id-ID')}</strong>` : '';
            this.dom.planCalcSettingHint.innerHTML = `Risk ${riskPct.toFixed(1)}%: Rp ${Number(maxRiskRp).toLocaleString('id-ID')}${hmbHint} • Saran: <button type="button" id="btn-apply-rec-lot" style="background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.4); color:#93c5fd; border-radius:4px; padding:1px 6px; font-size:9.5px; font-weight:700; cursor:pointer;" title="Klik untuk menerapkan saran ${recLots} lot">${recLots} Lot</button>`;
        }

        let lots = parseInt(this.dom.planInputLot?.value, 10);
        if (autoRecalcLot && (!lots || !this._userEditedLot)) {
            lots = recLots;
            if (this.dom.planInputLot) this.dom.planInputLot.value = lots;
        } else if (!lots) {
            lots = 1;
        }

        const totalInvested = lots * 100 * entry;
        const totalRiskNominal = lots * 100 * riskPerShare;
        const riskPctOfInvested = (riskPerShare / entry) * 100;

        let rrStr = '--';
        let totalRewardNominal = 0;
        let rewardPctOfInvested = 0;
        if (tp1 > entry) {
            const rewardPerShare = tp1 - entry;
            const rr = rewardPerShare / riskPerShare;
            rrStr = `1 : ${rr.toFixed(2)}`;
            totalRewardNominal = lots * 100 * rewardPerShare;
            rewardPctOfInvested = (rewardPerShare / entry) * 100;
        }

        if (this.dom.planCalcInvested) {
            this.dom.planCalcInvested.textContent = `Rp ${Math.round(totalInvested).toLocaleString('id-ID')}`;
        }
        if (this.dom.planCalcRr) {
            this.dom.planCalcRr.textContent = rrStr;
        }
        if (this.dom.planCalcRiskRp) {
            this.dom.planCalcRiskRp.textContent = `-Rp ${Math.round(totalRiskNominal).toLocaleString('id-ID')} (-${riskPctOfInvested.toFixed(1)}%)`;
        }
        if (this.dom.planCalcRewardRp) {
            this.dom.planCalcRewardRp.textContent = `+Rp ${Math.round(totalRewardNominal).toLocaleString('id-ID')} (+${rewardPctOfInvested.toFixed(1)}%)`;
        }
    }

    async submitPlanForm() {
        const planId = this.dom.planModalId?.value ? parseInt(this.dom.planModalId.value, 10) : null;
        const symbol = (this.dom.planInputSymbol?.value || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        const category = this.dom.planSelectCategory?.value || 'Breakout';
        const status = this.dom.planSelectStatus?.value || 'ANTRI';
        const orderType = this.dom.planSelectOrderType?.value || 'LIMIT';
        const entryPrice = parseFloat(this.dom.planInputEntry?.value) || 0;
        const slPrice = parseFloat(this.dom.planInputSl?.value) || 0;
        const tp1Price = parseFloat(this.dom.planInputTp1?.value) || 0;
        const lotSize = parseInt(this.dom.planInputLot?.value, 10) || this._recommendedLot || 1;
        const notes = this.dom.planInputNotes?.value?.trim() || null;

        if (!symbol || symbol.length < 4) {
            this.showToast('Masukkan kode saham yang valid (contoh: BBRI)', 'warning');
            return;
        }
        if (entryPrice <= 0) {
            this.showToast('Harga Entry harus lebih besar dari 0!', 'warning');
            return;
        }
        if (slPrice <= 0 || slPrice >= entryPrice) {
            this.showToast('Stop Loss harus lebih rendah dari harga Entry!', 'warning');
            return;
        }
        if (tp1Price <= entryPrice) {
            this.showToast('Target TP1 harus lebih tinggi dari harga Entry!', 'warning');
            return;
        }
        if (lotSize < 1) {
            this.showToast('Alokasi minimal 1 lot!', 'warning');
            return;
        }

        const payload = {
            symbol: symbol,
            category: category,
            order_type: orderType,
            entry_price: entryPrice,
            sl_price: slPrice,
            tp1_price: tp1Price,
            lot_size: lotSize,
            status: status,
            notes: notes
        };

        try {
            let res;
            if (planId) {
                res = await fetch(`/api/trading-plans/${planId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                res = await fetch('/api/trading-plans', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            const json = await res.json();
            if (res.ok && json.success) {
                this.showToast(planId ? `🎯 Trading plan ${symbol} berhasil diperbarui!` : `🎯 Trading plan ${symbol} berhasil disimpan!`, 'info');
                this.closePlanModal();
                await this.fetchTradingPlans(this.activePlanFilter);
            } else {
                const errMsg = Array.isArray(json.detail) 
                    ? json.detail.map(d => d.msg || JSON.stringify(d)).join(', ') 
                    : (json.detail || 'Gagal menyimpan trading plan');
                throw new Error(errMsg);
            }
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    async quickMatchPlan(planId) {
        const plan = (this.tradingPlans || []).find(p => p.id === planId);
        if (!plan) return;

        try {
            const todayStr = new Date().toISOString().split('T')[0];
            const res = await fetch(`/api/trading-plans/${planId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: 'HOLDING',
                    entry_date: todayStr
                })
            });
            const json = await res.json();
            if (res.ok && json.success) {
                this.showToast(`🚀 Order ${plan.symbol} MATCH! Menjadi posisi HOLDING.`, 'info');
                await this.fetchTradingPlans(this.activePlanFilter);
            } else {
                throw new Error(json.detail || 'Gagal mengubah status');
            }
        } catch (err) {
            this.showToast(`Gagal: ${err.message}`, 'error');
        }
    }

    openTrailingModal(plan) {
        if (!this.dom.trailingModal || !this.dom.trailingModalBackdrop) return;
        const stock = this.getStockInfo(plan.symbol);
        const livePrice = stock && stock.price ? stock.price : plan.entry_price;

        if (this.dom.trailingModalId) this.dom.trailingModalId.value = plan.id;
        if (this.dom.trailingModalTitle) this.dom.trailingModalTitle.textContent = `🛡️ Naikkan Trailing Stop — ${plan.symbol}`;
        if (this.dom.trailingInfoEntry) this.dom.trailingInfoEntry.textContent = `Rp ${Number(plan.entry_price).toLocaleString('id-ID')}`;
        if (this.dom.trailingInfoCurrSl) this.dom.trailingInfoCurrSl.textContent = `Rp ${Number(plan.sl_price).toLocaleString('id-ID')}`;
        if (this.dom.trailingInfoLivePrice) this.dom.trailingInfoLivePrice.textContent = `Rp ${Number(livePrice).toLocaleString('id-ID')}`;

        // Default trailing SL: set to above old SL
        let suggestedSl = plan.sl_price;
        if (livePrice > plan.entry_price) {
            suggestedSl = Math.max(plan.sl_price, Math.round(plan.entry_price * 1.01));
        } else {
            suggestedSl = Math.round(plan.sl_price * 1.01);
        }
        if (this.dom.trailingInputSl) {
            this.dom.trailingInputSl.value = suggestedSl;
        }

        this.dom.trailingModalBackdrop.classList.remove('hidden');
        this.dom.trailingModal.classList.remove('hidden');
    }

    closeTrailingModal() {
        if (this.dom.trailingModal) this.dom.trailingModal.classList.add('hidden');
        if (this.dom.trailingModalBackdrop) this.dom.trailingModalBackdrop.classList.add('hidden');
    }

    async submitTrailingStop() {
        const planId = parseInt(this.dom.trailingModalId?.value, 10);
        const newSl = parseFloat(this.dom.trailingInputSl?.value) || 0;
        const plan = (this.tradingPlans || []).find(p => p.id === planId);

        if (!plan) return;
        if (newSl <= plan.sl_price) {
            this.showToast(`Stop loss baru (Rp ${newSl}) harus lebih tinggi dari SL lama (Rp ${plan.sl_price})!`, 'warning');
            return;
        }

        try {
            const res = await fetch(`/api/trading-plans/${planId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sl_price: newSl })
            });
            const json = await res.json();
            if (res.ok && json.success) {
                this.showToast(`🛡️ Trailing Stop ${plan.symbol} berhasil dinaikkan ke Rp ${Number(newSl).toLocaleString('id-ID')}!`, 'info');
                this.closeTrailingModal();
                await this.fetchTradingPlans(this.activePlanFilter);
            } else {
                throw new Error(json.detail || 'Gagal mengubah SL');
            }
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    openExitModal(plan) {
        if (!this.dom.exitModal || !this.dom.exitModalBackdrop) return;
        const stock = this.getStockInfo(plan.symbol);
        const livePrice = stock && stock.price ? stock.price : plan.entry_price;

        if (this.dom.exitModalId) this.dom.exitModalId.value = plan.id;
        if (this.dom.exitModalTitle) this.dom.exitModalTitle.textContent = `🏁 Selesaikan & Bukukan Posisi — ${plan.symbol}`;
        if (this.dom.exitInputPrice) this.dom.exitInputPrice.value = livePrice;
        if (this.dom.exitInputNotes) this.dom.exitInputNotes.value = plan.notes || '';

        // Auto select win/loss based on price vs entry
        if (this.dom.exitSelectStatus) {
            this.dom.exitSelectStatus.value = livePrice >= plan.entry_price ? 'CLOSED_WIN' : 'CLOSED_LOSS';
        }

        this.updateExitPnlPreview();
        this.dom.exitModalBackdrop.classList.remove('hidden');
        this.dom.exitModal.classList.remove('hidden');
    }

    closeExitModal() {
        if (this.dom.exitModal) this.dom.exitModal.classList.add('hidden');
        if (this.dom.exitModalBackdrop) this.dom.exitModalBackdrop.classList.add('hidden');
    }

    updateExitPnlPreview() {
        const planId = parseInt(this.dom.exitModalId?.value, 10);
        const plan = (this.tradingPlans || []).find(p => p.id === planId);
        if (!plan) return;

        const exitPrice = parseFloat(this.dom.exitInputPrice?.value) || 0;
        const entryPrice = plan.entry_price || 1;
        const lotSize = plan.lot_size || 1;

        if (exitPrice <= 0) {
            if (this.dom.exitPnlPreview) this.dom.exitPnlPreview.textContent = 'Rp --';
            return;
        }

        const realizedPnl = (exitPrice - entryPrice) * lotSize * 100;
        const realizedPct = ((exitPrice - entryPrice) / entryPrice) * 100;
        const isProfit = realizedPnl >= 0;
        const sign = isProfit ? '+' : '';

        if (this.dom.exitPnlPreview) {
            this.dom.exitPnlPreview.textContent = `${sign}Rp ${Math.abs(Math.round(realizedPnl)).toLocaleString('id-ID')} (${sign}${realizedPct.toFixed(2)}%)`;
            this.dom.exitPnlPreview.style.color = isProfit ? '#34d399' : '#f87171';
        }
    }

    async submitExitPosition() {
        const planId = parseInt(this.dom.exitModalId?.value, 10);
        const exitPrice = parseFloat(this.dom.exitInputPrice?.value) || 0;
        const status = this.dom.exitSelectStatus?.value || 'CLOSED_WIN';
        const notes = this.dom.exitInputNotes?.value?.trim() || null;
        const plan = (this.tradingPlans || []).find(p => p.id === planId);

        if (!plan) return;
        if (exitPrice <= 0) {
            this.showToast('Masukkan harga jual / exit yang valid!', 'warning');
            return;
        }

        try {
            const todayStr = new Date().toISOString().split('T')[0];
            const res = await fetch(`/api/trading-plans/${planId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status: status,
                    exit_price: exitPrice,
                    exit_date: todayStr,
                    notes: notes
                })
            });
            const json = await res.json();
            if (res.ok && json.success) {
                const pnl = (exitPrice - plan.entry_price) * plan.lot_size * 100;
                const sign = pnl >= 0 ? '+' : '';
                this.showToast(`🏁 Posisi ${plan.symbol} dibukukan! Realized: ${sign}Rp ${Math.abs(Math.round(pnl)).toLocaleString('id-ID')}`, 'info');
                this.closeExitModal();
                await this.fetchTradingPlans(this.activePlanFilter);
            } else {
                throw new Error(json.detail || 'Gagal membukukan posisi');
            }
        } catch (err) {
            this.showToast(`Error: ${err.message}`, 'error');
        }
    }

    async confirmDeletePlan(planId, symbol) {
        if (!confirm(`Hapus trading plan ${symbol}? Tindakan ini tidak dapat dibatalkan.`)) return;

        try {
            const res = await fetch(`/api/trading-plans/${planId}`, { method: 'DELETE' });
            const json = await res.json();
            if (res.ok && json.success) {
                this.showToast(`🗑️ Trading plan ${symbol} telah dihapus`, 'info');
                this.tradingPlans = this.tradingPlans.filter(p => p.id !== planId);
                this.updateJournalStatsUI();
                this.renderTradingPlans();
            } else {
                throw new Error(json.detail || 'Gagal menghapus plan');
            }
        } catch (err) {
            this.showToast(`Gagal: ${err.message}`, 'error');
        }
    }

    openChartFromPlan(symbol) {
        this.updateChartBackButton('journal');
        const clean = (symbol || '').replace('IDX:', '').replace('.JK', '').toUpperCase().trim();
        if (this.tradingPlans && this.tradingPlans.length > 0) {
            this.activeNavigationList = Array.from(new Set(this.tradingPlans.map(p => p.symbol)));
        } else {
            this.activeNavigationList = [clean];
        }
        this.currentNavigationIndex = this.activeNavigationList.indexOf(clean);
        if (this.currentNavigationIndex === -1) this.currentNavigationIndex = 0;
        this.renderQuickChipsFromList(this.activeNavigationList, clean);
        this.updateNavIndex();
        this.switchView('chart', true, clean);
        this.setSymbol(clean, true);
    }
    
    async loadData(symbol, interval) {
        // P0 #2: Batalkan request sebelumnya yang masih berjalan
        if (this.abortController) {
            this.abortController.abort();
        }
        this.abortController = new AbortController();
        const currentReqId = ++this.reqId;
        
        this.showLoading(true);
        
        try {
            // P1 #9: Encode URL parameter
            const symEnc = encodeURIComponent(symbol);
            const intEnc = encodeURIComponent(interval);
            let historyUrl = `/api/history?symbol=${symEnc}&interval=${intEnc}`;
            if (interval === '1d' && this.riskSettings && this.riskSettings.daily_source) {
                historyUrl += `&source=${encodeURIComponent(this.riskSettings.daily_source)}`;
            }

            // Fetch history & Bandarmologi secara paralel
            const needBandarFetch = !this.bandarData || this.bandarData.symbol !== symbol;
            const historyPromise = fetch(historyUrl, {
                signal: this.abortController.signal
            });

            const bandarPromise = needBandarFetch 
                ? fetch(`/api/bandarmologi?symbol=${symEnc}`, { signal: this.abortController.signal })
                    .then(r => r.ok ? r.json() : null)
                    .catch(e => {
                        if (e.name !== 'AbortError') console.warn('Fetch bandarmologi error:', e);
                        return null;
                    })
                : Promise.resolve(this.bandarData);

            const [resp, bandarJson] = await Promise.all([historyPromise, bandarPromise]);
            
            // P0 #2: Jika ada request baru yang masuk selagi menunggu, buang respons stale ini!
            if (currentReqId !== this.reqId) return;
            
            const json = await resp.json();
            if (currentReqId !== this.reqId) return;

            // Simpan data bandarmologi jika ada update
            if (needBandarFetch) {
                if (bandarJson && bandarJson.success) {
                    this.bandarData = bandarJson;
                    this.updateBandarBadge(bandarJson.summary);
                } else {
                    this.bandarData = null;
                    this.updateBandarBadge(null);
                }
            } else if (this.bandarData) {
                this.updateBandarBadge(this.bandarData.summary);
            }
            
            if (resp.ok && json.success && Array.isArray(json.data) && json.data.length > 0) {
                // Pasangkan data Net Flow & HMB ke setiap candle
                this.syncBandarDataToCandles(json.data);

                // Apply data ke KLineCharts
                this.chart.applyNewData(json.data);
                
                // Muat coretan manual tersimpan untuk emiten ini dari localStorage
                this.loadOverlaysForSymbol(this.currentSymbol);

                // Update metrics di UI
                this.updateMetrics(json);

                // Auto-refresh SnR jika indikator sedang aktif
                if (this.indicatorState.SNR) {
                    this.refreshAutoSnR();
                }

                // Auto-refresh HMB jika indikator sedang aktif
                if (this.indicatorState.HMB) {
                    this.refreshHmbLine();
                }
            } else {
                const msg = json.detail || json.error || `Data tidak ditemukan untuk ${symbol} (${interval})`;
                this.showToast(msg, 'warning');
            }
        } catch (err) {
            if (err.name === 'AbortError') {
                return;
            }
            console.error('Fetch candlestick error:', err);
            this.showToast(`Koneksi bermasalah: ${err.message}`, 'error');
        } finally {
            if (currentReqId === this.reqId) {
                this.showLoading(false);
            }
        }
    }
    
    updateMetrics(payload) {
        const meta = payload.meta || {};
        const candles = payload.data || [];
        if (candles.length === 0) return;
        
        const latest = candles[candles.length - 1];
        
        if (this.dom.tickerInplaceInput) {
            this.dom.tickerInplaceInput.value = payload.symbol;
            this.dom.tickerInplaceInput.style.width = Math.max(payload.symbol.length * 12, 54) + 'px';
        }
        
        if (latest && this.dom.currentPrice) {
            this.dom.currentPrice.textContent = Number(latest.close).toLocaleString('id-ID');
            
            // P1 #7: Perbaikan kalkulasi % change yang benar
            let changePct = null;
            if (typeof meta.regularMarketChangePercent === 'number' && !isNaN(meta.regularMarketChangePercent)) {
                changePct = meta.regularMarketChangePercent;
            } else if (candles.length > 1) {
                const prevClose = candles[candles.length - 2].close;
                if (prevClose && prevClose > 0) {
                    changePct = ((latest.close - prevClose) / prevClose) * 100;
                }
            } else {
                changePct = 0;
            }
                
            if (this.dom.currentChange && changePct !== null && !isNaN(changePct)) {
                const isUp = changePct >= 0;
                this.dom.currentChange.className = `current-change ${isUp ? 'up' : 'down'}`;
                this.dom.currentChange.textContent = `${isUp ? '+' : ''}${changePct.toFixed(2)}%`;
            }
        }
        
        if (this.dom.sourceBadge) {
            const src = payload.source === 'neon_db' ? 'Neon DB' : 
                        payload.source === 'stockbit_byot' ? 'Stockbit' : 'Yahoo';
            const staleMarker = payload.stale ? ' [STALE]' : '';
            const tfUpper = (payload.interval || '').toUpperCase();
            this.dom.sourceBadge.textContent = `${src} • ${tfUpper}${staleMarker}`;
        }

        if (this.dom.activeTfLabel) {
            this.dom.activeTfLabel.textContent = (payload.interval || this.currentInterval).toUpperCase();
        }

        if (this.dom.tickerBoardBadge) {
            this.dom.tickerBoardBadge.classList.add('hidden');
            this.dom.tickerBoardBadge.style.display = 'none';
        }
    }
    
    showLoading(show) {
        if (!this.dom.loading) return;
        if (show) {
            this.dom.loading.classList.remove('hidden');
        } else {
            this.dom.loading.classList.add('hidden');
        }
    }
    
    // P2: Non-intrusive Toast Notification
    showToast(message, type = 'info') {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                bottom: 60px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 8px;
                pointer-events: none;
                max-width: 90%;
            `;
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        const bgColors = {
            error: 'rgba(242, 54, 69, 0.95)',
            warning: 'rgba(234, 179, 8, 0.95)',
            info: 'rgba(15, 23, 42, 0.95)'
        };
        toast.style.cssText = `
            background: ${bgColors[type] || bgColors.info};
            color: #fff;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            box-shadow: 0 4px 16px rgba(0,0,0,0.5);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.15);
            opacity: 0;
            transition: opacity 0.2s, transform 0.2s;
            transform: translateY(10px);
            text-align: center;
        `;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        
        requestAnimationFrame(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        });
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 250);
        }, 2200);
    }
}

// Inisialisasi Chart saat DOM siap
document.addEventListener('DOMContentLoaded', () => {
    window.candlify = new CandlifyChart();
});
