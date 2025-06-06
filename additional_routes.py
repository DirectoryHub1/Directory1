from flask import Blueprint, render_template, jsonify, request
from .chart_data import get_chart_data_api

# Create a blueprint for the new routes
additional_routes = Blueprint('additional_routes', __name__)

@additional_routes.route('/documents')
def documents():
    """Route for the Documents page"""
    # In a real implementation, this would fetch document data from the database
    # For now, we'll just render the template with sample data
    tools = [
        {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
        {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
        {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
        {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
        {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
    ]
    return render_template('documents.html', tools=tools)

@additional_routes.route('/promotional_texts')
def promotional_texts():
    """Route for the Promotional Texts page"""
    # In a real implementation, this would fetch promotional text data from the database
    # For now, we'll just render the template with sample data
    tools = [
        {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
        {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
        {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
        {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
        {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
    ]
    return render_template('promotional_texts.html', tools=tools)

@additional_routes.route('/settings')
def settings():
    """Route for the Settings page"""
    # In a real implementation, this would fetch settings data from the database
    # For now, we'll just render the template with sample data
    tools = [
        {'name': 'Email Marketing', 'url': 'https://www.ymlp.com', 'icon': 'envelope'},
        {'name': 'Postal Mail Service', 'url': 'https://www.postalmethods.com', 'icon': 'mail-bulk'},
        {'name': 'Label Templates', 'url': 'https://www.avery.com/templates', 'icon': 'tag'},
        {'name': 'Mass Calls & Texting', 'url': 'https://www.dialmycalls.com', 'icon': 'phone'},
        {'name': 'Promotional Texts', 'url': '/promotional_texts', 'icon': 'bullhorn'}
    ]
    return render_template('settings.html', tools=tools)

@additional_routes.route('/api/chart-data')
def chart_data():
    """API endpoint for chart data"""
    return get_chart_data_api()
