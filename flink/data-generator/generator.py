#!/usr/bin/env python3
"""
Streaming Event Generator for Flink POC
Generates synthetic events via TCP socket on port 9999
"""

import socket
import json
import time
import random
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Configuration
HOST = '0.0.0.0'
PORT = 9999
EVENTS_PER_SECOND = int(os.getenv('EVENTS_PER_SECOND', 100))

# Event types and their probabilities
EVENT_TYPES = {
    'page_view': 0.40,
    'click': 0.30,
    'purchase': 0.15,
    'search': 0.10,
    'cart_add': 0.05,
}

# Sample data for realistic events
PAGES = ['/home', '/products', '/about', '/contact', '/checkout', '/cart', '/product/123', '/product/456']
PRODUCTS = ['laptop', 'phone', 'tablet', 'headphones', 'keyboard', 'mouse', 'monitor', 'camera']
SEARCH_TERMS = ['laptop deals', 'best phone', 'gaming keyboard', 'wireless mouse', '4k monitor']
USERS = [f'user_{i}' for i in range(1, 101)]  # 100 unique users


def generate_event() -> Dict[str, Any]:
    """Generate a single synthetic event"""
    
    # Select event type based on probability
    event_type = random.choices(
        list(EVENT_TYPES.keys()),
        weights=list(EVENT_TYPES.values())
    )[0]
    
    # Base event structure
    event = {
        'event_id': f'evt_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}',
        'event_type': event_type,
        'user_id': random.choice(USERS),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_id': f'session_{random.randint(1, 1000)}',
    }
    
    # Add event-specific fields
    if event_type == 'page_view':
        event.update({
            'page': random.choice(PAGES),
            'referrer': random.choice(['google', 'direct', 'facebook', 'twitter', None]),
            'duration_seconds': random.randint(5, 300),
        })
    
    elif event_type == 'click':
        event.update({
            'element_id': f'btn_{random.choice(["buy", "add_cart", "learn_more", "subscribe"])}',
            'page': random.choice(PAGES),
            'x_position': random.randint(0, 1920),
            'y_position': random.randint(0, 1080),
        })
    
    elif event_type == 'purchase':
        event.update({
            'product': random.choice(PRODUCTS),
            'amount': round(random.uniform(10.0, 999.99), 2),
            'currency': 'USD',
            'quantity': random.randint(1, 5),
        })
    
    elif event_type == 'search':
        event.update({
            'query': random.choice(SEARCH_TERMS),
            'results_count': random.randint(0, 100),
        })
    
    elif event_type == 'cart_add':
        event.update({
            'product': random.choice(PRODUCTS),
            'quantity': random.randint(1, 3),
            'price': round(random.uniform(10.0, 999.99), 2),
        })
    
    return event


def main():
    """Main server loop"""
    print(f"Starting event generator on {HOST}:{PORT}")
    print(f"Target rate: {EVENTS_PER_SECOND} events/second")
    
    # Create server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(f"Socket server listening on port {PORT}")
    print("Waiting for Flink to connect...")
    
    while True:
        try:
            # Accept connection
            conn, addr = server.accept()
            print(f"✓ Connection established from {addr}")
            
            # Send events
            event_count = 0
            start_time = time.time()
            
            while True:
                try:
                    # Generate event
                    event = generate_event()
                    
                    # Send as JSON with newline delimiter
                    message = json.dumps(event) + '\n'
                    conn.sendall(message.encode('utf-8'))
                    
                    event_count += 1
                    
                    # Log progress every 1000 events
                    if event_count % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = event_count / elapsed if elapsed > 0 else 0
                        print(f"Sent {event_count} events | Rate: {rate:.1f} events/sec")
                    
                    # Rate limiting
                    time.sleep(1.0 / EVENTS_PER_SECOND)
                    
                except BrokenPipeError:
                    print("✗ Connection lost (broken pipe)")
                    break
                except ConnectionResetError:
                    print("✗ Connection reset by peer")
                    break
                except Exception as e:
                    print(f"✗ Error sending event: {e}")
                    break
            
            conn.close()
            print("Connection closed. Waiting for new connection...")
            
        except KeyboardInterrupt:
            print("\n✓ Shutting down gracefully...")
            break
        except Exception as e:
            print(f"✗ Server error: {e}")
            time.sleep(5)  # Wait before retry
    
    server.close()
    print("Server stopped.")


if __name__ == '__main__':
    main()
