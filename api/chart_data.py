from flask import jsonify, request

def get_chart_data_api():
    """API endpoint to provide business distribution data for charts"""
    business_type = request.args.get('type', 'all')
    
    # In a real implementation, this would query the database
    # For now, we'll return sample data that matches what's expected in the frontend
    
    # Sample data for different business types
    if business_type == 'vehicle_dealership':
        return jsonify({
            'labels': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Ohio', 'Pennsylvania', 'Michigan', 'Georgia', 'North Carolina'],
            'data': [8, 7, 6, 5, 4, 4, 3, 3, 2, 2]
        })
    elif business_type == 'real_estate':
        return jsonify({
            'labels': ['Florida', 'California', 'Texas', 'New York', 'Arizona', 'Colorado', 'Washington', 'Nevada', 'North Carolina', 'Georgia'],
            'data': [12, 10, 9, 7, 5, 4, 4, 3, 3, 2]
        })
    elif business_type == 'apartment_rental':
        return jsonify({
            'labels': ['New York', 'California', 'Texas', 'Florida', 'Illinois', 'Georgia', 'Massachusetts', 'Washington', 'Colorado', 'Arizona'],
            'data': [9, 8, 6, 5, 3, 2, 2, 2, 1, 1]
        })
    else:  # all business types
        return jsonify({
            'labels': ['California', 'Texas', 'Florida', 'New York', 'Illinois', 'Ohio', 'Pennsylvania', 'Georgia', 'North Carolina', 'Michigan'],
            'data': [25, 22, 20, 18, 12, 10, 9, 8, 7, 6]
        })
