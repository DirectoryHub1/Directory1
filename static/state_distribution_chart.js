// Enhanced Chart.js implementation for Business Distribution by State
document.addEventListener('DOMContentLoaded', function() {
    // Check if the chart container exists
    const chartContainer = document.getElementById('state-distribution-chart');
    if (!chartContainer) return;
    
    // Chart configuration
    let stateChart = null;
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'Business Distribution by State',
                font: {
                    size: 16,
                    weight: 'bold'
                },
                color: '#1e5799'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.parsed.y} businesses`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of Businesses',
                    font: {
                        weight: 'bold'
                    }
                },
                grid: {
                    color: 'rgba(200, 200, 200, 0.2)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'State',
                    font: {
                        weight: 'bold'
                    }
                },
                grid: {
                    display: false
                }
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        },
        hover: {
            animationDuration: 200
        }
    };
    
    // Load real data from API
    function loadChartData(businessType = null) {
        // Show loading indicator
        chartContainer.classList.add('loading');
        
        // Determine API endpoint based on whether a business type is specified
        const endpoint = businessType 
            ? `/data/state-distribution/${encodeURIComponent(businessType)}`
            : '/data/state-distribution';
        
        // Fetch data from API
        fetch(endpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Remove loading indicator
                chartContainer.classList.remove('loading');
                
                // Create or update chart
                if (stateChart) {
                    stateChart.data = data;
                    stateChart.update();
                } else {
                    const ctx = chartContainer.getContext('2d');
                    stateChart = new Chart(ctx, {
                        type: 'bar',
                        data: data,
                        options: chartOptions
                    });
                }
                
                // Update filter options if needed
                updateFilterOptions(data.labels);
            })
            .catch(error => {
                console.error('Error fetching chart data:', error);
                chartContainer.classList.remove('loading');
                
                // If API fails, try to load sample data
                loadSampleData();
            });
    }
    
    // Fallback to sample data if API fails
    function loadSampleData() {
        fetch('/data/sample-state-distribution')
            .then(response => response.json())
            .then(data => {
                const ctx = chartContainer.getContext('2d');
                stateChart = new Chart(ctx, {
                    type: 'bar',
                    data: data,
                    options: chartOptions
                });
                
                // Add a note that this is sample data
                const sampleDataNote = document.createElement('div');
                sampleDataNote.className = 'alert alert-warning mt-2';
                sampleDataNote.textContent = 'Note: Displaying sample data. Real data could not be loaded.';
                chartContainer.parentNode.insertBefore(sampleDataNote, chartContainer.nextSibling);
            })
            .catch(error => {
                console.error('Error loading sample data:', error);
                chartContainer.innerHTML = '<div class="alert alert-danger">Failed to load chart data</div>';
            });
    }
    
    // Update filter options based on available data
    function updateFilterOptions(labels) {
        const filterSelect = document.getElementById('state-chart-filter');
        if (!filterSelect) return;
        
        // Clear existing options except the default ones
        while (filterSelect.options.length > 3) { // Keep 'all', 'top5', 'bottom5'
            filterSelect.remove(3);
        }
        
        // Add individual state options
        labels.forEach(state => {
            const option = document.createElement('option');
            option.value = `state_${state}`;
            option.textContent = state;
            filterSelect.appendChild(option);
        });
    }
    
    // Add filter functionality
    const filterSelect = document.getElementById('state-chart-filter');
    const businessTypeSelect = document.getElementById('business-type-filter');
    
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const value = this.value;
            
            if (value === 'all' || value === 'top5' || value === 'bottom5') {
                // These are handled client-side with the full dataset
                const businessType = businessTypeSelect ? businessTypeSelect.value : null;
                loadChartData(businessType === 'all' ? null : businessType);
                
                // After data is loaded, apply the filter
                setTimeout(() => {
                    if (!stateChart) return;
                    
                    const originalData = {...stateChart.data};
                    
                    if (value === 'top5') {
                        // Get indices of top 5 values
                        const indices = [...originalData.datasets[0].data]
                            .map((val, idx) => ({val, idx}))
                            .sort((a, b) => b.val - a.val)
                            .slice(0, 5)
                            .map(item => item.idx);
                        
                        // Filter data to only include top 5
                        stateChart.data.labels = indices.map(i => originalData.labels[i]);
                        stateChart.data.datasets[0].data = indices.map(i => originalData.datasets[0].data[i]);
                        stateChart.data.datasets[0].backgroundColor = indices.map(i => originalData.datasets[0].backgroundColor[i]);
                        stateChart.data.datasets[0].borderColor = indices.map(i => originalData.datasets[0].borderColor[i]);
                    } else if (value === 'bottom5') {
                        // Get indices of bottom 5 values
                        const indices = [...originalData.datasets[0].data]
                            .map((val, idx) => ({val, idx}))
                            .sort((a, b) => a.val - b.val)
                            .slice(0, 5)
                            .map(item => item.idx);
                        
                        // Filter data to only include bottom 5
                        stateChart.data.labels = indices.map(i => originalData.labels[i]);
                        stateChart.data.datasets[0].data = indices.map(i => originalData.datasets[0].data[i]);
                        stateChart.data.datasets[0].backgroundColor = indices.map(i => originalData.datasets[0].backgroundColor[i]);
                        stateChart.data.datasets[0].borderColor = indices.map(i => originalData.datasets[0].borderColor[i]);
                    }
                    
                    stateChart.update();
                }, 100);
            } else if (value.startsWith('state_')) {
                // Filter to show only a specific state
                const state = value.substring(6); // Remove 'state_' prefix
                const index = stateChart.data.labels.indexOf(state);
                
                if (index !== -1) {
                    const originalData = {...stateChart.data};
                    
                    stateChart.data.labels = [originalData.labels[index]];
                    stateChart.data.datasets[0].data = [originalData.datasets[0].data[index]];
                    stateChart.data.datasets[0].backgroundColor = [originalData.datasets[0].backgroundColor[index]];
                    stateChart.data.datasets[0].borderColor = [originalData.datasets[0].borderColor[index]];
                    
                    stateChart.update();
                }
            }
        });
    }
    
    // Add business type filter functionality
    if (businessTypeSelect) {
        businessTypeSelect.addEventListener('change', function() {
            const businessType = this.value === 'all' ? null : this.value;
            
            // Reset state filter when changing business type
            if (filterSelect) {
                filterSelect.value = 'all';
            }
            
            loadChartData(businessType);
        });
    }
    
    // Add chart type toggle functionality
    const chartTypeToggle = document.getElementById('chart-type-toggle');
    if (chartTypeToggle) {
        chartTypeToggle.addEventListener('change', function() {
            if (!stateChart) return;
            
            const chartType = this.checked ? 'bar' : 'pie';
            stateChart.config.type = chartType;
            
            // Adjust options based on chart type
            if (chartType === 'pie') {
                stateChart.options.plugins.legend.display = true;
                stateChart.options.scales.x.display = false;
                stateChart.options.scales.y.display = false;
            } else {
                stateChart.options.plugins.legend.display = false;
                stateChart.options.scales.x.display = true;
                stateChart.options.scales.y.display = true;
            }
            
            stateChart.update();
        });
    }
    
    // Initial data load
    loadChartData();
    
    // Add export functionality
    const exportButton = document.getElementById('export-chart-button');
    if (exportButton && chartContainer) {
        exportButton.addEventListener('click', function() {
            if (!stateChart) return;
            
            // Create a temporary link element
            const link = document.createElement('a');
            link.download = 'business_distribution_by_state.png';
            
            // Convert chart to image
            link.href = chartContainer.toDataURL('image/png');
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
});
