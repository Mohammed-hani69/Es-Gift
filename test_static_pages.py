#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import url_for
from app import create_app

def test_static_pages_routes():
    app = create_app()
    
    with app.app_context():
        try:
            # Test static pages route
            url = url_for('static_pages.static_pages')
            print(f"✅ static_pages.static_pages URL: {url}")
        except Exception as e:
            print(f"❌ Error generating static_pages.static_pages URL: {e}")
            
        # List all routes containing 'static'
        print("\n📋 All routes containing 'static':")
        for rule in app.url_map.iter_rules():
            if 'static' in str(rule):
                print(f"  - {rule.endpoint}: {rule}")

if __name__ == '__main__':
    test_static_pages_routes()
