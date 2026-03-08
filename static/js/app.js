/**
 * IN-GRES: India Groundwater Resource Estimation System
 * Frontend JavaScript Application
 */

// API Base URL
const API_BASE = '/api';

// State Management
const state = {
    currentPage: 'dashboard',
    states: [],
    districts: [],
    groundwaterData: [],
    summary: null,
    filters: {
        stateId: null,
        districtId: null,
        year: 2022,
        category: null,
        search: ''
    },
    pagination: {
        page: 1,
        perPage: 20,
        total: 0,
        totalPages: 0
    }
};

// DOM Elements
const elements = {
    tabButtons: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    visitorCount: document.getElementById('visitorCount'),
    
    // Dashboard
    totalStates: document.getElementById('totalStates'),
    totalDistricts: document.getElementById('totalDistricts'),
    totalRecharge: document.getElementById('totalRecharge'),
    totalExtraction: document.getElementById('totalExtraction'),
    avgSoe: document.getElementById('avgSoe'),
    safeCount: document.getElementById('safeCount'),
    semiCriticalCount: document.getElementById('semiCriticalCount'),
    criticalCount: document.getElementById('criticalCount'),
    overExploitedCount: document.getElementById('overExploitedCount'),
    stateSummaryTable: document.getElementById('stateSummaryTable'),
    
    // Data Explorer
    filterState: document.getElementById('filterState'),
    filterDistrict: document.getElementById('filterDistrict'),
    filterYear: document.getElementById('filterYear'),
    filterCategory: document.getElementById('filterCategory'),
    searchInput: document.getElementById('searchInput'),
    dataTableBody: document.getElementById('dataTableBody'),
    pagination: document.getElementById('pagination'),
    
    // Chat
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    chatSendBtn: document.getElementById('chatSendBtn'),
    
    // Modal
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modalTitle'),
    modalBody: document.getElementById('modalBody'),
    modalClose: document.getElementById('modalClose'),
    
    // Data Management
    addDataTab: document.getElementById('addDataTab')
};

// ============== Utility Functions ==============

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('en-IN', { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals 
    });
}

function formatCategory(category) {
    const classMap = {
        'Safe': 'safe',
        'Semi-Critical': 'semi-critical',
        'Critical': 'critical',
        'Over-exploited': 'over-exploited'
    };
    return `<span class="status-badge ${classMap[category] || ''}">${category}</span>`;
}

