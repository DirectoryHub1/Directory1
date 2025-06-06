// Chart.js implementation for Directory Hub

// Global chart variables
let businessDistributionChart;
let currentChartType = 'bar';
let currentBusinessData = null;

// Initialize charts
function initCharts() {
    // Initialize business distribution chart
    initBusinessDistributionChart();
}

// Initialize business distribution chart
function initBusinessDistributionChart() {
    const ctx = document.getElementById('businessDistributionChart');
    
    if (!ctx) return;
    
    // Get business data from API or use mock data
    getBusinessDistributionData()
        .then(data => {
            currentBusinessData = data;
            
            // Create chart
            businessDistributionChart = new Chart(ctx, {
                type: currentChartType,
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Number of Businesses',
                        data: data.values,
                        backgroundColor: [
                            'rgba(78, 115, 223, 0.8)',
                            'rgba(28, 200, 138, 0.8)',
                            'rgba(54, 185, 204, 0.8)',
                            'rgba(246, 194, 62, 0.8)',
                            'rgba(231, 74, 59, 0.8)',
                            'rgba(133, 135, 150, 0.8)',
                            'rgba(105, 153, 255, 0.8)',
                            'rgba(78, 115, 223, 0.5)',
                            'rgba(28, 200, 138, 0.5)',
                            'rgba(54, 185, 204, 0.5)'
                        ],
                        borderColor: [
                            'rgba(78, 115, 223, 1)',
                            'rgba(28, 200, 138, 1)',
                            'rgba(54, 185, 204, 1)',
                            'rgba(246, 194, 62, 1)',
                            'rgba(231, 74, 59, 1)',
                            'rgba(133, 135, 150, 1)',
                            'rgba(105, 153, 255, 1)',
                            'rgba(78, 115, 223, 0.8)',
                            'rgba(28, 200, 138, 0.8)',
                            'rgba(54, 185, 204, 0.8)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    responsive: true,
                    plugins: {
                        legend: {
                            display: currentChartType === 'pie',
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'Business Distribution by State'
                        }
                    },
                    scales: {
                        y: {
                            display: currentChartType !== 'pie',
                            beginAtZero: true,
                            grid: {
                                color: "rgba(0, 0, 0, 0.05)"
                            }
                        },
                        x: {
                            display: currentChartType !== 'pie',
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            // Display error message in chart area
            document.querySelector('.chart-area').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> 
                    Error loading chart data. Please try again later.
                </div>
            `;
        });
}

// Get business distribution data from API or mock data
async function getBusinessDistributionData() {
    // In a real app, this would be an API call to the Flask backend
    // Try to fetch from API first
    try {
        const response = await fetchWithTimeout('/api/chart-data', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }, 2000); // 2 second timeout
        
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('API fetch failed, using mock data:', error);
    }
    
    // Fallback to mock data if API call fails
    return {
        labels: ['Texas', 'Florida', 'California', 'New York', 'Illinois', 'Georgia', 'Ohio', 'Pennsylvania', 'Michigan', 'North Carolina'],
        values: [28, 24, 22, 17, 14, 12, 10, 9, 8, 8],
        businessTypes: {
            'all': {
                labels: ['Texas', 'Florida', 'California', 'New York', 'Illinois', 'Georgia', 'Ohio', 'Pennsylvania', 'Michigan', 'North Carolina'],
                values: [28, 24, 22, 17, 14, 12, 10, 9, 8, 8]
            },
            'vehicle': {
                labels: ['Texas', 'California', 'Florida', 'Ohio', 'Michigan', 'Illinois', 'Georgia', 'Pennsylvania', 'New York', 'Tennessee'],
                values: [12, 9, 8, 5, 4, 3, 3, 2, 1, 1]
            },
            'realestate': {
                labels: ['Florida', 'California', 'New York', 'Texas', 'Illinois', 'Georgia', 'North Carolina', 'Arizona', 'Washington', 'Colorado'],
                values: [14, 12, 10, 8, 6, 5, 4, 3, 1, 1]
            },
            'apartment': {
                labels: ['New York', 'California', 'Texas', 'Florida', 'Illinois', 'Georgia', 'Massachusetts', 'Washington', 'Colorado', 'Oregon'],
                values: [9, 8, 7, 5, 4, 3, 1, 1, 1, 1]
            }
        }
    };
}

// Update chart type (bar or pie)
function updateChartType(chartType) {
    if (!businessDistributionChart || currentChartType === chartType) return;
    
    currentChartType = chartType;
    
    // Destroy existing chart
    businessDistributionChart.destroy();
    
    // Reinitialize with new type
    initBusinessDistributionChart();
}

// Filter business data by type
function filterBusinessData(businessType) {
    if (!businessDistributionChart || !currentBusinessData) return;
    
    let filteredData;
    
    if (businessType === 'all') {
        filteredData = {
            labels: currentBusinessData.labels,
            values: currentBusinessData.values
        };
    } else {
        filteredData = currentBusinessData.businessTypes[businessType];
    }
    
    // Update chart data
    businessDistributionChart.data.labels = filteredData.labels;
    businessDistributionChart.data.datasets[0].data = filteredData.values;
    businessDistributionChart.update();
    
    // Log activity
    logActivity(`Filtered business chart by ${getBusinessTypeDisplay(businessType)}`, 'business');
}

// Get display text for business type
function getBusinessTypeDisplay(type) {
    switch (type) {
        case 'vehicle':
            return 'Vehicle Dealerships';
        case 'realestate':
            return 'Real Estate Professionals';
        case 'apartment':
            return 'Apartment Rentals';
        default:
            return 'All Business Types';
    }
}

// Download chart as image
function downloadChart() {
    if (!businessDistributionChart) return;
    
    // Create a temporary link
    const link = document.createElement('a');
    link.download = 'business-distribution-chart.png';
    link.href = businessDistributionChart.toBase64Image();
    link.click();
    
    // Log activity
    logActivity('Downloaded business distribution chart', 'document');
}

// Fetch with timeout utility
async function fetchWithTimeout(resource, options = {}, timeout = 8000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(resource, {
        ...options,
        signal: controller.signal
    });
    
    clearTimeout(id);
    
    return response;
}
