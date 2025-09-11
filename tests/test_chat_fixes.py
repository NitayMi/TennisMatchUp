#!/usr/bin/env python
"""
Chat System End-to-End Test Script
Tests all critical endpoints and functionality after patches
"""
from app import create_app
from services.chat_service import ChatService

def test_api_endpoints():
    """Test API endpoints are accessible"""
    app = create_app()
    
    with app.test_client() as client:
        print("Testing API endpoints...")
        
        # Test unread counts endpoint (should require auth -> 302 redirect)
        response = client.get('/chat/api/unread-counts')
        print(f"  /chat/api/unread-counts: {response.status_code} (expected: 302)")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        
        # Test available users endpoint (should require auth -> 302 redirect)
        response = client.get('/api/users/available-for-chat')
        print(f"  /api/users/available-for-chat: {response.status_code} (expected: 302)")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        
        # Test conversation creation endpoint (should require auth -> 302 redirect)
        response = client.post('/chat/api/create-conversation', json={'recipient_id': 1, 'first_message': 'test'})
        print(f"  /chat/api/create-conversation: {response.status_code} (expected: 302)")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        
        print("✅ All API endpoints are accessible and properly protected")

def test_legacy_redirects():
    """Test legacy routes redirect to new system"""
    app = create_app()
    
    with app.test_client() as client:
        print("Testing legacy redirects...")
        
        # Test messaging inbox redirect
        response = client.get('/messaging/inbox')
        print(f"  /messaging/inbox: {response.status_code} (expected: 302)")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        
        # Test player messages redirect
        response = client.get('/player/messages')
        print(f"  /player/messages: {response.status_code} (expected: 302)")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        
        print("✅ Legacy routes properly redirect to new system")

def test_chat_service():
    """Test ChatService functionality"""
    app = create_app()
    
    with app.app_context():
        print("Testing ChatService...")
        
        # Test get_user_conversations
        try:
            conversations = ChatService.get_user_conversations(1)
            print(f"  ChatService.get_user_conversations(1): {len(conversations)} conversations")
            assert isinstance(conversations, list), "Expected list of conversations"
        except Exception as e:
            print(f"  ❌ ChatService.get_user_conversations failed: {e}")
            raise
        
        # Test conversation creation
        try:
            result = ChatService.get_or_create_direct_conversation(1, 2)
            print(f"  ChatService.get_or_create_direct_conversation(1, 2): {result['success']}")
            assert result['success'], f"Expected success, got {result}"
        except Exception as e:
            print(f"  ❌ ChatService.get_or_create_direct_conversation failed: {e}")
            raise
        
        print("✅ ChatService working correctly")

def test_route_registration():
    """Test route registration"""
    app = create_app()
    
    chat_routes = [str(rule) for rule in app.url_map.iter_rules() if '/chat' in str(rule)]
    messaging_routes = [str(rule) for rule in app.url_map.iter_rules() if '/messaging' in str(rule)]
    
    print(f"Chat routes registered: {len(chat_routes)}")
    print(f"Messaging routes registered: {len(messaging_routes)}")
    
    # Check critical routes exist
    critical_routes = [
        '/chat/conversations',
        '/chat/api/unread-counts',
        '/chat/api/create-conversation',
        '/messaging/inbox'
    ]
    
    all_routes = [str(rule) for rule in app.url_map.iter_rules()]
    
    for route in critical_routes:
        if route not in all_routes:
            print(f"❌ Missing critical route: {route}")
            raise AssertionError(f"Missing route: {route}")
        else:
            print(f"  ✅ {route}")
    
    print("✅ All critical routes registered")

def test_database_schema():
    """Test database schema is correct"""
    app = create_app()
    
    with app.app_context():
        print("Testing database schema...")
        
        # Test message columns exist
        from models.message import Message
        columns = [col.name for col in Message.__table__.columns]
        
        required_columns = [
            'conversation_id', 'reply_to_message_id', 'is_edited', 
            'edited_at', 'is_deleted', 'deleted_at'
        ]
        
        for col in required_columns:
            if col not in columns:
                print(f"❌ Missing column in messages: {col}")
                raise AssertionError(f"Missing column: {col}")
            else:
                print(f"  ✅ messages.{col}")
        
        # Test conversations table exists
        from models.conversation import Conversation
        try:
            count = Conversation.query.count()
            print(f"  ✅ conversations table: {count} records")
        except Exception as e:
            print(f"❌ Conversations table issue: {e}")
            raise
        
        print("✅ Database schema is correct")

def main():
    """Run all tests"""
    print("🎾 TennisMatchUp Chat System - End-to-End Test")
    print("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Route Registration", test_route_registration), 
        ("API Endpoints", test_api_endpoints),
        ("Legacy Redirects", test_legacy_redirects),
        ("ChatService", test_chat_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Chat system is ready!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please fix issues")
        return 1

if __name__ == "__main__":
    exit(main())