function showLoading(container) {
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// ============== API Functions ==============

async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// ============== Data Loading Functions ==============

async function loadStates() {
    try {
        state.states = await fetchAPI('/states');
        populateStateDropdowns();
    } catch (error) {
        console.error('Failed to load states:', error);
    }
}

async function loadDistricts(stateId = null) {
    try {
        const url = stateId ? `/districts?stateId=${stateId}` : '/districts';
        state.districts = await fetchAPI(url);
        populateDistrictDropdown();
    } catch (error) {
        console.error('Failed to load districts:', error);
    }
}

async function loadSummary(year = 2022) {
    try {
        const data = await fetchAPI(`/summary?year=${year}`);
        state.summary = data;
        updateDashboard(data);
    } catch (error) {
        console.error('Failed to load summary:', error);
    }
}

async function loadGroundwaterData() {
    try {
        const params = new URLSearchParams();
        
        if (state.filters.stateId) params.append('stateId', state.filters.stateId);
        if (state.filters.districtId) params.append('districtId', state.filters.districtId);
        if (state.filters.year) params.append('year', state.filters.year);
        if (state.filters.category) params.append('category', state.filters.category);
        if (state.filters.search) params.append('search', state.filters.search);
        
        params.append('page', state.pagination.page);
        params.append('perPage', state.pagination.perPage);
        
        const data = await fetchAPI(`/groundwater?${params.toString()}`);
        state.groundwaterData = data.data;
        state.pagination = data.pagination;
        
        renderDataTable();
        renderPagination();
    } catch (error) {
        console.error('Failed to load groundwater data:', error);
    }
}

async function loadVisitorCount() {
    try {
        const data = await fetchAPI('/visitor');
        if (elements.visitorCount) {
            elements.visitorCount.textContent = data.count.toLocaleString('en-IN');
        }
    } catch (error) {
        console.error('Failed to load visitor count:', error);
    }
}

// ============== UI Update Functions ==============

function populateStateDropdowns() {
    const dropdowns = [elements.filterState];
    
    dropdowns.forEach(dropdown => {
        if (!dropdown) return;
        
        dropdown.innerHTML = '<option value="">All States</option>';
        state.states.forEach(s => {
            dropdown.innerHTML += `<option value="${s.id}">${s.name}</option>`;
        });
    });
}

function populateDistrictDropdown() {
    if (!elements.filterDistrict) return;
    
    const filteredDistricts = state.filters.stateId
        ? state.districts.filter(d => d.state_id === state.filters.stateId)
        : state.districts;
    
    elements.filterDistrict.innerHTML = '<option value="">All Districts</option>';
    filteredDistricts.forEach(d => {
        elements.filterDistrict.innerHTML += `<option value="${d.id}">${d.name}</option>`;
    });
}

function updateDashboard(data) {
    const { summary, categories, state_summary } = data;
    
    // Overview cards
    if (elements.totalStates) elements.totalStates.textContent = summary.total_states || '0';
    if (elements.totalDistricts) elements.totalDistricts.textContent = summary.total_districts || '0';
    if (elements.totalRecharge) elements.totalRecharge.textContent = formatNumber(summary.total_recharge, 0) + ' MCM';
    if (elements.totalExtraction) elements.totalExtraction.textContent = formatNumber(summary.total_extraction, 0) + ' MCM';
    if (elements.avgSoe) elements.avgSoe.textContent = formatNumber(summary.avg_soe, 1) + '%';
    
    // Category counts
    categories.forEach(cat => {
        switch(cat.category) {
            case 'Safe':
                if (elements.safeCount) {
                    elements.safeCount.textContent = cat.count;
                    elements.safeCount.nextElementSibling.textContent = `${cat.percentage}%`;
                }
                break;
            case 'Semi-Critical':
                if (elements.semiCriticalCount) {
                    elements.semiCriticalCount.textContent = cat.count;
                    elements.semiCriticalCount.nextElementSibling.textContent = `${cat.percentage}%`;
                }
                break;
            case 'Critical':
                if (elements.criticalCount) {
                    elements.criticalCount.textContent = cat.count;
                    elements.criticalCount.nextElementSibling.textContent = `${cat.percentage}%`;
                }
                break;
            case 'Over-exploited':
                if (elements.overExploitedCount) {
                    elements.overExploitedCount.textContent = cat.count;
                    elements.overExploitedCount.nextElementSibling.textContent = `${cat.percentage}%`;
                }
                break;
        }
    });
    
    // State summary table
    renderStateSummaryTable(state_summary);
}

function renderStateSummaryTable(stateSummary) {
    if (!elements.stateSummaryTable) return;
    
    elements.stateSummaryTable.innerHTML = stateSummary.map(s => `
        <tr onclick="showStateReport(${s.id})" title="Click to view detailed report">
            <td>${s.name}</td>
            <td>${s.district_count}</td>
            <td>${formatNumber(s.total_recharge, 0)} MCM</td>
            <td>${formatNumber(s.total_extraction, 0)} MCM</td>
            <td>${formatNumber(s.avg_soe, 1)}%</td>
            <td>
                <span class="status-badge safe">${s.safe_count || 0}</span>
                <span class="status-badge semi-critical">${s.semi_critical_count || 0}</span>
                <span class="status-badge critical">${s.critical_count || 0}</span>
                <span class="status-badge over-exploited">${s.over_exploited_count || 0}</span>
            </td>
        </tr>
    `).join('');
}

function renderDataTable() {
    if (!elements.dataTableBody) return;
    
    if (state.groundwaterData.length === 0) {
        elements.dataTableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center">No data found</td>
            </tr>
        `;
        return;
    }
    
    elements.dataTableBody.innerHTML = state.groundwaterData.map(row => `
        <tr onclick="showDistrictReport(${row.district_id})" title="Click to view district report">
            <td>${row.state_name}</td>
            <td>${row.district_name}</td>
            <td>${row.assessment_year}</td>
            <td>${formatNumber(row.total_annual_recharge, 2)} MCM</td>
            <td>${formatNumber(row.total_extraction, 2)} MCM</td>
            <td>${formatNumber(row.stage_of_extraction, 1)}%</td>
            <td>${formatCategory(row.category)}</td>
            <td>${row.aquifer_type || 'N/A'}</td>
            <td>${row.rock_type || 'N/A'}</td>
        </tr>
    `).join('');
}

function renderPagination() {
    if (!elements.pagination) return;
    
    const { page, totalPages, total } = state.pagination;
    
    if (totalPages <= 1) {
        elements.pagination.innerHTML = '';
        return;
    }
    
    let html = `
        <button onclick="changePage(${page - 1})" ${page === 1 ? 'disabled' : ''}>
            ← Previous
        </button>
    `;
    
    // Show limited page numbers
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(totalPages, page + 2);
    
    if (startPage > 1) {
        html += `<button onclick="changePage(1)">1</button>`;
        if (startPage > 2) html += `<span class="page-info">...</span>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button onclick="changePage(${i})" class="${i === page ? 'active' : ''}">
                ${i}
            </button>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="page-info">...</span>`;
        html += `<button onclick="changePage(${totalPages})">${totalPages}</button>`;
    }
    
    html += `
        <button onclick="changePage(${page + 1})" ${page === totalPages ? 'disabled' : ''}>
            Next →
        </button>
        <span class="page-info">Total: ${total} records</span>
    `;
    
    elements.pagination.innerHTML = html;
}

// ============== Modal Functions ==============

function showModal(title, content) {
    if (elements.modalTitle) elements.modalTitle.textContent = title;
    if (elements.modalBody) elements.modalBody.innerHTML = content;
    elements.modal.classList.add('active');
}

function hideModal() {
    elements.modal.classList.remove('active');
}

async function showStateReport(stateId) {
    showModal('Loading...', '<div class="loading"><div class="spinner"></div></div>');
    
    try {
        const data = await fetchAPI(`/state/${stateId}?year=2022`);
        const { state: stateInfo, districts, totals } = data;
        
        const content = `
            <div class="report-section">
                <h3>📍 State Overview: ${stateInfo.name}</h3>
                <div class="two-column">
                    <div>
                        <p><strong>Total Districts:</strong> ${districts.length}</p>
                        <p><strong>Total Recharge:</strong> ${formatNumber(totals.total_recharge, 2)} MCM</p>
                        <p><strong>Total Extraction:</strong> ${formatNumber(totals.total_extraction, 2)} MCM</p>
                    </div>
                    <div>
                        <p><strong>Average SoE:</strong> ${formatNumber(totals.avg_soe, 1)}%</p>
                        <p><strong>Net Availability:</strong> ${formatNumber(totals.net_availability, 2)} MCM</p>
                        <p><strong>Assessment Year:</strong> 2022</p>
                    </div>
                </div>
            </div>
            
            <div class="report-section">
                <h3>📊 Category Distribution</h3>
                <p>
                    <span class="status-badge safe">Safe: ${totals.safe_count || 0}</span>
                    <span class="status-badge semi-critical">Semi-Critical: ${totals.semi_critical_count || 0}</span>
                    <span class="status-badge critical">Critical: ${totals.critical_count || 0}</span>
                    <span class="status-badge over-exploited">Over-exploited: ${totals.over_exploited_count || 0}</span>
                </p>
            </div>
            
            <div class="report-section">
                <h3>🏘️ District-wise Data</h3>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>District</th>
                                <th>Recharge (MCM)</th>
                                <th>Extraction (MCM)</th>
                                <th>SoE (%)</th>
                                <th>Category</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${districts.map(d => `
                                <tr>
                                    <td>${d.name}</td>
                                    <td>${formatNumber(d.total_annual_recharge, 2)}</td>
                                    <td>${formatNumber(d.total_extraction, 2)}</td>
                                    <td>${formatNumber(d.stage_of_extraction, 1)}</td>
                                    <td>${formatCategory(d.category)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="report-section">
                <h3>📋 GEC-2015 Methodology Notes</h3>
                <p><strong>Stage of Extraction (SoE)</strong> = (Total Extraction / Extractable Resources) × 100</p>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    <li>Safe: SoE &lt; 70%</li>
                    <li>Semi-Critical: 70% ≤ SoE &lt; 90%</li>
                    <li>Critical: 90% ≤ SoE ≤ 100%</li>
                    <li>Over-exploited: SoE &gt; 100%</li>
                </ul>
            </div>
        `;
        
        showModal(`GEC Report - ${stateInfo.name}`, content);
    } catch (error) {
        showModal('Error', '<p>Failed to load state report. Please try again.</p>');
    }
}

async function showDistrictReport(districtId) {
    showModal('Loading...', '<div class="loading"><div class="spinner"></div></div>');
    
    try {
        const data = await fetchAPI(`/district/${districtId}?year=2022`);
        const { district, groundwater, assessment_units } = data;
        
        const content = `
            <div class="report-section">
                <h3>📍 District Overview</h3>
                <p><strong>District:</strong> ${district.name}</p>
                <p><strong>State:</strong> ${district.state_name}</p>
                <p><strong>Assessment Year:</strong> ${groundwater.assessment_year}</p>
            </div>
            
            <div class="report-section">
                <h3>💧 Groundwater Resources</h3>
                <table class="report-table">
                    <tr>
                        <th>Total Annual Recharge</th>
                        <td>${formatNumber(groundwater.total_annual_recharge, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Monsoon Recharge</th>
                        <td>${formatNumber(groundwater.monsoon_recharge, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Non-Monsoon Recharge</th>
                        <td>${formatNumber(groundwater.non_monsoon_recharge, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Extractable Resource</th>
                        <td>${formatNumber(groundwater.extractable_resource, 2)} MCM</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>🚰 Groundwater Extraction</h3>
                <table class="report-table">
                    <tr>
                        <th>Total Extraction</th>
                        <td>${formatNumber(groundwater.total_extraction, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Irrigation</th>
                        <td>${formatNumber(groundwater.irrigation_extraction, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Domestic</th>
                        <td>${formatNumber(groundwater.domestic_extraction, 2)} MCM</td>
                    </tr>
                    <tr>
                        <th>Industrial</th>
                        <td>${formatNumber(groundwater.industrial_extraction, 2)} MCM</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>📈 Assessment Status</h3>
                <table class="report-table">
                    <tr>
                        <th>Stage of Extraction</th>
                        <td><strong>${formatNumber(groundwater.stage_of_extraction, 1)}%</strong></td>
                    </tr>
                    <tr>
                        <th>Category</th>
                        <td>${formatCategory(groundwater.category)}</td>
                    </tr>
                    <tr>
                        <th>Net Availability</th>
                        <td>${formatNumber(groundwater.net_availability, 2)} MCM</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>🌊 Water Level Data</h3>
                <table class="report-table">
                    <tr>
                        <th>Pre-Monsoon Level</th>
                        <td>${groundwater.pre_monsoon_level} m bgl</td>
                    </tr>
                    <tr>
                        <th>Post-Monsoon Level</th>
                        <td>${groundwater.post_monsoon_level} m bgl</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>⛽ Well Inventory</h3>
                <table class="report-table">
                    <tr>
                        <th>Dug Wells</th>
                        <td>${groundwater.dug_wells?.toLocaleString('en-IN') || 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Shallow Tubewells</th>
                        <td>${groundwater.shallow_tubewells?.toLocaleString('en-IN') || 'N/A'}</td>
                    </tr>
                    <tr>
                        <th>Deep Tubewells</th>
                        <td>${groundwater.deep_tubewells?.toLocaleString('en-IN') || 'N/A'}</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>🪨 Geological Information</h3>
                <p><strong>Aquifer Type:</strong> ${groundwater.aquifer_type || 'N/A'}</p>
                <p><strong>Rock Type:</strong> ${groundwater.rock_type || 'N/A'}</p>
            </div>
            
            <div class="report-section">
                <h3>🗺️ Area Information</h3>
                <table class="report-table">
                    <tr>
                        <th>Geographical Area</th>
                        <td>${formatNumber(groundwater.geographical_area, 2)} sq km</td>
                    </tr>
                    <tr>
                        <th>Cultivable Area</th>
                        <td>${formatNumber(groundwater.cultivable_area, 2)} sq km</td>
                    </tr>
                    <tr>
                        <th>Irrigated Area</th>
                        <td>${formatNumber(groundwater.irrigated_area, 2)} sq km</td>
                    </tr>
                </table>
            </div>
            
            <div class="report-section">
                <h3>📊 Assessment Units (${assessment_units.length})</h3>
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Unit Name</th>
                            <th>Area (sq km)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${assessment_units.map(u => `
                            <tr>
                                <td>${u.name}</td>
                                <td>${formatNumber(u.area_sqkm, 2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        showModal(`District Report - ${district.name}`, content);
    } catch (error) {
        showModal('Error', '<p>Failed to load district report. Please try again.</p>');
    }
}

// ============== Tab Navigation ==============

function switchTab(tabId) {
    // Update state
    state.currentPage = tabId;
    
    // Update UI
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabId);
    });
    
    // Load data for the tab
    if (tabId === 'dashboard') {
        loadSummary(state.filters.year);
    } else if (tabId === 'explorer') {
        loadGroundwaterData();
    }
}

// ============== Filter Handlers ==============

function handleFilterChange() {
    state.filters.stateId = elements.filterState?.value ? parseInt(elements.filterState.value) : null;
    state.filters.districtId = elements.filterDistrict?.value ? parseInt(elements.filterDistrict.value) : null;
    state.filters.year = elements.filterYear?.value ? parseInt(elements.filterYear.value) : null;
    state.filters.category = elements.filterCategory?.value || null;
    
    // Update districts dropdown when state changes
    if (elements.filterState) {
        populateDistrictDropdown();
    }
    
    // Reset pagination
    state.pagination.page = 1;
    
    // Reload data
    if (state.currentPage === 'explorer') {
        loadGroundwaterData();
    } else if (state.currentPage === 'dashboard') {
        loadSummary(state.filters.year);
    }
}

function handleSearch() {
    state.filters.search = elements.searchInput?.value || '';
    state.pagination.page = 1;
    loadGroundwaterData();
}

function changePage(page) {
    if (page < 1 || page > state.pagination.totalPages) return;
    state.pagination.page = page;
    loadGroundwaterData();
}

// ============== Chat Functions ==============

async function sendChatMessage() {
    const input = elements.chatInput;
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message assistant';
    typingDiv.innerHTML = '<div class="message-content"><div class="spinner"></div></div>';
    elements.chatMessages.appendChild(typingDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    try {
        const response = await fetchAPI('/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
        
        // Remove typing indicator
        typingDiv.remove();
        
        // Add assistant response
        addChatMessage(response.response, 'assistant');
    } catch (error) {
        typingDiv.remove();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addChatMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    // Convert markdown-like formatting
    let formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function handleQuickAction(action) {
    const actions = {
        'india': 'Tell me about India groundwater overview',
        'gec': 'Explain GEC-2015 methodology',
        'categories': 'Show category distribution',
        'help': 'Help me understand how to use this system'
    };
    
    elements.chatInput.value = actions[action] || action;
    sendChatMessage();
}

// ============== Data Management Functions ==============

async function addState() {
    const name = document.getElementById('newStateName').value.trim();
    const code = document.getElementById('newStateCode').value.trim().toUpperCase();
    
    if (!name || !code) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    try {
        await fetchAPI('/data/states', {
            method: 'POST',
            body: JSON.stringify({ name, code })
        });
        
        showToast('State added successfully!', 'success');
        document.getElementById('newStateName').value = '';
        document.getElementById('newStateCode').value = '';
        loadStates();
    } catch (error) {
        showToast('Failed to add state', 'error');
    }
}

async function addDistrict() {
    const stateId = document.getElementById('newDistrictState').value;
    const name = document.getElementById('newDistrictName').value.trim();
    
    if (!stateId || !name) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    try {
        await fetchAPI('/data/districts', {
            method: 'POST',
            body: JSON.stringify({ state_id: parseInt(stateId), name })
        });
        
        showToast('District added successfully!', 'success');
        document.getElementById('newDistrictName').value = '';
        loadDistricts();
    } catch (error) {
        showToast('Failed to add district', 'error');
    }
}

async function addGroundwaterData() {
    const form = document.getElementById('groundwaterForm');
    const formData = new FormData(form);
    
    const data = {};
    for (let [key, value] of formData.entries()) {
        if (value) {
            data[key] = parseFloat(value) || value;
        }
    }
    
    if (!data.district_id || !data.assessment_year || !data.total_annual_recharge || !data.total_extraction) {
        showToast('Please fill in required fields', 'error');
        return;
    }
    
    try {
        await fetchAPI('/data/groundwater', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        showToast('Groundwater data added successfully!', 'success');
        form.reset();
    } catch (error) {
        showToast('Failed to add groundwater data', 'error');
    }
}

// ============== Initialization ==============

function initializeApp() {
    // Load initial data
    loadStates();
    loadDistricts();
    loadSummary(2022);
    loadVisitorCount();
    
    // Set up event listeners
    
    // Tab navigation
    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Filters
    if (elements.filterState) {
        elements.filterState.addEventListener('change', handleFilterChange);
    }
    if (elements.filterDistrict) {
        elements.filterDistrict.addEventListener('change', handleFilterChange);
    }
    if (elements.filterYear) {
        elements.filterYear.addEventListener('change', handleFilterChange);
    }
    if (elements.filterCategory) {
        elements.filterCategory.addEventListener('change', handleFilterChange);
    }
    
    // Search with debounce
    if (elements.searchInput) {
        let searchTimeout;
        elements.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(handleSearch, 500);
        });
    }
    
    // Chat
    if (elements.chatSendBtn) {
        elements.chatSendBtn.addEventListener('click', sendChatMessage);
    }
    if (elements.chatInput) {
        elements.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    // Modal close
    if (elements.modalClose) {
        elements.modalClose.addEventListener('click', hideModal);
    }
    if (elements.modal) {
        elements.modal.addEventListener('click', (e) => {
            if (e.target === elements.modal) {
                hideModal();
            }
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal();
        }
    });
    
    // Initial chat message
    if (elements.chatMessages) {
        addChatMessage(`🇮🇳 **Welcome to IN-GRES - India Groundwater Resource Estimation System!**

I can help you with:
• **India Overview** - National groundwater statistics
• **GEC-2015 Methodology** - Assessment methodology explanation
• **Category Distribution** - Safe/Critical/Over-exploited areas
• **State Reports** - State-specific groundwater data

How can I assist you today?`, 'assistant');
    }
}

// Make functions globally available
window.changePage = changePage;
window.showStateReport = showStateReport;
window.showDistrictReport = showDistrictReport;
window.handleQuickAction = handleQuickAction;
window.addState = addState;
window.addDistrict = addDistrict;
window.addGroundwaterData = addGroundwaterData;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', initializeApp);
